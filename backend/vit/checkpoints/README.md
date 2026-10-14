# Model Checkpoints Directory

Place the trained model weight files here:
- `vit_b16.pth` (Vision Transformer weights, ~343MB)

Due to GitHub's 100MB file limit, large binary weights are distributed separately or generated via training scripts in `backend/`:
```bash
python backend/train_vit.py
```
