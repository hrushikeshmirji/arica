# Phase 3B: Class Mapping Governance and Raw Data Provenance Report

## 1. Evaluation of Configured 11-Class Schema

The file `backend/yolo/dataset.yaml` defines 11 classes (`nc: 11`), while the current YOLO dataset only contains samples for 5 classes.

### Investigation of Raw Source Directories (`D:\dataset_raw\dataset_raw`):

| Class ID | Class Name | Raw Category Folder | Raw Images Count | YOLO Dataset Images | Governance Status |
|:---:|:---|:---|:---:|:---:|:---|
| 0 | **Anthracnose** | `areca_diseased_fungal_anthracnose` | 70 | 72 | Verified Active in YOLO |
| 1 | **BudBorer** | `areca_pest_bud_borer` | 51 | 0 | **Available in Raw Dataset (51 images)** — Never Ingested into YOLO |
| 2 | **FruitRot** | `areca_diseased_fungal_fruit_rot` | 78 | 79 | Verified Active in YOLO |
| 3 | **Healthy** | `areca_healthy` | 73 | 73 | Verified Active in YOLO |
| 4 | **LeafSpotComplex** | `areca_diseased_fungal_leaf_spot` | 51 | 0 | **Available in Raw Dataset (51 images)** — Never Ingested into YOLO |
| 5 | **NutCracking** | `areca_diseased_physiological_nut_cracking` | 66 | 66 | Verified Active in YOLO |
| 6 | **PhytoplasmaYellowLeaf** | `areca_diseased_phytoplasma_yellow_leaf` | 51 | 0 | **Available in Raw Dataset (51 images)** — Never Ingested into YOLO |
| 7 | **SootyMold** | `areca_diseased_fungal_sooty_mold` | 59 | 59 | Verified Active in YOLO |
| 8 | **StemBleeding** | `areca_diseased_fungal_stem_bleeding` | 51 | 0 | **Available in Raw Dataset (51 images)** — Never Ingested into YOLO |
| 9 | **StemCracking** | `areca_diseased_physiological_stem_cracking` | 51 | 0 | **Available in Raw Dataset (51 images)** — Never Ingested into YOLO |
| 10 | **YellowLeaf** | `areca_diseased_yellow_leaf_chlorosis` | 51 | 0 | **Available in Raw Dataset (51 images)** — Never Ingested into YOLO |

---

## 2. Governance Findings & Defensible Mapping Rules

1. **Why 6 Classes Were Missing in YOLO**: The 6 missing classes (`BudBorer`, `LeafSpotComplex`, `PhytoplasmaYellowLeaf`, `StemBleeding`, `StemCracking`, `YellowLeaf`) **actually exist in `D:\dataset_raw\dataset_raw`** (51 images each). They were collected after the initial 5-class YOLO dataset was split, but were never formatted into YOLO splits.
2. **Strict Class ID Preservation**: Class IDs 0 through 10 must **NOT** be renumbered or compressed. The entire application (`AGRONOMIC_CATALOG`, ViT predictor, frontend localization, and API contracts) depends on the exact 11-class indices defined in `config.py` and `dataset.yaml`.
3. **Pathology Nature of Diseases**:
   - **Focal Detectable Lesions**: `Anthracnose` (leaf/nut spots), `FruitRot` (water-soaked nut lesions), `NutCracking` (split nut husks), `SootyMold` (black coating), `StemBleeding` (exudate lesions), `StemCracking` (longitudinal fissures), `LeafSpotComplex` (circular necrotic lesions).
   - **Systemic / Diffuse Pathologies**: `PhytoplasmaYellowLeaf` and `YellowLeaf` represent systemic vascular chlorosis of whole fronds with no distinct local lesion boundaries. These are naturally better suited to ViT full-frame attention than discrete bounding box detection.
   - **Healthy Palms**: No lesions; must be treated as negative background images.
