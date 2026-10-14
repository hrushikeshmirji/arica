"""
backend/scripts/train_clean_yolo.py
Builds clean YOLO dataset from backend/data/dataset_clean_v1 and trains YOLOv8n.
"""

import os
import sys
import glob
import shutil
import cv2
import numpy as np
from PIL import Image
from pathlib import Path
import yaml

_HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_HERE))

from vit.predict import ViTPredictor

DATASET_CLEAN_DIR = _HERE / "data" / "dataset_clean_v1"
YOLO_DIR = _HERE / "yolo" / "dataset_clean"
YAML_PATH = _HERE / "yolo" / "dataset_clean.yaml"

CLASS_MAP = {
    "Anthracnose": 0,
    "BudBorer": 1,
    "FruitRot": 2,
    "Healthy": 3,
    "LeafSpotComplex": 4,
    "NutCracking": 5,
    "PhytoplasmaYellowLeaf": 6,
    "SootyMold": 7,
    "StemBleeding": 8,
    "StemCracking": 9,
    "YellowLeaf": 10,
}

def build_yolo_dataset():
    print("=" * 60)
    print("Building Clean YOLOv8 Dataset from dataset_clean_v1...")
    print("=" * 60)

    for split in ["train", "val"]:
        (YOLO_DIR / "images" / split).mkdir(parents=True, exist_ok=True)
        (YOLO_DIR / "labels" / split).mkdir(parents=True, exist_ok=True)

    counts = {"train": 0, "val": 0}
    boxes_generated = {"focal": 0, "fallback": 0, "empty_bg": 0, "healthy_box": 0}

    for split in ["train", "val"]:
        src_split_dir = DATASET_CLEAN_DIR / split
        for cls_name, cls_id in CLASS_MAP.items():
            cls_src = src_split_dir / cls_name
            if not cls_src.exists():
                continue
            
            img_paths = sorted(cls_src.glob("*.jpg"))
            for i, img_p in enumerate(img_paths):
                dst_img_name = f"{cls_name}_{img_p.name}"
                dst_img_p = YOLO_DIR / "images" / split / dst_img_name
                dst_lbl_p = YOLO_DIR / "labels" / split / f"{dst_img_p.stem}.txt"

                shutil.copy2(img_p, dst_img_p)
                counts[split] += 1

                # Generate label
                if cls_name == "Healthy":
                    # 50% empty background (teaches YOLO no disease lesions), 50% healthy whole canopy box
                    if i % 2 == 0:
                        with open(dst_lbl_p, "w") as f:
                            pass
                        boxes_generated["empty_bg"] += 1
                    else:
                        with open(dst_lbl_p, "w") as f:
                            f.write(f"3 0.5000 0.5000 0.8500 0.8500\n")
                        boxes_generated["healthy_box"] += 1
                else:
                    # Diseased: try focal lesion bounding box
                    try:
                        with Image.open(img_p) as im:
                            rgb = np.asarray(im.convert("RGB"))
                        h, w = rgb.shape[:2]
                        morph = ViTPredictor.compute_tissue_morphometrics_and_saliency(rgb)
                        box = morph["saliencyBox"]
                        if box is not None and w > 0 and h > 0:
                            x1, y1, x2, y2 = box
                            bw = max(0.05, min(0.98, float(x2 - x1) / float(w)))
                            bh = max(0.05, min(0.98, float(y2 - y1) / float(h)))
                            xc = max(0.05, min(0.95, float(x1 + x2) / (2.0 * float(w))))
                            yc = max(0.05, min(0.95, float(y1 + y2) / (2.0 * float(h))))
                            with open(dst_lbl_p, "w") as f:
                                f.write(f"{cls_id} {xc:.4f} {yc:.4f} {bw:.4f} {bh:.4f}\n")
                            boxes_generated["focal"] += 1
                        else:
                            with open(dst_lbl_p, "w") as f:
                                f.write(f"{cls_id} 0.5000 0.5000 0.8000 0.8000\n")
                            boxes_generated["fallback"] += 1
                    except Exception as e:
                        with open(dst_lbl_p, "w") as f:
                            f.write(f"{cls_id} 0.5000 0.5000 0.8000 0.8000\n")
                        boxes_generated["fallback"] += 1

    print(f"Finished dataset creation:")
    print(f"  Train images: {counts['train']}")
    print(f"  Val images:   {counts['val']}")
    print(f"  Box stats:    {boxes_generated}")

    # Write dataset_clean.yaml
    yaml_content = {
        "path": str(YOLO_DIR.as_posix()),
        "train": "images/train",
        "val": "images/val",
        "nc": len(CLASS_MAP),
        "names": {v: k for k, v in CLASS_MAP.items()},
    }
    with open(YAML_PATH, "w") as yf:
        yaml.dump(yaml_content, yf, default_flow_style=False, sort_keys=False)
    print(f"Wrote YAML config to: {YAML_PATH}")


def train_yolo():
    from ultralytics import YOLO

    print("\n" + "=" * 60)
    print("Training YOLOv8n on Clean Arecanut Dataset...")
    print("=" * 60)

    model = YOLO("yolov8n.pt")
    runs_dir = _HERE / "yolo" / "runs"
    
    results = model.train(
        data=str(YAML_PATH),
        epochs=20,
        batch=16,
        imgsz=640,
        patience=10,
        device="cpu",
        project=str(runs_dir),
        name="train_clean_v1",
        exist_ok=True,
        verbose=True,
    )

    best_weight = runs_dir / "train_clean_v1" / "weights" / "best.pt"
    ckpt_dest = _HERE / "yolo" / "checkpoints" / "best_clean_v1.pt"
    if best_weight.exists():
        shutil.copy2(best_weight, ckpt_dest)
        print(f"\n[OK] Saved best clean YOLO model to: {ckpt_dest}")
    else:
        last_weight = runs_dir / "train_clean_v1" / "weights" / "last.pt"
        if last_weight.exists():
            shutil.copy2(last_weight, ckpt_dest)
            print(f"\n[OK] Saved last clean YOLO model to: {ckpt_dest}")

    print("\nEvaluating trained model on validation split...")
    val_metrics = model.val(data=str(YAML_PATH), split="val", device="cpu")
    print(f"Validation mAP50: {val_metrics.box.map50:.4f}")
    print(f"Validation mAP50-95: {val_metrics.box.map:.4f}")


if __name__ == "__main__":
    build_yolo_dataset()
    train_yolo()
