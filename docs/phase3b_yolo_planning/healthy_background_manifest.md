# Phase 3B: Healthy Palm Background (Negative Image) Manifest

## 1. Ultralytics YOLOv8 Negative Image Specification

In standard Ultralytics YOLOv8 architecture:
- **Negative/Background Images** are essential to teach the object detection head not to predict false positive lesion boxes on uninfected foliage, palm fronds, soil, or background canopy.
- **Negative Image Label Protocol**: In Ultralytics YOLO format, a negative background image must have an **empty 0-byte `.txt` label file** (or no label file). Adding a dummy full-screen box to a healthy leaf explicitly forces the detector to learn that healthy green tissue is an object of interest, leading to catastrophic false positive rates.

---

## 2. Identified Healthy Images (73 Total)

- **Train Split**: 51 images
- **Val Split**: 14 images
- **Test Split**: 8 images

| Split | Filename | Dimensions | Current Label Box | Target YOLOv8 Label Content |
|:---|:---|:---:|:---:|:---|
| train | `Healthy_existing_healthy_11.jpg` | 1040x1390 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_12.jpg` | 1600x1157 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_13.jpg` | 800x800 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_14.jpg` | 1300x956 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_15.jpg` | 1067x1690 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_17.jpg` | 1600x989 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_18.jpg` | 1189x1390 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_2.jpg` | 1241x1960 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_20.jpg` | 866x1390 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_22.jpg` | 1300x951 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_23.jpg` | 1024x1024 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_24.jpg` | 1024x768 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_25.jpg` | 1280x720 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_26.jpg` | 347x280 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_29.jpg` | 952x1690 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_31.jpg` | 351x388 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_33.jpg` | 425x265 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_34.jpg` | 550x733 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_35.jpg` | 600x600 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_36.jpg` | 1280x1690 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_37.jpg` | 1000x873 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_39.jpg` | 3000x3000 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_41.jpg` | 1200x700 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_42.jpg` | 1600x1290 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_43.jpg` | 1600x1157 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_45.jpg` | 800x533 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_46.jpg` | 1600x1370 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_47.jpg` | 1600x1156 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_48.jpg` | 866x1390 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_49.jpg` | 1060x1690 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_5.jpg` | 3480x1960 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_50.jpg` | 320x240 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_51.jpg` | 1300x956 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_55.jpg` | 1067x1690 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_56.jpg` | 1920x1080 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_57.jpg` | 1280x720 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_58.jpg` | 450x450 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_59.jpg` | 600x900 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_6.jpg` | 1600x1157 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_60.jpg` | 459x612 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_61.jpg` | 500x500 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_62.jpg` | 360x240 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_63.jpg` | 1342x1690 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_64.jpg` | 389x280 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_66.jpg` | 800x534 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_67.jpg` | 509x339 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_68.jpg` | 800x600 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_7.jpg` | 1300x956 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_70.jpg` | 1067x1690 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_72.jpg` | 575x571 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| train | `Healthy_existing_healthy_75.jpg` | 800x542 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| val | `Healthy_existing_healthy_1.jpg` | 1500x1093 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| val | `Healthy_existing_healthy_10.jpg` | 1600x990 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| val | `Healthy_existing_healthy_16.jpg` | 866x1390 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| val | `Healthy_existing_healthy_19.jpg` | 866x1390 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| val | `Healthy_existing_healthy_27.jpg` | 408x612 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| val | `Healthy_existing_healthy_28.jpg` | 1300x956 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| val | `Healthy_existing_healthy_30.jpg` | 1067x1690 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| val | `Healthy_existing_healthy_38.jpg` | 1200x1850 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| val | `Healthy_existing_healthy_40.jpg` | 960x640 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| val | `Healthy_existing_healthy_52.jpg` | 1038x1390 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| val | `Healthy_existing_healthy_53.jpg` | 1067x1690 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| val | `Healthy_existing_healthy_54.jpg` | 1600x1173 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| val | `Healthy_existing_healthy_71.jpg` | 500x284 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| val | `Healthy_existing_healthy_9.jpg` | 1300x861 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| test | `Healthy_existing_healthy_21.jpg` | 576x411 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| test | `Healthy_existing_healthy_3.jpg` | 866x1390 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| test | `Healthy_existing_healthy_32.jpg` | 612x408 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| test | `Healthy_existing_healthy_4.jpg` | 1300x956 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| test | `Healthy_existing_healthy_44.jpg` | 1500x1225 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| test | `Healthy_existing_healthy_69.jpg` | 1300x951 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| test | `Healthy_existing_healthy_73.jpg` | 1600x1153 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
| test | `Healthy_existing_healthy_8.jpg` | 866x1390 | `3 0.5 0.5 0.9 0.9` | **Empty File (0 bytes)** |
