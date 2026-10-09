"""CIRCULO - Main Application Entrypoint
Sustainable Consumption Decision Engine for Campus | SDG 12
Handles user authentication, demo account switching, and home landing hub.
"""
import streamlit as st
from config import APP_NAME, APP_TAGLINE, SDG_ALIGNMENT, LOGO_PATH
from db.database import init_db
from services.auth_service import authenticate_user, get_demo_accounts, get_user_by_id
from services.impact_service import get_impact_summary
from services.rescue_service import get_campus_idle_count
from ui.components import load_css, render_header, render_hero, render_metric_card, render_impact_showcase, render_footer

st.set_page_config(
    page_title=f"{APP_NAME} - Sustainable Campus Decision Engine",
    page_icon="♻️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Ensure database tables exist
init_db()

# Initialize session state variables
if "user" not in st.session_state:
    st.session_state["user"] = None
if "need_text" not in st.session_state:
    st.session_state["need_text"] = ""
if "parsed" not in st.session_state:
    st.session_state["parsed"] = None
if "candidates" not in st.session_state:
    st.session_state["candidates"] = []
if "options" not in st.session_state:
    st.session_state["options"] = []
if "selected_item" not in st.session_state:
    st.session_state["selected_item"] = None
if "flash" not in st.session_state:
    st.session_state["flash"] = None

load_css()

# Flash messages
if st.session_state["flash"]:
    msg_type, msg_text = st.session_state["flash"]
    if msg_type == "success":
        st.success(msg_text)
    elif msg_type == "error":
        st.error(msg_text)
    elif msg_type == "info":
        st.info(msg_text)
    st.session_state["flash"] = None

# If not authenticated, render Login view
if not st.session_state["user"]:
    render_header()
    st.markdown("<br>", unsafe_allow_html=True)
    # Public Live Sustainability & Circularity Impact Showcase — TOP OF PAGE
    render_impact_showcase(show_cta=False)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns([1.1, 1.3])

    with col1:
        st.markdown(
            f"""
            <div style='background:#ffffff; border:1.5px solid #bbf7d0; border-radius:16px; padding:2rem; box-shadow:0 4px 12px rgba(22,101,52,0.08);'>
                <h2 style='color:#14532d; margin-top:0;'>Sign In to {APP_NAME}</h2>
                <p style='color:#64748b; font-size:0.95rem;'>Enter your campus credentials to access shared equipment, borrow resources, and track circular savings.</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.write("")
        with st.form("login_form"):
            email = st.text_input("Campus Email", placeholder="arun@campus.edu")
            password = st.text_input("Password", type="password", placeholder="••••••••")
            submit_btn = st.form_submit_button("Sign In", type="primary", use_container_width=True)

            if submit_btn:
                user = authenticate_user(email, password)
                if user:
                    st.session_state["user"] = user
                    st.session_state["flash"] = ("success", f"Welcome back, {user['name']}!")
                    st.switch_page("pages/1_Home.py")
                else:
                    st.error("Invalid email or password. You can also select a quick demo account on the right.")

    with col2:
        st.markdown(
            """
            <div style='background:#f0fdf4; border:1.5px solid #86efac; border-radius:16px; padding:2rem;'>
                <h3 style='color:#166534; margin-top:0;'>⚡ One-Click Demo Accounts</h3>
                <p style='color:#334155; font-size:0.9rem;'>For hackathon judges and evaluators, instantly log in with pre-seeded personas across departments:</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        st.write("")
        demo_users = get_demo_accounts()
        
        # Student personas
        st.markdown("##### 🎓 Student Personas")
        s_cols = st.columns(2)
        student_list = [u for u in demo_users if u["role"] == "student"]
        for idx, u in enumerate(student_list[:4]):
            with s_cols[idx % 2]:
                if st.button(f"👤 {u['name']} ({u['department'].split()[0]})", key=f"demo_u_{u['id']}", use_container_width=True):
                    st.session_state["user"] = u
                    st.session_state["flash"] = ("success", f"Logged in as {u['name']} ({u['role'].capitalize()})")
                    st.switch_page("pages/1_Home.py")

        st.write("")
        # Lab & Admin personas
        st.markdown("##### 🔬 Labs & Administration")
        la_cols = st.columns(2)
        other_list = [u for u in demo_users if u["role"] in ("lab", "admin")]
        for idx, u in enumerate(other_list):
            with la_cols[idx % 2]:
                icon = "🔬" if u["role"] == "lab" else "🛡️"
                if st.button(f"{icon} {u['name']}", key=f"demo_u_{u['id']}", use_container_width=True):
                    st.session_state["user"] = u
                    st.session_state["flash"] = ("success", f"Logged in as {u['name']} ({u['role'].capitalize()})")
                    st.switch_page("pages/1_Home.py")

    render_footer()

else:
    # When user is signed in, redirect directly to the Home dashboard
    st.switch_page("pages/1_Home.py")
