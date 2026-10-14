import os
import glob
import shutil
import random
from pathlib import Path

# Add project root to sys.path
_HERE = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = r"D:\dataset_raw\dataset_raw"
YOLO_DIR = os.path.join(_HERE, "yolo", "dataset")

CATEGORY_MAP = {
    "areca_diseased_fungal_anthracnose": (0, "Anthracnose"),
    "areca_diseased_fungal_fruit_rot": (2, "FruitRot"),
    "areca_healthy": (3, "Healthy"),
    "areca_diseased_physiological_nut_cracking": (5, "NutCracking"),
    "areca_diseased_fungal_sooty_mold": (7, "SootyMold"),
}

def setup_yolo_dataset():
    print("=" * 60)
    print("  Setting up Local YOLOv8 Dataset for Training & Smoke-Tests")
    print("=" * 60)

    for split in ["train", "val", "test"]:
        os.makedirs(os.path.join(YOLO_DIR, "images", split), exist_ok=True)
        os.makedirs(os.path.join(YOLO_DIR, "labels", split), exist_ok=True)

    # Copy a balanced subset from RAW_DIR to ensure quick, verified dataset
    random.seed(42)
    for cat_folder, (cls_id, cls_name) in CATEGORY_MAP.items():
        src_folder = os.path.join(RAW_DIR, cat_folder)
        if not os.path.exists(src_folder):
            continue

        images = glob.glob(os.path.join(src_folder, "*.*"))
        random.shuffle(images)

        # Split 70% train, 20% val, 10% test (capped for fast verification)
        n_total = min(len(images), 100)
        selected = images[:n_total]
        n_train = int(n_total * 0.7)
        n_val = int(n_total * 0.2)

        splits_data = {
            "train": selected[:n_train],
            "val": selected[n_train:n_train + n_val],
            "test": selected[n_train + n_val:],
        }

        for split, split_files in splits_data.items():
            for fpath in split_files:
                fname = os.path.basename(fpath)
                new_fname = f"{cls_name}_{fname}"
                stem = os.path.splitext(new_fname)[0]

                dst_img = os.path.join(YOLO_DIR, "images", split, new_fname)
                shutil.copy2(fpath, dst_img)

                dst_lbl = os.path.join(YOLO_DIR, "labels", split, f"{stem}.txt")
                with open(dst_lbl, "w") as lf:
                    lf.write(f"{cls_id} 0.5 0.5 0.90 0.90\n")

    print(f"YOLO dataset prepared at: {YOLO_DIR}")

if __name__ == "__main__":
    setup_yolo_dataset()
