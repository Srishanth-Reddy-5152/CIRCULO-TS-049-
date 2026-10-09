"""CIRCULO - Home Dashboard Page
"""
import streamlit as st
from ui.components import render_header, render_hero, render_metric_card, render_footer

st.set_page_config(page_title="CIRCULO - Home", page_icon="♹", layout="wide")

if not st.session_state.get("user"):
    st.warning("Please sign in from the main portal first.")
    if st.button("Go to Login"):
        st.switch_page("app.py")
    st.stop()

render_header()
user = st.session_state["user"]


render_hero(
    title="Before you buy, what else could you do?",
    subtitle=f"Welcome back, {user['name']}. CIRCULO searches underutilized campus hardware, lab inventory, and peer resources to recommend the most sustainable route."
)

cta_col1, cta_col2 = st.columns(2)
with cta_col1:
    st.markdown(
        """
        <div style='background:#ffffff; border:2px solid #16a34a; border-radius:14px; padding:1.5rem; box-shadow:0 4px 12px rgba(22,101,52,0.06);'>
            <h3 style='color:#14532d; margin-top:0;'>🔍 I Need Something</h3>
            <p style='color:#475569;'>Describe what you want to accomplish in plain English. Our decision engine compares Borrow, Repair, Reuse, and Buy routes.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("🚀 Find Sustainable Options", key="home_page_need", type="primary", use_container_width=True):
        st.switch_page("pages/2_I_Need.py")

with cta_col2:
    st.markdown(
        """
        <div style='background:#ffffff; border:2px solid #0d9488; border-radius:14px; padding:1.5rem; box-shadow:0 4px 12px rgba(13,148,136,0.06);'>
            <h3 style='color:#115e59; margin-top:0;'>📦 I Have Something</h3>
            <p style='color:#475569;'>Have an idle development board, cable, or textbook? List it for sharing or donation in under 60 seconds.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    if st.button("➕ List a Campus Resource", key="home_page_have", type="secondary", use_container_width=True):
        st.switch_page("pages/4_I_Have.py")

st.markdown("<br>", unsafe_allow_html=True)
st.subheader("&#128161; Popular Search Scenarios")
sc1, sc2, sc3, sc4 = st.columns(4)

with sc1:
    if st.button("&#128268; Connect laptop to projector", key="p_sc_proj", use_container_width=True):
        st.session_state["need_text"] = "I need to connect my laptop to a projector in the seminar hall"
        st.switch_page("pages/2_I_Need.py")
with sc2:
    if st.button("&#9889; WiFi IoT microcontroller", key="p_sc_mcu", use_container_width=True):
        st.session_state["need_text"] = "I need a WiFi microcontroller for my IoT project"
        st.switch_page("pages/2_I_Need.py")
with sc3:
    if st.button("&#128208; Mini drafter & board", key="p_sc_draft", use_container_width=True):
        st.session_state["need_text"] = "Looking for a mini drafter and drawing board for engineering graphics"
        st.switch_page("pages/2_I_Need.py")
with sc4:
    if st.button("&#128223; Scientific calculator for exam", key="p_sc_calc", use_container_width=True):
        st.session_state["need_text"] = "I need an exam-approved scientific calculator for my math test"
        st.switch_page("pages/2_I_Need.py")

render_footer()
