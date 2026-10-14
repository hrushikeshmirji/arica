import os
import sys
import glob

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from cnn.predict import CNNPredictor
from vit.predict import ViTPredictor

def main():
    cnn = CNNPredictor()
    vit = ViTPredictor()

    print("=" * 80)
    print("1. TESTING THE 8 NON-ARECA FALSE POSITIVES")
    print("=" * 80)
    raw_dir = r"D:\dataset_raw\dataset_raw\non_areca"
    fps = [
        "download_1333.jpg",
        "download_1423.jpg",
        "download_1594.jpg",
        "download_1696.jpg",
        "download_574.jpg",
        "download_577.jpg",
        "download_578.jpg",
        "download_580.jpeg",
    ]
    fp_rejected = 0
    for name in fps:
        p = os.path.join(raw_dir, name)
        c_lbl, c_cnf = cnn.predict(p)
        if c_lbl == "Not_Arecanut":
            fp_rejected += 1
            print(f"[{name:20s}] -> REJECTED by Gatekeeper (Stage 1) [{c_cnf:.1%}]")
        else:
            v_out = vit.predict_tta_ensemble(p)
            psim = v_out.get("maxProtoSim", 0.0)
            if v_out.get("isOOD") or v_out["label"] == "Not_Arecanut":
                fp_rejected += 1
                print(f"[{name:20s}] -> REJECTED by ViT OOD Guard (Stage 3) [ProtoSim={psim:.3f}]")
            else:
                lbl = v_out["label"]
                cnf = v_out["confidence"]
                print(f"[{name:20s}] -> FAILED: ACCEPTED as {lbl} ({cnf:.1%})")

    print(f"\nNon-Areca Rejected: {fp_rejected}/{len(fps)} ({fp_rejected/len(fps):.1%})\n")

    print("=" * 80)
    print("2. TESTING REAL ARECANUT FIELD SAMPLES")
    print("=" * 80)
    tests = [
        ("areca_diseased_physiological_nut_cracking", "NutCracking"),
        ("areca_diseased_fungal_anthracnose", "Anthracnose"),
        ("areca_healthy", "Healthy"),
        ("areca_diseased_fungal_fruit_rot", "FruitRot"),
        ("areca_diseased_fungal_leaf_spot", "LeafSpotComplex"),
        ("areca_pest_bud_borer", "BudBorer"),
        ("areca_diseased_fungal_stem_bleeding", "StemBleeding"),
        ("areca_diseased_physiological_stem_cracking", "StemCracking"),
        ("areca_diseased_phytoplasma_yellow_leaf", "PhytoplasmaYellowLeaf"),
        ("areca_diseased_yellow_leaf_chlorosis", "YellowLeaf"),
        ("areca_diseased_fungal_sooty_mold", "SootyMold"),
    ]
    real_accepted = 0
    real_correct = 0
    total_real = 0

    for folder, exp in tests:
        imgs = glob.glob(os.path.join(r"D:\dataset_raw\dataset_raw", folder, "*.*"))[:2]
        for idx, p in enumerate(imgs):
            total_real += 1
            c_lbl, c_cnf = cnn.predict(p)
            if c_lbl == "Arecanut":
                real_accepted += 1
            v_out = vit.predict_tta_ensemble(p)
            v_lbl = v_out["label"]
            v_cnf = v_out["confidence"]
            is_match = (v_lbl == exp)
            if is_match:
                real_correct += 1
            status = "MATCH" if is_match else "MISMATCH"
            print(f"[{exp:22s} #{idx+1}] -> Gate: {c_lbl:12s} ({c_cnf:.0%}) | ViT: {v_lbl:20s} ({v_cnf:.1%}) | {status}")

    print("=" * 80)
    print(f"Real Arecanut Gatekeeper Pass Rate: {real_accepted}/{total_real} ({real_accepted/total_real:.1%})")
    print(f"Real Arecanut ViT Diagnostic Accuracy: {real_correct}/{total_real} ({real_correct/total_real:.1%})")
    print("=" * 80)

if __name__ == "__main__":
    main()
