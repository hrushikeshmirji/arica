import glob
import os
import sys
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

from pipeline.hybrid_pipeline import HybridPipeline

pipeline = HybridPipeline()

categories = [
    'areca_diseased_fungal_anthracnose',
    'areca_diseased_fungal_fruit_rot',
    'areca_diseased_fungal_sooty_mold',
    'areca_diseased_physiological_nut_cracking',
    'areca_healthy'
]

for category in categories:
    print(f"\n=== Category: {category} ===")
    files = glob.glob(f"D:/dataset_raw/dataset_raw/{category}/*")[:6]
    for f in files:
        fname = os.path.basename(f)
        res = pipeline.predict(f)
        dets = res['detections']
        det_summary = ", ".join([f"{d['vit_class']}({d['vit_conf']*100:.1f}%)" for d in dets])
        print(f"  {fname:25s} | Arecanut: {str(res['is_arecanut']):5s} ({res['cnn_conf']*100:.1f}%) | Detections: {len(dets)} | {det_summary}")
