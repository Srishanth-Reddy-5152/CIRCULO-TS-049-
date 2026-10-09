"""CIRCULO - I Need Something
Natural Language Requirement Capture & Semantic Extraction
"""
import streamlit as st
from ui.components import render_header, render_hero
from services.need_service import parse_need
from services.matching_service import find_matches

st.set_page_config(page_title="CIRCULO - I Need", page_icon="🔍", layout="wide")

if not st.session_state.get("user"):
    st.warning("Please sign in from the main portal first.")
    if st.button("Go to Login"):
        st.switch_page("app.py")
    st.stop()

render_header()
user = st.session_state["user"]

render_hero(
    title="What are you trying to accomplish?",
    subtitle="Describe your academic goal, project milestone, or hardware need. CIRCULO will translate your need into functional capabilities and scan campus resources."
)

# Example Chips
st.markdown("##### 💡 Try an Example Requirement:")
chip_col1, chip_col2, chip_col3 = st.columns(3)
with chip_col1:
    if st.button("🔌 'connect laptop to a projector'", key="chip_proj", use_container_width=True):
        st.session_state["need_text"] = "I need to connect my laptop to a projector in the seminar hall"
    if st.button("⚡ 'WiFi microcontroller for IoT project'", key="chip_iot", use_container_width=True):
        st.session_state["need_text"] = "I need a WiFi microcontroller for my IoT project"
with chip_col2:
    if st.button("🤖 'Arduino Uno for robotics'", key="chip_ard", use_container_width=True):
        st.session_state["need_text"] = "I need an Arduino Uno for robotics obstacle avoidance car"
    if st.button("📟 'scientific calculator for math exam'", key="chip_calc", use_container_width=True):
        st.session_state["need_text"] = "I need an exam-approved scientific calculator for my math test"
with chip_col3:
    if st.button("📐 'drafter for engineering graphics'", key="chip_draft", use_container_width=True):
        st.session_state["need_text"] = "Looking for a mini drafter and drawing board for engineering graphics"
    if st.button("🔬 'multimeter for circuit debugging'", key="chip_dmm", use_container_width=True):
        st.session_state["need_text"] = "Need a digital multimeter to measure voltage and test circuit continuity"

st.markdown("<br>", unsafe_allow_html=True)

with st.form("need_form"):
    need_input = st.text_area(
        "Enter your requirement in plain words:",
        value=st.session_state.get("need_text", ""),
        placeholder="e.g. I need to connect my laptop to a projector for a seminar presentation, or I need an ESP32 board for smart home automation...",
        height=120
    )
    
    col_submit, col_clear = st.columns([2, 1])
    with col_submit:
        submit = st.form_submit_button("🔍 Find Sustainable Options", type="primary", use_container_width=True)
    with col_clear:
        clear = st.form_submit_button("Clear", type="secondary", use_container_width=True)
        if clear:
            st.session_state["need_text"] = ""
            st.rerun()

if submit:
    if not need_input.strip():
        st.error("Please enter a requirement or pick one of the sample chips above.")
    else:
        with st.spinner("Analyzing requirement and searching campus resources..."):
            # 1. Parse requirement
            parsed_req = parse_need(need_input, user_id=user["id"])
            st.session_state["parsed"] = parsed_req
            st.session_state["need_text"] = need_input

            # 2. Find matching candidates
            candidates = find_matches(parsed_req)
            st.session_state["candidates"] = candidates
            st.session_state["selected_item"] = candidates[0] if candidates else None

            # Navigate to Results
            st.switch_page("pages/3_Results.py")
