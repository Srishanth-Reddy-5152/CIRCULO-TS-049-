"""CIRCULO - Database Access Layer
Encapsulates SQLite connection management, initialization, and parameterized operations.
"""
import sqlite3
import os
from contextlib import contextmanager
from pathlib import Path
from config import DB_PATH, SCHEMA_PATH, DATA_DIR

def dict_factory(cursor, row):
    """Convert SQLite row to dictionary."""
    fields = [column[0] for column in cursor.description]
    return {key: value for key, value in zip(fields, row)}

def get_connection():
    """Return a configured connection to the SQLite database."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False, timeout=10.0)
    conn.row_factory = dict_factory
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn

@contextmanager
def atomic_transaction():
    """Provide a transactional scope around a series of operations."""
    conn = get_connection()
    try:
        conn.execute("BEGIN IMMEDIATE")
        yield conn
        conn.commit()
    except Exception as exc:
        conn.rollback()
        raise exc
    finally:
        conn.close()

def execute_query(query, params=()):
    """Execute a read query and return all rows as dicts."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.fetchall()
    finally:
        conn.close()

def execute_one(query, params=()):
    """Execute a read query and return single row as dict, or None."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        return cur.fetchone()
    finally:
        conn.close()

def execute_update(query, params=()):
    """Execute an INSERT/UPDATE/DELETE query and return lastrowid and rowcount."""
    conn = get_connection()
    try:
        with conn:
            cur = conn.cursor()
            cur.execute(query, params)
            return cur.lastrowid, cur.rowcount
    finally:
        conn.close()

def init_db(force_recreate=False):
    """Initialize database from schema.sql. Auto-invokes if DB doesn't exist."""
    if force_recreate and DB_PATH.exists():
        try:
            DB_PATH.unlink()
        except Exception:
            pass

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = get_connection()
    try:
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        conn.executescript(schema_sql)
    finally:
        conn.close()
