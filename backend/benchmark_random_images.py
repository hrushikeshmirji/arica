"""
benchmark_random_images.py — Rigorous benchmark of the 2-step ArecaVision pipeline
using randomly sampled images from D:\\dataset_raw\\dataset_raw.
"""
import glob
import os
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import config
from cnn.predict import CNNPredictor
from vit.predict import ViTPredictor
from yolo.detect import YOLODetector

DATASET_ROOT = Path("D:/dataset_raw/dataset_raw")

CATEGORY_MAPPING = {
    "non_areca": "Not_Arecanut",
    "areca_healthy": "Healthy",
    "areca_diseased_fungal_anthracnose": "Anthracnose",
    "areca_diseased_fungal_fruit_rot": "FruitRot",
    "areca_diseased_fungal_sooty_mold": "SootyMold",
    "areca_diseased_physiological_nut_cracking": "NutCracking",
}

def benchmark(samples_per_class: int = 5, seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)

    print("=" * 80)
    print(f"ARECAVISION AI — BENCHMARK ON RANDOM IMAGES (Seed={seed}, Samples/Class={samples_per_class})")
    print(f"Dataset root: {DATASET_ROOT}")
    print("=" * 80)

    print("\n[Init] Loading models...")
    t_start = time.perf_counter()
    cnn = CNNPredictor()
    yolo = YOLODetector(conf_threshold=0.15)
    vit = ViTPredictor()
    print(f"[Init] All 3 models loaded in {time.perf_counter() - t_start:.2f}s\n")

    # Sample random images from each directory
    test_samples = []
    for folder_name, true_class in CATEGORY_MAPPING.items():
        folder_path = DATASET_ROOT / folder_name
        if not folder_path.is_dir():
            print(f"[WARN] Folder not found: {folder_path}")
            continue
        all_files = [p for p in folder_path.iterdir() if p.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp")]
        if not all_files:
            print(f"[WARN] No images in: {folder_path}")
            continue
        
        sample_count = min(samples_per_class, len(all_files))
        selected = random.sample(all_files, sample_count)
        for p in selected:
            test_samples.append((p, folder_name, true_class))

    # Shuffle the combined sample pool
    random.shuffle(test_samples)
    print(f"Total randomly selected test samples: {len(test_samples)} across {len(CATEGORY_MAPPING)} classes.\n")

    gate_correct = 0
    gate_total = 0
    gate_non_areca_correct = 0
    gate_non_areca_total = 0
    gate_areca_correct = 0
    gate_areca_total = 0

    disease_correct = 0
    disease_total = 0
    disease_per_class_total = Counter()
    disease_per_class_correct = Counter()

    overall_correct = 0
    latencies = []

    print("-" * 115)
    print(f"{'#':<3} | {'True Category':<22} | {'Step 1 (Gate)':<25} | {'Step 2 (Disease)':<25} | {'Status':<8} | {'Latency'}")
    print("-" * 115)

    for idx, (img_path, folder_name, true_class) in enumerate(test_samples, 1):
        t0 = time.perf_counter()
        
        # Load image
        bgr = cv2.imread(str(img_path))
        if bgr is None:
            print(f"{idx:<3} | {folder_name:<22} | FAILED TO READ IMAGE")
            continue
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

        # Step 1: Gatekeeper
        cnn_label, cnn_conf = cnn.predict(rgb)
        cnn_conf_pct = cnn_conf * 100.0

        is_non_areca = (true_class == "Not_Arecanut")
        gate_total += 1
        
        if is_non_areca:
            gate_non_areca_total += 1
            if cnn_label == "Not_Arecanut":
                gate_non_areca_correct += 1
                gate_correct += 1
                step1_pass = True
            else:
                step1_pass = False
        else:
            gate_areca_total += 1
            if cnn_label == "Arecanut":
                gate_areca_correct += 1
                gate_correct += 1
                step1_pass = True
            else:
                step1_pass = False

        # Step 2: Disease Detection
        final_prediction = ""
        final_conf = 0.0
        step2_pass = False

        if cnn_label != "Arecanut":
            # Gated out
            final_prediction = "Not_Arecanut"
            final_conf = cnn_conf_pct
            step2_pass = is_non_areca
        else:
            # Proceed to YOLO + ViT
            disease_total += 1
            disease_per_class_total[true_class] += 1

            detections, _ = yolo.detect(rgb)
            if detections:
                results = []
                for det in detections:
                    v_label, v_conf, _ = vit.predict(det["crop"])
                    results.append((v_label, v_conf * 100.0))
                # Aggregate: pick highest diseased, else highest overall
                diseased = [r for r in results if r[0] != "Healthy"]
                top_label, top_conf = max(diseased, key=lambda r: r[1]) if diseased else max(results, key=lambda r: r[1])
                final_prediction = top_label
                final_conf = top_conf
            else:
                # Fallback to whole image ViT
                v_label, v_conf, _ = vit.predict(rgb)
                final_prediction = v_label
                final_conf = v_conf * 100.0

            if final_prediction == true_class:
                disease_correct += 1
                disease_per_class_correct[true_class] += 1
                step2_pass = True

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies.append(elapsed_ms)

        is_match = (final_prediction == true_class)
        if is_match:
            overall_correct += 1
            status_str = "MATCH"
        else:
            status_str = "FAIL"

        gate_str = f"{cnn_label} ({cnn_conf_pct:.1f}%)"
        disease_str = f"{final_prediction} ({final_conf:.1f}%)"

        print(f"{idx:<3} | {true_class:<22} | {gate_str:<25} | {disease_str:<25} | {status_str:<8} | {elapsed_ms:6.1f} ms")

    print("-" * 115)
    print("\n" + "=" * 80)
    print("BENCHMARK SUMMARY & METRICS")
    print("=" * 80)

    print("\n1. STEP 1 GATEKEEPER PERFORMANCE:")
    print(f"   • Non-Arecanut Rejection Rate : {gate_non_areca_correct}/{gate_non_areca_total} "
          f"({(gate_non_areca_correct/gate_non_areca_total*100) if gate_non_areca_total else 0:.1f}%)")
    print(f"   • Arecanut Acceptance Rate    : {gate_areca_correct}/{gate_areca_total} "
          f"({(gate_areca_correct/gate_areca_total*100) if gate_areca_total else 0:.1f}%)")
    print(f"   • Gatekeeper Total Accuracy   : {gate_correct}/{gate_total} ({(gate_correct/gate_total*100):.1f}%)")

    print("\n2. STEP 2 DISEASE IDENTIFICATION PERFORMANCE (on Arecanut samples):")
    for cls in sorted(disease_per_class_total.keys()):
        tot = disease_per_class_total[cls]
        cor = disease_per_class_correct[cls]
        print(f"   • {cls:<16}: {cor}/{tot} ({cor/tot*100:.1f}%)")
    if disease_total > 0:
        print(f"   • Disease Top-1 Accuracy: {disease_correct}/{disease_total} ({(disease_correct/disease_total*100):.1f}%)")

    print("\n3. OVERALL SYSTEM BENCHMARK:")
    print(f"   • End-to-End Correctness     : {overall_correct}/{len(test_samples)} ({(overall_correct/len(test_samples)*100):.1f}%)")
    print(f"   • Average Inference Latency  : {np.mean(latencies):.1f} ms / image (CPU)")
    print(f"   • Min / Max Latency          : {np.min(latencies):.1f} ms / {np.max(latencies):.1f} ms")
    print("=" * 80)

if __name__ == "__main__":
    n_samples = 5
    if len(sys.argv) > 1:
        n_samples = int(sys.argv[1])
    seed_val = 42
    if len(sys.argv) > 2:
        seed_val = int(sys.argv[2])
    benchmark(samples_per_class=n_samples, seed=seed_val)
