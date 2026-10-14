# ArecaVision 2.0 — Rollback & Recovery Guide

## 1. Overview & Golden Baseline

This document provides definitive, fail-safe procedures for rolling back changes, recovering runtime databases, and restoring the ArecaVision 2.0 repository to verified historical baselines.

### Primary Verified Baseline
- **Commit Hash**: `35b3b904cc03866f52fbfa44a80547dd2785c93a` (`35b3b90`)
- **Date**: 2026-10-12
- **Description**: Clean dataset manifest generated (`backend/data/clean_dataset_manifest.json`), 130 cross-class label conflicts eliminated, data leakage quarantined, full ML verification passed.

### Historical Commit Checkpoints
- `b65bc88`: Unclamped gate scoring and trilingual (EN/KN/HI) agronomic localization.
- `932874e`: Hardened gatekeeper thresholds (`0.7404 / 0.5180`) and removal of synthetic YOLO boxes.
- `0ec7562`: Guest public access permitted on `/detection` and `/diseases`.

---

## 2. Emergency Recovery Scenarios

### Scenario A: Discard Working Tree Changes (Code Only)

To discard uncommitted changes in tracked files without touching the database or model weights:

```powershell
# 1. Review all unstaged modifications
git diff

# 2. Revert modifications to a specific file (e.g. backend/server/app.py)
git restore backend/server/app.py

# 3. Discard all working tree modifications across all tracked files
git restore .
```

> [!CAUTION]
> `git restore .` only reverts tracked files. Untracked files and ignored files (such as local databases) will remain untouched.

---

### Scenario B: Hard Reset to Golden Baseline `35b3b90`

If the working tree or staging index enters an inconsistent state and must be reset entirely to the Phase 1 entry baseline:

```powershell
# 1. Verify working directory status
git status

# 2. Unstage any currently staged changes
git restore --staged .

# 3. Hard reset tracked files to commit 35b3b90
git reset --hard 35b3b904cc03866f52fbfa44a80547dd2785c93a

# 4. Confirm clean tree
git status
```

> [!IMPORTANT]
> `git reset --hard` will **NOT** delete files that are ignored by `.gitignore` (such as `backend/data/arecavision.db` or model weights).

---

### Scenario C: Database Recovery & Restoration

The operational runtime database `backend/data/arecavision.db` contains diagnostic scan telemetry and GIS digital twin state. The root `backend/arecavision.db` file is an empty (0 bytes) placeholder untracked from Git.

#### Local Backup Storage
During Phase 1 hardening, pre-modification snapshots were preserved in the persistent workspace scratch directory:
- `C:\Users\Hrushikesh Mirji\.gemini\antigravity\brain\fe624d87-e861-458c-a7da-19cd9caa26ab\scratch\backup\arecavision_data.db` (268.8 MB)
- `C:\Users\Hrushikesh Mirji\.gemini\antigravity\brain\fe624d87-e861-458c-a7da-19cd9caa26ab\scratch\backup\arecavision_root.db` (0 bytes placeholder)
- `C:\Users\Hrushikesh Mirji\.gemini\antigravity\brain\fe624d87-e861-458c-a7da-19cd9caa26ab\scratch\backup\auth_check.json` (5.2 KB)

#### Database Restoration Commands

If the SQLite database becomes corrupted or needs to be reset to its pristine state:

```powershell
# 1. Terminate any running backend server processes to release SQLite WAL locks
Get-Process -Name "python" | Stop-Process -Force

# 2. Remove lingering WAL journal and shared-memory files if present
Remove-Item -Path "D:\ArecaVision_Combined\backend\data\arecavision.db-wal" -ErrorAction SilentlyContinue
Remove-Item -Path "D:\ArecaVision_Combined\backend\data\arecavision.db-shm" -ErrorAction SilentlyContinue

# 3. Restore the 268MB operational database from scratch backup
Copy-Item `
  -Path "C:\Users\Hrushikesh Mirji\.gemini\antigravity\brain\fe624d87-e861-458c-a7da-19cd9caa26ab\scratch\backup\arecavision_data.db" `
  -Destination "D:\ArecaVision_Combined\backend\data\arecavision.db" `
  -Force

# 4. Verify restored database size (must be ~268,795,904 bytes)
(Get-Item "D:\ArecaVision_Combined\backend\data\arecavision.db").Length
```

---

### Scenario D: Re-Tracking a File Untracked from Git

If `backend/arecavision.db` or `backend/tests/results/auth_check.json` was untracked (`git rm --cached`) and needs to be re-staged:

```powershell
# 1. Unstage the cached deletion
git restore --staged backend/arecavision.db
git restore --staged backend/tests/results/auth_check.json

# 2. Confirm both files return to unmodified tracked state
git status
```

---

## 3. Model Weight Protection & Verification

Model weights must **NEVER** be deleted, overwritten, or modified during git checkouts or rollbacks.

### Checkpoint File Inventory
Run this PowerShell command to verify that all three model checkpoints exist with their expected non-zero sizes:

```powershell
Get-ChildItem -Path @(
  "D:\ArecaVision_Combined\backend\cnn\checkpoints\cnn_efficientnet_b0.pth",
  "D:\ArecaVision_Combined\backend\yolo\checkpoints\best.pt",
  "D:\ArecaVision_Combined\backend\vit\checkpoints\vit_b16.pth"
) | Select-Object FullName, Length, LastWriteTime
```

### Expected Checkpoint Profile
| Model | Path | Verified File Size | Architecture |
|---|---|---|---|
| Gatekeeper | `backend/cnn/checkpoints/cnn_efficientnet_b0.pth` | 18,972,509 bytes (~18.1 MiB / 18.97 MB) | EfficientNet-B0 (Binary) |
| Detector | `backend/yolo/checkpoints/best.pt` | 24,464,679 bytes (~23.3 MiB / 24.46 MB) | YOLOv8n (Ultralytics) |
| Classifier | `backend/vit/checkpoints/vit_b16.pth` | 343,294,539 bytes (~327.4 MiB / 343.29 MB) | ViT-B/16 (timm) |

---

## 4. Post-Rollback Health Verification

After performing any rollback or database restoration:

1. **Verify Git Status**:
   ```powershell
   git status
   ```
   Ensure no unintended deletions or untracked changes remain.

2. **Verify Database Ignore Rules**:
   ```powershell
   git check-ignore -v backend/data/arecavision.db
   git check-ignore -v backend/arecavision.db
   git check-ignore -v backend/tests/results/auth_check.json
   ```
   All three commands must output their matching rule in `.gitignore`.

3. **Verify FastAPI Backend Initialization**:
   ```powershell
   & "D:\ArecaVision_Combined\backend\venv\Scripts\python.exe" -c "from server.app import app; print('Backend loaded successfully')"
   ```
