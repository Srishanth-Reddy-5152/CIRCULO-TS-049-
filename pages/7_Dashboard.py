"""CIRCULO - Impact Dashboard & Analytics
Transparent circularity outcomes, financial savings, and category circulation charts.
"""
import streamlit as st
import plotly.express as px
import pandas as pd
from ui.components import render_header, render_hero, render_metric_card
from services.impact_service import get_impact_summary, get_category_breakdown, get_recent_impact_events
from services.rescue_service import get_all_campus_idle_items, get_campus_idle_count

st.set_page_config(page_title="CIRCULO - Impact Dashboard", page_icon="📊", layout="wide")

if not st.session_state.get("user"):
    st.warning("Please sign in from the main portal first.")
    if st.button("Go to Login"):
        st.switch_page("app.py")
    st.stop()

render_header()
user = st.session_state["user"]

render_hero(
    title="Campus Circularity & Impact Accounting",
    subtitle="Verified outcomes tracked by CIRCULO. Every metric is backed by completed transactions and documented estimation methodologies."
)

# View toggle: Campus-wide vs Personal
view_mode = st.radio(
    "Select Scope:",
    ["🏫 Campus-Wide View", "👤 My Personal Impact"],
    horizontal=True
)
is_personal = ("Personal" in view_mode)
summary = get_impact_summary(user_id=user["id"] if is_personal else None)
idle_count = get_campus_idle_count()

# Metric Tiles Row (5 Pillars of Circular Impact)
m1, m2, m3, m4, m5 = st.columns(5)
with m1:
    render_metric_card("Items Reused", f"{summary['items_reused']}", "Verified return cycles", "♻️")
with m2:
    render_metric_card("Purchases Avoided", f"{summary['purchases_avoided']}", "Single-use orders prevented", "🛍️")
with m3:
    render_metric_card("Total Money Saved", f"₹{int(summary['money_saved']):,}", "Retail costs avoided", "💰")
with m4:
    render_metric_card("E-Waste Diverted", f"{summary.get('ewaste_diverted_kg', 0.0)} kg", "Hardware out of landfills", "⚡")
with m5:
    render_metric_card("CO₂e Avoided", f"{summary.get('co2_avoided_kg', 0.0)} kg", "Manufacturing carbon cut", "🌍")

st.markdown("<br>", unsafe_allow_html=True)

# Charts & Breakdown Row
col_chart, col_rescue = st.columns([1.4, 1.0])

with col_chart:
    st.markdown("### 📈 Circulated Categories & Savings")
    st.caption("Distribution of campus equipment recirculated through CIRCULO")
    
    cat_data = get_category_breakdown()
    if cat_data:
        df = pd.DataFrame(cat_data)
        fig = px.bar(
            df,
            x="category",
            y="circulation_count",
            color="circulation_count",
            color_continuous_scale=["#bbf7d0", "#22c55e", "#15803d"],
            labels={"category": "Equipment Category", "circulation_count": "Times Reused"},
            hover_data=["total_savings"]
        )
        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            coloraxis_showscale=False
        )
        st.plotly_chart(fig, use_container_width=True)

with col_rescue:
    st.markdown("### ⏳ Campus Resource Rescue Status")
    st.caption(f"Currently **{idle_count} assets** on campus have been idle for > 30 days")
    
    idle_campus_items = get_all_campus_idle_items(threshold_days=30)[:4]
    for item in idle_campus_items:
        st.markdown(
            f"""
            <div style='background:#fefce8; border:1px solid #fef08a; border-radius:10px; padding:10px 14px; margin-bottom:8px;'>
                <div style='display:flex; justify-content:space-between;'>
                    <b style='color:#854d0e; font-size:0.9rem;'>{item['name']}</b>
                    <span style='color:#a16207; font-size:0.75rem; font-weight:700;'>{item['idle_days']}d idle</span>
                </div>
                <div style='font-size:0.78rem; color:#713f12; margin-top:4px;'>
                    Owner: {item['owner_name']} ({item['owner_department']})
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    if st.button("Manage My Idle Items (Resource Rescue)"):
        st.switch_page("pages/5_My_Resources.py")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("### 📜 Verified Impact Audit Trail")
st.caption("Recent circular transactions with documented savings methodologies")

recent_events = get_recent_impact_events(limit=6)
if recent_events:
    for ev in recent_events:
        st.markdown(
            f"""
            <div style='background:#ffffff; border:1px solid #e2e8f0; border-radius:10px; padding:10px 14px; margin-bottom:6px; font-size:0.85rem;'>
                <b>{ev['created_at'][:16]}</b> &nbsp;|&nbsp; 
                <span style='color:#166534; font-weight:700;'>{ev['metric_type'].upper().replace('_', ' ')}:</span> 
                {ev['item_name']} &nbsp;|&nbsp; 
                👤 {ev['user_name']} ({ev['user_department']})  
                <div style='color:#64748b; font-size:0.8rem; margin-top:2px;'>
                    Methodology: <i>{ev['methodology']}</i>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
