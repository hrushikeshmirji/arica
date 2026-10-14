import os
import sys
import json
import shutil
import platform
import psutil

# Package versions
import torch
import torchvision
import timm
import ultralytics
import numpy as np
import PIL

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.makedirs(os.path.join(REPO_ROOT, "results", "train"), exist_ok=True)

# Disk space
c_disk = shutil.disk_usage("C:\\")
d_disk = shutil.disk_usage("D:\\")

# RAM
ram = psutil.virtual_memory()

# CPU
cpu_name = "AMD Ryzen 7 7445HS w/ Radeon 740M Graphics"

info = {
    "python_version": sys.version,
    "torch_version": torch.__version__,
    "torchvision_version": torchvision.__version__,
    "timm_version": timm.__version__,
    "ultralytics_version": ultralytics.__version__,
    "numpy_version": np.__version__,
    "pillow_version": PIL.__version__,
    "cpu_model": cpu_name,
    "cpu_count_physical": psutil.cpu_count(logical=False),
    "cpu_count_logical": psutil.cpu_count(logical=True),
    "ram_total_gb": round(ram.total / (1024**3), 2),
    "ram_available_gb": round(ram.available / (1024**3), 2),
    "cuda_available": torch.cuda.is_available(),
    "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
    "disk_free_c_gb": round(c_disk.free / (1024**3), 2),
    "disk_free_d_gb": round(d_disk.free / (1024**3), 2),
}

output_path = os.path.join(REPO_ROOT, "results", "train", "env_telemetry.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(info, f, indent=2)

print("=== ENVIRONMENT TELEMETRY ===")
for k, v in info.items():
    print(f"{k}: {v}")
print(f"Saved to: {output_path}")
