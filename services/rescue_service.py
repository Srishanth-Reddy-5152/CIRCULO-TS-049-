"""CIRCULO - Resource Rescue Service
Detects underutilized and idle items across campus (last_used > 30 days).
Allows owners to keep, recirculate, donate, repair, or retire idle assets.
"""
from typing import Dict, Any, List
from config import IDLE_THRESHOLD_DAYS
from db.database import execute_query, execute_one, execute_update

def get_idle_items_for_owner(owner_id: int, threshold_days: int = IDLE_THRESHOLD_DAYS) -> List[Dict[str, Any]]:
    """
    Fetch all items belonging to an owner that have not been used in > threshold_days.
    """
    query = """
    SELECT 
        i.*,
        c.name as category_name,
        CAST((julianday('now') - julianday(i.last_used)) AS INTEGER) as idle_days
    FROM items i
    LEFT JOIN categories c ON i.category_id = c.id
    WHERE i.owner_id = ? 
      AND (julianday('now') - julianday(i.last_used)) >= ?
      AND i.availability != 'UNAVAILABLE'
    ORDER BY idle_days DESC
    """
    items = execute_query(query, (owner_id, threshold_days))
    for item in items:
        caps = execute_query("SELECT capability FROM item_capabilities WHERE item_id = ?", (item["id"],))
        item["capabilities"] = [c["capability"] for c in caps]
    return items

def get_all_campus_idle_items(threshold_days: int = IDLE_THRESHOLD_DAYS) -> List[Dict[str, Any]]:
    """
    Campus-wide view of idle resources for the sustainability dashboard & admin overview.
    """
    query = """
    SELECT 
        i.*,
        u.name as owner_name, u.department as owner_department, u.role as owner_role,
        c.name as category_name,
        CAST((julianday('now') - julianday(i.last_used)) AS INTEGER) as idle_days
    FROM items i
    JOIN users u ON i.owner_id = u.id
    LEFT JOIN categories c ON i.category_id = c.id
    WHERE (julianday('now') - julianday(i.last_used)) >= ?
      AND i.availability != 'UNAVAILABLE'
    ORDER BY idle_days DESC
    """
    return execute_query(query, (threshold_days,))

def get_campus_idle_count(threshold_days: int = IDLE_THRESHOLD_DAYS) -> int:
    """Return total count of idle items on campus."""
    row = execute_one(
        "SELECT COUNT(*) as count FROM items WHERE (julianday('now') - julianday(last_used)) >= ? AND availability != 'UNAVAILABLE'",
        (threshold_days,)
    )
    return row["count"] if row else 0

def handle_rescue_action(item_id: int, owner_id: int, action: str, details: str = "") -> bool:
    """
    Execute owner decision on an idle asset:
    - 'keep': updates last_used to now
    - 'make_available': sets availability = 'AVAILABLE' and refreshes last_used
    - 'donate': sets available_for = 'donate'
    - 'repair': registers repair ticket
    - 'retire': sets availability = 'UNAVAILABLE'
    """
    # Verify ownership
    item = execute_one("SELECT * FROM items WHERE id = ? AND owner_id = ?", (item_id, owner_id))
    if not item:
        return False

    if action == "keep":
        execute_update("UPDATE items SET last_used = datetime('now') WHERE id = ?", (item_id,))
    elif action == "make_available":
        execute_update(
            "UPDATE items SET availability = 'AVAILABLE', quantity_available = quantity, last_used = datetime('now') WHERE id = ?",
            (item_id,)
        )
    elif action == "donate":
        execute_update(
            "UPDATE items SET available_for = 'donate', availability = 'AVAILABLE', last_used = datetime('now') WHERE id = ?",
            (item_id,)
        )
    elif action == "repair":
        execute_update("UPDATE items SET availability = 'UNAVAILABLE' WHERE id = ?", (item_id,))
        execute_update(
            "INSERT INTO repairs (item_id, issue, estimated_cost, status) VALUES (?, ?, 100.0, 'REQUESTED')",
            (item_id, details or "Flagged during Resource Rescue review")
        )
    elif action == "retire":
        execute_update("UPDATE items SET availability = 'UNAVAILABLE' WHERE id = ?", (item_id,))
    return True
