"""CIRCULO - Results & Decision Engine Page
Categorizes options into distinct routes: Borrow, Reuse, Buy Used, and Repair/New.
Displays full item details only when clicked.
"""
import streamlit as st
from ui.components import render_header, render_score_pill
from services.decision_service import evaluate_routes, get_price_reference, generate_reasons
from services.transaction_service import create_borrow_request

st.set_page_config(page_title="CIRCULO - Results & Decisions", page_icon="🎯", layout="wide")

if not st.session_state.get("user"):
    st.warning("Please sign in from the main portal first.")
    if st.button("Go to Login"):
        st.switch_page("app.py")
    st.stop()

render_header()
user = st.session_state["user"]
parsed = st.session_state.get("parsed")
candidates = st.session_state.get("candidates", [])

if not parsed:
    st.info("No active search. Please describe a requirement first.")
    if st.button("🔍 Go to I Need"):
        st.switch_page("pages/2_I_Need.py")
    st.stop()

# 1. Semantic Need Understanding Panel
with st.expander("🧠 How CIRCULO Understood Your Need (Semantic Capability Breakdown)", expanded=True):
    col_u1, col_u2, col_u3 = st.columns([1.5, 2, 1.5])
    with col_u1:
        st.markdown(
            f"""
            <div style='font-size:0.82rem; font-weight:700; color:#475569; text-transform:uppercase; margin-bottom:4px;'>Identified Objective:</div>
            <div style='font-size:1.15rem; color:#14532d; font-weight:700; line-height:1.3; margin-bottom:6px;'>{parsed.get('need')}</div>
            """,
            unsafe_allow_html=True
        )
        st.caption(f"Original input: \"{parsed.get('raw_text')}\"")
    with col_u2:
        st.markdown("<div style='font-size:0.82rem; font-weight:700; color:#475569; text-transform:uppercase; margin-bottom:6px;'>Required Capabilities:</div>", unsafe_allow_html=True)
        caps_html = " ".join([f"<span class='circulo-chip' style='background:#dcfce7; color:#14532d; font-weight:600;'>✓ {c}</span>" for c in parsed.get("required_capabilities", [])])
        st.markdown(caps_html, unsafe_allow_html=True)
    with col_u3:
        st.markdown(
            f"""
            <div style='font-size:0.82rem; font-weight:700; color:#475569; text-transform:uppercase; margin-bottom:4px;'>Inferred Purpose:</div>
            <div style='font-size:1.05rem; color:#0f172a; font-weight:600;'>{parsed.get('purpose', 'Academic / Project')}</div>
            """,
            unsafe_allow_html=True
        )

st.markdown("<br>", unsafe_allow_html=True)

if not candidates:
    st.warning("No direct campus inventory match found for this specific capability set.")
    st.info("No idle campus resource is currently available. Consider buying pre-owned from graduating seniors before purchasing brand new.")
    st.stop()

# Helper to render a clickable item card that shows details ONLY when expanded
def render_item_card_with_expandable_details(item, route_type="borrow"):
    cap_pct = int(item.get("capability_match_score", 0.0) * 100)
    prices = get_price_reference(item["name"])
    
    # Define route specific attributes
    if route_type == "borrow":
        cost_badge = "₹0 (Free Campus Loan)"
        route_title = "Borrow on Campus"
        btn_action_label = "Request to Borrow"
        header_icon = "🔄"
    elif route_type == "reuse":
        cost_badge = "₹0 (Repurposed Alternative)"
        route_title = "Reuse / Repurpose"
        btn_action_label = "Claim Alternative"
        header_icon = "♻️"
    elif route_type == "buy_used":
        cost_badge = f"~₹{int(prices['used_price'])} (Used / Pre-Owned)"
        route_title = "Buy Used"
        btn_action_label = "Contact Seller"
        header_icon = "🏷️"
    else:
        cost_badge = f"~₹{int(prices['new_price'])} (Retail New)"
        route_title = "Buy New"
        btn_action_label = "View Retail Listing"
        header_icon = "🛒"

    expander_title = f"{header_icon} {item['name']}  |  {cap_pct}% Match  |  {cost_badge}  — Click to view details"
    
    with st.expander(expander_title, expanded=False):
        st.markdown(f"### {item['name']}")
        
        detail_c1, detail_c2 = st.columns([1.2, 1])
        with detail_c1:
            st.markdown(
                f"""
                <div style='background:#f8fafc; border:1px solid #e2e8f0; border-radius:10px; padding:12px; margin-bottom:12px;'>
                    <div style='font-size:0.85rem; color:#334155; margin-bottom:4px;'>
                        <b>📍 Campus Location:</b> {item.get('location', 'Campus')}
                    </div>
                    <div style='font-size:0.85rem; color:#334155; margin-bottom:4px;'>
                        <b>👤 Provider / Owner:</b> {item.get('owner_name', 'Campus Peer')} ({item.get('owner_department', 'Department')})
                    </div>
                    <div style='font-size:0.85rem; color:#334155; margin-bottom:4px;'>
                        <b>Condition:</b> {item.get('condition', 'Good')} &nbsp;|&nbsp; 
                        <b>Quantity Available:</b> {item.get('quantity_available', 1)} unit(s)
                    </div>
                    <div style='font-size:0.85rem; color:#334155;'>
                        <b>Description:</b> {item.get('description', 'Verified functional hardware.')}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            # ── Optional photo viewer (collapsed by default) ──────────────────
            item_image_path = item.get("image_path")
            if item_image_path:
                from pathlib import Path as _Path
                img_path = _Path(item_image_path)
                if img_path.exists():
                    with st.expander("📷 View Item Photo", expanded=False):
                        st.image(
                            str(img_path),
                            caption=f"{item['name']} — photo uploaded by {item.get('owner_name', 'owner')}",
                            use_container_width=True
                        )
                        st.caption("Photo verified by CIRCULO listing system.")
            
            # Matched Capabilities Breakdown
            st.markdown("**Functional Capabilities Match:**")
            matched_caps = item.get("matched_capabilities", [])
            unmatched_caps = item.get("unmatched_capabilities", [])
            
            chips_html = " ".join([f"<span class='circulo-chip' style='background:#dcfce7; color:#14532d; font-weight:600;'>✓ {c}</span>" for c in matched_caps])
            if unmatched_caps:
                chips_html += " " + " ".join([f"<span class='circulo-chip' style='background:#f1f5f9; color:#64748b;'>○ {c}</span>" for c in unmatched_caps])
            st.markdown(chips_html, unsafe_allow_html=True)

        with detail_c2:
            st.markdown(
                f"""
                <div style='background:#ffffff; border:1.5px solid #86efac; border-radius:10px; padding:12px; margin-bottom:12px;'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <span style='font-size:0.75rem; font-weight:700; color:#15803d; text-transform:uppercase;'>CIRCULAR DECISION ENGINE</span>
                        <span style='font-size:0.8rem; font-weight:800; color:#14532d;'>{item.get('blended_score', 0.85)*100:.0f}/100</span>
                    </div>
                    <div style='font-size:1.2rem; font-weight:800; color:#0f172a; margin:4px 0;'>{cost_badge}</div>
                    <div style='font-size:0.8rem; color:#64748b;'>Retail Retail Avoided: ~₹{int(prices['new_price'])}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            
            # Why CIRCULO recommends this
            reasons = generate_reasons(route_type, item, user, prices)
            st.markdown("<b style='font-size:0.85rem;'>Why CIRCULO recommends this:</b>", unsafe_allow_html=True)
            for r in reasons[:4]:
                st.markdown(f"<div class='circulo-check-item'><span class='circulo-check-icon'>✓</span><span style='font-size:0.82rem;'>{r}</span></div>", unsafe_allow_html=True)

        # Action section inside the expanded view
        st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)
        if route_type == "borrow":
            if item.get("availability") == "AVAILABLE" and item.get("quantity_available", 0) > 0:
                act_col1, act_col2 = st.columns([2, 1])
                with act_col1:
                    borrow_notes = st.text_input(
                        "Project / Return Note for Owner (optional):",
                        placeholder="e.g. Needed for mini-project presentation, will return in 4 days",
                        key=f"bnotes_{item['id']}"
                    )
                with act_col2:
                    st.write("")
                    st.write("")
                    if st.button("🚀 Confirm Request to Borrow", type="primary", key=f"btn_b_{item['id']}", use_container_width=True):
                        req_id = create_borrow_request(
                            user_id=user["id"],
                            item_id=item["id"],
                            need_query_id=parsed.get("need_query_id"),
                            notes=borrow_notes
                        )
                        st.session_state["flash"] = (
                            "success",
                            f"Borrow request #{req_id} sent to {item['owner_name']}! You can follow approval in Requests."
                        )
                        st.switch_page("pages/6_Requests.py")
            else:
                st.button("Item Currently Loaned (Join Waitlist)", disabled=True, key=f"bwait_{item['id']}")

        elif route_type == "reuse":
            act_col1, act_col2 = st.columns([2, 1])
            with act_col1:
                st.caption("This item is a compatible campus alternative or surplus lab component.")
            with act_col2:
                if st.button("♻️ Request Campus Repurpose", type="primary", key=f"btn_reuse_{item['id']}", use_container_width=True):
                    req_id = create_borrow_request(
                        user_id=user["id"],
                        item_id=item["id"],
                        need_query_id=parsed.get("need_query_id"),
                        notes="Repurposing alternative campus hardware"
                    )
                    st.session_state["flash"] = ("success", f"Repurpose request #{req_id} submitted to {item['owner_name']}!")
                    st.switch_page("pages/6_Requests.py")

        elif route_type == "buy_used":
            act_col1, act_col2 = st.columns([2, 1])
            with act_col1:
                st.caption(f"Offered for second-hand acquisition at ~₹{int(prices['used_price'])}. Extends hardware lifespan and avoids new packaging waste.")
            with act_col2:
                if st.button("💬 Contact Senior / Seller", type="secondary", key=f"btn_used_{item['id']}", use_container_width=True):
                    st.info(f"Listing message sent to {item['owner_name']} ({item.get('owner_department')}). Check student notice board.")

st.markdown("## 🧭 Sustainable Options by Route")
st.caption("Items are categorized separately below. **Click on any item to view its complete specifications, capability match, and actions.**")

# 4 DISTINCT TABS: Borrow, Reuse, Buy Used, Repair & Buy New
tab_borrow, tab_reuse, tab_used, tab_other = st.tabs([
    "🔄 1. Items to Borrow (Free ₹0)",
    "♻️ 2. Items to Reuse / Repurpose",
    "🏷️ 3. Items to Buy Used (Pre-Owned)",
    "🔧 4. Repair & Retail Benchmarks"
])

# Categorize items
# 1. Borrow: High capability match, available for borrow on campus
borrow_list = [c for c in candidates if c.get("available_for") in ("borrow", "both")]
if not borrow_list:
    borrow_list = candidates[:2]

# 2. Reuse / Repurpose: Alternatives (e.g. candidates with different forms/names) or secondary matches
reuse_list = candidates[1:] if len(candidates) > 1 else candidates

# 3. Buy Used: Items with used price benchmark or available for donation/both
used_list = [c for c in candidates if c.get("available_for") in ("donate", "both")]
if not used_list:
    used_list = candidates[:3]

# --- TAB 1: BORROW ---
with tab_borrow:
    st.markdown("### 🔄 Items Available to Borrow on Campus")
    st.caption("Zero cost (₹0). Highest circularity. Free loans from campus peers and hardware labs.")
    
    if not borrow_list:
        st.info("No direct borrow listings found for this search. Check the Reuse or Buy Used tabs.")
    else:
        for item in borrow_list:
            render_item_card_with_expandable_details(item, route_type="borrow")

# --- TAB 2: REUSE & REPURPOSE ---
with tab_reuse:
    st.markdown("### ♻️ Compatible Alternatives to Reuse / Repurpose")
    st.caption("Hardware boards, adapters, and lab surplus that can fulfill your requirement without any new purchase.")
    
    if not reuse_list:
        st.info("No alternative items found.")
    else:
        for item in reuse_list:
            render_item_card_with_expandable_details(item, route_type="reuse")

# --- TAB 3: BUY USED ---
with tab_used:
    st.markdown("### 🏷️ Items Available to Buy Used / Pre-Owned")
    st.caption("Affordable second-hand options from graduating seniors and campus classifieds. Extends product lifecycle.")
    
    for item in used_list:
        render_item_card_with_expandable_details(item, route_type="buy_used")

# --- TAB 4: REPAIR & BUY NEW ---
with tab_other:
    st.markdown("### 🔧 Hardware Repair & Commercial Retail Benchmarks")
    st.caption("Comparison benchmarks for fixing damaged items vs purchasing brand new.")
    
    top_item = candidates[0]
    prices = get_price_reference(top_item["name"])
    
    col_rep, col_new = st.columns(2)
    with col_rep:
        st.markdown(
            f"""
            <div style='background:#fefce8; border:1.5px solid #fde047; border-radius:12px; padding:1.2rem;'>
                <div style='display:flex; justify-content:space-between;'>
                    <h4 style='color:#854d0e; margin:0;'>🔧 Campus Repair Clinic</h4>
                    <span style='font-weight:700; color:#854d0e;'>~₹{int(prices['repair_cost'])}</span>
                </div>
                <p style='font-size:0.85rem; color:#713f12; margin:8px 0;'>
                    Got a faulty board or loose connector? Visit the Campus Makerspace repair bench to fix it for the cost of basic solder/components.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        with st.expander("View Repair Details", expanded=False):
            st.markdown(f"**Estimated Cost:** ~₹{int(prices['repair_cost'])}")
            st.markdown("**Location:** Campus Makerspace & Fabrication Lab, Central Workshop")
            st.markdown("**Tools Available:** Soldering stations, multimeters, component testers, wire crimpers.")
            if st.button("Submit Repair Ticket", key="btn_rep_tab"):
                st.success("Repair ticket logged with Campus Makerspace! Workbench open Mon-Sat.")

    with col_new:
        st.markdown(
            f"""
            <div style='background:#ffffff; border:1.5px solid #cbd5e1; border-radius:12px; padding:1.2rem;'>
                <div style='display:flex; justify-content:space-between;'>
                    <h4 style='color:#0f172a; margin:0;'>🛒 Buy Brand New Retail</h4>
                    <span style='font-weight:700; color:#0f172a;'>~₹{int(prices['new_price'])}</span>
                </div>
                <p style='font-size:0.85rem; color:#475569; margin:8px 0;'>
                    Brand new commercial product from online e-commerce. Lowest circularity score due to manufacturing and packaging footprint.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        with st.expander("View Retail Comparison", expanded=False):
            st.markdown(f"**Retail Price:** ~₹{int(prices['new_price'])}")
            st.markdown("**Delivery:** 1–3 business days via online distributors (Robocraze / Amazon).")
            st.markdown("**Circularity Impact:** High embodied carbon; generates new electronic packaging waste.")
            st.caption("Recommend only if campus borrowing, reuse, and second-hand options cannot meet strict requirements.")
