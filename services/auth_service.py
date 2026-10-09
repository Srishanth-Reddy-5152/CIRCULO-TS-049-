"""CIRCULO - Authentication and User Service
Handles demo logins, password hashing, user fetching, and role checks.
"""
import hashlib
from typing import Optional, Dict, Any, List
from db.database import execute_one, execute_query

def hash_pw(password: str) -> str:
    """Create a SHA-256 hash with campus salt for demo authentication."""
    salt = "circulo_campus_salt_2026"
    return hashlib.sha256(f"{salt}{password}".encode("utf-8")).hexdigest()

def authenticate_user(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Validate user credentials and return user object if valid."""
    user = execute_one("SELECT * FROM users WHERE email = ?", (email.strip().lower(),))
    if not user:
        return None
    hashed = hash_pw(password)
    if user.get("password_hash") == hashed:
        # Return user without password hash
        return {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "department": user["department"],
            "role": user["role"],
        }
    return None

def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Fetch user by id."""
    user = execute_one("SELECT id, name, email, department, role, created_at FROM users WHERE id = ?", (user_id,))
    return user

def get_demo_accounts() -> List[Dict[str, Any]]:
    """Return seeded demo accounts for one-click demo switching."""
    return execute_query(
        "SELECT id, name, email, department, role FROM users ORDER BY role DESC, id ASC"
    )
