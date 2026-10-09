"""CIRCULO - Global Configuration & Decision Weights
Master baseline settings aligned with CIRCULO SDG 12 Hackathon Project Dossier.
"""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = DATA_DIR / "circulo.db"
CAPABILITIES_PATH = DATA_DIR / "capabilities.json"
SCHEMA_PATH = BASE_DIR / "db" / "schema.sql"
ASSETS_DIR = BASE_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"

# Hackathon / Demo Configuration
DEMO_MODE = True
APP_NAME = "CIRCULO"
APP_TAGLINE = "Before You Buy, Check CIRCULO."
SDG_ALIGNMENT = "SDG 12: Responsible Consumption and Production"

# AI / Gemini API Configuration
GEMINI_MODEL = "gemini-3.8-flash"  # Latest GA release (or "gemini-3.5-flash-lite", "gemini-2.5-flash")
GEMINI_API_VERSION = "v1beta"

# Resource Rescue threshold (days without use)
IDLE_THRESHOLD_DAYS = 30

# Canonical Circular Decision Engine Weights (sum = 1.0)
DECISION_WEIGHTS = {
    "compatibility": 0.40,
    "availability": 0.25,
    "cost": 0.15,
    "proximity": 0.10,
    "circularity": 0.10,
}

# Circular hierarchy scores (Base score out of 100)
CIRCULARITY_HIERARCHY_SCORES = {
    "borrow": 95,
    "repair": 88,
    "reuse": 82,
    "buy_used": 70,
    "buy_new": 35,
}

# Canonical statuses (Section 62.1)
ITEM_STATUSES = ["AVAILABLE", "RESERVED", "BORROWED", "UNAVAILABLE"]
REQUEST_STATUSES = ["PENDING", "APPROVED", "REJECTED", "CANCELLED"]
TRANSACTION_STATUSES = ["RESERVED", "BORROWED", "RETURNED", "OVERDUE", "CANCELLED"]
REPAIR_STATUSES = ["REQUESTED", "IN_REPAIR", "REPAIRED", "NOT_REPAIRABLE"]

# Default loan duration in days
DEFAULT_LOAN_DAYS = 7
