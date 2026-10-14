import os
import glob
import sys
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from cnn.predict import CNNPredictor
from vit.predict import ViTPredictor
from yolo.detect import YOLODetector
import config

RAW_DIR = r"D:\dataset_raw\dataset_raw"
CATEGORY_TO_DISEASE = {
    "areca_diseased_fungal_anthracnose": "Anthracnose",
    "areca_pest_bud_borer": "BudBorer",
    "areca_diseased_fungal_fruit_rot": "FruitRot",
    "areca_healthy": "Healthy",
    "areca_diseased_fungal_leaf_spot": "LeafSpotComplex",
    "areca_diseased_physiological_nut_cracking": "NutCracking",
    "areca_diseased_phytoplasma_yellow_leaf": "PhytoplasmaYellowLeaf",
    "areca_diseased_fungal_sooty_mold": "SootyMold",
    "areca_diseased_fungal_stem_bleeding": "StemBleeding",
    "areca_diseased_physiological_stem_cracking": "StemCracking",
    "areca_diseased_yellow_leaf_chlorosis": "YellowLeaf",
}

def main():
    print("=" * 80)
    print("EVALUATING PIPELINE ACROSS ALL 11 REAL FIELD CLASSES")
    print("=" * 80)

    cnn = CNNPredictor()
    vit = ViTPredictor()
    yolo = YOLODetector()

    total_tested = 0
    correct_vit = 0
    correct_gate = 0

    for cat_folder, expected_cls in CATEGORY_TO_DISEASE.items():
        folder_path = os.path.join(RAW_DIR, cat_folder)
        imgs = glob.glob(os.path.join(folder_path, "*.*"))
        valid_imgs = [i for i in imgs if i.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
        if not valid_imgs:
            continue

        test_samples = valid_imgs[:3]
        for idx, sample in enumerate(test_samples):
            total_tested += 1
            cnn_label, cnn_conf = cnn.predict(sample)
            if cnn_label == "Arecanut":
                correct_gate += 1

            yolo_dets, _ = yolo.detect(sample)
            yolo_crops = [d["crop"] for d in yolo_dets if "crop" in d]
            vit_out = vit.predict_tta_ensemble(sample, yolo_crops=yolo_crops)
            pred_vit = vit_out["label"]
            conf_vit = vit_out["confidence"]
            has_sal = "Yes" if vit_out.get("saliencyBox") else "No"
            is_match = (pred_vit == expected_cls)
            if is_match:
                correct_vit += 1

            status = "MATCH" if is_match else "MISMATCH"
            print(f"[{expected_cls:22s} #{idx+1}] -> Pred: {pred_vit:20s} ({conf_vit:.1%}) | Gate: {cnn_label} ({cnn_conf:.0%}) | LesionBox: {has_sal:3s} | {status}")

    print("=" * 80)
    print(f"Total Tested: {total_tested}")
    print(f"Gatekeeper Accuracy: {correct_gate}/{total_tested} ({correct_gate/total_tested:.1%})")
    print(f"ViT Disease Top-1 Accuracy: {correct_vit}/{total_tested} ({correct_vit/total_tested:.1%})")
    print("=" * 80)

if __name__ == "__main__":
    main()
