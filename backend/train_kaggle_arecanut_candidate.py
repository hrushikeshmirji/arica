from __future__ import annotations

import json
import os
import random
from collections import Counter
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score
from sklearn.model_selection import StratifiedGroupKFold
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0


SEED = 42
DATA_DIR = Path(__file__).resolve().parent / "data" / "kaggle_arecanut_candidate"
MANIFEST_PATH = DATA_DIR / "manifest.json"
OUTPUT_PATH = DATA_DIR / "model_candidate_efficientnet_b0.pth"
RESULTS_PATH = DATA_DIR / "evaluation_candidate.json"
CLASS_NAMES = ["Healthy", "FruitRot", "StemBleeding", "PhytoplasmaYellowLeaf"]
BATCH_SIZE = 4
FOLDS = 4


def load_samples(manifest: dict) -> tuple[list[Path], np.ndarray, np.ndarray]:
    paths = []
    labels = []
    groups = []
    class_to_index = {name: index for index, name in enumerate(CLASS_NAMES)}

    for record in manifest["records"]:
        if not record.get("training_eligible", False):
            continue
        class_name = record["class_name"]
        path = DATA_DIR / record["local_path"]
        if class_name not in class_to_index or not path.is_file():
            continue
        paths.append(path)
        labels.append(class_to_index[class_name])
        groups.append(f"{class_name}:{record['source_key']}")

    if not paths:
        raise RuntimeError(f"No eligible images found under {DATA_DIR}")
    counts = Counter(labels)
    if len(counts) != len(CLASS_NAMES) or min(counts.values()) < FOLDS:
        raise RuntimeError(f"Insufficient examples for {FOLDS}-fold evaluation: {counts}")
    return paths, np.asarray(labels, dtype=np.int64), np.asarray(groups)


def perceptual_groups(paths: list[Path], labels: np.ndarray) -> tuple[np.ndarray, int]:
    hashes = []
    for path in paths:
        with Image.open(path) as image:
            pixels = np.asarray(
                image.convert("L").resize((9, 8), Image.Resampling.LANCZOS),
                dtype=np.int16,
            )
        hashes.append(sum(
            int(bit) << offset
            for offset, bit in enumerate((pixels[:, 1:] > pixels[:, :-1]).ravel())
        ))

    parents = list(range(len(paths)))

    def find(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    for first in range(len(paths)):
        for second in range(first + 1, len(paths)):
            if (hashes[first] ^ hashes[second]).bit_count() <= 6:
                root_first = find(first)
                root_second = find(second)
                if root_first != root_second:
                    parents[root_second] = root_first

    roots = np.asarray([find(index) for index in range(len(paths))])
    component_labels: dict[int, set[int]] = {}
    for index, root in enumerate(roots):
        component_labels.setdefault(int(root), set()).add(int(labels[index]))
    conflicts = [root for root, class_ids in component_labels.items() if len(class_ids) > 1]
    if conflicts:
        raise RuntimeError(f"Perceptual duplicate clusters cross class labels: {conflicts}")
    return np.asarray([f"dhash:{root}" for root in roots]), len(component_labels)


def extract_features(paths: list[Path], weights) -> np.ndarray:
    device = torch.device("cpu")
    model = efficientnet_b0(weights=weights).to(device)
    model.classifier = nn.Identity()
    model.eval()
    transform = weights.transforms()
    features = []
    torch.set_num_threads(max(1, min(8, os.cpu_count() or 1)))

    with torch.inference_mode():
        for start in range(0, len(paths), BATCH_SIZE):
            tensors = []
            for path in paths[start : start + BATCH_SIZE]:
                with Image.open(path) as image:
                    tensors.append(transform(image.convert("RGB")))
            batch = torch.stack(tensors).to(device)
            features.append(model(batch).cpu().numpy())
            print(f"Extracted features for {min(start + len(tensors), len(paths))}/{len(paths)} images")

    return np.concatenate(features, axis=0)


def main() -> None:
    random.seed(SEED)
    np.random.seed(SEED)
    torch.manual_seed(SEED)

    if not MANIFEST_PATH.is_file():
        raise FileNotFoundError(f"Run download_kaggle_candidate.py first: {MANIFEST_PATH}")
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("dataset_license") != "CC BY-NC-SA 4.0":
        raise RuntimeError("Unexpected dataset license; refusing to train candidate")

    paths, labels, groups = load_samples(manifest)
    groups, cluster_count = perceptual_groups(paths, labels)
    counts = {name: int(np.sum(labels == index)) for index, name in enumerate(CLASS_NAMES)}
    print(f"Candidate classes: {CLASS_NAMES}")
    print(f"Eligible source images: {len(paths)}; per-class counts: {counts}")
    print(f"Perceptual groups at dHash distance <= 6: {cluster_count}")
    print("The app checkpoint and 11-class configuration will not be loaded or modified.")

    weights = EfficientNet_B0_Weights.DEFAULT
    features = extract_features(paths, weights)
    predictions = np.full(labels.shape, -1, dtype=np.int64)
    splitter = StratifiedGroupKFold(n_splits=FOLDS, shuffle=True, random_state=SEED)
    fold_scores = []

    for fold, (train_indices, val_indices) in enumerate(
        splitter.split(features, labels, groups), start=1
    ):
        classifier = LogisticRegression(
            class_weight="balanced",
            max_iter=2000,
            C=1.0,
            random_state=SEED,
        )
        classifier.fit(features[train_indices], labels[train_indices])
        fold_predictions = classifier.predict(features[val_indices])
        predictions[val_indices] = fold_predictions
        score = f1_score(labels[val_indices], fold_predictions, average="macro", zero_division=0)
        fold_scores.append(float(score))
        print(
            f"Fold {fold}/{FOLDS}: train={len(train_indices)} val={len(val_indices)} "
            f"macro_f1={score:.4f}"
        )

    if np.any(predictions < 0):
        raise RuntimeError("Cross-validation did not produce predictions for every image")

    oof_macro_f1 = float(f1_score(labels, predictions, average="macro", zero_division=0))
    report = classification_report(
        labels,
        predictions,
        labels=list(range(len(CLASS_NAMES))),
        target_names=CLASS_NAMES,
        output_dict=True,
        zero_division=0,
    )
    matrix = confusion_matrix(labels, predictions, labels=list(range(len(CLASS_NAMES))))
    print(f"Out-of-fold macro F1: {oof_macro_f1:.4f}")
    print(classification_report(
        labels,
        predictions,
        labels=list(range(len(CLASS_NAMES))),
        target_names=CLASS_NAMES,
        digits=4,
        zero_division=0,
    ))
    print("Out-of-fold confusion matrix:")
    print(matrix)

    final_classifier = LogisticRegression(
        class_weight="balanced",
        max_iter=2000,
        C=1.0,
        random_state=SEED,
    )
    final_classifier.fit(features, labels)

    final_model = efficientnet_b0(weights=weights)
    in_features = final_model.classifier[1].in_features
    final_model.classifier[1] = nn.Linear(in_features, len(CLASS_NAMES))
    with torch.no_grad():
        final_model.classifier[1].weight.copy_(torch.from_numpy(final_classifier.coef_).float())
        final_model.classifier[1].bias.copy_(torch.from_numpy(final_classifier.intercept_).float())

    evaluation = {
        "classes": CLASS_NAMES,
        "eligible_images": len(paths),
        "per_class_counts": counts,
        "fold_macro_f1": fold_scores,
        "mean_fold_macro_f1": float(np.mean(fold_scores)),
        "std_fold_macro_f1": float(np.std(fold_scores)),
        "out_of_fold_macro_f1": oof_macro_f1,
        "out_of_fold_report": report,
        "out_of_fold_confusion_matrix": matrix.tolist(),
        "group_policy": "One selected image per filename-derived source-photo ID; dHash connected components at Hamming distance <= 6 are kept within one StratifiedGroupKFold fold.",
        "perceptual_group_count": cluster_count,
        "dhash_hamming_threshold": 6,
        "limitations": [
            "This is a four-class research candidate, not the requested five-class model.",
            "LeafSpotComplex is absent and was not relabeled from Ring Spot.",
            "The source dataset is CC BY-NC-SA 4.0; non-commercial/share-alike conditions apply.",
            "Small per-class source counts and observed label noise make metrics exploratory, not deployment evidence.",
        ],
    }
    checkpoint = {
        "model_state_dict": final_model.state_dict(),
        "classes": CLASS_NAMES,
        "architecture": "torchvision.efficientnet_b0",
        "initialization": weights.url,
        "dataset": manifest["dataset"],
        "dataset_license": manifest["dataset_license"],
        "attribution": manifest["attribution"],
        "evaluation": evaluation,
    }
    torch.save(checkpoint, OUTPUT_PATH)
    RESULTS_PATH.write_text(json.dumps(evaluation, indent=2), encoding="utf-8")
    print(f"Saved isolated research candidate: {OUTPUT_PATH}")
    print(f"Saved grouped cross-validation report: {RESULTS_PATH}")


if __name__ == "__main__":
    main()