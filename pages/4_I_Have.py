"""CIRCULO - I Have Something
Photo-first resource listing with AI image scan & form auto-fill.
Upload a photo → image is analysed → form fields auto-fill.
"""
import streamlit as st
from ui.components import render_header, render_hero
from services.resource_service import suggest_capabilities_for_item, add_resource
from services.image_scan_service import scan_image_for_autofill, save_item_image
from db.database import execute_query

st.set_page_config(page_title="CIRCULO - List Resource", page_icon="📦", layout="wide")

if not st.session_state.get("user"):
    st.warning("Please sign in from the main portal first.")
    if st.button("Go to Login"):
        st.switch_page("app.py")
    st.stop()

render_header()
user = st.session_state["user"]

render_hero(
    title="List a Resource in Under 60 Seconds",
    subtitle="Upload a photo → our scanner auto-fills the form for you. Make idle equipment visible to your campus community!"
)

# ─── Session state for scan results & form reset ─────────────────────────────
if st.session_state.get("reset_have_form"):
    st.session_state["scan_result"] = None
    st.session_state["scan_image_name"] = None
    st.session_state["new_item_title"] = ""
    st.session_state["item_caps_input"] = ""
    st.session_state["item_desc_input"] = ""
    st.session_state["reset_have_form"] = False

if "scan_result" not in st.session_state:
    st.session_state["scan_result"] = None
if "scan_image_name" not in st.session_state:
    st.session_state["scan_image_name"] = None

# Fetch available categories
cat_rows = execute_query("SELECT id, name FROM categories ORDER BY name ASC")
categories_map = {c["name"]: c["id"] for c in cat_rows}
cat_names = list(categories_map.keys())

# ─── PHOTO UPLOAD (top, triggers scan) ────────────────────────────────────────
st.markdown("---")
st.markdown("### 📷 Step 1 — Upload a Photo *(optional but recommended)*")
st.caption("Upload a photo of your hardware, tool, or book. AI Vision analyzes the image to auto-detect item model, specs, and condition.")

photo_col, hint_col = st.columns([1.4, 1])
with photo_col:
    uploaded_photo = st.file_uploader(
        "Upload item photo (JPG / PNG)",
        type=["jpg", "jpeg", "png"],
        key="item_photo_upload"
    )

with hint_col:
    if st.session_state["scan_result"]:
        sr = st.session_state["scan_result"]
        conf = sr.get("scan_confidence", 0)
        conf_color = "#15803d" if conf >= 60 else ("#d97706" if conf >= 30 else "#9ca3af")
        st.markdown(
            f"""
            <div style='background:linear-gradient(135deg,#0f3d2e,#1a4a35);
                        border-radius:12px; padding:14px; color:#fff;'>
                <div style='font-size:0.72rem; font-weight:700; color:#86efac;
                            text-transform:uppercase; letter-spacing:.05em; margin-bottom:6px;'>
                    🔍 SCAN COMPLETE
                </div>
                <div style='font-size:0.88rem; margin-bottom:4px;'>
                    <b>Matched via:</b> {sr.get('matched_by','—')}
                </div>
                <div style='font-size:0.88rem; margin-bottom:8px;'>
                    <b>Condition detected:</b>
                    <span style='color:#fde047; font-weight:700;'>{sr.get('suggested_condition','—')}</span>
                </div>
                <div style='font-size:0.75rem; color:#a7f3d0;'>{sr.get('condition_note','')}</div>
                <div style='margin-top:10px; background:rgba(0,0,0,.3); border-radius:8px;
                            height:8px; overflow:hidden;'>
                    <div style='height:100%; width:{conf}%; background:linear-gradient(90deg,#22c55e,#86efac);
                                border-radius:8px; transition:width .4s;'></div>
                </div>
                <div style='font-size:0.7rem; color:#86efac; margin-top:4px;'>
                    Scan confidence: {conf}%
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            """
            <div style='background:#f0fdf4; border:1.5px dashed #86efac;
                        border-radius:12px; padding:18px; text-align:center; color:#15803d;'>
                <div style='font-size:2rem;'>📷</div>
                <div style='font-size:0.88rem; font-weight:600; margin-top:4px;'>
                    Upload a photo to auto-fill
                </div>
                <div style='font-size:0.75rem; color:#64748b; margin-top:4px;'>
                    Detects item type, capabilities &amp; condition
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# ─── Run scan when a new photo is uploaded ────────────────────────────────────
if uploaded_photo and uploaded_photo.name != st.session_state.get("scan_image_name"):
    with st.spinner("🔍 Scanning image with Gemini AI Vision…"):
        result = scan_image_for_autofill(uploaded_photo)
        st.session_state["scan_result"]     = result
        st.session_state["scan_image_name"] = uploaded_photo.name
        if result.get("suggested_name"):
            st.session_state["new_item_title"] = result["suggested_name"]
        if result.get("suggested_capabilities"):
            st.session_state["item_caps_input"] = ", ".join(result["suggested_capabilities"])
        if result.get("condition_note"):
            st.session_state["item_desc_input"] = result["condition_note"]
    st.rerun()

# ─── Resolve auto-fill defaults ───────────────────────────────────────────────
sr = st.session_state.get("scan_result") or {}

# If user typed a title and there's no scan, use text-based suggestions
def _text_suggestions(title: str):
    if title:
        return suggest_capabilities_for_item(title)
    return {"suggested_category": "", "suggested_capabilities": [], "suggested_tags": []}

# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("### 📝 Step 2 — Review & Complete Details")

col_form, col_preview = st.columns([1.3, 1.0])

with col_form:
    # 1. Title
    prefill_name = st.session_state.get("new_item_title", sr.get("suggested_name", ""))
    item_title = st.text_input(
        "Resource Name / Model:",
        value=prefill_name,
        placeholder="e.g. Raspberry Pi 4, HDMI Cable, Casio fx-991EX…",
        key="new_item_title"
    )

    # Text-based suggestions only kick in if NO scan result yet
    text_sugg = _text_suggestions(item_title) if not sr else {}

    # 2. Category
    suggested_cat = sr.get("suggested_category") or text_sugg.get("suggested_category", "")
    cat_default_idx = 0
    for idx, cname in enumerate(cat_names):
        if suggested_cat.lower() in cname.lower() or cname.lower() in suggested_cat.lower():
            cat_default_idx = idx
            break
    selected_cat_name = st.selectbox("Category:", cat_names, index=cat_default_idx)
    selected_cat_id   = categories_map.get(selected_cat_name, 1)

    # 3. Description
    item_desc = st.text_area(
        "Description & Specs:",
        value=st.session_state.get("item_desc_input", ""),
        placeholder="e.g. Works perfectly, includes original power cable, pre-tested in lab practicals…",
        height=90,
        key="item_desc_input"
    )

    # 4. Condition & Quantity
    col_cond, col_qty = st.columns(2)
    with col_cond:
        detected_cond = sr.get("suggested_condition", "Good")
        cond_options  = ["Good", "New", "Fair"]
        cond_idx      = cond_options.index(detected_cond) if detected_cond in cond_options else 0

        # Show badge if auto-detected
        if sr.get("suggested_condition"):
            st.markdown(
                f"<div style='font-size:0.72rem; color:#15803d; font-weight:700; margin-bottom:2px;'>"
                f"🤖 Auto-detected from photo</div>",
                unsafe_allow_html=True
            )
        condition = st.selectbox("Condition:", cond_options, index=cond_idx)

    with col_qty:
        quantity = st.number_input("Quantity Available:", min_value=1, max_value=20, value=1)

    # 5. Location (always blank, user must fill)
    location = st.text_input(
        "Campus Location / Pickup Spot:",
        value="",
        placeholder="e.g. ECE Hostel Block B Room 214 or CSE Lab Bench 3"
    )

    # 6. Available for / until
    col_avail_for, col_until = st.columns(2)
    with col_avail_for:
        available_for = st.selectbox("Available For:", ["borrow", "donate", "both"])
    with col_until:
        until_date = st.date_input("Available Until (Optional):", value=None)

    # 7. Capabilities
    st.markdown("##### ⚙️ Functional Capabilities (for AI & Semantic Search):")
    st.caption("Comma-separated attributes auto-detected from your photo — edit freely.")

    suggested_caps = sr.get("suggested_capabilities") or text_sugg.get("suggested_capabilities", [])
    caps_val = st.session_state.get("item_caps_input", ", ".join(suggested_caps) if suggested_caps else "")
    caps_str = st.text_input(
        "Capabilities:",
        value=caps_val,
        placeholder="e.g. wifi, hdmi, microcontroller, voltage measurement",
        key="item_caps_input"
    )

    # ─── PUBLISH ──────────────────────────────────────────────────────────────
    st.markdown("")
    if st.button("🚀 Publish Resource to Campus", type="primary", use_container_width=True):
        if not item_title.strip():
            st.error("Please enter an item name before publishing.")
        elif not location.strip():
            st.error("Please enter a campus location / pickup spot.")
        else:
            caps_list = [c.strip() for c in caps_str.split(",") if c.strip()]

            # Save image if one was uploaded
            saved_path = None
            if uploaded_photo:
                uploaded_photo.seek(0)
                saved_path = save_item_image(uploaded_photo, item_title.strip())

            new_id = add_resource(
                owner_id      = user["id"],
                name          = item_title.strip(),
                category_id   = selected_cat_id,
                description   = item_desc.strip(),
                condition     = condition,
                location      = location.strip(),
                quantity      = quantity,
                available_for = available_for,
                available_until = str(until_date) if until_date else None,
                capabilities  = caps_list,
                image_path    = saved_path
            )

            # Flag form to reset on next entry
            st.session_state["reset_have_form"] = True

            st.session_state["flash"] = (
                "success",
                f"✅ '{item_title}' published! Campus peers can now discover and borrow it."
            )
            st.switch_page("pages/5_My_Resources.py")

# ─── LIVE PREVIEW PANEL ───────────────────────────────────────────────────────
with col_preview:
    st.markdown("### 🔍 Live Listing Preview")

    # Show uploaded photo preview
    if uploaded_photo:
        uploaded_photo.seek(0)
        st.image(uploaded_photo, caption="Uploaded item photo", use_container_width=True)

    st.markdown(
        f"""
        <div style='background:#f0fdf4; border:1.5px solid #86efac;
                    border-radius:14px; padding:1.4rem; margin-top:12px;'>
            <div style='font-size:0.75rem; font-weight:700; color:#15803d;
                        text-transform:uppercase; margin-bottom:4px;'>
                LISTING PREVIEW
            </div>
            <h3 style='color:#14532d; margin:6px 0;'>
                {item_title or "<i style='color:#94a3b8;'>Item name will appear here</i>"}
            </h3>
            <div style='font-size:0.85rem; color:#475569; margin-bottom:10px;'>
                <b>Category:</b> {selected_cat_name} &nbsp;|&nbsp;
                <b>Condition:</b> {condition}
            </div>
            <div style='font-size:0.85rem; color:#334155; margin-bottom:8px;'>
                <b>Detected Capabilities:</b>
            </div>
            <div>
                {
                    ' '.join([
                        f"<span class='circulo-chip' style='background:#dcfce7;color:#14532d;'>✓ {c.strip()}</span>"
                        for c in caps_str.split(',') if c.strip()
                    ]) or '<i style="color:#94a3b8; font-size:0.85rem;">Upload photo or type an item name to detect capabilities</i>'
                }
            </div>
            <hr style='border:none; border-top:1px solid #bbf7d0; margin:14px 0;'>
            <div style='font-size:0.8rem; color:#475569;'>
                🛡️ <b>Note:</b> Capabilities determine if your item appears in peer searches.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
