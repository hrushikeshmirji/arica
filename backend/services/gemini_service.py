"""
services/gemini_service.py — Multimodal Google Gemini Agronomy Pathologist Copilot.
Provides second-opinion validation, visual symptom analysis, and trilingual Q&A.
"""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import requests

_HERE = Path(__file__).resolve().parent.parent
_ENV_FILE = _HERE / ".env"


def get_gemini_api_key() -> str | None:
    """Retrieve GEMINI_API_KEY from environment or backend/.env file."""
    key = os.environ.get("GEMINI_API_KEY")
    if key and key.strip():
        return key.strip()
    if _ENV_FILE.is_file():
        try:
            with open(_ENV_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("GEMINI_API_KEY="):
                        return line.split("=", 1)[1].strip()
        except Exception:
            pass
    return None


def is_gemini_available() -> bool:
    """Check if a valid Gemini API key is configured."""
    return get_gemini_api_key() is not None


def verify_diagnosis(
    image_rgb: np.ndarray,
    local_disease: str | None = None,
    timeout: float = 12.0,
) -> dict[str, Any]:
    """
    Perform multimodal verification of arecanut disease using Gemini 2.5 Flash.
    Returns structured analysis or a graceful fallback if offline.
    """
    api_key = get_gemini_api_key()
    if not api_key:
        return {"available": False, "reason": "GEMINI_API_KEY not configured"}

    try:
        # Resize image if larger than 640px to ensure rapid transmission
        h, w = image_rgb.shape[:2]
        img_to_send = image_rgb
        if max(h, w) > 640:
            scale = 640.0 / max(h, w)
            img_to_send = cv2.resize(
                image_rgb, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA
            )

        # Convert RGB to BGR for cv2 JPEG encode
        bgr = cv2.cvtColor(img_to_send, cv2.COLOR_RGB2BGR)
        success, buf = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, 82])
        if not success:
            return {"available": False, "reason": "Failed to encode image for Gemini"}

        b64_img = base64.b64encode(buf).decode("utf-8")

        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
        prompt = (
            "You are an expert plant pathologist specializing in Arecanut (Areca catechu) in India, "
            "strictly adhering to ICAR-CPCRI and CIBRC standards.\n"
            "Classify the primary condition shown in this image among these standardized classes:\n"
            "- Fruit Rot (Koleroga)\n"
            "- Nut Cracking\n"
            "- Yellow Leaf Disease\n"
            "- Leaf Spot Complex\n"
            "- Anthracnose\n"
            "- Bud Borer\n"
            "- Sooty Mold\n"
            "- Stem Bleeding\n"
            "- Stem Cracking\n"
            "- Healthy\n"
            "- Not_Arecanut\n\n"
            "Note: The image may be a multi-panel collage or web advisory graphic with side-by-side symptom photos.\n"
            "Provide your response as valid JSON with the following keys:\n"
            "{\n"
            '  "disease": "Standardized class name",\n'
            '  "confidence": 95.0,\n'
            '  "observations": "Concise botanical description of symptoms and visual cues",\n'
            '  "recommendedAction": "Immediate cultural, organic, and CIBRC chemical management",\n'
            '  "isArecanut": true\n'
            "}"
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": b64_img,
                            }
                        },
                    ]
                }
            ],
            "generationConfig": {
                "response_mime_type": "application/json",
                "temperature": 0.1,
            },
        }

        models_to_try = ["gemini-2.5-flash", "gemini-flash-latest"]
        resp = None
        for mod in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={api_key}"
            try:
                resp = requests.post(url, json=payload, timeout=timeout)
                if resp.status_code == 200:
                    break
            except Exception:
                continue

        if resp is None or resp.status_code != 200:
            status = resp.status_code if resp is not None else "Timeout"
            return {
                "available": False,
                "reason": f"Gemini API returned status {status} (overloaded or rate limited)",
            }

        res_json = resp.json()
        raw_text = res_json["candidates"][0]["content"]["parts"][0]["text"]
        parsed = json.loads(raw_text)

        g_disease = parsed.get("disease", "Unknown")
        g_conf = float(parsed.get("confidence", 85.0))
        g_obs = parsed.get("observations", "")
        g_rec = parsed.get("recommendedAction", "")
        g_is_areca = bool(parsed.get("isArecanut", True))

        agrees = False
        if local_disease and g_disease:
            norm_local = local_disease.lower().replace(" ", "").replace("_", "")
            norm_g = g_disease.lower().replace(" ", "").replace("_", "")
            agrees = (norm_local in norm_g) or (norm_g in norm_local)

        return {
            "available": True,
            "provider": "Google Gemini 2.5 Flash",
            "verifiedDisease": g_disease,
            "confidence": g_conf,
            "observations": g_obs,
            "recommendedAction": g_rec,
            "isArecanut": g_is_areca,
            "agreesWithLocalModel": agrees,
        }

    except requests.exceptions.Timeout:
        return {"available": False, "reason": "Gemini request timed out"}
    except Exception as e:
        return {"available": False, "reason": str(e)}


def ask_agronomy_assistant(
    question: str,
    language: str = "en",
    context_disease: str | None = None,
    image_rgb: np.ndarray | None = None,
    timeout: float = 15.0,
) -> dict[str, Any]:
    """
    Trilingual agronomy advisory chat assistant for arecanut farmers.
    Supported languages: 'en' (English), 'kn' (Kannada), 'hi' (Hindi).
    """
    api_key = get_gemini_api_key()
    if not api_key:
        return {
            "available": False,
            "answer": "Gemini API key is not configured. Please add GEMINI_API_KEY to your environment.",
        }

    lang_instructions = {
        "kn": "Respond completely in clear, farmer-friendly Kannada (ಕನ್ನಡ). Use terms familiar to Malnad and coastal Karnataka arecanut growers.",
        "hi": "Respond completely in clear, farmer-friendly Hindi (हिन्दी).",
        "en": "Respond in clear, professional English tailored to arecanut growers and agronomists.",
    }
    lang_prompt = lang_instructions.get(language, lang_instructions["en"])

    context_str = f"The current diagnosis on the palm is: {context_disease}." if context_disease else ""

    system_instruction = (
        "You are 'ArecaVision AI Agronomist', a compassionate, certified expert advisor for arecanut (Areca catechu) growers. "
        "Your recommendations must align strictly with ICAR - Central Plantation Crops Research Institute (CPCRI) and "
        "Central Insecticides Board & Registration Committee (CIBRC) approved practices. "
        "Never recommend banned organophosphates (like Chlorpyrifos) for crown drenching. "
        "Always provide practical dosage (e.g. 1% Bordeaux mixture = 10g CuSO4 + 10g Quicklime / 1L water), application timing, and safety guidance.\n"
        f"{lang_prompt}\n"
        f"{context_str}"
    )

    parts: list[dict[str, Any]] = [{"text": f"Farmer Question: {question}"}]

    if image_rgb is not None:
        try:
            h, w = image_rgb.shape[:2]
            scale = 512.0 / max(h, w) if max(h, w) > 512 else 1.0
            resized = cv2.resize(image_rgb, (int(w * scale), int(h * scale))) if scale < 1.0 else image_rgb
            bgr = cv2.cvtColor(resized, cv2.COLOR_RGB2BGR)
            _, buf = cv2.imencode(".jpg", bgr, [cv2.IMWRITE_JPEG_QUALITY, 80])
            b64_img = base64.b64encode(buf).decode("utf-8")
            parts.append({
                "inline_data": {
                    "mime_type": "image/jpeg",
                    "data": b64_img,
                }
            })
        except Exception:
            pass

    models_to_try = ["gemini-2.5-flash", "gemini-flash-latest"]
    payload = {
        "system_instruction": {"parts": [{"text": system_instruction}]},
        "contents": [{"parts": parts}],
        "generationConfig": {"temperature": 0.3, "maxOutputTokens": 800},
    }

    try:
        resp = None
        for mod in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{mod}:generateContent?key={api_key}"
            try:
                resp = requests.post(url, json=payload, timeout=timeout)
                if resp.status_code == 200:
                    break
            except Exception:
                continue

        if resp is not None and resp.status_code == 200:
            reply = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            return {
                "available": True,
                "answer": reply,
                "language": language,
                "disclaimer": "Grounded in ICAR-CPCRI & CIBRC Package of Practices.",
            }
        err_code = resp.status_code if resp is not None else "Timeout"
        return {
            "available": False,
            "answer": f"Agronomy assistant service unavailable (Error {err_code}).",
        }
    except Exception as e:
        return {"available": False, "answer": f"Unable to reach advisory service: {e}"}
