from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0


SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data" / "kaggle_arecanut_candidate"
CHECKPOINT_PATH = DATA_DIR / "model_candidate_efficientnet_b0.pth"
CONFLICTS_PATH = SCRIPT_DIR / "tests" / "results" / "label_conflicts.csv"
RESULT_PATH = DATA_DIR / "external_local_screening.json"
CLASS_NAMES = ["Healthy", "FruitRot", "StemBleeding", "PhytoplasmaYellowLeaf"]
LOCAL_CLASS_FOLDERS = {
    "areca_healthy": "Healthy",
    "areca_diseased_fungal_fruit_rot": "FruitRot",
}
DASH_THRESHOLD = 6


def difference_hash(path: Path) -> int:
    with Image.open(path) as image:
        pixels = np.asarray(
            image.convert("L").resize((9, 8), Image.Resampling.LANCZOS),
            dtype=np.int16,
        )
    value = 0
    for bit in (pixels[:, 1:] > pixels[:, :-1]).ravel():
        value = (value << 1) | int(bit)
    return value


def load_unresolved_conflicts(path: Path) -> set[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        rows = csv.DictReader(source)
        return {
            row.get("file", "").strip().casefold()
            for row in rows
            if row.get("file", "").strip()
            and not row.get("resolved_label", "").strip()
        }


def candidate_hashes(manifest: dict) -> list[int]:
    hashes = []
    for record in manifest["records"]:
        if not record.get("training_eligible", False):
            continue
        hashes.append(difference_hash(DATA_DIR / record["local_path"]))
    return hashes


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Screen the candidate on independent local Healthy/Fruit Rot photos."
    )
    parser.add_argument("--dataset-root", type=Path, default=Path(r"D:\dataset"))
    parser.add_argument("--checkpoint", type=Path, default=CHECKPOINT_PATH)
    parser.add_argument("--conflicts-csv", type=Path, default=CONFLICTS_PATH)
    parser.add_argument("--output", type=Path, default=RESULT_PATH)
    args = parser.parse_args()

    for required in (args.checkpoint, args.conflicts_csv):
        if not required.is_file():
            parser.error(f"Required file not found: {required}")
    if not args.dataset_root.is_dir():
        parser.error(f"Dataset root not found: {args.dataset_root}")

    manifest_path = DATA_DIR / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    unresolved = load_unresolved_conflicts(args.conflicts_csv)
    training_hashes = candidate_hashes(manifest)
    samples = []
    excluded = Counter()

    for folder_name, class_name in LOCAL_CLASS_FOLDERS.items():
        class_dir = args.dataset_root / folder_name
        if not class_dir.is_dir():
            continue
        for path in sorted(class_dir.iterdir()):
            if not path.is_file() or path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
                continue
            if path.name.casefold() in unresolved:
                excluded["unresolved_label_conflict"] += 1
                continue
            try:
                digest = difference_hash(path)
            except Exception:
                excluded["unreadable_image"] += 1
                continue
            if min((digest ^ value).bit_count() for value in training_hashes) <= DASH_THRESHOLD:
                excluded["perceptual_overlap_with_candidate_training"] += 1
                continue
            samples.append({"path": path, "class_name": class_name, "dhash": digest})

    kept = []
    for index, sample in enumerate(samples):
        is_duplicate = any(
            (sample["dhash"] ^ other["dhash"]).bit_count() <= DASH_THRESHOLD
            for other_index, other in enumerate(samples)
            if other_index != index
        )
        if is_duplicate:
            excluded["perceptual_duplicate_in_external_set"] += 1
        else:
            kept.append(sample)

    if not kept:
        raise RuntimeError("No conflict-free, perceptually independent local images remain.")

    checkpoint = torch.load(args.checkpoint, map_location="cpu", weights_only=True)
    if checkpoint.get("classes") != CLASS_NAMES:
        raise RuntimeError(f"Unexpected candidate class order: {checkpoint.get('classes')}")
    model = efficientnet_b0(weights=None)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(CLASS_NAMES))
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.eval()
    transform = EfficientNet_B0_Weights.DEFAULT.transforms()

    observations = []
    with torch.inference_mode():
        for sample in kept:
            with Image.open(sample["path"]) as image:
                tensor = transform(image.convert("RGB")).unsqueeze(0)
            probabilities = model(tensor).softmax(dim=1)[0].tolist()
            predicted_index = int(np.argmax(probabilities))
            observations.append({
                "file": sample["path"].name,
                "true_class": sample["class_name"],
                "predicted_class": CLASS_NAMES[predicted_index],
                "top_score": float(probabilities[predicted_index]),
                "correct": CLASS_NAMES[predicted_index] == sample["class_name"],
                "probabilities": {
                    name: float(probabilities[index])
                    for index, name in enumerate(CLASS_NAMES)
                },
            })

    true_counts = Counter(item["true_class"] for item in observations)
    correct_counts = Counter(
        item["true_class"] for item in observations if item["correct"]
    )
    prediction_counts = Counter(item["predicted_class"] for item in observations)
    class_recall = {
        class_name: {
            "correct": correct_counts[class_name],
            "support": true_counts[class_name],
            "recall": correct_counts[class_name] / true_counts[class_name],
        }
        for class_name in sorted(true_counts)
    }
    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_checkpoint": str(args.checkpoint),
        "dataset_root": str(args.dataset_root),
        "candidate_training_dataset": manifest["dataset"],
        "external_ground_truth_classes": sorted(true_counts),
        "images_evaluated": len(observations),
        "accuracy": sum(item["correct"] for item in observations) / len(observations),
        "class_recall": class_recall,
        "prediction_counts": dict(prediction_counts),
        "excluded_counts": dict(excluded),
        "unavailable_external_classes": ["StemBleeding", "PhytoplasmaYellowLeaf", "LeafSpotComplex"],
        "limitations": [
            "This is a screening check on local internet-derived photos, not a clinical or deployment validation.",
            "Unresolved label-conflict rows and dHash-near duplicates were excluded.",
            "Stem Bleeding and Phytoplasma Yellow Leaf have no independent local raw test images.",
            "Leaf Spot is not a candidate output and remains unsupported.",
            "The Kaggle candidate is licensed CC BY-NC-SA 4.0 and is research-only/non-commercial.",
        ],
        "observations": observations,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Evaluated {len(observations)} images; accuracy={report['accuracy']:.3f}")
    print("Class recall:", class_recall)
    print("Excluded:", dict(excluded))
    print(f"Saved screening report: {args.output}")


if __name__ == "__main__":
    main()