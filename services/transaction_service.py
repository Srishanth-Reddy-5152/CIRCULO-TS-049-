"""CIRCULO - Transaction Lifecycle Service
Implements the canonical borrow lifecycle:
Request (PENDING) -> Approve (RESERVED) -> Handover (BORROWED) -> Return (RETURNED)
Ensures atomic state transitions and inventory concurrency safety.
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from db.database import execute_query, execute_one, execute_update, atomic_transaction
from config import DEFAULT_LOAN_DAYS

def create_borrow_request(user_id: int, item_id: int, need_query_id: Optional[int] = None, notes: str = "") -> int:
    """
    Submits a borrow intention (PENDING request).
    Does NOT modify item inventory state until approved by the owner.
    """
    req_id, _ = execute_update(
        """INSERT INTO requests (user_id, item_id, need_query_id, notes, status)
           VALUES (?, ?, ?, ?, 'PENDING')""",
        (user_id, item_id, need_query_id, notes)
    )
    return req_id

def approve_request(request_id: int, owner_id: int) -> bool:
    """
    Owner approves the borrow request atomically.
    Re-checks quantity_available > 0.
    Updates request to APPROVED.
    Creates transaction as RESERVED.
    Decrements quantity_available and updates availability if needed.
    """
    with atomic_transaction() as conn:
        cur = conn.cursor()
        
        # 1. Fetch request and verify
        cur.execute("""
            SELECT r.*, i.owner_id as item_owner, i.quantity_available, i.name as item_name
            FROM requests r
            JOIN items i ON r.item_id = i.id
            WHERE r.id = ?
        """, (request_id,))
        req = cur.fetchone()
        
        if not req or req["status"] != "PENDING" or req["item_owner"] != owner_id:
            return False
            
        if req["quantity_available"] <= 0:
            return False

        item_id = req["item_id"]
        borrower_id = req["user_id"]
        start_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        due_date = (datetime.now() + timedelta(days=DEFAULT_LOAN_DAYS)).strftime("%Y-%m-%d %H:%M:%S")

        # 2. Update request to APPROVED
        cur.execute("UPDATE requests SET status = 'APPROVED' WHERE id = ?", (request_id,))

        # 3. Create transaction as RESERVED
        cur.execute("""
            INSERT INTO transactions (item_id, lender_id, borrower_id, request_id, start_date, due_date, status)
            VALUES (?, ?, ?, ?, ?, ?, 'RESERVED')
        """, (item_id, owner_id, borrower_id, request_id, start_date, due_date))

        # 4. Decrement quantity_available and update item status if 0
        new_qty = req["quantity_available"] - 1
        new_avail = "RESERVED" if new_qty == 0 else "AVAILABLE"
        cur.execute("""
            UPDATE items 
            SET quantity_available = ?, availability = ?
            WHERE id = ?
        """, (new_qty, new_avail, item_id))

        return True

def reject_request(request_id: int, owner_id: int) -> bool:
    """Owner rejects the borrow request."""
    with atomic_transaction() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT r.id FROM requests r
            JOIN items i ON r.item_id = i.id
            WHERE r.id = ? AND i.owner_id = ? AND r.status = 'PENDING'
        """, (request_id, owner_id))
        if not cur.fetchone():
            return False
        cur.execute("UPDATE requests SET status = 'REJECTED' WHERE id = ?", (request_id,))
        return True

def confirm_handover(transaction_id: int, user_id: int) -> bool:
    """Marks physical handover of the item: RESERVED -> BORROWED."""
    with atomic_transaction() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT t.*, i.quantity_available FROM transactions t
            JOIN items i ON t.item_id = i.id
            WHERE t.id = ? AND (t.lender_id = ? OR t.borrower_id = ?) AND t.status = 'RESERVED'
        """, (transaction_id, user_id, user_id))
        tx = cur.fetchone()
        if not tx:
            return False

        # Transition transaction to BORROWED
        cur.execute("UPDATE transactions SET status = 'BORROWED' WHERE id = ?", (transaction_id,))
        
        # If item was marked RESERVED, change to BORROWED
        cur.execute("""
            UPDATE items 
            SET availability = 'BORROWED' 
            WHERE id = ? AND availability = 'RESERVED'
        """, (tx["item_id"],))
        return True

def mark_returned(transaction_id: int, user_id: int) -> bool:
    """
    Marks item returned: BORROWED/RESERVED -> RETURNED.
    Restores quantity_available and marks item AVAILABLE.
    Updates last_used timestamp.
    Logs impact event.
    """
    from services.impact_service import record_return_impact
    with atomic_transaction() as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT t.*, i.quantity, i.quantity_available, i.name as item_name
            FROM transactions t
            JOIN items i ON t.item_id = i.id
            WHERE t.id = ? AND (t.lender_id = ? OR t.borrower_id = ?) 
              AND t.status IN ('RESERVED', 'BORROWED', 'OVERDUE')
        """, (transaction_id, user_id, user_id))
        tx = cur.fetchone()
        if not tx:
            return False

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 1. Update transaction
        cur.execute("""
            UPDATE transactions 
            SET status = 'RETURNED', returned_at = ? 
            WHERE id = ?
        """, (now_str, transaction_id))

        # 2. Restore item quantity and availability
        new_qty = min(tx["quantity"], tx["quantity_available"] + 1)
        cur.execute("""
            UPDATE items 
            SET quantity_available = ?, availability = 'AVAILABLE', last_used = ?
            WHERE id = ?
        """, (new_qty, now_str, tx["item_id"]))

    # Record impact event safely outside the locking tx
    record_return_impact(tx["id"], tx["borrower_id"], tx["item_id"])
    return True

def get_incoming_requests(owner_id: int) -> List[Dict[str, Any]]:
    """Fetch borrow requests submitted for items owned by this user."""
    query = """
    SELECT 
        r.id as request_id, r.status, r.notes, r.created_at,
        i.id as item_id, i.name as item_name, i.location, i.quantity_available,
        u.id as borrower_id, u.name as borrower_name, u.email as borrower_email, u.department as borrower_department
    FROM requests r
    JOIN items i ON r.item_id = i.id
    JOIN users u ON r.user_id = u.id
    WHERE i.owner_id = ? AND r.status = 'PENDING'
    ORDER BY r.created_at DESC
    """
    return execute_query(query, (owner_id,))

def get_user_requests(user_id: int) -> List[Dict[str, Any]]:
    """Fetch requests initiated by this user."""
    query = """
    SELECT 
        r.id as request_id, r.status, r.notes, r.created_at,
        i.name as item_name, i.location,
        u.name as owner_name, u.email as owner_email, u.department as owner_department
    FROM requests r
    JOIN items i ON r.item_id = i.id
    JOIN users u ON i.owner_id = u.id
    WHERE r.user_id = ?
    ORDER BY r.created_at DESC
    """
    return execute_query(query, (user_id,))

def get_active_loans(user_id: int) -> List[Dict[str, Any]]:
    """Fetch active loan transactions (as borrower or lender)."""
    query = """
    SELECT 
        t.id as transaction_id, t.status, t.start_date, t.due_date, t.returned_at,
        i.id as item_id, i.name as item_name, i.location,
        l.name as lender_name, l.department as lender_department,
        b.name as borrower_name, b.department as borrower_department,
        t.lender_id, t.borrower_id
    FROM transactions t
    JOIN items i ON t.item_id = i.id
    JOIN users l ON t.lender_id = l.id
    JOIN users b ON t.borrower_id = b.id
    WHERE (t.lender_id = ? OR t.borrower_id = ?) AND t.status IN ('RESERVED', 'BORROWED', 'OVERDUE')
    ORDER BY t.start_date DESC
    """
    return execute_query(query, (user_id, user_id))
