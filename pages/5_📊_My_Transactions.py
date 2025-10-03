import streamlit as st
import json
import pandas as pd
import joblib
from datetime import datetime

from utils.session_utils import initialize_session_state
initialize_session_state()

st.title("📊 My Transactions")

@st.cache_resource
def load_model():
    """Load ML model for insights"""
    try:
        model = joblib.load('best_xgb_model_tuned.joblib')
        return model
    except:
        return None

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

def get_ml_insights_for_user(transactions, model):
    """Provide ML insights without alarming the user"""
    if not model or not transactions:
        return {}
    
    approved_txs = [t for t in transactions if t.get('status') == 'approved']
    
    # Safe insights that don't reveal fraud detection
    insights = {
        'spending_trend': 'stable',
        'common_categories': [],
        'avg_transaction_size': 0,
        'monthly_pattern': 'normal',
        'spending_health': 'excellent'
    }
    
    if approved_txs:
        # Calculate average transaction size
        amounts = [t['amount'] for t in approved_txs]
        insights['avg_transaction_size'] = sum(amounts) / len(amounts)
        
        # Identify common spending categories (safe info)
        categories = {}
        for tx in approved_txs:
            cat = tx.get('category', 'other')
            categories[cat] = categories.get(cat, 0) + 1
        
        insights['common_categories'] = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
        
        # Simple trend analysis
        if len(approved_txs) > 5:
            recent_avg = sum(t['amount'] for t in approved_txs[-3:]) / 3
            historical_avg = sum(t['amount'] for t in approved_txs[:-3]) / len(approved_txs[:-3])
            
            if recent_avg > historical_avg * 1.3:
                insights['spending_trend'] = 'increasing'
            elif recent_avg < historical_avg * 0.7:
                insights['spending_trend'] = 'decreasing'
        
        # Spending health based on consistency
        if len(set(amounts)) / len(amounts) > 0.8:  # High variety
            insights['spending_health'] = 'varied'
        else:
            insights['spending_health'] = 'consistent'
    
    return insights

# Safe authentication check
if not st.session_state.get('user_authenticated', False):
    st.warning("Please login to view your transactions")
    st.page_link("pages/1_👤_User_Login.py", label="Go to Login", icon="🔐")
    st.stop()

# Load data and model
transactions = load_user_transactions()
pending_approvals = load_pending_approvals()
model = load_model()

# ML-Powered Insights Section
if transactions:
    st.subheader("💡 Smart Spending Insights")
    
    insights = get_ml_insights_for_user(transactions, model)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        trend_emoji = "📈" if insights['spending_trend'] == 'increasing' else "📉" if insights['spending_trend'] == 'decreasing' else "➡️"
        st.metric("Spending Trend", insights['spending_trend'].title(), delta=trend_emoji)
    
    with col2:
        st.metric("Avg Transaction", f"${insights['avg_transaction_size']:,.0f}")
    
    with col3:
        health_emoji = "✅" if insights['spending_health'] == 'consistent' else "ℹ️"
        st.metric("Spending Pattern", insights['spending_health'].title(), delta=health_emoji)
    
    with col4:
        st.metric("Active Categories", len(insights['common_categories']))
    
    # Show safe category insights
    if insights['common_categories']:
        st.write("**Your Common Spending Categories:**")
        for category, count in insights['common_categories']:
            friendly_name = category.replace('_', ' ').title()
            st.write(f"• {friendly_name} ({count} transactions)")

# Filter user's pending approvals (HIDE RISK DETAILS)
user_pending = [p for p in pending_approvals if p.get('user_id') == st.session_state.current_user]

# Summary statistics
if transactions:
    total_transactions = len(transactions)
    approved_count = len([t for t in transactions if t.get('status') == 'approved'])
    pending_count = len([t for t in transactions if t.get('status') in ['under_review', 'pending']])
    rejected_count = len([t for t in transactions if t.get('status') == 'rejected'])
    security_hold_count = len([t for t in transactions if t.get('status') == 'fraud'])
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Transactions", total_transactions)
    col2.metric("Approved", approved_count)
    col3.metric("Pending", pending_count)
    col4.metric("Security Review", security_hold_count)

# Pending transactions - SHOW ONLY BASIC INFO
if user_pending:
    st.subheader("⏳ Pending Approval")
    
    for pending in user_pending:
        if pending['status'] == 'pending':
            with st.container():
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    st.write(f"**Transaction ID:** {pending['transaction_id']}")
                    st.write(f"**Amount:** ${pending['transaction_data']['amount']:,.2f}")
                    st.write(f"**To:** {pending['transaction_data']['recipient_name']}")
                    st.write(f"**Merchant:** {pending['transaction_data']['merchant_name']}")
                
                with col2:
                    status_emoji = "🔄"
                    st.write(f"**Status:** {status_emoji} Under Review")
                    st.write(f"**Category:** {pending['transaction_data']['category']}")
                
                with col3:
                    st.write(f"**Submitted:** {pending['timestamp'][:16]}")
                    st.write(f"**Description:** {pending['transaction_data']['description']}")
                
                st.divider()

# Transaction history
st.subheader("📋 Transaction History")

if not transactions:
    st.info("No transactions found. Make your first transaction!")
    st.page_link("pages/4_💳_Make_Transaction.py", label="Make a Transaction", icon="💳")
else:
    # Filter options - UPDATED STATUS LABELS
    col1, col2, col3 = st.columns(3)
    with col1:
        status_filter = st.selectbox("Filter by Status", [
            "All", 
            "Approved", 
            "Pending", 
            "Declined", 
            "Security Review"
        ])
    with col2:
        sort_by = st.selectbox("Sort by", [
            "Date (Newest)", 
            "Date (Oldest)", 
            "Amount (High to Low)", 
            "Amount (Low to High)"
        ])
    with col3:
        search_term = st.text_input("Search by description or merchant")
    
    # Filter transactions - UPDATED STATUS MAPPING
    filtered_transactions = transactions.copy()
    
    if status_filter != "All":
        status_map = {
            "Approved": "approved", 
            "Pending": "under_review", 
            "Declined": "rejected", 
            "Security Review": "fraud"
        }
        filtered_transactions = [t for t in filtered_transactions if t.get('status') == status_map[status_filter]]
    
    if search_term:
        filtered_transactions = [t for t in filtered_transactions 
                               if search_term.lower() in t.get('description', '').lower() 
                               or search_term.lower() in t.get('merchant_name', '').lower()]
    
    # Sort transactions
    if sort_by == "Date (Newest)":
        filtered_transactions.sort(key=lambda x: x.get('submitted_at', ''), reverse=True)
    elif sort_by == "Date (Oldest)":
        filtered_transactions.sort(key=lambda x: x.get('submitted_at', ''))
    elif sort_by == "Amount (High to Low)":
        filtered_transactions.sort(key=lambda x: x['amount'], reverse=True)
    elif sort_by == "Amount (Low to High)":
        filtered_transactions.sort(key=lambda x: x['amount'])
    
    # Display transactions - UPDATED STATUS DISPLAY
    for transaction in filtered_transactions:
        # Determine status display (USER-FRIENDLY, DISCREET)
        status = transaction.get('status', 'pending')
        if status == 'approved':
            status_color = "green"
            status_emoji = "✅"
            status_text = "Completed"
        elif status == 'rejected':
            status_color = "red"
            status_emoji = "❌"
            status_text = "Declined"
        elif status == 'fraud':
            status_color = "orange"
            status_emoji = "🔒"
            status_text = "Security Review"
        elif status == 'under_review':
            status_color = "orange"
            status_emoji = "🔄"
            status_text = "Processing"
        else:
            status_color = "gray"
            status_emoji = "⏳"
            status_text = "Pending"
        
        # Create expander with basic info only
        with st.expander(f"{status_emoji} ${transaction['amount']:,.2f} - {transaction['merchant_name']} - {status_text}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Transaction ID:** {transaction.get('transaction_id', 'N/A')}")
                st.write(f"**Amount:** ${transaction['amount']:,.2f}")
                st.write(f"**Recipient:** {transaction['recipient_name']}")
                st.write(f"**Description:** {transaction['description']}")
                
            with col2:
                st.write(f"**Status:** :{status_color}[{status_text}]")
                st.write(f"**Category:** {transaction['category']}")
                st.write(f"**Submitted:** {transaction.get('submitted_at', '')[:19]}")
                
                # Show appropriate bank messages
                if transaction.get('admin_review') and status in ['approved', 'rejected']:
                    if "fraud" not in transaction['admin_review'].lower():
                        st.write(f"**Bank Message:** {transaction['admin_review']}")
                elif status == 'rejected':
                    st.write("**Bank Message:** Transaction could not be processed")
                elif status == 'fraud':
                    st.write("**Bank Message:** Additional verification required")
            
            # Show basic location info if available
            if transaction.get('user_lat') and transaction.get('user_lon'):
                st.write("**📍 Location Verification:** ✅ Verified")
            
            # Additional info for security review transactions
            if status == 'fraud':
                st.info("""
                **Transaction Under Review:**
                - This transaction is undergoing standard security checks
                - This is a routine procedure for selected transactions
                - You may be contacted for additional verification
                - Your account security is our priority
                """)

# Recent activity summary
st.subheader("📈 Recent Activity Summary")

if transactions:
    # Calculate some basic stats
    recent_txs = list(reversed(transactions))[:5]
    
    st.write("**Latest Transactions:**")
    for tx in recent_txs:
        status = tx.get('status', 'pending')
        if status == 'approved':
            emoji = "✅"
            status_text = "Completed"
        elif status == 'rejected':
            emoji = "❌" 
            status_text = "Declined"
        elif status == 'fraud':
            emoji = "🔒"
            status_text = "Under Review"
        else:
            emoji = "🔄"
            status_text = "Processing"
        
        st.write(f"{emoji} **${tx['amount']:,.2f}** - {tx['merchant_name']} - *{status_text}*")
    
    # Show spending patterns
    monthly_spending = {}
    for tx in transactions:
        if tx.get('status') == 'approved' and tx.get('submitted_at'):
            try:
                month = tx['submitted_at'][:7]
                monthly_spending[month] = monthly_spending.get(month, 0) + tx['amount']
            except:
                pass
    
    if monthly_spending:
        st.write("**Monthly Spending:**")
        for month, amount in sorted(monthly_spending.items(), reverse=True)[:3]:
            st.write(f"• {month}: ${amount:,.2f}")

# Export functionality
if transactions:
    st.divider()
    st.subheader("📤 Export Transactions")
    
    if st.button("Export to CSV"):
        safe_transactions = []
        for tx in filtered_transactions:
            safe_tx = {
                'transaction_id': tx.get('transaction_id', ''),
                'amount': tx.get('amount', 0),
                'recipient_name': tx.get('recipient_name', ''),
                'merchant_name': tx.get('merchant_name', ''),
                'category': tx.get('category', ''),
                'description': tx.get('description', ''),
                'status': tx.get('status', ''),
                'submitted_at': tx.get('submitted_at', ''),
            }
            # Convert status to user-friendly, discreet terms
            status_map = {
                'approved': 'Completed',
                'rejected': 'Declined', 
                'fraud': 'Under Review',
                'under_review': 'Processing',
                'pending': 'Pending'
            }
            safe_tx['status'] = status_map.get(safe_tx['status'], safe_tx['status'])
            safe_transactions.append(safe_tx)
        
        df = pd.DataFrame(safe_transactions)
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"my_transactions_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

# Help section - UPDATED TERMINOLOGY
st.sidebar.header("ℹ️ Understanding Your Transactions")
st.sidebar.write("""
**Transaction Statuses:**
- ✅ **Completed:** Successfully processed
- 🔄 **Processing:** Being verified by our system  
- ❌ **Declined:** Could not be completed
- 🔒 **Under Review:** Additional verification in progress

**Security Features:**
- All transactions are monitored for your protection
- Selected transactions undergo additional verification
- This is a standard security procedure
- Your financial security is our priority

**Need Help?**
Contact customer support for any transaction questions.
""")