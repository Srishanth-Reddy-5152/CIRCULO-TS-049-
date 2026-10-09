# CIRCULO — Sustainable Consumption Decision Engine

> **"Before You Buy, Check CIRCULO."**  
> Aligned with **UN Sustainable Development Goal 12: Responsible Consumption & Production**

---

## 🌍 Executive Summary

**CIRCULO** is an AI-assisted sustainable consumption decision engine built for college campuses. Rather than acting as a generic buy/sell marketplace, CIRCULO intervenes at the exact moment of intent: **before a student makes an unnecessary new purchase**.

A student describes what they are trying to accomplish in everyday natural language (e.g. *"I need to connect my laptop to a projector in the seminar hall"* or *"I need a WiFi microcontroller for my IoT project"*). CIRCULO:
1. Translates the student's goal into functional capabilities.
2. Scans existing campus labs, departmental inventories, and peer-owned resources.
3. Evaluates and ranks **5 Circular Routes**: **Borrow → Repair → Reuse → Buy Used → Buy New**.
4. Provides an explainable, data-driven checklist explaining *"Why CIRCULO recommends this"*.
5. Executes the full atomic loan lifecycle (**Request → Approval → Handover → Return**) and records verified campus impact metrics.

---

## ⚡ Quickstart & Running Locally

### 1. Activate Environment & Run
The application runs on Python 3.11+ with Streamlit:

```powershell
# Using the dedicated virtual environment (.venv)
.venv\Scripts\streamlit.exe run app.py
```

The application will launch in your browser at `http://localhost:8501`.

### 2. Demo Personas (One-Click Sign-in on Home)
Pre-seeded personas are provided for hackathon demonstration:
- **Arun Kumar (Student, CSE)**: `arun@campus.edu` (pw: `student123`)
- **Sneha Rao (Student, ECE)**: `sneha@campus.edu` (pw: `student123`)
- **CSE Hardware Lab (Lab Manager)**: `cselab@campus.edu` (pw: `lab123`)
- **Campus Makerspace & Repair**: `makerspace@campus.edu` (pw: `lab123`)
- **Campus Sustainability Admin**: `admin@circulo.campus.edu` (pw: `admin123`)

---

## 🏗️ Architecture & Technical Stack

```
circulo/
├── app.py                  # Entry portal: Login & Home landing hub
├── config.py               # Decision weights, idle threshold (30 days), DEMO_MODE
├── requirements.txt        # Pinned dependencies
├── assets/
│   └── logo.png            # Official CIRCULO circular arrow & leaf branding
├── data/
│   ├── capabilities.json   # Capability dictionary with synonyms & aliases
│   └── circulo.db          # Relational SQLite database
├── db/
│   ├── schema.sql          # Canonical relational schema with foreign keys
│   ├── database.py         # Thread-safe connection & transaction management
│   └── seed.py             # Realistic campus inventory & past impact seeding
├── services/
│   ├── auth_service.py     # Persona management & salted password hashing
│   ├── need_service.py     # Natural language parsing -> capabilities
│   ├── matching_service.py # Capability match score + TF-IDF cosine similarity
│   ├── decision_service.py # 5-route weighted scoring & explanation generator
│   ├── resource_service.py # Fast listing with auto-capability suggestions
│   ├── transaction_service.py # Concurrency-safe borrow lifecycle
│   ├── rescue_service.py   # Idle asset detector (last_used > 30 days)
│   └── impact_service.py   # Honest impact accounting with methodology logs
├── ui/
│   ├── components.py       # Stylized metric tiles, badges, and score pills
│   └── style.css           # Premium circular forest-green design theme
├── pages/
│   ├── 1_Home.py           # Home dashboard & quick search scenarios
│   ├── 2_I_Need.py         # Natural language need entry
│   ├── 3_Results.py        # Semantic matches & 5-route decision engine
│   ├── 4_I_Have.py         # Fast 60-second resource listing
│   ├── 5_My_Resources.py   # Personal inventory & Resource Rescue
│   ├── 6_Requests.py       # Incoming approvals, handovers, returns
│   ├── 7_Dashboard.py      # Campus circularity metrics & Plotly charts
│   └── 8_Admin.py          # Departmental analytics & 1-click state reset
└── tests/
    └── test_circulo.py     # Automated test suite (matching, scoring, lifecycle)
```

---

## 🔬 Core Algorithms & Formulae

### 1. Capability Overlap Score
$$\text{Capability Match Score} = \frac{|\text{Matched Capabilities}|}{|\text{Required Capabilities}|}$$
- E.g., for `["microcontroller", "wifi", "iot"]`:
  - **ESP32**: Matches all 3 $\rightarrow$ **100% Match**
  - **Arduino Uno / Nano**: Matches 2 of 3 $\rightarrow$ **67% Match**

### 2. Circular Decision Engine (Multi-Factor Weighted Scoring)
$$\text{Score} = (\text{Compat} \times 0.40) + (\text{Avail} \times 0.25) + (\text{Cost} \times 0.15) + (\text{Proximity} \times 0.10) + (\text{Circularity} \times 0.10)$$

Hierarchy of circularity base scores:
- **Borrow**: 95 / 100
- **Repair**: 88 / 100
- **Reuse / Repurpose**: 82 / 100
- **Buy Used**: 70 / 100
- **Buy New**: 35 / 100

### 3. Resource Rescue (Idle Asset Detection)
$$\text{Idle Days} = \text{Current Date} - \text{last\_used}$$
- Any asset idle for **$\ge 30$ days** is automatically surfaced to its owner with 5 proactive actions: **Keep (Active)**, **Make Available (Recirculate)**, **Donate**, **Repair**, or **Retire**.

### 4. Honest Impact Accounting
- Avoids unsubstantiated carbon claims.
- Tracks verified, transactional metrics:
  - **Items Reused** (Count of physical returns)
  - **Purchases Avoided** (Substitutions for single-use purchases)
  - **Student Money Saved** (Actual retail benchmark savings)
  - **Repairs Facilitated** (Hardware components restored)
- Enforces `UNIQUE (transaction_id, metric_type)` to eliminate duplicate counting.

---

## 🧪 Running Automated Tests

```powershell
.venv\Scripts\python.exe -m unittest tests/test_circulo.py
```
Outputs:
```
....
Ran 4 tests in 0.381s
OK
```
