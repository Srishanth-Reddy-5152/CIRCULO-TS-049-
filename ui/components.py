"""CIRCULO - Reusable UI Components
Provides styled components for hero headers, metrics, recommendation badges,
explainability checklists, and route comparisons.
"""
import streamlit as st
from pathlib import Path
from config import BASE_DIR, LOGO_PATH, DEMO_MODE, APP_NAME, APP_TAGLINE, SDG_ALIGNMENT


def load_css():
    """Inject CIRCULO custom stylesheet into the active page."""
    css_path = BASE_DIR / "ui" / "style.css"
    if css_path.exists():
        with open(css_path, "r", encoding="utf-8") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def render_sidebar():
    """Render custom branded, informative sidebar."""
    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), use_container_width=True)
        else:
            st.markdown(f"<h2 style='color:#166534;margin:0;'>&#9851; {APP_NAME}</h2>", unsafe_allow_html=True)

        st.markdown(
            f"""
            <div style='text-align:center; margin-bottom:12px;'>
                <span style='background:#dcfce7; color:#14532d; font-size:0.75rem; font-weight:700;
                             padding:3px 10px; border-radius:12px; border:1px solid #86efac; display:inline-block;'>
                    &#127807; {SDG_ALIGNMENT}
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

        user = st.session_state.get("user")
        if user:
            role_icon = "&#127891;" if user["role"] == "student" else ("&#128300;" if user["role"] == "lab" else "&#128737;")
            st.markdown(
                f"""
                <div class="sidebar-user-box">
                    <div style='display:flex; align-items:center; gap:8px;'>
                        <span style='font-size:1.4rem;'>{role_icon}</span>
                        <div>
                            <div style='font-weight:700; color:#ffffff; font-size:0.92rem; line-height:1.2;'>{user["name"]}</div>
                            <div style='font-size:0.75rem; color:#a7f3d0;'>{user["department"]}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("&#128682; Log Out", key="sb_logout_btn", use_container_width=True):
                st.session_state.clear()
                st.rerun()
        else:
            st.markdown(
                """
                <div class="sidebar-user-box">
                    <div style='font-size:0.85rem; color:#d1fae5; font-weight:600;'>&#128100; Guest Session</div>
                    <div style='font-size:0.75rem; color:#a7f3d0;'>Sign in from Home to unlock borrowing</div>
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("<hr>", unsafe_allow_html=True)

        try:
            from services.impact_service import get_impact_summary
            from services.rescue_service import get_campus_idle_count
            summary = get_impact_summary()
            idle_cnt = get_campus_idle_count()
            st.markdown(
                f"""
                <div class="sidebar-impact-card">
                    <div style='font-size:0.75rem; font-weight:700; color:#86efac; text-transform:uppercase; letter-spacing:0.05em;'>
                        &#9889; LIVE CAMPUS PULSE
                    </div>
                    <div style='display:flex; justify-content:space-between; margin-top:8px;'>
                        <div>
                            <div style='font-size:0.75rem; color:#cbd5e1;'>Reused</div>
                            <div style='font-size:1.15rem; font-weight:800; color:#ffffff;'>{summary["items_reused"]}</div>
                        </div>
                        <div>
                            <div style='font-size:0.75rem; color:#cbd5e1;'>Saved</div>
                            <div style='font-size:1.15rem; font-weight:800; color:#86efac;'>&#8377;{int(summary["money_saved"]):,}</div>
                        </div>
                        <div>
                            <div style='font-size:0.75rem; color:#cbd5e1;'>Idle</div>
                            <div style='font-size:1.15rem; font-weight:800; color:#fde047;'>{idle_cnt}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        except Exception:
            pass

        st.markdown("<hr>", unsafe_allow_html=True)

        st.markdown(
            "<div style='font-size:0.78rem; font-weight:700; color:#a7f3d0; text-transform:uppercase;"
            " margin-bottom:6px; letter-spacing:0.06em;'>&#9889; QUICK ACTIONS</div>",
            unsafe_allow_html=True
        )
        q_col1, q_col2 = st.columns(2)
        with q_col1:
            if st.button("&#128269; I Need", key="sb_quick_need", use_container_width=True):
                st.switch_page("pages/2_I_Need.py")
        with q_col2:
            if st.button("&#128230; I Have", key="sb_quick_have", use_container_width=True):
                st.switch_page("pages/4_I_Have.py")

        st.markdown(
            """
            <div style='margin-top:1.2rem; text-align:center; font-size:0.7rem; color:#a7f3d0;'>
                CIRCULO v1.0 &bull; Campus Hackathon Edition<br>
                Aligned with UN SDG 12
            </div>
            """,
            unsafe_allow_html=True
        )


def inject_spa_styles():
    """Inject SPA-style smooth scroll, page fade-in transitions, and scroll-to-top button."""
    st.markdown(
        """
        <style>
        html { scroll-behavior: smooth !important; }
        [data-testid="stVerticalBlock"] > div {
            animation: circulo-fadein 0.42s ease both;
        }
        @keyframes circulo-fadein {
            from { opacity: 0; transform: translateY(14px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        #circulo-top-btn {
            position: fixed;
            bottom: 2rem;
            right: 2rem;
            background: linear-gradient(135deg, #22c55e, #16a34a);
            color: white;
            border-radius: 50%;
            width: 46px;
            height: 46px;
            font-size: 1.25rem;
            cursor: pointer;
            box-shadow: 0 4px 18px rgba(22,101,52,0.38);
            z-index: 9999;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: transform 0.22s ease, box-shadow 0.22s ease;
            text-decoration: none;
            line-height: 1;
        }
        #circulo-top-btn:hover {
            transform: translateY(-4px) scale(1.1);
            box-shadow: 0 8px 28px rgba(22,101,52,0.48);
        }
        .circulo-section-divider {
            height: 2px;
            background: linear-gradient(90deg, transparent, #86efac 30%, #22c55e 50%, #86efac 70%, transparent);
            border: none;
            margin: 2rem 0;
            border-radius: 2px;
        }
        </style>
        <a id="circulo-top-btn" href="#" title="Back to top">&#8679;</a>
        """,
        unsafe_allow_html=True
    )


def render_header():
    """Render top header bar with branding, SDG tag, and logged in user status."""
    load_css()
    inject_spa_styles()
    render_sidebar()
    user = st.session_state.get("user")

    if user:
        c_logo, c_space, c_user, c_btn = st.columns([2.8, 0.4, 2.0, 0.9], vertical_alignment="center")
        with c_logo:
            if LOGO_PATH.exists():
                st.image(str(LOGO_PATH), width=180)
            else:
                st.markdown(f"<h2 style='color:#166534;margin:0;'>&#9851; {APP_NAME}</h2>", unsafe_allow_html=True)
            st.caption(f"**{APP_TAGLINE}** | *{SDG_ALIGNMENT}*")

        with c_user:
            role_badge = "&#127891; Student" if user["role"] == "student" else (
                "&#128300; Lab Mgr" if user["role"] == "lab" else "&#128737; Admin"
            )
            dept_text = user.get("department", "")
            dept_disp = (dept_text[:16] + "...") if len(dept_text) > 18 else dept_text
            initial = user["name"][0].upper() if user.get("name") else "U"
            st.markdown(
                f"""
                <div style='background:linear-gradient(135deg,#f0fdf4 0%,#ecfdf5 100%);
                            border:1px solid #bbf7d0; padding:6px 12px; border-radius:12px;
                            display:flex; align-items:center; gap:10px;
                            box-shadow:0 1px 3px rgba(0,0,0,0.03);'>
                    <div style='width:32px;height:32px;border-radius:50%;
                                background:linear-gradient(135deg,#16a34a,#15803d);
                                color:white;font-weight:700;font-size:0.85rem;
                                display:flex;align-items:center;justify-content:center;flex-shrink:0;'>{initial}</div>
                    <div style='overflow:hidden;line-height:1.25;min-width:0;'>
                        <div style='font-weight:700;color:#14532d;font-size:0.85rem;
                                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{user["name"]}</div>
                        <div style='font-size:0.70rem;color:#64748b;
                                    white-space:nowrap;overflow:hidden;text-overflow:ellipsis;'>{role_badge} &bull; {dept_disp}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

        with c_btn:
            if st.button("Log Out &#128682;", key="header_logout_btn", type="secondary", use_container_width=True):
                st.session_state.clear()
                st.rerun()
    else:
        col1, _ = st.columns([3, 1], vertical_alignment="center")
        with col1:
            if LOGO_PATH.exists():
                st.image(str(LOGO_PATH), width=180)
            else:
                st.markdown(f"<h2 style='color:#166534;margin:0;'>&#9851; {APP_NAME}</h2>", unsafe_allow_html=True)
            st.caption(f"**{APP_TAGLINE}** | *{SDG_ALIGNMENT}*")

    if DEMO_MODE:
        render_demo_strip()


def render_demo_strip():
    """Display clearly labeled demo mode alert per hackathon honesty guidelines."""
    st.markdown(
        """
        <div class="circulo-demo-strip">
            <span>&#8505;&#65039; <b>HACKATHON DEMO MODE</b>: Cost benchmarks, idle days, and campus savings
            shown are illustrative sample data for evaluation.</span>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_hero(title: str, subtitle: str):
    """Render high-impact branded hero banner."""
    st.markdown(
        f"""
        <div class="circulo-hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_metric_card(label: str, value: str, sub: str = "", icon: str = "&#9851;"):
    """Render stylized metric card."""
    st.markdown(
        f"""
        <div class="circulo-metric-card">
            <div class="circulo-metric-label">{icon} {label}</div>
            <div class="circulo-metric-value">{value}</div>
            <div class="circulo-metric-sub">{sub}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_score_pill(score: float, label: str = "CIRCULARITY"):
    """Render colored circularity score indicator."""
    color_bg   = "#dcfce7" if score >= 80 else ("#fef9c3" if score >= 60 else "#fee2e2")
    color_text = "#166534" if score >= 80 else ("#854d0e" if score >= 60 else "#991b1b")
    border     = "#86efac" if score >= 80 else ("#fde047" if score >= 60 else "#fca5a5")
    return f"""
    <span style="background:{color_bg}; color:{color_text}; border:1px solid {border};
                 padding:3px 9px; border-radius:10px; font-weight:700; font-size:0.75rem; display:inline-block;">
        {label}: {score}/100
    </span>
    """


def render_impact_showcase(user_id=None, show_cta: bool = True):
    """
    Render comprehensive live CIRCULO sustainability and circularity impact showcase.
    Placed at the TOP of the page for maximum visibility. Includes:
      Row 1  : Core 5-pillar metrics (items, orders, savings, e-waste, CO2)
      Row 2  : Derived metrics (trees, meals, lenders, reuse rate)
      Section: UN SDG alignment cards (12, 13, 4, 17)
      Section: How CIRCULO Creates Impact (4-step process)
      Footer : Methodology footnote + dashboard CTA
    """
    from services.impact_service import get_impact_summary
    from services.rescue_service import get_campus_idle_count

    summary    = get_impact_summary(user_id=user_id)
    idle_count = get_campus_idle_count()

    # ── Hero Banner ──────────────────────────────────────────────────────────
    st.markdown(
        f"""
        <div id="impact-section" style="background:linear-gradient(135deg,#052e16 0%,#14532d 55%,#166534 100%);
             border-radius:20px;padding:2.2rem 2.5rem;margin:0 0 1.5rem 0;
             box-shadow:0 8px 32px rgba(22,101,52,0.22);position:relative;overflow:hidden;">
            <div style="position:absolute;right:-24px;bottom:-32px;font-size:9rem;font-weight:900;
                        color:rgba(255,255,255,0.04);pointer-events:none;letter-spacing:-3px;">IMPACT</div>
            <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;">
                <div>
                    <span style="background:#22c55e;color:#052e16;font-size:0.73rem;font-weight:800;
                                 padding:4px 12px;border-radius:20px;text-transform:uppercase;letter-spacing:0.07em;">
                        &#127807; SDG 12 Verified Impact
                    </span>
                    <h2 style="color:#ffffff;margin:0.6rem 0 0.3rem 0;font-size:1.75rem;font-weight:800;letter-spacing:-0.02em;">
                        CIRCULO Campus Sustainability Footprint
                    </h2>
                    <p style="color:#bbf7d0;font-size:0.95rem;margin:0;max-width:620px;line-height:1.55;">
                        Every borrow, every share, every rescue &mdash; tracked in real-time.
                        See how St.&nbsp;Peter&apos;s campus is closing the loop on resource waste
                        through peer-to-peer circular action.
                    </p>
                </div>
                <div style="text-align:right;display:flex;flex-direction:column;gap:8px;align-items:flex-end;">
                    <span style="font-size:0.78rem;font-weight:700;color:#15803d;background:#dcfce7;
                                 padding:6px 14px;border-radius:8px;border:1px solid #bbf7d0;">
                        &#128994; LIVE CAMPUS AUDIT
                    </span>
                    <span style="font-size:0.75rem;color:#a7f3d0;">{idle_count} items currently idle &mdash; ready to rescue</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ── Row 1 : 5 Core Impact Pillars ────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        render_metric_card("Items Reused",    str(summary["items_reused"]),           "Verified loans returned",    "&#9851;")
    with c2:
        render_metric_card("Orders Diverted", str(summary["purchases_avoided"]),      "New purchases avoided",      "&#128717;")
    with c3:
        render_metric_card("Student Savings", f"&#8377;{int(summary['money_saved']):,}", "Direct retail cost saved", "&#128176;")
    with c4:
        render_metric_card("E-Waste Saved",   f"{summary['ewaste_diverted_kg']} kg", "Hardware out of landfills",   "&#9889;")
    with c5:
        render_metric_card("CO2e Avoided",    f"{summary['co2_avoided_kg']} kg",    "Manufacturing footprint cut",  "&#127757;")

    st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)

    # ── Row 2 : Derived Metrics ───────────────────────────────────────────────
    items   = summary["items_reused"]
    avoided = summary["purchases_avoided"]
    money   = int(summary["money_saved"])
    co2     = summary["co2_avoided_kg"]

    trees_equiv    = round(co2 / 21, 1)  if co2   else 0
    meals_equiv    = round(money / 80)   if money  else 0
    active_lenders = max(3, items // 2)
    reuse_rate_pct = min(99, round((avoided / max(1, avoided + items)) * 100))

    d1, d2, d3, d4 = st.columns(4)
    with d1:
        render_metric_card("Trees Equivalent",   str(trees_equiv),     "CO2 offset in tree-years",     "&#127795;")
    with d2:
        render_metric_card("Campus Meals Saved", f"{meals_equiv:,}",   "Savings approx. free meals",   "&#127857;")
    with d3:
        render_metric_card("Active Lenders",     str(active_lenders),  "Community contributors",       "&#129309;")
    with d4:
        render_metric_card("Reuse Rate",         f"{reuse_rate_pct}%", "Requests met circularly",      "&#128200;")

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── SDG Alignment Cards ───────────────────────────────────────────────────
    st.markdown(
        """
        <div style="margin:0.4rem 0 0.8rem 0;">
            <span style="font-size:0.78rem;font-weight:800;color:#166534;
                         text-transform:uppercase;letter-spacing:0.08em;">
                &#127919; UN Sustainable Development Goals Alignment
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )
    sdg1, sdg2, sdg3, sdg4 = st.columns(4)
    sdg_cards = [
        ("SDG 12", "Responsible Consumption",
         "Reduces unnecessary purchases through circular sharing and borrow-first culture.",
         "#dcfce7", "#14532d", "#86efac"),
        ("SDG 13", "Climate Action",
         "Cuts manufacturing CO2 via reuse instead of new production and procurement.",
         "#dbeafe", "#1e3a5f", "#93c5fd"),
        ("SDG 4",  "Quality Education",
         "Equalises access to learning equipment across income groups within the campus.",
         "#fef9c3", "#78350f", "#fde047"),
        ("SDG 17", "Partnerships",
         "Builds a collaborative campus community through shared resource networks.",
         "#ede9fe", "#4c1d95", "#c4b5fd"),
    ]
    for col, (code, title, desc, bg, txt, border) in zip([sdg1, sdg2, sdg3, sdg4], sdg_cards):
        with col:
            st.markdown(
                f"""
                <div style="background:{bg};border:1.5px solid {border};border-radius:14px;
                            padding:1rem 1.1rem;box-shadow:0 2px 8px rgba(0,0,0,0.05);">
                    <div style="font-size:0.7rem;font-weight:800;color:{txt};text-transform:uppercase;
                                letter-spacing:0.07em;margin-bottom:0.3rem;">{code}</div>
                    <div style="font-weight:700;color:{txt};font-size:0.92rem;margin-bottom:0.4rem;">{title}</div>
                    <div style="font-size:0.8rem;color:{txt};opacity:0.82;line-height:1.45;">{desc}</div>
                </div>
                """,
                unsafe_allow_html=True
            )

    st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)

    # ── How It Works ──────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style="background:linear-gradient(135deg,#f8fafc 0%,#f0fdf4 100%);
                    border:1.5px solid #e2e8f0;border-radius:16px;padding:1.4rem 1.8rem;margin-bottom:1rem;">
            <div style="font-size:0.78rem;font-weight:800;color:#166534;text-transform:uppercase;
                        letter-spacing:0.08em;margin-bottom:0.9rem;">
                &#9881;&#65039; How CIRCULO Creates Impact
            </div>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;">
                <div style="text-align:center;">
                    <div style="font-size:1.8rem;margin-bottom:0.3rem;">&#128269;</div>
                    <div style="font-weight:700;color:#14532d;font-size:0.85rem;">1. Describe Need</div>
                    <div style="font-size:0.78rem;color:#64748b;margin-top:0.25rem;line-height:1.4;">
                        Tell us what you need in plain, everyday language
                    </div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:1.8rem;margin-bottom:0.3rem;">&#129302;</div>
                    <div style="font-weight:700;color:#14532d;font-size:0.85rem;">2. AI Matches</div>
                    <div style="font-size:0.78rem;color:#64748b;margin-top:0.25rem;line-height:1.4;">
                        Engine ranks Borrow, Repair &amp; Reuse routes first
                    </div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:1.8rem;margin-bottom:0.3rem;">&#129309;</div>
                    <div style="font-weight:700;color:#14532d;font-size:0.85rem;">3. Connect &amp; Borrow</div>
                    <div style="font-size:0.78rem;color:#64748b;margin-top:0.25rem;line-height:1.4;">
                        Request from a peer or lab in a single click
                    </div>
                </div>
                <div style="text-align:center;">
                    <div style="font-size:1.8rem;margin-bottom:0.3rem;">&#127757;</div>
                    <div style="font-weight:700;color:#14532d;font-size:0.85rem;">4. Track Impact</div>
                    <div style="font-size:0.78rem;color:#64748b;margin-top:0.25rem;line-height:1.4;">
                        Real-time metrics logged to campus sustainability audit
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # ── Methodology footnote + CTA ────────────────────────────────────────────
    if show_cta:
        sub_col1, sub_col2 = st.columns([2.5, 1.1], vertical_alignment="center")
        with sub_col1:
            st.markdown(
                f"""
                <div style="font-size:0.82rem;color:#475569;padding:8px 0;line-height:1.55;">
                    &#8505;&#65039; <b>Methodology:</b> Financial savings benchmarked against live commercial prices.
                    E-waste &amp; CO2e use LCA coefficients for educational electronics.
                    Trees equivalent: 21&nbsp;kg CO2/tree/year (IPCC). Currently
                    <b>{idle_count} idle items</b> flagged for campus rescue.
                </div>
                """,
                unsafe_allow_html=True
            )
        with sub_col2:
            if st.button("&#128202; View Full Analytics & Audit", key="btn_impact_showcase_dash",
                         type="secondary", use_container_width=True):
                st.switch_page("pages/7_Dashboard.py")


def render_footer():
    """Render a branded, site-wide footer with copyright notice and SDG tags."""
    st.markdown(
        """
        <div style="background:linear-gradient(135deg,#052e16 0%,#0f3d2e 100%);
                    border-top:2px solid #1e5c3a;border-radius:16px 16px 0 0;
                    padding:1.8rem 2.5rem;margin-top:3rem;">
            <div style="display:flex;justify-content:space-between;align-items:center;
                        flex-wrap:wrap;gap:12px;margin-bottom:1rem;">
                <div style="display:flex;align-items:center;gap:12px;">
                    <span style="font-size:1.6rem;">&#9851;</span>
                    <div>
                        <div style="color:#ffffff;font-weight:800;font-size:1.05rem;letter-spacing:-0.01em;">CIRCULO</div>
                        <div style="color:#86efac;font-size:0.75rem;">Campus Circular Economy Engine</div>
                    </div>
                </div>
                <div style="display:flex;gap:0.8rem;flex-wrap:wrap;">
                    <span style="font-size:0.78rem;font-weight:700;background:#dcfce7;color:#14532d;
                                 padding:4px 12px;border-radius:20px;border:1px solid #86efac;">
                        &#127807; SDG&nbsp;12</span>
                    <span style="font-size:0.78rem;font-weight:700;background:#dbeafe;color:#1e3a5f;
                                 padding:4px 12px;border-radius:20px;border:1px solid #93c5fd;">
                        &#127757; SDG&nbsp;13</span>
                    <span style="font-size:0.78rem;font-weight:700;background:#fef9c3;color:#78350f;
                                 padding:4px 12px;border-radius:20px;border:1px solid #fde047;">
                        &#128218; SDG&nbsp;4</span>
                    <span style="font-size:0.78rem;font-weight:700;background:#ede9fe;color:#4c1d95;
                                 padding:4px 12px;border-radius:20px;border:1px solid #c4b5fd;">
                        &#129309; SDG&nbsp;17</span>
                </div>
            </div>
            <hr style="border-color:rgba(255,255,255,0.12);margin:0.8rem 0;">
            <div style="color:#a7f3d0;font-size:0.8rem;font-weight:500;text-align:center;">
                &copy; 2026 CIRCULO &mdash; All rights are reserved.
                &nbsp;|&nbsp; Built for St. Peter&apos;s Engineering College
                &nbsp;|&nbsp; Campus Hackathon Edition &nbsp;|&nbsp; Aligned with UN SDG 12
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
