from __future__ import annotations

import argparse
from pathlib import Path

import torch
import torch.nn as nn
from PIL import Image
from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0


DEFAULT_CHECKPOINT = (
    Path(__file__).resolve().parent
    / "data"
    / "kaggle_arecanut_candidate"
    / "model_candidate_efficientnet_b0.pth"
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run an experimental four-class Arecanut candidate; not a diagnosis."
    )
    parser.add_argument("image", type=Path, help="Path to an image to inspect")
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    parser.add_argument(
        "--research-only",
        action="store_true",
        help="Show raw candidate scores despite failed external validation; never use diagnostically.",
    )
    args = parser.parse_args()

    if not args.research_only:
        print("BLOCKED: this candidate failed external local screening (25.3% accuracy on 91 images).")
        print("No disease prediction will be made. Pass --research-only only to inspect raw experimental scores.")
        raise SystemExit(2)
    if not args.image.is_file():
        parser.error(f"Image not found: {args.image}")
    if not args.checkpoint.is_file():
        parser.error(f"Candidate checkpoint not found: {args.checkpoint}")

    device = torch.device("cpu")
    checkpoint = torch.load(args.checkpoint, map_location=device, weights_only=True)
    classes = checkpoint.get("classes")
    expected_classes = [
        "Healthy",
        "FruitRot",
        "StemBleeding",
        "PhytoplasmaYellowLeaf",
    ]
    if classes != expected_classes:
        raise RuntimeError(f"Unexpected candidate classes: {classes}")

    model = efficientnet_b0(weights=None)
    model.classifier[1] = nn.Linear(model.classifier[1].in_features, len(classes))
    model.load_state_dict(checkpoint["model_state_dict"], strict=True)
    model.eval()

    weights = EfficientNet_B0_Weights.DEFAULT
    with Image.open(args.image) as image:
        tensor = weights.transforms()(image.convert("RGB")).unsqueeze(0)
    with torch.inference_mode():
        probabilities = model(tensor).softmax(dim=1)[0]

    ordered = sorted(
        zip(classes, probabilities.tolist()), key=lambda result: result[1], reverse=True
    )
    predicted_class, confidence = ordered[0]

    print("RESEARCH-ONLY SCORES; this candidate failed external local screening.")
    print("Not a diagnosis or treatment recommendation. Disposition: REVIEW REQUIRED.")
    print("Supported candidate outputs: Healthy, FruitRot, StemBleeding, PhytoplasmaYellowLeaf.")
    print("Leaf Spot is not included; uncertain images should be reviewed by an expert.")
    print(f"Highest raw score (not calibrated): {predicted_class} ({confidence:.1%})")
    for class_name, probability in ordered:
        print(f"  {class_name}: {probability:.1%}")


if __name__ == "__main__":
    main()