# pages/3_🏠_User_Dashboard.py - SECURITY FIXED VERSION
import streamlit as st
import json
from datetime import datetime

from utils.session_utils import initialize_session_state
initialize_session_state()

st.title("🏠 Banking Dashboard")

def load_user_data():
    try:
        with open('data/users.json', 'r') as f:
            users = json.load(f)
        return users.get(st.session_state.current_user, {})
    except:
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

# Safe authentication check
if not st.session_state.get('user_authenticated', False):
    st.warning("Please login to access dashboard")
    st.page_link("pages/1_👤_User_Login.py", label="Go to Login", icon="🔐")
    st.stop()

user_data = load_user_data()
transactions = load_user_transactions()
pending_approvals = load_pending_approvals()

# User notifications - GENERIC MESSAGES ONLY
user_pending = [p for p in pending_approvals if p.get('user_id') == st.session_state.current_user and p.get('status') == 'pending']

if user_pending:
    st.subheader("📢 Account Notifications")
    for pending in user_pending[:3]:  # Show max 3 notifications
        # 🚨 SECURITY FIX: Generic messages only, no risk details
        amount = pending.get('transaction_data', {}).get('amount', 0)
        merchant = pending.get('transaction_data', {}).get('merchant_name', 'Unknown')
        
        st.info(f"""
        **Transaction Processing**
        - Amount: ${amount:,.2f}
        - Merchant: {merchant}
        - Status: Being verified
        - *Standard security procedure*
        """)

# Account summary - SAFE INFORMATION ONLY
st.subheader("💰 Account Summary")

col1, col2, col3 = st.columns(3)
col1.metric("Current Balance", f"${user_data.get('balance', 0):,.2f}")
col2.metric("Transactions in Progress", len(user_pending))
col3.metric("Completed Transactions", len([t for t in transactions if t.get('status') == 'approved']))

# Security status (generic, non-technical)
st.subheader("🛡️ Account Security")
col1, col2, col3 = st.columns(3)

with col1:
    st.success("**Protection Status**")
    st.write("✅ Active")

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

# Recent transactions - USER-FRIENDLY DISPLAY ONLY
st.subheader("📋 Recent Activity")

if not transactions:
    st.info("No recent transactions. Make your first payment!")
    st.page_link("pages/4_💳_Make_Transaction.py", label="Make a Payment", icon="💳")
else:
    # Show last 5 transactions with safe status display
    for tx in list(reversed(transactions))[:5]:
        status = tx.get('status', 'pending')
        
        # 🚨 SECURITY FIX: User-friendly statuses only
        if status == 'approved':
            status_color = "green"
            status_emoji = "✅"
            status_text = "Completed"
        elif status == 'rejected':
            status_color = "red"
            status_emoji = "❌"
            status_text = "Declined"
        elif status == 'fraud':
            status_color = "red"
            status_emoji = "🚫"
            status_text = "Security Hold"  # Generic term
        elif status == 'under_review':
            status_color = "orange"
            status_emoji = "🔄"
            status_text = "Verifying"
        else:
            status_color = "gray"
            status_emoji = "⏳"
            status_text = "Processing"
        
        # Display safe transaction info
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.write(f"**${tx.get('amount', 0):,.2f}** - {tx.get('merchant_name', 'Unknown')}")
            st.write(f"*{tx.get('description', 'No description')}*")
        
        with col2:
            st.write(f"{status_emoji} **{status_text}**")
        
        with col3:
            st.write(f"_{tx.get('submitted_at', '')[:16]}_")
        
        st.divider()

# Spending insights - SAFE ANALYTICS ONLY
if len(transactions) >= 3:
    st.subheader("📈 Spending Overview")
    
    approved_transactions = [t for t in transactions if t.get('status') == 'approved']
    if approved_transactions:
        total_spent = sum(t['amount'] for t in approved_transactions)
        avg_transaction = total_spent / len(approved_transactions) if approved_transactions else 0
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Spending", f"${total_spent:,.2f}")
        with col2:
            st.metric("Average Payment", f"${avg_transaction:,.0f}")
        
        # Safe category breakdown (no sensitive patterns)
        categories = {}
        for tx in approved_transactions:
            cat = tx.get('category', 'other')
            categories[cat] = categories.get(cat, 0) + tx['amount']
        
        if categories:
            st.write("**Spending by Category:**")
            for category, amount in list(categories.items())[:4]:  # Top 4 only
                st.write(f"• {category.replace('_', ' ').title()}: ${amount:,.0f}")

# Security tips (generic, helpful)
st.subheader("💡 Security Tips")
col1, col2 = st.columns(2)

with col1:
    st.info("""
    **Protect Your Account:**
    - Never share your password
    - Log out after each session
    - Monitor your transactions regularly
    - Report suspicious activity immediately
    """)

with col2:
    st.info("""
    **Safe Banking:**
    - Use secure networks
    - Keep contact info updated
    - Enable transaction alerts
    - Verify merchant details
    """)

# Customer support information
st.subheader("📞 Need Help?")
st.write("""
Our customer support team is available 24/7 to assist you with:

• Transaction questions
• Account security
• Payment issues
• General inquiries

**Contact Support:** 1-800-SECURE-BANK
**Email:** support@securebank.com
""")

# Footer with last login (generic)
st.divider()
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | SecureBank™")

# Sidebar with safe information only
st.sidebar.header("👤 Account Overview")
st.sidebar.write(f"**Welcome,** {user_data.get('full_name', 'User')}!")

st.sidebar.write("**Account Details:**")
st.sidebar.write(f"• Member since: {user_data.get('account_created', 'Recent')[:10]}")
st.sidebar.write(f"• Account type: Premium")
st.sidebar.write(f"• Security level: Maximum")

st.sidebar.header("🔒 Security Status")
st.sidebar.success("""
✅ All systems secure
✅ Identity verified  
✅ Monitoring active
✅ Protection enabled
""")

st.sidebar.header("📊 Quick Stats")
if transactions:
    completed = len([t for t in transactions if t.get('status') == 'approved'])
    in_progress = len([t for t in transactions if t.get('status') in ['under_review', 'pending']])
    
    st.sidebar.write(f"• Completed: {completed}")
    st.sidebar.write(f"• In progress: {in_progress}")
    st.sidebar.write(f"• Total: {len(transactions)}")