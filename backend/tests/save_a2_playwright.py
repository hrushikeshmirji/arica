import json
import os

RESULTS_DIR = r"D:\ArecaVision_Combined\backend\tests\results"
os.makedirs(RESULTS_DIR, exist_ok=True)

data = {
  "detection_page": {
    "1_dataset_fruit_rot": {
      "image": "1_dataset_fruit_rot.jpg",
      "jobStatus": "done",
      "request": {
        "url": "http://localhost:8000/api/v1/detect",
        "method": "POST",
        "contentType": "multipart/form-data; boundary=----WebKitFormBoundarysUky70fAuA4zBBBp"
      },
      "gate_score": 100.0,
      "stage": "Review Required",
      "disease": "Review Required: No Lesions Detected (Fruit Rot (Koleroga))",
      "confidence": 61.8,
      "vit_top3": [
        ["Fruit Rot (Koleroga)", 61.8],
        ["Nut Cracking", 20.9],
        ["Anthracnose", 10.0]
      ],
      "displayedText": "Review Required: No Lesions Detected (Fruit Rot (Koleroga))"
    },
    "2_dataset_healthy": {
      "image": "2_dataset_healthy.jpg",
      "jobStatus": "done",
      "request": {
        "url": "http://localhost:8000/api/v1/detect",
        "method": "POST",
        "contentType": "multipart/form-data; boundary=----WebKitFormBoundaryvfBsbo1s4rABJYaj"
      },
      "gate_score": 99.8,
      "stage": "Low confidence",
      "disease": "Low confidence: Healthy",
      "confidence": 58.2,
      "vit_top3": [
        ["Healthy", 58.2],
        ["Anthracnose", 13.9],
        ["Stem Cracking", 4.9]
      ],
      "displayedText": "Low confidence: Healthy"
    },
    "3_alpha_png": {
      "image": "3_alpha.png",
      "jobStatus": "done",
      "request": {
        "url": "http://localhost:8000/api/v1/detect",
        "method": "POST",
        "contentType": "multipart/form-data; boundary=----WebKitFormBoundaryQlxvjMXT70VWXF7i"
      },
      "gate_score": 100.0,
      "stage": "Review Required",
      "disease": "Review Required: No Lesions Detected (Fruit Rot (Koleroga))",
      "confidence": 61.8,
      "vit_top3": [
        ["Fruit Rot (Koleroga)", 61.8],
        ["Nut Cracking", 20.9],
        ["Anthracnose", 10.0]
      ],
      "displayedText": "Review Required: No Lesions Detected (Fruit Rot (Koleroga))"
    },
    "4_format_webp": {
      "image": "4_format.webp",
      "jobStatus": "done",
      "request": {
        "url": "http://localhost:8000/api/v1/detect",
        "method": "POST",
        "contentType": "multipart/form-data; boundary=----WebKitFormBoundary2KajZPhhQqfIAEow"
      },
      "gate_score": 99.8,
      "stage": "Low confidence",
      "disease": "Low confidence: Healthy",
      "confidence": 60.3,
      "vit_top3": [
        ["Healthy", 60.3],
        ["Anthracnose", 12.5],
        ["Stem Cracking", 4.7]
      ],
      "displayedText": "Low confidence: Healthy"
    },
    "5_exif_rotated": {
      "image": "5_exif_rotated.jpg",
      "jobStatus": "done",
      "request": {
        "url": "http://localhost:8000/api/v1/detect",
        "method": "POST",
        "contentType": "multipart/form-data; boundary=----WebKitFormBoundary4yxnjkJAFeuE7NDW"
      },
      "gate_score": 100.0,
      "stage": "Review Required",
      "disease": "Review Required: No Lesions Detected (Fruit Rot (Koleroga))",
      "confidence": 66.8,
      "vit_top3": [
        ["Fruit Rot (Koleroga)", 66.8],
        ["Nut Cracking", 23.9],
        ["Anthracnose", 2.5]
      ],
      "displayedText": "Review Required: No Lesions Detected (Fruit Rot (Koleroga))"
    },
    "6_non_areca": {
      "image": "6_non_areca.jpg",
      "jobStatus": "done",
      "request": {
        "url": "http://localhost:8000/api/v1/detect",
        "method": "POST",
        "contentType": "multipart/form-data; boundary=----WebKitFormBoundarySBIqGtQMDIORmius"
      },
      "gate_score": 99.8,
      "stage": "Gatekeeper Defense",
      "disease": "Not an Arecanut image",
      "confidence": 99.8,
      "vit_top3": [],
      "displayedText": "Not an Arecanut Image — Please Upload an Arecanut Photo"
    }
  },
  "dashboard_page": {
    "1_dataset_fruit_rot": {
      "image": "1_dataset_fruit_rot.jpg",
      "jobStatus": "done",
      "request": {
        "url": "http://localhost:8000/api/v1/detect",
        "method": "POST",
        "contentType": "multipart/form-data; boundary=----WebKitFormBoundary02IOQ0tzihndmmtl"
      },
      "gate_score": 100.0,
      "stage": "Review Required",
      "disease": "Review Required: No Lesions Detected (Fruit Rot (Koleroga))",
      "confidence": 61.8,
      "vit_top3": [
        ["Fruit Rot (Koleroga)", 61.8],
        ["Nut Cracking", 20.9],
        ["Anthracnose", 10.0]
      ],
      "displayedText": "Review Required: No Lesions Detected (Fruit Rot (Koleroga))"
    },
    "2_dataset_healthy": {
      "image": "2_dataset_healthy.jpg",
      "jobStatus": "done",
      "request": {
        "url": "http://localhost:8000/api/v1/detect",
        "method": "POST",
        "contentType": "multipart/form-data; boundary=----WebKitFormBoundaryi41AMjVXoHBzPo9A"
      },
      "gate_score": 99.8,
      "stage": "Low confidence",
      "disease": "Low confidence: Healthy",
      "confidence": 58.2,
      "vit_top3": [
        ["Healthy", 58.2],
        ["Anthracnose", 13.9],
        ["Stem Cracking", 4.9]
      ],
      "displayedText": "Low confidence: Healthy"
    },
    "3_alpha_png": {
      "image": "3_alpha.png",
      "jobStatus": "done",
      "request": {
        "url": "http://localhost:8000/api/v1/detect",
        "method": "POST",
        "contentType": "multipart/form-data; boundary=----WebKitFormBoundaryAWbHCTVqLxqfdqTi"
      },
      "gate_score": 100.0,
      "stage": "Review Required",
      "disease": "Review Required: No Lesions Detected (Fruit Rot (Koleroga))",
      "confidence": 61.8,
      "vit_top3": [
        ["Fruit Rot (Koleroga)", 61.8],
        ["Nut Cracking", 20.9],
        ["Anthracnose", 10.0]
      ],
      "displayedText": "Review Required: No Lesions Detected (Fruit Rot (Koleroga))"
    },
    "4_format_webp": {
      "image": "4_format.webp",
      "jobStatus": "done",
      "request": {
        "url": "http://localhost:8000/api/v1/detect",
        "method": "POST",
        "contentType": "multipart/form-data; boundary=----WebKitFormBoundaryIS8eIDH9OSeyBlUl"
      },
      "gate_score": 99.8,
      "stage": "Low confidence",
      "disease": "Low confidence: Healthy",
      "confidence": 60.3,
      "vit_top3": [
        ["Healthy", 60.3],
        ["Anthracnose", 12.5],
        ["Stem Cracking", 4.7]
      ],
      "displayedText": "Low confidence: Healthy"
    },
    "5_exif_rotated": {
      "image": "5_exif_rotated.jpg",
      "jobStatus": "done",
      "request": {
        "url": "http://localhost:8000/api/v1/detect",
        "method": "POST",
        "contentType": "multipart/form-data; boundary=----WebKitFormBoundaryBjaJsHKJ5Vf8rnnS"
      },
      "gate_score": 100.0,
      "stage": "Review Required",
      "disease": "Review Required: No Lesions Detected (Fruit Rot (Koleroga))",
      "confidence": 66.8,
      "vit_top3": [
        ["Fruit Rot (Koleroga)", 66.8],
        ["Nut Cracking", 23.9],
        ["Anthracnose", 2.5]
      ],
      "displayedText": "Review Required: No Lesions Detected (Fruit Rot (Koleroga))"
    },
    "6_non_areca": {
      "image": "6_non_areca.jpg",
      "jobStatus": "done",
      "request": {
        "url": "http://localhost:8000/api/v1/detect",
        "method": "POST",
        "contentType": "multipart/form-data; boundary=----WebKitFormBoundary0aBzkBgZRNAUi3lb"
      },
      "gate_score": 99.8,
      "stage": "Gatekeeper Defense",
      "disease": "Not an Arecanut image",
      "confidence": 99.8,
      "vit_top3": [],
      "displayedText": "Not an Arecanut Image — Please Upload an Arecanut Photo"
    }
  }
}

out_path = os.path.join(RESULTS_DIR, "a2_playwright_experiment.json")
with open(out_path, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
print("Saved to", out_path)
