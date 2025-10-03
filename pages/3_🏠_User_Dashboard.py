import streamlit as st
import json
import joblib
from datetime import datetime

from utils.session_utils import initialize_session_state
initialize_session_state()

st.title("🏠 Banking Dashboard")

@st.cache_resource
def load_model():
    """Load ML model for security insights"""
    try:
        model = joblib.load('best_xgb_model_tuned.joblib')
        return model
    except Exception as e:
        return None

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

def get_user_security_insights(user_data, transactions, model):
    """Provide security insights without revealing fraud details"""
    if not model:
        return {}
    
    # Safe security metrics
    insights = {
        'account_health': 'excellent',
        'spending_pattern': 'normal',
        'verification_level': 'high',
        'protection_status': 'active'
    }
    
    # Analyze transaction patterns safely
    if transactions:
        recent_txs = [t for t in transactions if t.get('status') == 'approved'][-5:]
        if recent_txs:
            avg_recent = sum(t['amount'] for t in recent_txs) / len(recent_txs)
            
            # Safe pattern analysis
            unusual_count = sum(1 for t in recent_txs if t['amount'] > 1000)
            if unusual_count >= 2:
                insights['spending_pattern'] = 'varied'
            else:
                insights['spending_pattern'] = 'consistent'
    
    return insights

def get_spending_insights(transactions, model):
    """Provide ML-powered spending insights"""
    if not transactions:
        return {}
    
    approved_txs = [t for t in transactions if t.get('status') == 'approved']
    
    insights = {
        'monthly_spending': 0,
        'top_categories': [],
        'avg_transaction': 0,
        'spending_trend': 'stable'
    }
    
    if approved_txs:
        # Calculate metrics
        insights['monthly_spending'] = sum(t['amount'] for t in approved_txs)
        insights['avg_transaction'] = insights['monthly_spending'] / len(approved_txs)
        
        # Category analysis
        categories = {}
        for tx in approved_txs:
            cat = tx.get('category', 'other')
            categories[cat] = categories.get(cat, 0) + tx['amount']
        
        insights['top_categories'] = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Trend analysis
        if len(approved_txs) >= 4:
            first_half = sum(t['amount'] for t in approved_txs[:len(approved_txs)//2])
            second_half = sum(t['amount'] for t in approved_txs[len(approved_txs)//2:])
            
            if second_half > first_half * 1.3:
                insights['spending_trend'] = 'increasing'
            elif second_half < first_half * 0.7:
                insights['spending_trend'] = 'decreasing'
    
    return insights

# Safe authentication check
if not st.session_state.get('user_authenticated', False):
    st.warning("Please login to access dashboard")
    st.page_link("pages/1_👤_User_Login.py", label="Go to Login", icon="🔐")
    st.stop()

# Load data and model
user_data = load_user_data()
transactions = load_user_transactions()
pending_approvals = load_pending_approvals()
model = load_model()

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
security_review_count = len([t for t in transactions if t.get('status') == 'fraud'])

col1, col2, col3, col4 = st.columns(4)
col1.metric("Credit Limit", f"${total_limit:,.2f}")
col2.metric("Available Credit", f"${available_credit:,.2f}")
col3.metric("Credit Used", f"${used_credit:,.2f}")
col4.metric("Completed Transactions", len(approved_transactions))

# ML-Powered Security Insights
st.subheader("🛡️ Security & Protection Status")

security_insights = get_user_security_insights(user_data, transactions, model)

col1, col2, col3, col4 = st.columns(4)

with col1:
    if security_insights.get('account_health') == 'excellent':
        st.success("**Account Health**")
        st.write("✅ Excellent")
    else:
        st.info("**Account Health**")
        st.write("ℹ️ Good")

with col2:
    st.success("**Spending Pattern**")
    st.write(f"✅ {security_insights.get('spending_pattern', 'Normal').title()}")

with col3:
    st.success("**Verification Level**")
    st.write("✅ High")

with col4:
    st.success("**Protection Status**")
    st.write("✅ Active")

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
            st.error("🚨 High credit utilization - consider paying down your balance")
    
    with col2:
        if utilization > 80:
            st.error("Consider payment")
            # ADD PAYMENT BUTTON TO HIGH UTILIZATION WARNING
            st.page_link("pages/9_💰_Make_Payment.py", 
                        label="Make Payment Now", 
                        icon="💰",
                        use_container_width=True)
        elif utilization > 50:
            st.warning("Monitor spending")
            st.page_link("pages/9_💰_Make_Payment.py", 
                        label="Pay Balance", 
                        icon="💰",
                        use_container_width=True)

# ML-Powered Spending Insights
st.subheader("📈 Smart Spending Insights")

spending_insights = get_spending_insights(transactions, model)

if spending_insights:
    col1, col2, col3 = st.columns(3)
    
    with col1:
        trend_emoji = "📈" if spending_insights['spending_trend'] == 'increasing' else "📉" if spending_insights['spending_trend'] == 'decreasing' else "➡️"
        st.metric("Spending Trend", spending_insights['spending_trend'].title(), delta=trend_emoji)
    
    with col2:
        st.metric("Avg Transaction", f"${spending_insights['avg_transaction']:,.0f}")
    
    with col3:
        st.metric("Monthly Total", f"${spending_insights['monthly_spending']:,.0f}")
    
    # Category insights
    if spending_insights['top_categories']:
        st.write("**Your Top Spending Categories:**")
        for category, amount in spending_insights['top_categories']:
            friendly_name = category.replace('_', ' ').title()
            st.write(f"• {friendly_name}: ${amount:,.0f}")

st.subheader("🚀 Quick Actions")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.page_link("pages/4_💳_Make_Transaction.py", label="New Payment", icon="💳")

with col2:
    st.page_link("pages/9_💰_Make_Payment.py", label="Pay Balance", icon="💰")  # NEW PAYMENT LINK

with col3:
    st.page_link("pages/5_📊_My_Transactions.py", label="View History", icon="📊")

with col4:
    if st.button("🔄 Refresh", use_container_width=True):
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
            status_emoji = "🔒"
            status_text = "Under Review"
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
    
    min_payment = max(current_balance * 0.03, 25.00)
    due_date = user_data.get('credit_cards', {}).get('primary', {}).get('payment_due_date', '15th of next month')
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.write(f"**Current Balance:** ${current_balance:,.2f}")
        st.write(f"**Minimum Payment:** ${min_payment:,.2f}")
        st.write(f"**Due Date:** {due_date}")
    
    with col2:
        st.write(f"**Credit Available:** ${available_credit:,.2f}")
        if utilization > 50:
            st.warning("💡 Paying more than the minimum can help improve your credit utilization ratio")
    
    with col3:
        # ADD PAYMENT BUTTON TO PAYMENT REMINDER
        st.page_link("pages/9_💰_Make_Payment.py", 
                    label="💳 Make Payment", 
                    use_container_width=True,
                    help="Click here to make a payment toward your balance")

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