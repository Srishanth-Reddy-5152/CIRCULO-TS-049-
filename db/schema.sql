-- CIRCULO SQLite Database Schema
-- Aligned with CIRCULO Master Project Document (Section 56 & Section 62)

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,
  email TEXT NOT NULL UNIQUE,
  department TEXT,
  role TEXT NOT NULL DEFAULT 'student' CHECK (role IN ('student','lab','admin')),
  password_hash TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  parent_id INTEGER REFERENCES categories(id),
  synonyms TEXT
);

CREATE TABLE IF NOT EXISTS items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_id INTEGER NOT NULL REFERENCES users(id),
  name TEXT NOT NULL,
  category_id INTEGER REFERENCES categories(id),
  description TEXT,
  condition TEXT CHECK (condition IN ('New','Good','Fair')),
  location TEXT,
  quantity INTEGER NOT NULL DEFAULT 1 CHECK (quantity > 0),
  quantity_available INTEGER NOT NULL DEFAULT 1 CHECK (quantity_available BETWEEN 0 AND quantity),
  availability TEXT NOT NULL DEFAULT 'AVAILABLE' CHECK (availability IN ('AVAILABLE','RESERVED','BORROWED','UNAVAILABLE')),
  available_for TEXT DEFAULT 'borrow' CHECK (available_for IN ('borrow','donate','both')),
  available_until TEXT,
  last_used TEXT,
  image_path TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS item_capabilities (
  item_id INTEGER NOT NULL REFERENCES items(id) ON DELETE CASCADE,
  capability TEXT NOT NULL,
  PRIMARY KEY (item_id, capability)
);

CREATE TABLE IF NOT EXISTS need_queries (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  raw_text TEXT NOT NULL,
  parsed_json TEXT,
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','matched','fulfilled','cancelled')),
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS requests (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL REFERENCES users(id),
  item_id INTEGER NOT NULL REFERENCES items(id),
  need_query_id INTEGER REFERENCES need_queries(id),
  notes TEXT,
  status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING','APPROVED','REJECTED','CANCELLED')),
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id INTEGER NOT NULL REFERENCES items(id),
  lender_id INTEGER NOT NULL REFERENCES users(id),
  borrower_id INTEGER NOT NULL REFERENCES users(id),
  request_id INTEGER REFERENCES requests(id),
  start_date TEXT,
  due_date TEXT,
  returned_at TEXT,
  status TEXT NOT NULL DEFAULT 'RESERVED' CHECK (status IN ('RESERVED','BORROWED','RETURNED','OVERDUE','CANCELLED'))
);

CREATE TABLE IF NOT EXISTS repairs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  item_id INTEGER NOT NULL REFERENCES items(id),
  issue TEXT,
  estimated_cost REAL,
  status TEXT DEFAULT 'REQUESTED' CHECK (status IN ('REQUESTED','IN_REPAIR','REPAIRED','NOT_REPAIRABLE')),
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS impact_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER REFERENCES users(id),
  item_id INTEGER REFERENCES items(id),
  transaction_id INTEGER REFERENCES transactions(id),
  action TEXT NOT NULL,        -- borrow | repair | reuse | buy_used
  metric_type TEXT NOT NULL,   -- item_reused | purchase_avoided | money_saved
  estimated_value REAL,
  methodology TEXT,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP,
  UNIQUE (transaction_id, metric_type)
);

CREATE TABLE IF NOT EXISTS price_reference (
  item_key TEXT PRIMARY KEY,
  repair_cost REAL,
  used_price REAL,
  new_price REAL,
  note TEXT DEFAULT 'demo data'
);
