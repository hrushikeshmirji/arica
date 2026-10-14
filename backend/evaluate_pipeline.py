"""
evaluate_pipeline.py — Genuine end-to-end accuracy of the full CNN -> YOLO -> ViT
pipeline against a labeled test set.

This does NOT reuse any single model's own training-time metric (those only
measure that one stage in isolation). It runs the exact same chained
inference path server/app.py uses, on real held-out images, and compares
the pipeline's final predicted disease against the true label -- which is
the only way to get a number you can honestly call "overall accuracy."

Expected test set layout (same convention vit/dataset.py already uses):

    <test_dir>/
        Anthracnose/    *.jpg / *.png / ...
        BudBorer/
        FruitRot/
        Healthy/
        LeafSpotComplex/
        NutCracking/
        PhytoplasmaYellowLeaf/
        SootyMold/
        StemBleeding/
        StemCracking/
        YellowLeaf/

One subfolder per disease class, matching config.DISEASE_CLASSES. This
should NOT be the same images used to train or validate any of the three
models -- ask whoever built the dataset which split is the true held-out
test set (usually dataset/*/test/, separate from train/ and val/).

Usage (from inside project/, with the venv active):

    python evaluate_pipeline.py --test-dir path/to/test_set

Optional:
    --output results.csv     Save per-image predictions to a CSV
    --limit 200               Only evaluate the first N images (quick check)
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import config  # noqa: E402
from cnn.predict import CNNPredictor  # noqa: E402
from vit.predict import ViTPredictor  # noqa: E402
from yolo.detect import YOLODetector  # noqa: E402

_IMG_EXTS = {".bmp", ".jpeg", ".jpg", ".png", ".tif", ".tiff", ".webp"}


def run_pipeline(rgb: np.ndarray, cnn, yolo, vit) -> tuple[str, float, bool]:
    """Mirrors server/app.py's inference logic exactly.

    Returns (predicted_label, confidence, was_gated_out).
    was_gated_out=True means the CNN stage rejected the image as
    "Not_Arecanut" before disease classification even ran.
    """
    cnn_label, cnn_conf = cnn.predict(rgb)
    if cnn_label != "Arecanut":
        return "Not_Arecanut", cnn_conf, True

    detections, _ = yolo.detect(rgb)

    if not detections:
        vit_label, vit_conf, _ = vit.predict(rgb)
        return vit_label, vit_conf, False

    results = []
    for det in detections:
        vit_label, vit_conf, _ = vit.predict(det["crop"])
        results.append((vit_label, vit_conf))

    diseased = [r for r in results if r[0] != "Healthy"]
    top_label, top_conf = max(diseased, key=lambda r: r[1]) if diseased else max(results, key=lambda r: r[1])
    return top_label, top_conf, False


def load_test_set(test_dir: Path, limit: int | None) -> list[tuple[Path, str]]:
    samples: list[tuple[Path, str]] = []
    classes = sorted(d.name for d in test_dir.iterdir() if d.is_dir())
    if not classes:
        raise RuntimeError(
            f"No class subfolders found under {test_dir}. "
            f"Expected one folder per disease class, e.g. {test_dir}/Anthracnose/"
        )
    print(f"Found {len(classes)} class folders: {classes}")

    for cls in classes:
        for p in sorted((test_dir / cls).rglob("*")):
            if p.is_file() and p.suffix.lower() in _IMG_EXTS:
                samples.append((p, cls))

    if limit:
        samples = samples[:limit]
    return samples


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate the full ArecaVision pipeline on a labeled test set")
    parser.add_argument("--test-dir", required=True, help="Path to the held-out test set (folder-per-class)")
    parser.add_argument("--output", default="pipeline_eval_results.csv", help="Where to save per-image predictions")
    parser.add_argument("--limit", type=int, default=None, help="Only evaluate the first N images (quick check)")
    args = parser.parse_args()

    test_dir = Path(args.test_dir)
    if not test_dir.is_dir():
        raise FileNotFoundError(f"Test directory not found: {test_dir}")

    samples = load_test_set(test_dir, args.limit)
    print(f"Evaluating {len(samples)} images...\n")

    print("Loading models...")
    cnn = CNNPredictor()
    yolo = YOLODetector()
    vit = ViTPredictor()
    print("Models loaded.\n")

    correct = 0
    gated_out_count = 0
    per_class_total: Counter = Counter()
    per_class_correct: Counter = Counter()
    confusion: dict[str, Counter] = defaultdict(Counter)  # confusion[true_label][pred_label] += 1
    rows = []

    for i, (path, true_label) in enumerate(samples):
        try:
            pil_img = Image.open(path).convert("RGB")
            rgb = np.asarray(pil_img)
        except Exception as exc:
            print(f"  [skip] {path}: could not read image ({exc})")
            continue

        pred_label, pred_conf, was_gated = run_pipeline(rgb, cnn, yolo, vit)
        is_correct = pred_label == true_label

        per_class_total[true_label] += 1
        if is_correct:
            correct += 1
            per_class_correct[true_label] += 1
        if was_gated:
            gated_out_count += 1

        confusion[true_label][pred_label] += 1
        rows.append({
            "image": str(path),
            "true_label": true_label,
            "predicted_label": pred_label,
            "confidence": f"{pred_conf:.4f}",
            "correct": is_correct,
            "gated_out": was_gated,
        })

        if (i + 1) % 20 == 0 or (i + 1) == len(samples):
            print(f"  Progress: {i + 1}/{len(samples)}  (running accuracy: {correct / (i + 1):.1%})")

    total = len(rows)
    overall_accuracy = correct / total if total else 0.0

    print("\n" + "=" * 60)
    print("OVERALL PIPELINE ACCURACY (CNN gate -> YOLO -> ViT, end to end)")
    print("=" * 60)
    print(f"Total test images:     {total}")
    print(f"Correct predictions:   {correct}")
    print(f"Overall accuracy:      {overall_accuracy:.2%}")
    print(f"Images gated out by CNN as 'Not_Arecanut': {gated_out_count} "
          f"({gated_out_count / total:.1%} of test set -- these ALWAYS count as wrong here, "
          f"since every test image should genuinely be an Arecanut image)")

    print("\nPer-class accuracy:")
    for cls in sorted(per_class_total):
        n = per_class_total[cls]
        c = per_class_correct[cls]
        print(f"  {cls:<24s} {c:>4d}/{n:<4d}  ({c / n:.1%})")

    print("\nConfusion matrix (rows = true label, columns = predicted label):")
    all_labels = sorted(set(list(per_class_total.keys()) + ["Not_Arecanut"]))
    header = "true\\pred".ljust(24) + "".join(f"{l[:10]:>12s}" for l in all_labels)
    print(header)
    for true_label in sorted(per_class_total):
        row = confusion[true_label]
        print(true_label.ljust(24) + "".join(f"{row.get(l, 0):>12d}" for l in all_labels))

    with open(args.output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["image", "true_label", "predicted_label", "confidence", "correct", "gated_out"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nPer-image results saved to {args.output}")


if __name__ == "__main__":
    main()
