"""CIRCULO - Image Scan & Auto-Fill Service
Uses PIL to analyze uploaded item photos and extract:
  - Item name / model  (from filename keyword matching against capabilities dict)
  - Category & capabilities (from capabilities dictionary)
  - Condition estimate  (from image brightness, contrast & quality analysis)

100% offline — no external AI API required.
"""
import os
import re
import json
import uuid
import base64
import requests
from difflib import SequenceMatcher
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from config import CAPABILITIES_PATH, ASSETS_DIR, GEMINI_MODEL, GEMINI_API_VERSION


# ─────────────────────────────────────────────
# Gemini API Helper
# ─────────────────────────────────────────────

def get_gemini_api_key() -> Optional[str]:
    """Retrieve Gemini API key from Streamlit secrets or environment variables."""
    try:
        import streamlit as st
        if "GEMINI_API_KEY" in st.secrets:
            key = str(st.secrets["GEMINI_API_KEY"]).strip()
            if key and key != "YOUR_GEMINI_API_KEY_HERE":
                return key
    except Exception:
        pass

    env_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if env_key and env_key != "YOUR_GEMINI_API_KEY_HERE":
        return env_key
    return None


def get_gemini_model() -> str:
    """Retrieve model name from Streamlit secrets, environment, or config default."""
    try:
        import streamlit as st
        if "GEMINI_MODEL" in st.secrets:
            return str(st.secrets["GEMINI_MODEL"]).strip()
    except Exception:
        pass
    return os.environ.get("GEMINI_MODEL", GEMINI_MODEL).strip()


def _call_gemini_vision(img_bytes: bytes, mime_type: str, api_key: str) -> Optional[Dict[str, Any]]:
    """
    Call Google Gemini Multimodal Vision API to identify the item, category,
    capabilities, and condition from raw image bytes.
    """
    try:
        model = get_gemini_model()
        b64_data = base64.b64encode(img_bytes).decode("utf-8")

        prompt = (
            "You are an AI assistant for CIRCULO, a campus circular resource sharing platform. "
            "Analyze this uploaded photo of an academic, lab, hardware, or campus item that a student wants to list. "
            "Identify the exact item and return ONLY a strict JSON object with this exact structure:\n"
            "{\n"
            '  "item_name": "Accurate item name and model (e.g. Arduino Uno R3, Raspberry Pi 4 Model B, Casio fx-991EX Calculator, Mini Drafter, Digital Multimeter)",\n'
            '  "category": "One of: Electronics, Lab Equipment, Books & Course Materials, Tools & Prototyping, Audio/Visual & Adapters, Miscellaneous",\n'
            '  "capabilities": ["3 to 6 specific technical capabilities or features like gpio, wifi, microcontroller, 5v logic, video transmission, calculus, etc."],\n'
            '  "condition": "New, Good, or Fair based on physical appearance, wear, scratches, or packaging",\n'
            '  "condition_note": "A brief 1-sentence note about the item appearance and condition"\n'
            "}\n"
            "Do not include markdown code block formatting. Return pure JSON only."
        )

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": mime_type or "image/jpeg",
                                "data": b64_data
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json"
            }
        }

        model = get_gemini_model()
        models_to_try = [model]
        for m in ["gemini-3.8-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash"]:
            if m not in models_to_try:
                models_to_try.append(m)

        headers = {
            "x-goog-api-key": api_key,
            "Content-Type": "application/json"
        }

        for candidate_model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/{GEMINI_API_VERSION}/models/{candidate_model}:generateContent"
            resp = requests.post(url, headers=headers, json=payload, timeout=14)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates:
                    text_part = candidates[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                    cleaned_text = re.sub(r"^```(?:json)?\s*", "", text_part.strip())
                    cleaned_text = re.sub(r"\s*```$", "", cleaned_text.strip())
                    parsed = json.loads(cleaned_text)
                    return parsed
    except Exception:
        pass
    return None


# ─────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────

def _load_capabilities_dict() -> Dict[str, Any]:
    if not CAPABILITIES_PATH.exists():
        return {}
    with open(CAPABILITIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _extract_keywords(filename: str) -> List[str]:
    """Pull meaningful words out of an image filename."""
    stem = Path(filename).stem
    raw_words = re.findall(r"[a-zA-Z0-9]+", stem)
    noise = {
        "img", "image", "photo", "pic", "dsc", "jpg", "jpeg", "png",
        "scan", "camera", "screenshot", "capture", "file", "copy",
        "new", "old", "tmp", "temp", "001", "002", "untitled"
    }
    return [w.lower() for w in raw_words if len(w) >= 3 and w.lower() not in noise]


def _analyze_condition(img) -> Tuple[str, str]:
    """
    Estimate item condition from PIL image statistics.

    Heuristic:
      - High brightness + high contrast  → New / Good
      - Medium brightness               → Good
      - Low brightness / low contrast   → Fair (possibly worn or poorly lit)

    Returns (condition_label, human_readable_note)
    """
    try:
        from PIL import ImageStat

        rgb = img.convert("RGB")
        stat = ImageStat.Stat(rgb)

        brightness = sum(stat.mean) / 3        # 0–255
        contrast   = sum(stat.stddev) / 3      # 0–128+

        if brightness >= 180 and contrast >= 40:
            return "New",  "Image is bright and sharp — item appears brand new or like-new."
        elif brightness >= 130 and contrast >= 25:
            return "Good", "Image shows good clarity — item looks in good working condition."
        elif brightness >= 80:
            return "Good", "Reasonably lit image — item appears usable, in good condition."
        else:
            return "Fair", "Low brightness or contrast detected — item may show wear, or photo was taken in poor lighting."
    except Exception:
        return "Good", "Could not analyse image quality — defaulting to 'Good' condition."


def _match_capabilities(keywords: List[str]) -> Dict[str, Any]:
    """Score keywords against the capabilities dictionary and return the best match."""
    cap_dict = _load_capabilities_dict()
    best_score = 0
    best_data  = None

    for key, data in cap_dict.items():
        aliases = data.get("aliases", []) + [key]
        score = 0
        for kw in keywords:
            for alias in aliases:
                alias_l = alias.lower()
                if kw in alias_l or alias_l in kw or kw == alias_l:
                    score += 2
                elif any(part in kw for part in alias_l.split()):
                    score += 1
                else:
                    ratio = SequenceMatcher(None, kw, alias_l).ratio()
                    if ratio >= 0.65:
                        score += 2
        if score > best_score:
            best_score = score
            best_data  = (key, data)

    if best_data and best_score > 0:
        key, data = best_data
        return {
            "suggested_name":         data.get("name", key.replace("_", " ").title()),
            "suggested_category":     data.get("category", "Electronics"),
            "suggested_capabilities": data.get("capabilities", []),
            "suggested_tags":         data.get("tags", []),
            "matched_by":             f"dictionary key '{key}'",
            "scan_confidence":        min(95, 40 + best_score * 15),
        }

    # Fallback — use the raw keywords themselves
    if keywords:
        return {
            "suggested_name":         " ".join(k.title() for k in keywords[:3]),
            "suggested_category":     "Electronics",
            "suggested_capabilities": keywords[:6],
            "suggested_tags":         keywords[:3],
            "matched_by":             "filename keywords (no dictionary match)",
            "scan_confidence":        20,
        }

    return {
        "suggested_name":         "",
        "suggested_category":     "",
        "suggested_capabilities": [],
        "suggested_tags":         [],
        "matched_by":             "none",
        "scan_confidence":        0,
    }


# ─────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────

def scan_image_for_autofill(uploaded_file) -> Dict[str, Any]:
    """
    Analyse an uploaded image file and return form auto-fill suggestions.

    Result keys:
      suggested_name, suggested_category, suggested_capabilities,
      suggested_tags, suggested_condition, condition_note,
      matched_by, scan_confidence  (0–100)
    """
    result = {
        "suggested_name":         "",
        "suggested_category":     "",
        "suggested_capabilities": [],
        "suggested_tags":         [],
        "suggested_condition":    "Good",
        "condition_note":         "",
        "matched_by":             "none",
        "scan_confidence":        0,
    }

    try:
        from PIL import Image

        # 0. Check for Google Gemini Vision AI (Level 2 AI Auto-fill)
        gemini_key = get_gemini_api_key()
        if gemini_key:
            try:
                uploaded_file.seek(0)
                img_bytes = uploaded_file.read()
                mime = getattr(uploaded_file, "type", "image/jpeg") or "image/jpeg"
                gemini_data = _call_gemini_vision(img_bytes, mime, gemini_key)
                if gemini_data and gemini_data.get("item_name"):
                    cond = gemini_data.get("condition", "Good")
                    result["suggested_name"]         = gemini_data.get("item_name", "").strip()
                    result["suggested_category"]     = gemini_data.get("category", "Electronics")
                    result["suggested_capabilities"] = gemini_data.get("capabilities", [])
                    result["suggested_tags"]         = gemini_data.get("capabilities", [])[:3]
                    result["suggested_condition"]    = cond if cond in ["New", "Good", "Fair"] else "Good"
                    result["condition_note"]         = gemini_data.get("condition_note", "Visual analysis via Google Gemini Vision AI.")
                    result["matched_by"]             = f"Google Gemini Vision AI ({get_gemini_model()})"
                    result["scan_confidence"]        = 98
                    uploaded_file.seek(0)
                    return result
            except Exception:
                pass  # Fall back to offline PIL analysis below

        # Reset stream position for PIL
        uploaded_file.seek(0)
        img = Image.open(uploaded_file)

        # 1. Condition from image quality
        condition, note = _analyze_condition(img)
        result["suggested_condition"] = condition
        result["condition_note"]      = note

        # 2. Keyword extraction from filename
        keywords = _extract_keywords(uploaded_file.name)

        # 3. Capabilities / name / category match
        cap_result = _match_capabilities(keywords)
        result.update(cap_result)

        # Reset stream so caller can save the file too
        uploaded_file.seek(0)

    except Exception as exc:
        result["condition_note"] = f"Scan encountered an issue: {exc}"

    return result


def save_item_image(uploaded_file, item_name: str) -> Optional[str]:
    """
    Persist the uploaded image to  assets/item_images/<safe_name>_<uuid>.jpg
    Returns the absolute path string on success, None on failure.
    """
    try:
        from PIL import Image

        images_dir = ASSETS_DIR / "item_images"
        images_dir.mkdir(parents=True, exist_ok=True)

        ext       = Path(uploaded_file.name).suffix.lower() or ".jpg"
        safe_name = re.sub(r"[^\w]", "_", item_name.lower())[:28]
        uid       = str(uuid.uuid4())[:8]
        filename  = f"{safe_name}_{uid}.jpg"
        save_path = images_dir / filename

        uploaded_file.seek(0)
        img = Image.open(uploaded_file).convert("RGB")

        # Cap at 900 px wide to save disk space
        if img.width > 900:
            ratio = 900 / img.width
            img = img.resize((900, int(img.height * ratio)), Image.LANCZOS)

        img.save(str(save_path), "JPEG", quality=85, optimize=True)
        return str(save_path)

    except Exception:
        return None
