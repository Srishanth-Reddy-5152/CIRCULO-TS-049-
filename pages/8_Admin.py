"""CIRCULO - Institutional Administration & System Management
Overview of campus-wide inventory, department analytics, and demo state controls.
"""
import streamlit as st
import pandas as pd
from ui.components import render_header, render_hero
from db.database import execute_query
from db.seed import seed_database

st.set_page_config(page_title="CIRCULO - Admin Portal", page_icon="🛡️", layout="wide")

if not st.session_state.get("user"):
    st.warning("Please sign in from the main portal first.")
    if st.button("Go to Login"):
        st.switch_page("app.py")
    st.stop()

render_header()
user = st.session_state["user"]

render_hero(
    title="Institutional Oversight & Campus Administration",
    subtitle="Campus sustainability overview, departmental circulation statistics, inventory moderation, and demo database controls."
)

tab_overview, tab_inventory, tab_demo = st.tabs([
    "🏛️ Departmental Analytics",
    "📋 Campus Inventory Registry",
    "⚙️ Demo Controls & State Reset"
])

with tab_overview:
    st.markdown("### 📊 Resource Sharing by Department")
    dept_query = """
    SELECT 
        u.department,
        COUNT(DISTINCT i.id) as total_items_listed,
        SUM(CASE WHEN i.availability = 'AVAILABLE' THEN 1 ELSE 0 END) as items_available,
        COUNT(DISTINCT t.id) as total_loans_facilitated
    FROM users u
    LEFT JOIN items i ON u.id = i.owner_id
    LEFT JOIN transactions t ON u.id = t.lender_id
    GROUP BY u.department
    ORDER BY total_items_listed DESC
    """
    dept_rows = execute_query(dept_query)
    if dept_rows:
        df_dept = pd.DataFrame(dept_rows)
        st.dataframe(df_dept, use_container_width=True)

with tab_inventory:
    st.markdown("### 📦 Full Campus Inventory Registry")
    inv_query = """
    SELECT 
        i.id, i.name, c.name as category, i.condition, i.location,
        i.quantity_available, i.quantity, i.availability,
        u.name as owner, u.department
    FROM items i
    JOIN users u ON i.owner_id = u.id
    LEFT JOIN categories c ON i.category_id = c.id
    ORDER BY i.id ASC
    """
    inv_rows = execute_query(inv_query)
    if inv_rows:
        df_inv = pd.DataFrame(inv_rows)
        st.dataframe(df_inv, use_container_width=True)

with tab_demo:
    st.markdown("### 🔄 Demo Rehearsal Controls")
    st.caption("Quickly reset the SQLite database to the initial clean benchmark state between hackathon presentation runs.")
    
    col_reset, col_info = st.columns([1, 2])
    with col_reset:
        if st.button("⚠️ Reset & Re-Seed Database", type="secondary"):
            seed_database()
            st.session_state["flash"] = ("success", "Database successfully re-seeded to clean demo state!")
            st.rerun()
    with col_info:
        st.info("Re-seeding resets 10 demo accounts, 23 catalog items, capabilities, and past verified impact events.")
