"""CIRCULO - Resource Management Service
Handles listing new resources with capability auto-suggestions,
inventory queries, and availability toggles.
"""
import json
import re
from typing import Dict, Any, List
from config import CAPABILITIES_PATH
from db.database import execute_query, execute_one, execute_update, atomic_transaction

def load_capabilities_dict() -> Dict[str, Any]:
    if not CAPABILITIES_PATH.exists():
        return {}
    with open(CAPABILITIES_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def suggest_capabilities_for_item(item_name: str) -> Dict[str, Any]:
    """
    Given a raw item title, suggest standard category, capabilities, and tags
    from the dictionary for owner confirmation.
    """
    cleaned = item_name.strip().lower()
    cap_dict = load_capabilities_dict()
    
    suggested_name = item_name.strip().title()
    suggested_category = "Electronics"
    suggested_caps = []
    suggested_tags = []

    # Check direct dictionary entries
    for key, data in cap_dict.items():
        if key in cleaned or any(a in cleaned for a in data.get("aliases", [])):
            suggested_name = data.get("name", suggested_name)
            suggested_category = data.get("category", suggested_category)
            suggested_caps = data.get("capabilities", [])
            suggested_tags = data.get("tags", [])
            break

    # If no exact match, infer keywords
    if not suggested_caps:
        words = re.findall(r'\b[a-z]{3,}\b', cleaned)
        suggested_caps = words[:4]
        suggested_tags = words[:4]

    return {
        "suggested_name": suggested_name,
        "suggested_category": suggested_category,
        "suggested_capabilities": suggested_caps,
        "suggested_tags": suggested_tags
    }

def add_resource(
    owner_id: int,
    name: str,
    category_id: int,
    description: str,
    condition: str,
    location: str,
    quantity: int,
    available_for: str = "borrow",
    available_until: str = None,
    capabilities: List[str] = None,
    image_path: str = None
) -> int:
    """
    Add a new resource and its associated capabilities atomically.
    """
    with atomic_transaction() as conn:
        cur = conn.cursor()
        cur.execute(
            """INSERT INTO items (
                owner_id, name, category_id, description, condition, location,
                quantity, quantity_available, availability, available_for,
                available_until, last_used, image_path
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'AVAILABLE', ?, ?, datetime('now'), ?)""",
            (owner_id, name, category_id, description, condition, location,
             quantity, quantity, available_for, available_until, image_path)
        )
        item_id = cur.lastrowid

        if capabilities:
            for cap in capabilities:
                cleaned_cap = cap.strip().lower()
                if cleaned_cap:
                    cur.execute(
                        "INSERT OR IGNORE INTO item_capabilities (item_id, capability) VALUES (?, ?)",
                        (item_id, cleaned_cap)
                    )
        return item_id

def get_items_by_owner(owner_id: int) -> List[Dict[str, Any]]:
    """Return all listings owned by a specific user with capabilities and idle days."""
    query = """
    SELECT 
        i.*,
        c.name as category_name,
        CAST((julianday('now') - julianday(i.last_used)) AS INTEGER) as idle_days
    FROM items i
    LEFT JOIN categories c ON i.category_id = c.id
    WHERE i.owner_id = ?
    ORDER BY i.created_at DESC
    """
    items = execute_query(query, (owner_id,))
    for item in items:
        caps = execute_query("SELECT capability FROM item_capabilities WHERE item_id = ?", (item["id"],))
        item["capabilities"] = [c["capability"] for c in caps]
    return items

def update_item_availability(item_id: int, availability: str):
    """Toggle item availability between AVAILABLE and UNAVAILABLE."""
    execute_update("UPDATE items SET availability = ? WHERE id = ?", (availability, item_id))
