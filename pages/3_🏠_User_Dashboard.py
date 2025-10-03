# pages/3_🏠_User_Dashboard.py - UPDATED WITH SAFER TERMINOLOGY
import streamlit as st
import json
from datetime import datetime

from utils.session_utils import initialize_session_state
initialize_session_state()

st.title("🏠 Banking Dashboard")

def load_user_data():
    """Load fresh user data every time"""
    try:
        with open('data/users.json', 'r') as f:
            users = json.load(f)
        return users.get(st.session_state.current_user, {})
    except Exception as e:
        st.error(f"Error loading user data: {e}")
        return {}

def load_user_transactions():
    try:
        with open('data/transactions.json', 'r') as f:
            transactions = json.load(f)
        return transactions.get(st.session_state.current_user, [])
    except:
        return []

def load_pending_approvals():
    try:
        with open('data/pending_approvals.json', 'r') as f:
            return json.load(f)
    except:
        return []

def get_credit_utilization(user_data):
    """Calculate credit utilization percentage"""
    total_limit = user_data.get('total_credit_limit', 0)
    available_credit = user_data.get('total_available_credit', 0)
    
    if total_limit <= 0:
        return 0, 0, 0
    
    used_credit = total_limit - available_credit
    utilization = (used_credit / total_limit) * 100
    
    return utilization, used_credit, total_limit

# Safe authentication check
if not st.session_state.get('user_authenticated', False):
    st.warning("Please login to access dashboard")
    st.page_link("pages/1_👤_User_Login.py", label="Go to Login", icon="🔐")
    st.stop()

# Load fresh data every time
user_data = load_user_data()
transactions = load_user_transactions()
pending_approvals = load_pending_approvals()

# Debug info in sidebar
st.sidebar.write("🔍 Current Data")
st.sidebar.write(f"Available Credit: ${user_data.get('total_available_credit', 0):,.2f}")
st.sidebar.write(f"Credit Limit: ${user_data.get('total_credit_limit', 0):,.2f}")

# User notifications
user_pending = [p for p in pending_approvals if p.get('user_id') == st.session_state.current_user and p.get('status') == 'pending']

if user_pending:
    st.subheader("📢 Account Notifications")
    for pending in user_pending[:3]:
        amount = pending.get('transaction_data', {}).get('amount', 0)
        merchant = pending.get('transaction_data', {}).get('merchant_name', 'Unknown')
        
        st.info(f"""
        **Transaction Processing**
        - Amount: ${amount:,.2f}
        - Merchant: {merchant}
        - Status: Being verified
        - *Standard security procedure*
        """)

# Account summary - ALWAYS FRESH DATA
st.subheader("💰 Account Summary")

utilization, used_credit, total_limit = get_credit_utilization(user_data)
available_credit = user_data.get('total_available_credit', 0)
approved_transactions = [t for t in transactions if t.get('status') == 'approved']
security_review_count = len([t for t in transactions if t.get('status') == 'fraud'])  # Updated count

col1, col2, col3, col4 = st.columns(4)
col1.metric("Credit Limit", f"${total_limit:,.2f}")
col2.metric("Available Credit", f"${available_credit:,.2f}")
col3.metric("Credit Used", f"${used_credit:,.2f}")
col4.metric("Completed Transactions", len(approved_transactions))

# Credit utilization with dynamic warnings
st.subheader("💳 Credit Utilization")

if total_limit > 0:
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.write(f"**Utilization Rate:** {utilization:.1f}%")
        
        # Dynamic progress bar with color coding
        progress_value = utilization / 100
        
        if utilization < 30:
            st.progress(progress_value)
            st.success("✅ Excellent credit utilization")
        elif utilization < 50:
            st.progress(progress_value)
            st.info("ℹ️ Good credit utilization")
        elif utilization < 80:
            st.progress(progress_value)
            st.warning("⚠️ Moderate credit utilization")
        else:
            st.progress(progress_value)
            st.error("🚨 High credit utilization - consider paying down balance")
    
    with col2:
        if utilization > 80:
            st.error("Consider payment")
        elif utilization > 50:
            st.warning("Monitor spending")

# Security status
st.subheader("🛡️ Account Security")
col1, col2, col3 = st.columns(3)

security_status = user_data.get('account_status', 'active')
with col1:
    if security_status == 'active':
        st.success("**Account Status**")
        st.write("✅ Active")
    else:
        st.error("**Account Status**")
        st.write("❌ Restricted")

with col2:
    st.success("**Verification**")
    st.write("✅ Complete")

with col3:
    st.success("**Monitoring**")
    st.write("✅ 24/7 Active")

# Quick actions
st.subheader("🚀 Quick Actions")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.page_link("pages/4_💳_Make_Transaction.py", label="New Payment", icon="💳")

with col2:
    st.page_link("pages/5_📊_My_Transactions.py", label="View History", icon="📊")

with col3:
    if st.button("🔄 Refresh", use_container_width=True):
        st.rerun()

with col4:
    if st.button("🚪 Logout", use_container_width=True):
        st.session_state.user_authenticated = False
        st.session_state.current_user = None
        st.session_state.user_data = {}
        st.rerun()

# Recent transactions
st.subheader("📋 Recent Activity")

if not transactions:
    st.info("No recent transactions. Make your first payment!")
    st.page_link("pages/4_💳_Make_Transaction.py", label="Make a Payment", icon="💳")
else:
    for tx in list(reversed(transactions))[:5]:
        status = tx.get('status', 'pending')
        
        # UPDATED STATUS DISPLAY - SAFER TERMINOLOGY
        if status == 'approved':
            status_emoji = "✅"
            status_text = "Completed"
        elif status == 'rejected':
            status_emoji = "❌"
            status_text = "Declined"
        elif status == 'fraud':
            status_emoji = "🔒"  # Changed from 🚫
            status_text = "Under Review"  # Changed from "Security Hold"
        elif status == 'under_review':
            status_emoji = "🔄"
            status_text = "Processing"
        else:
            status_emoji = "⏳"
            status_text = "Processing"
        
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"**${tx.get('amount', 0):,.2f}** - {tx.get('merchant_name', 'Unknown')}")
            st.write(f"*{tx.get('description', 'No description')}*")
        
        with col2:
            st.write(f"{status_emoji} **{status_text}**")
        
        with col3:
            st.write(f"_{tx.get('submitted_at', '')[:16]}_")
        
        st.divider()

# Spending insights - DYNAMIC CALCULATIONS
if len(approved_transactions) >= 1:
    st.subheader("📈 Spending Overview")
    
    total_spent = sum(t['amount'] for t in approved_transactions)
    avg_transaction = total_spent / len(approved_transactions) if approved_transactions else 0
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Spending", f"${total_spent:,.2f}")
    with col2:
        st.metric("Average Payment", f"${avg_transaction:,.0f}")
    
    # Dynamic category breakdown
    categories = {}
    for tx in approved_transactions:
        cat = tx.get('category', 'other')
        categories[cat] = categories.get(cat, 0) + tx['amount']
    
    if categories:
        st.write("**Spending by Category:**")
        for category, amount in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:4]:
            st.write(f"• {category.replace('_', ' ').title()}: ${amount:,.0f}")

# Security notifications (if any transactions under review)
security_review_txs = [t for t in transactions if t.get('status') == 'fraud']
if security_review_txs:
    st.subheader("🔒 Transactions Under Review")
    st.info("""
    Some of your transactions are undergoing additional verification. 
    This is a standard security procedure to protect your account.
    
    **What to expect:**
    - Routine security checks
    - Possible contact for verification
    - Temporary processing delays
    - Enhanced account protection
    """)

# Payment reminder based on actual balance
current_balance = user_data.get('total_current_balance', 0)
if current_balance > 0:
    st.subheader("💰 Payment Reminder")
    
    min_payment = max(current_balance * 0.03, 25.00)  # 3% or $25, whichever is higher
    due_date = user_data.get('credit_cards', {}).get('primary', {}).get('payment_due_date', '15th of next month')
    
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Current Balance:** ${current_balance:,.2f}")
        st.write(f"**Minimum Payment:** ${min_payment:,.2f}")
    with col2:
        st.write(f"**Due Date:** {due_date}")
        st.write(f"**Credit Available:** ${available_credit:,.2f}")
    
    if utilization > 50:
        st.warning("💡 Paying more than the minimum can help improve your credit utilization ratio.")

# Help section with updated terminology
st.sidebar.header("ℹ️ Account Information")
st.sidebar.write("""
**Transaction Statuses:**
- ✅ **Completed:** Successfully processed
- 🔄 **Processing:** Being verified
- ❌ **Declined:** Could not be completed  
- 🔒 **Under Review:** Additional verification

**Security Features:**
- All transactions are monitored
- Selected transactions undergo additional checks
- This protects your account from unauthorized use
- Contact support with any questions
""")

# Footer
st.divider()
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | SecureBank™")