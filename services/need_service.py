"""CIRCULO - Need Understanding Service
Parses free-form natural language queries into structured requirements:
(need, required_capabilities, purpose).
Uses deterministic dictionary-based semantic extraction with synonym mapping.
"""
import json
import re
from difflib import SequenceMatcher
from typing import Dict, Any, List
from config import CAPABILITIES_PATH
from db.database import execute_update

def load_capabilities_dict() -> Dict[str, Any]:
    """Load canonical capability dictionary from disk."""
    if not CAPABILITIES_PATH.exists():
        return {}
    with open(CAPABILITIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# Common synonym mappings for campus intent recognition
CAMPUS_SYNONYMS = {
    "projector": ["video transmission", "hdmi", "display output", "projector connection"],
    "screen": ["video transmission", "display output", "monitor connection"],
    "display": ["video transmission", "display output", "monitor connection"],
    "present": ["video transmission", "projector connection"],
    "presentation": ["video transmission", "projector connection", "hdmi"],
    "laptop": ["usb-c", "hdmi", "video transmission"],
    "macbook": ["usb-c", "hdmi", "video transmission", "macbook display"],
    "connect": ["video transmission", "hdmi"],
    "wifi": ["wifi", "microcontroller", "wireless"],
    "wireless": ["wifi", "bluetooth", "wireless"],
    "iot": ["iot", "wifi", "microcontroller"],
    "robot": ["robotics", "obstacle detection", "microcontroller", "gpio"],
    "robotics": ["robotics", "obstacle detection", "microcontroller", "gpio"],
    "circuit": ["prototyping", "circuit building", "solderless testing"],
    "breadboard": ["prototyping", "circuit building", "solderless testing"],
    "wires": ["prototyping", "gpio connections"],
    "measure": ["voltage measurement", "current measurement", "continuity test"],
    "voltage": ["voltage measurement"],
    "exam": ["scientific calculation", "exam approved"],
    "calculate": ["scientific calculation", "matrix calculation"],
    "math": ["calculus", "differential equations", "linear algebra", "engineering math"],
    "calculus": ["calculus", "engineering math"],
    "solder": ["soldering", "pcb assembly", "wire joining"],
    "drawing": ["drafting", "engineering drawing", "geometric construction"],
    "drafter": ["drafting", "engineering drawing"],
    "distance": ["distance measurement", "obstacle detection"],
    "ultrasonic": ["distance measurement", "obstacle detection"],
    "temp": ["temperature measurement", "humidity measurement"],
    "temperature": ["temperature measurement", "humidity measurement"],
}

# Common hardware misspellings — maps typo → (identified_need, [capabilities])
HARDWARE_TYPOS = {
    # Arduino variants
    "ardo":      ("Arduino Microcontroller", ["microcontroller", "gpio", "analog input", "prototyping", "embedded", "5v logic"]),
    "aurudio":   ("Arduino Microcontroller", ["microcontroller", "gpio", "analog input", "prototyping", "embedded", "5v logic"]),
    "aurudinoo": ("Arduino Microcontroller", ["microcontroller", "gpio", "analog input", "prototyping", "embedded", "5v logic"]),
    "arduno":    ("Arduino Microcontroller", ["microcontroller", "gpio", "analog input", "prototyping", "embedded", "5v logic"]),
    "arduinoo":  ("Arduino Microcontroller", ["microcontroller", "gpio", "analog input", "prototyping", "embedded", "5v logic"]),
    "aurdino":   ("Arduino Microcontroller", ["microcontroller", "gpio", "analog input", "prototyping", "embedded", "5v logic"]),
    "ardiuno":   ("Arduino Microcontroller", ["microcontroller", "gpio", "analog input", "prototyping", "embedded", "5v logic"]),
    # Raspberry Pi variants
    "rasberry":  ("Raspberry Pi", ["single board computer", "linux", "wifi", "bluetooth", "hdmi output", "python"]),
    "raspbery":  ("Raspberry Pi", ["single board computer", "linux", "wifi", "bluetooth", "hdmi output", "python"]),
    "raspi":     ("Raspberry Pi", ["single board computer", "linux", "wifi", "bluetooth", "python"]),
    # ESP32 variants
    "esp 32":    ("ESP32 Dev Board", ["microcontroller", "wifi", "bluetooth", "iot", "gpio"]),
    "esp-32":    ("ESP32 Dev Board", ["microcontroller", "wifi", "bluetooth", "iot", "gpio"]),
}

def parse_need(text: str, user_id: int = 1) -> Dict[str, Any]:
    """
    Parse a student's natural-language query into a structured requirement.
    Returns:
    {
        "need": str,
        "required_capabilities": List[str],
        "purpose": str,
        "raw_text": str,
        "need_query_id": int
    }
    """
    cleaned = text.strip().lower()
    capabilities_dict = load_capabilities_dict()
    
    extracted_caps = set()
    identified_need = "general resource"

    # 0. Explicit typo/misspelling lookup (highest priority, instant match)
    for typo, (need_label, caps) in HARDWARE_TYPOS.items():
        if typo in cleaned:
            identified_need = need_label
            extracted_caps.update(caps)
            break

    # 1. Match against capability dictionary keys, aliases, and tags
    for key, data in capabilities_dict.items():
        # Check direct key
        if key in cleaned:
            identified_need = data.get("name", key)
            for cap in data.get("capabilities", []):
                extracted_caps.add(cap)
        # Check aliases
        for alias in data.get("aliases", []):
            if alias in cleaned:
                identified_need = data.get("name", key)
                for cap in data.get("capabilities", []):
                    extracted_caps.add(cap)
        # Check tags
        for tag in data.get("tags", []):
            if re.search(r'\b' + re.escape(tag) + r'\b', cleaned):
                for cap in data.get("capabilities", []):
                    extracted_caps.add(cap)

    # 2. Match against campus synonyms
    for keyword, caps in CAMPUS_SYNONYMS.items():
        if re.search(r'\b' + re.escape(keyword) + r'\b', cleaned):
            for c in caps:
                extracted_caps.add(c)
            if identified_need == "general resource":
                identified_need = keyword.capitalize()

    # 3. Specific canonical hackathon baseline examples
    if "projector" in cleaned or ("laptop" in cleaned and "connect" in cleaned):
        identified_need = "Video Connectivity & Display Adapter"
        extracted_caps.update(["video transmission", "hdmi", "projector connection", "display output"])
    elif "microcontroller" in cleaned or "iot" in cleaned:
        identified_need = "IoT Microcontroller Board"
        extracted_caps.update(["microcontroller", "wifi", "iot", "gpio"])
    elif "arduino" in cleaned:
        identified_need = "Arduino Microcontroller"
        extracted_caps.update(["microcontroller", "gpio", "prototyping"])
    elif "drafter" in cleaned or "drawing kit" in cleaned or "graphics" in cleaned:
        identified_need = "Engineering Drawing Set"
        extracted_caps.update(["drafting", "engineering drawing"])

    # 4. Fuzzy / typo-tolerant matching — catches misspellings like
    #    'aurudio' → 'arduino', 'rasberry' → 'raspberry pi', etc.
    if not extracted_caps or identified_need == "general resource":
        words = re.findall(r'\b[a-z]{3,}\b', cleaned)
        for word in words:
            best_ratio = 0.0
            best_match_data = None
            best_match_key = ""
            for key, data in capabilities_dict.items():
                # Compare against each word in the key (handles 'arduino uno', 'raspberry pi')
                for key_part in key.split():
                    ratio = SequenceMatcher(None, word, key_part).ratio()
                    if ratio > best_ratio:
                        best_ratio = ratio
                        best_match_data = data
                        best_match_key = key
                # Compare against aliases
                for alias in data.get("aliases", []):
                    for alias_word in alias.lower().split():
                        if len(alias_word) >= 3:
                            r = SequenceMatcher(None, word, alias_word).ratio()
                            if r > best_ratio:
                                best_ratio = r
                                best_match_data = data
                                best_match_key = key
            # Threshold = 0.65 — catches 1-3 char typos in typical hardware names
            if best_ratio >= 0.65 and best_match_data:
                identified_need = best_match_data.get("name", best_match_key)
                for cap in best_match_data.get("capabilities", []):
                    extracted_caps.add(cap)
                break  # Use first strong fuzzy match

    # 5. Final fallback — use raw words as capabilities if still empty
    if not extracted_caps:
        words = re.findall(r'\b[a-z]{3,}\b', cleaned)
        identified_need = " ".join(words[:3]).capitalize() if words else "Campus Resource"
        extracted_caps.update(words[:3])

    # Extract purpose ("for my IoT project", "to connect laptop", etc.)
    purpose = "Campus academic/project work"
    purpose_match = re.search(r'(?:for|to|trying to|need to)\s+([^.,;]+)', cleaned)
    if purpose_match:
        purpose = purpose_match.group(1).strip().capitalize()

    required_caps_list = sorted(list(extracted_caps))

    parsed_data = {
        "need": identified_need,
        "required_capabilities": required_caps_list,
        "purpose": purpose
    }

    # Record in need_queries table
    query_id, _ = execute_update(
        "INSERT INTO need_queries (user_id, raw_text, parsed_json, status) VALUES (?, ?, ?, ?)",
        (user_id, text, json.dumps(parsed_data), "matched")
    )

    return {
        **parsed_data,
        "raw_text": text,
        "need_query_id": query_id
    }
