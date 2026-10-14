"""
backend/tests/verify_current_api.py
Tests the live backend server on port 8000 using multipart/form-data.
"""

import urllib.request
import json
import time

def test_api(image_path, expected_title):
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    with open(image_path, "rb") as f:
        img_bytes = f.read()

    headers_part = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="test.jpg"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("latin1")
    footer_part = f"\r\n--{boundary}--\r\n".encode("latin1")
    body = headers_part + img_bytes + footer_part

    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/detect",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    res = json.loads(urllib.request.urlopen(req).read().decode())
    job_id = res["data"]["job_id"]
    print(f"Submitted {image_path} -> Job {job_id}")

    for _ in range(40):
        time.sleep(0.5)
        job_res = json.loads(urllib.request.urlopen(f"http://127.0.0.1:8000/api/v1/jobs/{job_id}").read().decode())
        status = job_res["data"]["status"]
        if status == "done":
            r = job_res["data"]["result"]
            print(f"  [RESULT] Disease: '{r.get('disease')}' | Stage: '{r.get('stage')}' | Confidence: {r.get('confidence')}%")
            diff = [(d["disease"], d["probability"]) for d in r.get("differentialDiagnosis", [])[:3]]
            print(f"  Differential: {diff}")
            return r
        elif status == "failed":
            print(f"  [FAILED]: {job_res['data'].get('error')}")
            return None
    print("  [TIMEOUT]")
    return None

if __name__ == "__main__":
    print("=== 1. Fruit Rot Real Image Test ===")
    test_api("backend/data/uploads/job-bfd163d5cc18.jpg", "Fruit Rot (Koleroga)")

    print("\n=== 2. Nut Cracking Real Image Test ===")
    test_api("backend/data/uploads/job-50d6db5a8310.jpg", "Nut Cracking")

    print("\n=== 3. Leaf Symptom Real Image Test ===")
    test_api("backend/data/uploads/job-88dd4945ada1.jpg", "Leaf Spot Complex")
