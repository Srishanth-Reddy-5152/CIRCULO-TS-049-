"""CIRCULO - My Resources
Resource Management, Status Toggles, and Personal Resource Rescue
"""
import streamlit as st
from ui.components import render_header, render_hero
from services.resource_service import get_items_by_owner, update_item_availability
from services.rescue_service import get_idle_items_for_owner, handle_rescue_action
from services.transaction_service import get_active_loans, mark_returned

st.set_page_config(page_title="CIRCULO - My Resources", page_icon="📋", layout="wide")

if not st.session_state.get("user"):
    st.warning("Please sign in from the main portal first.")
    if st.button("Go to Login"):
        st.switch_page("app.py")
    st.stop()

render_header()
user = st.session_state["user"]

render_hero(
    title="Manage Your Resources & Idle Assets",
    subtitle="Monitor items you've shared on campus, manage availability, review loans, and respond to Resource Rescue recommendations."
)

tab_listed, tab_rescue, tab_borrowed = st.tabs([
    "📦 Listed by Me",
    "⏳ Resource Rescue (Idle Items)",
    "🔄 Borrowed by Me"
])

# 1. TAB: Listed by Me
with tab_listed:
    my_items = get_items_by_owner(user["id"])
    if not my_items:
        st.info("You haven't listed any resources yet.")
        if st.button("➕ List Your First Resource"):
            st.switch_page("pages/4_I_Have.py")
    else:
        st.markdown(f"**Total Listings: {len(my_items)}**")
        for item in my_items:
            with st.container():
                st.markdown(
                    f"""
                    <div style='background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; padding:1.2rem; margin-bottom:0.8rem;'>
                        <div style='display:flex; justify-content:space-between;'>
                            <h4 style='margin:0; color:#14532d;'>{item['name']}</h4>
                            <span style='background:#f1f5f9; padding:2px 8px; border-radius:8px; font-weight:700; font-size:0.75rem;'>
                                Status: {item['availability']}
                            </span>
                        </div>
                        <div style='font-size:0.85rem; color:#64748b; margin:6px 0;'>
                            Category: {item.get('category_name', 'General')} &nbsp;|&nbsp; 
                            Available: {item['quantity_available']}/{item['quantity']} &nbsp;|&nbsp; 
                            Idle: {item.get('idle_days', 0)} days
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                col_btn1, col_btn2 = st.columns([1, 4])
                with col_btn1:
                    if item["availability"] == "AVAILABLE":
                        if st.button("Pause / Withdraw", key=f"withdraw_{item['id']}"):
                            update_item_availability(item["id"], "UNAVAILABLE")
                            st.rerun()
                    else:
                        if st.button("Make Available", key=f"avail_{item['id']}"):
                            update_item_availability(item["id"], "AVAILABLE")
                            st.rerun()

# 2. TAB: Resource Rescue (Idle Items)
with tab_rescue:
    st.markdown("### ⏳ Resource Rescue: Idle Asset Alert")
    st.caption("Items that haven't been used in over 30 days. Don't let functional hardware gather dust!")
    
    idle_items = get_idle_items_for_owner(user["id"], threshold_days=30)
    if not idle_items:
        st.success("🎉 Excellent! None of your listed assets are currently idle (>30 days).")
    else:
        for item in idle_items:
            with st.container():
                st.markdown(
                    f"""
                    <div class="rescue-card">
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <h4 style='color:#92400e; margin:0;'>⚠️ {item['name']}</h4>
                            <span style='background:#fef3c7; color:#b45309; font-weight:700; padding:3px 8px; border-radius:8px; font-size:0.8rem;'>
                                Idle for {item['idle_days']} days
                            </span>
                        </div>
                        <p style='color:#78350f; font-size:0.88rem; margin:8px 0;'>
                            This item has not circulated recently. Choose an action to keep it active or recirculate it on campus.
                        </p>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                b1, b2, b3, b4 = st.columns(4)
                with b1:
                    if st.button("✅ Keep (In Active Use)", key=f"r_keep_{item['id']}", use_container_width=True):
                        handle_rescue_action(item["id"], user["id"], "keep")
                        st.success("Refreshed active use date!")
                        st.rerun()
                with b2:
                    if st.button("♻️ Make Available to Campus", key=f"r_avail_{item['id']}", use_container_width=True):
                        handle_rescue_action(item["id"], user["id"], "make_available")
                        st.success("Item recirculated for borrowing!")
                        st.rerun()
                with b3:
                    if st.button("🎁 Mark for Donation", key=f"r_don_{item['id']}", use_container_width=True):
                        handle_rescue_action(item["id"], user["id"], "donate")
                        st.success("Item marked for campus donation!")
                        st.rerun()
                with b4:
                    if st.button("📦 Retire / Archive", key=f"r_ret_{item['id']}", use_container_width=True):
                        handle_rescue_action(item["id"], user["id"], "retire")
                        st.info("Item archived from active catalog.")
                        st.rerun()

# 3. TAB: Borrowed by Me
with tab_borrowed:
    my_loans = [l for l in get_active_loans(user["id"]) if l["borrower_id"] == user["id"]]
    if not my_loans:
        st.info("You do not currently have any active borrowed items.")
    else:
        for loan in my_loans:
            st.markdown(
                f"""
                <div style='background:#ffffff; border:1px solid #cbd5e1; border-radius:12px; padding:1.2rem; margin-bottom:1rem;'>
                    <h4 style='color:#0f172a; margin:0;'>{loan['item_name']}</h4>
                    <div style='font-size:0.85rem; color:#475569; margin:6px 0;'>
                        Lender: <b>{loan['lender_name']}</b> ({loan['lender_department']}) &nbsp;|&nbsp; 
                        Location: {loan['location']}
                    </div>
                    <div style='font-size:0.82rem; color:#166534;'>
                        Due Date: <b>{loan['due_date']}</b> (Status: {loan['status']})
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            if st.button("Mark Item Returned", key=f"ret_b_{loan['transaction_id']}"):
                success = mark_returned(loan["transaction_id"], user["id"])
                if success:
                    st.success("Loan completed! Verified impact event recorded.")
                    st.rerun()
