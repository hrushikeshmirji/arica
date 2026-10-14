# Phase 3B: Duplicate Images and Label Conflict Report

**Total Images Scanned**: 349
**Unique Images (by MD5 hash)**: 288
**Duplicate Hash Clusters**: 54 clusters involving 115 files
**Conflicting Label Clusters (Same Image, Different Diseases/Healthy)**: 54 clusters
**Cross-Split Contamination Clusters (Leakage between Train/Val/Test)**: 31 clusters

---

## 1. Conflicting Label Clusters (Severe Integrity Violation)

The following duplicate image clusters have **different ground-truth labels assigned to the exact same image**:

| MD5 Hash | Copies | Conflicting Classes | Splits Involved | Example Files |
|:---|:---:|:---|:---|:---|
| `63ad9e13f745...` | 3 | **Anthracnose, FruitRot, NutCracking** | train, val | `train/Anthracnose_existing_anthracnose_1.jpg` (Anthracnose)<br>`train/FruitRot_existing_fruit_rot_2.jpg` (FruitRot)<br>`val/NutCracking_existing_nut_cracking_4.jpg` (NutCracking) |
| `4ff8581d0ac3...` | 2 | **Anthracnose, SootyMold** | train | `train/Anthracnose_existing_anthracnose_13.jpg` (Anthracnose)<br>`train/SootyMold_existing_sooty_mold_15.jpg` (SootyMold) |
| `cc8e028985c3...` | 2 | **Anthracnose, SootyMold** | train | `train/Anthracnose_existing_anthracnose_16.jpg` (Anthracnose)<br>`train/SootyMold_existing_sooty_mold_52.jpg` (SootyMold) |
| `9257d59b244a...` | 2 | **Anthracnose, Healthy** | train | `train/Anthracnose_existing_anthracnose_19.jpg` (Anthracnose)<br>`train/Healthy_existing_healthy_6.jpg` (Healthy) |
| `c15ae2ccff99...` | 3 | **Anthracnose, Healthy, SootyMold** | test, train | `train/Anthracnose_existing_anthracnose_23.jpg` (Anthracnose)<br>`train/SootyMold_existing_sooty_mold_29.jpg` (SootyMold)<br>`test/Healthy_existing_healthy_69.jpg` (Healthy) |
| `475c0104386b...` | 3 | **Anthracnose, Healthy, SootyMold** | train, val | `train/Anthracnose_existing_anthracnose_24.jpg` (Anthracnose)<br>`train/SootyMold_existing_sooty_mold_25.jpg` (SootyMold)<br>`val/Healthy_existing_healthy_16.jpg` (Healthy) |
| `c90bf250051f...` | 2 | **Anthracnose, Healthy** | train | `train/Anthracnose_existing_anthracnose_26.jpg` (Anthracnose)<br>`train/Healthy_existing_healthy_34.jpg` (Healthy) |
| `70b004403af4...` | 2 | **Anthracnose, SootyMold** | train | `train/Anthracnose_existing_anthracnose_27.jpg` (Anthracnose)<br>`train/SootyMold_existing_sooty_mold_62.jpg` (SootyMold) |
| `c21217439f07...` | 4 | **Anthracnose, Healthy, NutCracking, SootyMold** | train, val | `train/Anthracnose_existing_anthracnose_29.jpg` (Anthracnose)<br>`train/Healthy_existing_healthy_61.jpg` (Healthy)<br>`train/NutCracking_existing_nut_cracking_70.jpg` (NutCracking)<br>`val/SootyMold_existing_sooty_mold_47.jpg` (SootyMold) |
| `2a857c31c0a3...` | 2 | **Anthracnose, NutCracking** | train, val | `train/Anthracnose_existing_anthracnose_3.jpg` (Anthracnose)<br>`val/NutCracking_existing_nut_cracking_66.jpg` (NutCracking) |
| `cda02c56fc74...` | 2 | **Anthracnose, Healthy** | train, val | `train/Anthracnose_existing_anthracnose_32.jpg` (Anthracnose)<br>`val/Healthy_existing_healthy_28.jpg` (Healthy) |
| `d6208e0ac014...` | 2 | **Anthracnose, SootyMold** | train | `train/Anthracnose_existing_anthracnose_46.jpg` (Anthracnose)<br>`train/SootyMold_existing_sooty_mold_42.jpg` (SootyMold) |
| `af1a2d567114...` | 2 | **Anthracnose, SootyMold** | train, val | `train/Anthracnose_existing_anthracnose_48.jpg` (Anthracnose)<br>`val/SootyMold_existing_sooty_mold_71.jpg` (SootyMold) |
| `2cb1cb103389...` | 2 | **Anthracnose, SootyMold** | train, val | `train/Anthracnose_existing_anthracnose_65.jpg` (Anthracnose)<br>`val/SootyMold_existing_sooty_mold_68.jpg` (SootyMold) |
| `cb7d307ac5f2...` | 2 | **FruitRot, NutCracking** | train | `train/FruitRot_existing_fruit_rot_1.jpg` (FruitRot)<br>`train/NutCracking_existing_nut_cracking_27.jpg` (NutCracking) |
| `49b4dceef020...` | 2 | **FruitRot, NutCracking** | train | `train/FruitRot_existing_fruit_rot_10.jpg` (FruitRot)<br>`train/NutCracking_existing_nut_cracking_2.jpg` (NutCracking) |
| `cbfbc77e2d23...` | 2 | **FruitRot, NutCracking** | train | `train/FruitRot_existing_fruit_rot_13.jpg` (FruitRot)<br>`train/NutCracking_existing_nut_cracking_10.jpg` (NutCracking) |
| `e98cdd6740d6...` | 2 | **FruitRot, NutCracking** | train, val | `train/FruitRot_existing_fruit_rot_18.jpg` (FruitRot)<br>`val/NutCracking_existing_nut_cracking_12.jpg` (NutCracking) |
| `5cd2bac8250c...` | 2 | **FruitRot, NutCracking** | train | `train/FruitRot_existing_fruit_rot_21.jpg` (FruitRot)<br>`train/NutCracking_existing_nut_cracking_69.jpg` (NutCracking) |
| `d9a883519792...` | 2 | **FruitRot, NutCracking** | train | `train/FruitRot_existing_fruit_rot_24.jpg` (FruitRot)<br>`train/NutCracking_existing_nut_cracking_13.jpg` (NutCracking) |
| `3ba6bab49394...` | 2 | **FruitRot, NutCracking** | test, train | `train/FruitRot_existing_fruit_rot_25.jpg` (FruitRot)<br>`test/NutCracking_existing_nut_cracking_23.jpg` (NutCracking) |
| `16c1046fcde2...` | 2 | **FruitRot, NutCracking** | train, val | `train/FruitRot_existing_fruit_rot_3.jpg` (FruitRot)<br>`val/NutCracking_existing_nut_cracking_9.jpg` (NutCracking) |
| `7fafef9d890a...` | 2 | **FruitRot, NutCracking** | train | `train/FruitRot_existing_fruit_rot_36.jpg` (FruitRot)<br>`train/NutCracking_existing_nut_cracking_55.jpg` (NutCracking) |
| `b914d49a4bac...` | 2 | **FruitRot, NutCracking** | train | `train/FruitRot_existing_fruit_rot_45.jpg` (FruitRot)<br>`train/NutCracking_existing_nut_cracking_25.jpg` (NutCracking) |
| `316e0a482b62...` | 2 | **FruitRot, NutCracking** | train | `train/FruitRot_existing_fruit_rot_46.jpg` (FruitRot)<br>`train/NutCracking_existing_nut_cracking_18.jpg` (NutCracking) |
| `d46412bd8b28...` | 2 | **FruitRot, NutCracking** | train | `train/FruitRot_existing_fruit_rot_49.jpg` (FruitRot)<br>`train/NutCracking_existing_nut_cracking_59.jpg` (NutCracking) |
| `1c53b794c7f0...` | 2 | **FruitRot, NutCracking** | train | `train/FruitRot_existing_fruit_rot_5.jpg` (FruitRot)<br>`train/NutCracking_existing_nut_cracking_11.jpg` (NutCracking) |
| `8764fa3cff36...` | 2 | **FruitRot, NutCracking** | train | `train/FruitRot_existing_fruit_rot_52.jpg` (FruitRot)<br>`train/NutCracking_existing_nut_cracking_17.jpg` (NutCracking) |
| `026cbdead614...` | 2 | **FruitRot, NutCracking** | train | `train/FruitRot_existing_fruit_rot_55.jpg` (FruitRot)<br>`train/NutCracking_existing_nut_cracking_5.jpg` (NutCracking) |
| `970555c67135...` | 2 | **FruitRot, NutCracking** | train | `train/FruitRot_existing_fruit_rot_57.jpg` (FruitRot)<br>`train/NutCracking_existing_nut_cracking_6.jpg` (NutCracking) |
| `b7d65eadd2fb...` | 2 | **FruitRot, NutCracking** | train | `train/FruitRot_existing_fruit_rot_58.jpg` (FruitRot)<br>`train/NutCracking_existing_nut_cracking_33.jpg` (NutCracking) |
| `83eda4077436...` | 2 | **FruitRot, NutCracking** | train | `train/FruitRot_existing_fruit_rot_60.jpg` (FruitRot)<br>`train/NutCracking_existing_nut_cracking_19.jpg` (NutCracking) |
| `7693b8eeb818...` | 2 | **FruitRot, NutCracking** | test, train | `train/FruitRot_existing_fruit_rot_75.jpg` (FruitRot)<br>`test/NutCracking_existing_nut_cracking_61.jpg` (NutCracking) |
| `07a3ed099d21...` | 2 | **FruitRot, NutCracking** | test, train | `train/FruitRot_existing_fruit_rot_8.jpg` (FruitRot)<br>`test/NutCracking_existing_nut_cracking_7.jpg` (NutCracking) |
| `f68bfca73e9c...` | 2 | **FruitRot, NutCracking** | train, val | `train/FruitRot_existing_fruit_rot_83.jpg` (FruitRot)<br>`val/NutCracking_existing_nut_cracking_68.jpg` (NutCracking) |
| `e6d33d7fb6c1...` | 2 | **FruitRot, NutCracking** | train, val | `train/FruitRot_existing_fruit_rot_93.jpg` (FruitRot)<br>`val/NutCracking_existing_nut_cracking_30.jpg` (NutCracking) |
| `0a0d6272fc07...` | 2 | **FruitRot, NutCracking** | test, train | `train/FruitRot_existing_fruit_rot_95.jpg` (FruitRot)<br>`test/NutCracking_existing_nut_cracking_38.jpg` (NutCracking) |
| `c1570268da49...` | 2 | **Anthracnose, Healthy** | test, train | `train/Healthy_existing_healthy_18.jpg` (Healthy)<br>`test/Anthracnose_existing_anthracnose_21.jpg` (Anthracnose) |
| `473d3c6d214b...` | 2 | **Anthracnose, Healthy** | test, train | `train/Healthy_existing_healthy_2.jpg` (Healthy)<br>`test/Anthracnose_existing_anthracnose_12.jpg` (Anthracnose) |
| `a50431d51fb5...` | 2 | **Anthracnose, Healthy** | train, val | `train/Healthy_existing_healthy_41.jpg` (Healthy)<br>`val/Anthracnose_existing_anthracnose_70.jpg` (Anthracnose) |
| `bbc98c96f621...` | 2 | **FruitRot, NutCracking** | test, train | `train/NutCracking_existing_nut_cracking_1.jpg` (NutCracking)<br>`test/FruitRot_existing_fruit_rot_4.jpg` (FruitRot) |
| `944baecc8ce0...` | 2 | **FruitRot, NutCracking** | train, val | `train/NutCracking_existing_nut_cracking_16.jpg` (NutCracking)<br>`val/FruitRot_existing_fruit_rot_44.jpg` (FruitRot) |
| `d2524fb4b71f...` | 2 | **FruitRot, NutCracking** | test, train | `train/NutCracking_existing_nut_cracking_29.jpg` (NutCracking)<br>`test/FruitRot_existing_fruit_rot_63.jpg` (FruitRot) |
| `983a39fa8505...` | 3 | **Anthracnose, FruitRot, NutCracking** | train, val | `train/NutCracking_existing_nut_cracking_3.jpg` (NutCracking)<br>`val/Anthracnose_existing_anthracnose_5.jpg` (Anthracnose)<br>`val/FruitRot_existing_fruit_rot_23.jpg` (FruitRot) |
| `7e722251795d...` | 2 | **Anthracnose, NutCracking** | train, val | `train/NutCracking_existing_nut_cracking_39.jpg` (NutCracking)<br>`val/Anthracnose_existing_anthracnose_9.jpg` (Anthracnose) |
| `3f114b855213...` | 2 | **FruitRot, NutCracking** | test, train | `train/NutCracking_existing_nut_cracking_62.jpg` (NutCracking)<br>`test/FruitRot_existing_fruit_rot_87.jpg` (FruitRot) |
| `c9c100aa6ff9...` | 2 | **Anthracnose, SootyMold** | train, val | `train/SootyMold_existing_sooty_mold_12.jpg` (SootyMold)<br>`val/Anthracnose_existing_anthracnose_11.jpg` (Anthracnose) |
| `d55f994e5035...` | 2 | **Anthracnose, SootyMold** | test, train | `train/SootyMold_existing_sooty_mold_17.jpg` (SootyMold)<br>`test/Anthracnose_existing_anthracnose_25.jpg` (Anthracnose) |
| `dced788c6e4f...` | 2 | **Anthracnose, SootyMold** | test, val | `val/Anthracnose_existing_anthracnose_14.jpg` (Anthracnose)<br>`test/SootyMold_existing_sooty_mold_20.jpg` (SootyMold) |
| `a9b0f517de8f...` | 2 | **Anthracnose, Healthy** | val | `val/Anthracnose_existing_anthracnose_39.jpg` (Anthracnose)<br>`val/Healthy_existing_healthy_40.jpg` (Healthy) |
| `9cf343f44859...` | 2 | **Anthracnose, Healthy** | test, val | `val/Anthracnose_existing_anthracnose_47.jpg` (Anthracnose)<br>`test/Healthy_existing_healthy_73.jpg` (Healthy) |
| `6b4903b5af5d...` | 3 | **Anthracnose, NutCracking, SootyMold** | test, val | `val/NutCracking_existing_nut_cracking_54.jpg` (NutCracking)<br>`test/Anthracnose_existing_anthracnose_35.jpg` (Anthracnose)<br>`test/SootyMold_existing_sooty_mold_24.jpg` (SootyMold) |
| `6ebfba1029cd...` | 2 | **FruitRot, NutCracking** | test, val | `val/NutCracking_existing_nut_cracking_57.jpg` (NutCracking)<br>`test/FruitRot_existing_fruit_rot_19.jpg` (FruitRot) |
| `efb6e87919ec...` | 2 | **FruitRot, NutCracking** | test | `test/FruitRot_existing_fruit_rot_51.jpg` (FruitRot)<br>`test/NutCracking_existing_nut_cracking_24.jpg` (NutCracking) |

---

## 2. Cross-Split Contamination Clusters

These identical images span multiple dataset splits (e.g., appear in both `train` and `val`, or `train` and `test`):

| MD5 Hash | Copies | Splits | Classes | File Manifest |
|:---|:---:|:---|:---|:---|
| `63ad9e13f745...` | 3 | train, val | Anthracnose, FruitRot, NutCracking | `train/Anthracnose_existing_anthracnose_1.jpg` (Anthracnose)<br>`train/FruitRot_existing_fruit_rot_2.jpg` (FruitRot)<br>`val/NutCracking_existing_nut_cracking_4.jpg` (NutCracking) |
| `c15ae2ccff99...` | 3 | test, train | Anthracnose, Healthy, SootyMold | `train/Anthracnose_existing_anthracnose_23.jpg` (Anthracnose)<br>`train/SootyMold_existing_sooty_mold_29.jpg` (SootyMold)<br>`test/Healthy_existing_healthy_69.jpg` (Healthy) |
| `475c0104386b...` | 3 | train, val | Anthracnose, Healthy, SootyMold | `train/Anthracnose_existing_anthracnose_24.jpg` (Anthracnose)<br>`train/SootyMold_existing_sooty_mold_25.jpg` (SootyMold)<br>`val/Healthy_existing_healthy_16.jpg` (Healthy) |
| `c21217439f07...` | 4 | train, val | Anthracnose, Healthy, NutCracking, SootyMold | `train/Anthracnose_existing_anthracnose_29.jpg` (Anthracnose)<br>`train/Healthy_existing_healthy_61.jpg` (Healthy)<br>`train/NutCracking_existing_nut_cracking_70.jpg` (NutCracking)<br>`val/SootyMold_existing_sooty_mold_47.jpg` (SootyMold) |
| `2a857c31c0a3...` | 2 | train, val | Anthracnose, NutCracking | `train/Anthracnose_existing_anthracnose_3.jpg` (Anthracnose)<br>`val/NutCracking_existing_nut_cracking_66.jpg` (NutCracking) |
| `cda02c56fc74...` | 2 | train, val | Anthracnose, Healthy | `train/Anthracnose_existing_anthracnose_32.jpg` (Anthracnose)<br>`val/Healthy_existing_healthy_28.jpg` (Healthy) |
| `af1a2d567114...` | 2 | train, val | Anthracnose, SootyMold | `train/Anthracnose_existing_anthracnose_48.jpg` (Anthracnose)<br>`val/SootyMold_existing_sooty_mold_71.jpg` (SootyMold) |
| `2cb1cb103389...` | 2 | train, val | Anthracnose, SootyMold | `train/Anthracnose_existing_anthracnose_65.jpg` (Anthracnose)<br>`val/SootyMold_existing_sooty_mold_68.jpg` (SootyMold) |
| `e98cdd6740d6...` | 2 | train, val | FruitRot, NutCracking | `train/FruitRot_existing_fruit_rot_18.jpg` (FruitRot)<br>`val/NutCracking_existing_nut_cracking_12.jpg` (NutCracking) |
| `3ba6bab49394...` | 2 | test, train | FruitRot, NutCracking | `train/FruitRot_existing_fruit_rot_25.jpg` (FruitRot)<br>`test/NutCracking_existing_nut_cracking_23.jpg` (NutCracking) |
| `16c1046fcde2...` | 2 | train, val | FruitRot, NutCracking | `train/FruitRot_existing_fruit_rot_3.jpg` (FruitRot)<br>`val/NutCracking_existing_nut_cracking_9.jpg` (NutCracking) |
| `7693b8eeb818...` | 2 | test, train | FruitRot, NutCracking | `train/FruitRot_existing_fruit_rot_75.jpg` (FruitRot)<br>`test/NutCracking_existing_nut_cracking_61.jpg` (NutCracking) |
| `07a3ed099d21...` | 2 | test, train | FruitRot, NutCracking | `train/FruitRot_existing_fruit_rot_8.jpg` (FruitRot)<br>`test/NutCracking_existing_nut_cracking_7.jpg` (NutCracking) |
| `f68bfca73e9c...` | 2 | train, val | FruitRot, NutCracking | `train/FruitRot_existing_fruit_rot_83.jpg` (FruitRot)<br>`val/NutCracking_existing_nut_cracking_68.jpg` (NutCracking) |
| `e6d33d7fb6c1...` | 2 | train, val | FruitRot, NutCracking | `train/FruitRot_existing_fruit_rot_93.jpg` (FruitRot)<br>`val/NutCracking_existing_nut_cracking_30.jpg` (NutCracking) |
| `0a0d6272fc07...` | 2 | test, train | FruitRot, NutCracking | `train/FruitRot_existing_fruit_rot_95.jpg` (FruitRot)<br>`test/NutCracking_existing_nut_cracking_38.jpg` (NutCracking) |
| `c1570268da49...` | 2 | test, train | Anthracnose, Healthy | `train/Healthy_existing_healthy_18.jpg` (Healthy)<br>`test/Anthracnose_existing_anthracnose_21.jpg` (Anthracnose) |
| `473d3c6d214b...` | 2 | test, train | Anthracnose, Healthy | `train/Healthy_existing_healthy_2.jpg` (Healthy)<br>`test/Anthracnose_existing_anthracnose_12.jpg` (Anthracnose) |
| `a50431d51fb5...` | 2 | train, val | Anthracnose, Healthy | `train/Healthy_existing_healthy_41.jpg` (Healthy)<br>`val/Anthracnose_existing_anthracnose_70.jpg` (Anthracnose) |
| `bbc98c96f621...` | 2 | test, train | FruitRot, NutCracking | `train/NutCracking_existing_nut_cracking_1.jpg` (NutCracking)<br>`test/FruitRot_existing_fruit_rot_4.jpg` (FruitRot) |
| `944baecc8ce0...` | 2 | train, val | FruitRot, NutCracking | `train/NutCracking_existing_nut_cracking_16.jpg` (NutCracking)<br>`val/FruitRot_existing_fruit_rot_44.jpg` (FruitRot) |
| `d2524fb4b71f...` | 2 | test, train | FruitRot, NutCracking | `train/NutCracking_existing_nut_cracking_29.jpg` (NutCracking)<br>`test/FruitRot_existing_fruit_rot_63.jpg` (FruitRot) |
| `983a39fa8505...` | 3 | train, val | Anthracnose, FruitRot, NutCracking | `train/NutCracking_existing_nut_cracking_3.jpg` (NutCracking)<br>`val/Anthracnose_existing_anthracnose_5.jpg` (Anthracnose)<br>`val/FruitRot_existing_fruit_rot_23.jpg` (FruitRot) |
| `7e722251795d...` | 2 | train, val | Anthracnose, NutCracking | `train/NutCracking_existing_nut_cracking_39.jpg` (NutCracking)<br>`val/Anthracnose_existing_anthracnose_9.jpg` (Anthracnose) |
| `3f114b855213...` | 2 | test, train | FruitRot, NutCracking | `train/NutCracking_existing_nut_cracking_62.jpg` (NutCracking)<br>`test/FruitRot_existing_fruit_rot_87.jpg` (FruitRot) |
| `c9c100aa6ff9...` | 2 | train, val | Anthracnose, SootyMold | `train/SootyMold_existing_sooty_mold_12.jpg` (SootyMold)<br>`val/Anthracnose_existing_anthracnose_11.jpg` (Anthracnose) |
| `d55f994e5035...` | 2 | test, train | Anthracnose, SootyMold | `train/SootyMold_existing_sooty_mold_17.jpg` (SootyMold)<br>`test/Anthracnose_existing_anthracnose_25.jpg` (Anthracnose) |
| `dced788c6e4f...` | 2 | test, val | Anthracnose, SootyMold | `val/Anthracnose_existing_anthracnose_14.jpg` (Anthracnose)<br>`test/SootyMold_existing_sooty_mold_20.jpg` (SootyMold) |
| `9cf343f44859...` | 2 | test, val | Anthracnose, Healthy | `val/Anthracnose_existing_anthracnose_47.jpg` (Anthracnose)<br>`test/Healthy_existing_healthy_73.jpg` (Healthy) |
| `6b4903b5af5d...` | 3 | test, val | Anthracnose, NutCracking, SootyMold | `val/NutCracking_existing_nut_cracking_54.jpg` (NutCracking)<br>`test/Anthracnose_existing_anthracnose_35.jpg` (Anthracnose)<br>`test/SootyMold_existing_sooty_mold_24.jpg` (SootyMold) |
| `6ebfba1029cd...` | 2 | test, val | FruitRot, NutCracking | `val/NutCracking_existing_nut_cracking_57.jpg` (NutCracking)<br>`test/FruitRot_existing_fruit_rot_19.jpg` (FruitRot) |

---

## 3. Recommended Remediation & Prevention Strategy

1. **Quarantine Conflicting Clusters**: Images in conflicting clusters must not be used for model training or benchmark evaluation until an agronomist resolves the ground-truth diagnosis.
2. **Deduplication Keyed by SHA256**: All dataset ingestion scripts must deduplicate strictly on content SHA256 hashes rather than filenames.
3. **Grouped Split Allocation (Cluster-Aware Splitting)**: If duplicates are retained for augmentation purposes, all copies sharing the same hash must be assigned to the **exact same split** (`GroupKFold` or hash-bucketed) to prevent train-test data leakage.
