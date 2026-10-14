import os
import shutil
import hashlib
from PIL import Image

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TRAIN_DIR = os.path.join(REPO_ROOT, "backend", "yolo", "dataset_repaired_phase3b_v2", "images", "train")
OOD_DIR = os.path.join(REPO_ROOT, "backend", "tests", "ood_probe")
TEST_DIR = os.path.join(REPO_ROOT, "backend", "tests", "test_images")
os.makedirs(TEST_DIR, exist_ok=True)

# 1. Dataset Image 1 (Fruit Rot)
src_fr = os.path.join(TRAIN_DIR, "FruitRot_existing_fruit_rot_15.jpg")
dst_fr = os.path.join(TEST_DIR, "1_dataset_fruit_rot.jpg")
shutil.copyfile(src_fr, dst_fr)

# 2. Dataset Image 2 (Healthy)
src_hl = os.path.join(TRAIN_DIR, "Healthy_existing_healthy_11.jpg")
dst_hl = os.path.join(TEST_DIR, "2_dataset_healthy.jpg")
shutil.copyfile(src_hl, dst_hl)

# 3. PNG with Alpha (RGBA)
dst_png = os.path.join(TEST_DIR, "3_alpha.png")
with Image.open(src_fr) as im:
    rgba = im.convert("RGBA")
    w, h = rgba.size
    for x in range(min(40, w)):
        for y in range(min(40, h)):
            r, g, b, _ = rgba.getpixel((x, y))
            rgba.putpixel((x, y), (r, g, b, 128))
    rgba.save(dst_png, "PNG")

# 4. WebP Image
dst_webp = os.path.join(TEST_DIR, "4_format.webp")
with Image.open(src_hl) as im:
    im.save(dst_webp, "WEBP", quality=90)

# 5. EXIF-rotated Image (Orientation tag 6 = 90 deg clockwise)
dst_exif = os.path.join(TEST_DIR, "5_exif_rotated.jpg")
with Image.open(src_fr) as im:
    exif = im.getexif()
    exif[0x0112] = 6  # Orientation = 6 (Rotate 90 CW)
    im.save(dst_exif, "JPEG", exif=exif)

# 6. Non-areca Image
src_na = os.path.join(OOD_DIR, "bus.jpg")
dst_na = os.path.join(TEST_DIR, "6_non_areca.jpg")
shutil.copyfile(src_na, dst_na)

print("Created 6 test images in:", TEST_DIR)
for f in sorted(os.listdir(TEST_DIR)):
    fp = os.path.join(TEST_DIR, f)
    h = hashlib.sha256(open(fp, "rb").read()).hexdigest().upper()
    size = os.path.getsize(fp)
    print(f"  {f:25s} | {size:7d} bytes | SHA256: {h}")
