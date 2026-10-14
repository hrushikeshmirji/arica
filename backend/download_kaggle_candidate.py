from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import requests
from PIL import Image


DATASET_REF = "sumanthsadiga/arecanut-plant-disease-dataset"
DATASET_PAGE = f"https://www.kaggle.com/datasets/{DATASET_REF}"
API_BASE = f"https://www.kaggle.com/api/v1/datasets"
OUTPUT_DIR = Path(__file__).resolve().parent / "data" / "kaggle_arecanut_candidate"
LICENSE = "CC BY-NC-SA 4.0"
LICENSE_URL = "https://creativecommons.org/licenses/by-nc-sa/4.0/"
CLASS_IDS = {
    "2": "Healthy",
    "5": "FruitRot",
    "7": "StemBleeding",
    "8": "PhytoplasmaYellowLeaf",
}
PAGE_SIZE = 200
MAX_WORKERS = 4
UUID_SUFFIX = re.compile(
    r"_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}.*$",
    re.IGNORECASE,
)


def list_dataset_files() -> list[dict]:
    url = f"{API_BASE}/list/{DATASET_REF}"
    params: dict[str, str | int] = {"pageSize": PAGE_SIZE}
    files: list[dict] = []

    while True:
        response = requests.get(
            url,
            params=params,
            headers={"User-Agent": "ArecaVisionResearch/1.0"},
            timeout=60,
        )
        response.raise_for_status()
        page = response.json()
        files.extend(page.get("datasetFiles", []))
        token = page.get("nextPageTokenNullable")
        if not token:
            return files
        params = {"pageSize": PAGE_SIZE, "pageToken": token}


def source_key(filename: str) -> str:
    key = UUID_SUFFIX.sub("", filename)
    return re.sub(r"\s+- Copy(?=\.)", "", key, flags=re.IGNORECASE)


def select_source_images(files: list[dict]) -> list[dict]:
    grouped: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for item in files:
        name = item.get("name") or item.get("nameNullable", "")
        parts = name.split("/")
        if len(parts) != 4 or parts[0] != "dataset":
            continue
        split, class_id, filename = parts[1], parts[2], parts[3]
        if split not in {"train", "test"} or class_id not in CLASS_IDS:
            continue
        item = dict(item)
        item.update(
            class_name=CLASS_IDS[class_id],
            original_split=split,
            source_key=source_key(filename),
        )
        grouped[(class_id, item["source_key"])].append(item)

    selected = []
    for (_class_id, _source_key), variants in sorted(grouped.items()):
        representative = max(
            variants,
            key=lambda item: (
                int(item.get("totalBytes", 0)),
                item.get("name") or item.get("nameNullable", ""),
            ),
        )
        representative["source_variants"] = [
            {
                "path": item.get("name") or item.get("nameNullable", ""),
                "split": item["original_split"],
                "bytes": int(item.get("totalBytes", 0)),
            }
            for item in sorted(variants, key=lambda value: value["name"])
        ]
        selected.append(representative)
    return selected


def download_image(item: dict) -> dict:
    name = item.get("name") or item.get("nameNullable", "")
    class_dir = OUTPUT_DIR / "source_images" / item["class_name"]
    digest_name = hashlib.sha256(item["source_key"].encode("utf-8")).hexdigest()[:12]
    target = class_dir / f"{digest_name}.jpg"
    class_dir.mkdir(parents=True, exist_ok=True)

    if not target.exists():
        response = requests.get(
            f"{API_BASE}/download/{DATASET_REF}",
            params={"filename": name},
            headers={"User-Agent": "ArecaVisionResearch/1.0"},
            stream=True,
            timeout=(30, 180),
        )
        response.raise_for_status()
        temporary = target.with_suffix(".part")
        file_hash = hashlib.sha256()
        try:
            with temporary.open("wb") as output:
                for chunk in response.iter_content(chunk_size=1024 * 1024):
                    if chunk:
                        output.write(chunk)
                        file_hash.update(chunk)
            with Image.open(temporary) as image:
                image.verify()
            temporary.replace(target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise
        finally:
            response.close()
        sha256 = file_hash.hexdigest()
    else:
        with Image.open(target) as image:
            image.verify()
        sha256 = hashlib.sha256(target.read_bytes()).hexdigest()

    with Image.open(target) as image:
        width, height = image.size
        image_format = image.format
    return {
        "class_name": item["class_name"],
        "source_key": item["source_key"],
        "kaggle_path": name,
        "original_splits": sorted({v["split"] for v in item["source_variants"]}),
        "source_variants": item["source_variants"],
        "selected_source_bytes": int(item.get("totalBytes", 0)),
        "local_path": target.relative_to(OUTPUT_DIR).as_posix(),
        "sha256": sha256,
        "width": width,
        "height": height,
        "format": image_format,
    }


def write_manifest(records: list[dict], selected: list[dict]) -> None:
    hash_classes: dict[str, set[str]] = defaultdict(set)
    hash_records: dict[str, list[dict]] = defaultdict(list)
    for record in records:
        hash_classes[record["sha256"]].add(record["class_name"])
        hash_records[record["sha256"]].append(record)

    for digest, matching in hash_records.items():
        classes = hash_classes[digest]
        if len(classes) > 1:
            for record in matching:
                record["training_eligible"] = False
                record["exclusion_reason"] = "exact_hash_cross_class_conflict"
        elif len(matching) > 1:
            for duplicate in matching[1:]:
                duplicate["training_eligible"] = False
                duplicate["exclusion_reason"] = "exact_hash_duplicate_source"
        for record in matching:
            record.setdefault("training_eligible", True)

    counts: dict[str, dict[str, int]] = {}
    for class_name in CLASS_IDS.values():
        class_records = [record for record in records if record["class_name"] == class_name]
        counts[class_name] = {
            "source_groups": sum(1 for item in selected if item["class_name"] == class_name),
            "downloaded_images": len(class_records),
            "eligible_images": sum(record["training_eligible"] for record in class_records),
        }

    manifest = {
        "dataset": DATASET_REF,
        "dataset_url": DATASET_PAGE,
        "dataset_license": LICENSE,
        "license_url": LICENSE_URL,
        "attribution": "Sumanth S Adiga, Arecanut Plant Disease Dataset, Kaggle (2026)",
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "intended_use": "Research-only candidate; CC BY-NC-SA 4.0, non-commercial and share-alike terms apply.",
        "class_mapping": {
            "2": "Healthy Leaf -> Healthy",
            "5": "Male Koleroga -> FruitRot",
            "7": "Stem Bleeding -> StemBleeding",
            "8": "Yellow Leaf -> PhytoplasmaYellowLeaf",
        },
        "not_included": {
            "LeafSpotComplex": "No Leaf Spot class is present in this dataset.",
            "reason": "No unsupported class relabeling was performed.",
        },
        "split_policy": "Kaggle train/test source IDs overlap; all images are regrouped by source key before grouped validation splitting.",
        "counts": counts,
        "records": sorted(records, key=lambda record: (record["class_name"], record["source_key"])),
    }
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = OUTPUT_DIR / "manifest.json"
    temporary = manifest_path.with_suffix(".json.part")
    temporary.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    temporary.replace(manifest_path)


def main() -> int:
    parser = argparse.ArgumentParser(description="Download a research-only Kaggle Arecanut subset.")
    parser.add_argument("--dry-run", action="store_true", help="List selected source groups without downloading images.")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS)
    args = parser.parse_args()
    if args.workers < 1 or args.workers > 8:
        parser.error("--workers must be between 1 and 8")

    print(f"Reading public Kaggle manifest for {DATASET_REF}...")
    selected = select_source_images(list_dataset_files())
    if not selected:
        print("No matching image files found.", file=sys.stderr)
        return 1

    total_bytes = sum(int(item.get("totalBytes", 0)) for item in selected)
    for class_name in CLASS_IDS.values():
        class_items = [item for item in selected if item["class_name"] == class_name]
        print(
            f"{class_name}: {len(class_items)} source images, "
            f"{sum(int(item.get('totalBytes', 0)) for item in class_items) / 1_000_000:.1f} MB"
        )
    print(f"Selected {len(selected)} source groups ({total_bytes / 1_000_000:.1f} MB).")
    if args.dry_run:
        return 0

    records: list[dict] = []
    failures = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(download_image, item): item for item in selected}
        for index, future in enumerate(as_completed(futures), start=1):
            try:
                records.append(future.result())
            except Exception as error:
                item = futures[future]
                failures.append({
                    "path": item.get("name") or item.get("nameNullable", ""),
                    "error": str(error),
                })
            if index % 20 == 0 or index == len(selected):
                print(f"Processed {index}/{len(selected)} source images; failures={len(failures)}")

    write_manifest(records, selected)
    if failures:
        failure_path = OUTPUT_DIR / "download_failures.json"
        failure_path.write_text(json.dumps(failures, indent=2), encoding="utf-8")
        print(f"Download completed with {len(failures)} failures; see {failure_path}.", file=sys.stderr)
        return 1
    print(f"Downloaded and verified {len(records)} images. Manifest: {OUTPUT_DIR / 'manifest.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())