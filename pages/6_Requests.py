"""CIRCULO - Requests & Borrow Lifecycle Management
Handles Request -> Approval -> Handover -> Return workflow with atomic database consistency.
"""
import streamlit as st
from ui.components import render_header, render_hero
from services.transaction_service import (
    get_incoming_requests,
    get_user_requests,
    get_active_loans,
    approve_request,
    reject_request,
    confirm_handover,
    mark_returned
)

st.set_page_config(page_title="CIRCULO - Requests & Loans", page_icon="🤝", layout="wide")

if not st.session_state.get("user"):
    st.warning("Please sign in from the main portal first.")
    if st.button("Go to Login"):
        st.switch_page("app.py")
    st.stop()

render_header()
user = st.session_state["user"]

render_hero(
    title="Borrow Requests & Loan Lifecycle",
    subtitle="Manage incoming requests for your equipment, track items you've requested, confirm physical handovers, and complete returns."
)

tab_in, tab_my, tab_loans = st.tabs([
    "📥 Incoming Requests (For My Items)",
    "📤 My Submitted Requests",
    "🤝 Active Loans (Handover & Returns)"
])

# 1. TAB: Incoming Requests
with tab_in:
    incoming = get_incoming_requests(user["id"])
    if not incoming:
        st.info("No pending requests for your equipment right now.")
    else:
        st.markdown(f"**Pending Requests ({len(incoming)}):**")
        for req in incoming:
            with st.container():
                st.markdown(
                    f"""
                    <div style='background:#ffffff; border:1.5px solid #bbf7d0; border-radius:12px; padding:1.2rem; margin-bottom:1rem;'>
                        <div style='display:flex; justify-content:space-between;'>
                            <h4 style='margin:0; color:#14532d;'>Item: {req['item_name']}</h4>
                            <span style='background:#fef3c7; color:#b45309; padding:2px 8px; border-radius:8px; font-weight:700; font-size:0.75rem;'>
                                PENDING APPROVAL
                            </span>
                        </div>
                        <div style='font-size:0.85rem; color:#475569; margin:6px 0;'>
                            Requester: <b>{req['borrower_name']}</b> ({req['borrower_department']}) &nbsp;|&nbsp; 
                            Email: {req['borrower_email']}
                        </div>
                        <div style='font-size:0.85rem; color:#334155; margin-bottom:8px;'>
                            <b>Note:</b> {req['notes'] or 'No specific note provided'}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                col_app, col_rej = st.columns([1, 4])
                with col_app:
                    if st.button("✅ Approve Request", key=f"app_{req['request_id']}", type="primary"):
                        success = approve_request(req["request_id"], user["id"])
                        if success:
                            st.success("Request approved! Item is now RESERVED for handover.")
                            st.rerun()
                        else:
                            st.error("Failed to approve: item may already be reserved.")
                with col_rej:
                    if st.button("❌ Reject", key=f"rej_{req['request_id']}", type="secondary"):
                        reject_request(req["request_id"], user["id"])
                        st.info("Request rejected.")
                        st.rerun()

# 2. TAB: My Submitted Requests
with tab_my:
    my_requests = get_user_requests(user["id"])
    if not my_requests:
        st.info("You haven't submitted any borrow requests yet.")
    else:
        for r in my_requests:
            badge_color = "#dcfce7" if r["status"] == "APPROVED" else ("#fee2e2" if r["status"] == "REJECTED" else "#fef3c7")
            text_color = "#166534" if r["status"] == "APPROVED" else ("#991b1b" if r["status"] == "REJECTED" else "#854d0e")
            
            st.markdown(
                f"""
                <div style='background:#ffffff; border:1px solid #e2e8f0; border-radius:12px; padding:1.2rem; margin-bottom:1rem;'>
                    <div style='display:flex; justify-content:space-between;'>
                        <h4 style='margin:0; color:#0f172a;'>{r['item_name']}</h4>
                        <span style='background:{badge_color}; color:{text_color}; font-weight:700; padding:3px 10px; border-radius:8px; font-size:0.75rem;'>
                            {r['status']}
                        </span>
                    </div>
                    <div style='font-size:0.85rem; color:#64748b; margin-top:6px;'>
                        Owner: <b>{r['owner_name']}</b> ({r['owner_department']}) &nbsp;|&nbsp; Location: {r['location']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

# 3. TAB: Active Loans
with tab_loans:
    loans = get_active_loans(user["id"])
    if not loans:
        st.info("No active loan transactions involving your account.")
    else:
        for loan in loans:
            is_lender = (loan["lender_id"] == user["id"])
            role_label = "LENDER (You are providing the item)" if is_lender else "BORROWER (You are using the item)"
            
            with st.container():
                st.markdown(
                    f"""
                    <div style='background:#ffffff; border:1.5px solid #86efac; border-radius:12px; padding:1.2rem; margin-bottom:1rem;'>
                        <div style='display:flex; justify-content:space-between;'>
                            <h4 style='margin:0; color:#14532d;'>{loan['item_name']}</h4>
                            <span style='background:#dcfce7; color:#14532d; font-weight:700; padding:3px 10px; border-radius:8px; font-size:0.8rem;'>
                                LOAN STATUS: {loan['status']}
                            </span>
                        </div>
                        <div style='font-size:0.85rem; color:#475569; margin:6px 0;'>
                            <b>Your Role:</b> {role_label}  
                            <br>
                            Lender: <b>{loan['lender_name']}</b> &nbsp;|&nbsp; Borrower: <b>{loan['borrower_name']}</b> &nbsp;|&nbsp; Pickup: {loan['location']}
                        </div>
                        <div style='font-size:0.85rem; color:#166534;'>
                            Loan Due Date: <b>{loan['due_date']}</b>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
                col_action1, col_action2 = st.columns([1.5, 3])
                with col_action1:
                    # If RESERVED, confirm physical handover
                    if loan["status"] == "RESERVED":
                        if st.button("🤝 Confirm Physical Handover", key=f"hand_{loan['transaction_id']}", type="primary"):
                            confirm_handover(loan["transaction_id"], user["id"])
                            st.success("Handover confirmed! Status updated to BORROWED.")
                            st.rerun()
                            
                    # If BORROWED, confirm return
                    elif loan["status"] in ("BORROWED", "OVERDUE"):
                        if st.button("🔄 Mark Item Returned", key=f"ret_{loan['transaction_id']}", type="primary"):
                            mark_returned(loan["transaction_id"], user["id"])
                            st.success("Return confirmed! Equipment restored to inventory and impact logged.")
                            st.rerun()
