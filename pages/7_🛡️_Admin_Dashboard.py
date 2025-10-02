# pages/7_🛡️_Admin_Dashboard.py
import streamlit as st
import json
import pandas as pd
from datetime import datetime
from utils.helpers import update_transaction_status, create_fraud_alert, convert_to_serializable

from utils.session_utils import initialize_session_state
initialize_session_state()

st.title("🛡️ Bank Security Dashboard")

# Admin authentication check
if not st.session_state.get('admin_authenticated', False):
    st.error("🔒 Access Denied: Admin authentication required")
    st.page_link("pages/6_👨💼_Admin_Login.py", label="Go to Admin Login", icon="🛡️")
    st.stop()

def load_pending_approvals():
    try:
        with open('data/pending_approvals.json', 'r') as f:
            return json.load(f)
    except:
        return []

def load_users():
    try:
        with open('data/users.json', 'r') as f:
            return json.load(f)
    except:
        return {}

def load_fraud_alerts():
    try:
        with open('data/fraud_alerts.json', 'r') as f:
            return json.load(f)
    except:
        return []

def load_transactions():
    try:
        with open('data/transactions.json', 'r') as f:
            return json.load(f)
    except:
        return {}

def detect_potential_criminal(user_id):
    """Analyze user patterns to detect potential criminal activity"""
    try:
        with open('data/transactions.json', 'r') as f:
            all_transactions = json.load(f)
        with open('data/pending_approvals.json', 'r') as f:
            pending = json.load(f)
    except:
        return False, []
    
    user_transactions = all_transactions.get(user_id, [])
    user_pending = [p for p in pending if p['user_id'] == user_id and p['status'] == 'pending']
    
    red_flags = []
    
    # 1. New user with multiple high-risk transactions
    if len(user_transactions) == 0 and len(user_pending) > 2:
        red_flags.append("New user with multiple pending high-risk transactions")
    
    # 2. Rapid transaction attempts
    if len(user_pending) >= 3:
        recent_times = []
        for pending_tx in user_pending[-3:]:
            try:
                tx_time = datetime.fromisoformat(pending_tx['timestamp'].replace('Z', '+00:00'))
                recent_times.append(tx_time)
            except:
                continue
        
        if len(recent_times) >= 3:
            time_diffs = [(recent_times[i] - recent_times[i-1]).total_seconds() for i in range(1, len(recent_times))]
            if any(diff < 600 for diff in time_diffs):  # Multiple transactions within 10 minutes
                red_flags.append("Rapid transaction attempts (multiple within 10 minutes)")
    
    # 3. High cumulative risk score
    total_risk = sum(tx['fraud_probability'] for tx in user_pending)
    if total_risk > 2.0:  # Very high cumulative risk
        red_flags.append(f"Very high cumulative risk score: {total_risk:.2f}")
    
    # 4. Geographic anomalies across transactions
    locations = []
    for tx in user_pending:
        tx_data = tx['transaction_data']
        if tx_data.get('merch_lat') and tx_data.get('merch_lon'):
            locations.append((tx_data['merch_lat'], tx_data['merch_lon']))
    
    if len(locations) >= 2:
        # Check if transactions are from very different locations
        lat_range = max(lat for lat, lon in locations) - min(lat for lat, lon in locations)
        lon_range = max(lon for lat, lon in locations) - min(lon for lat, lon in locations)
        if lat_range > 5.0 or lon_range > 5.0:  # Large geographic spread
            red_flags.append("Transactions from geographically dispersed locations")
    
    # 5. Unusual transaction amounts
    pending_amounts = [tx['transaction_data']['amount'] for tx in user_pending]
    if pending_amounts:
        avg_amount = sum(pending_amounts) / len(pending_amounts)
        if any(amount > avg_amount * 10 for amount in pending_amounts):  # 10x average amount
            red_flags.append("Extremely high amount transactions")
    
    # 6. Multiple high-risk transactions
    high_risk_count = len([tx for tx in user_pending if tx['risk_level'] == 'HIGH_RISK'])
    if high_risk_count >= 2:
        red_flags.append(f"Multiple high-risk transactions: {high_risk_count}")
    
    is_potential_criminal = len(red_flags) >= 2
    return is_potential_criminal, red_flags

def get_user_profile(user_id):
    """Get comprehensive user profile for investigation"""
    users = load_users()
    transactions = load_transactions()
    pending_approvals = load_pending_approvals()
    
    user_data = users.get(user_id, {})
    user_txs = transactions.get(user_id, [])
    user_pending = [p for p in pending_approvals if p['user_id'] == user_id]
    
    profile = {
        'user_data': user_data,
        'total_transactions': len(user_txs),
        'pending_transactions': len(user_pending),
        'account_age': None,
        'high_risk_count': len([tx for tx in user_pending if tx.get('risk_level') == 'HIGH_RISK']),
        'total_amount_pending': sum(tx['transaction_data']['amount'] for tx in user_pending)
    }
    
    # Calculate account age
    if user_data.get('account_created'):
        try:
            created_date = datetime.fromisoformat(user_data['account_created'].replace('Z', '+00:00'))
            account_age = (datetime.now() - created_date).days
            profile['account_age'] = account_age
        except:
            pass
    
    return profile

# Load data
pending_approvals = load_pending_approvals()
fraud_alerts = load_fraud_alerts()
users = load_users()
transactions = load_transactions()

# Welcome message
st.success(f"Welcome, {st.session_state.admin_details.get('name', 'Admin')}! 👨💼")

# Dashboard overview
st.subheader("📊 Security Overview")

active_alerts = [a for a in fraud_alerts if a['status'] == 'new']
high_risk_pending = [p for p in pending_approvals if p['risk_level'] == 'HIGH_RISK' and p['status'] == 'pending']
suspicious_users = []

# Check for suspicious users
for user_id in users.keys():
    is_suspicious, _ = detect_potential_criminal(user_id)
    if is_suspicious:
        suspicious_users.append(user_id)

col1, col2, col3, col4 = st.columns(4)
col1.metric("Pending Approvals", len(pending_approvals))
col2.metric("High Risk Transactions", len(high_risk_pending))
col3.metric("Active Fraud Alerts", len(active_alerts))
col4.metric("Suspicious Users", len(suspicious_users))

# Quick actions
st.subheader("🚀 Quick Actions")
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.button("🔄 Refresh Data"):
        st.rerun()

with col2:
    if st.button("📊 Generate Report"):
        st.info("Comprehensive security report would be generated here")

with col3:
    if st.button("👮 Mass Alert"):
        if suspicious_users:
            st.warning(f"🚨 Law enforcement notified for {len(suspicious_users)} suspicious users")
        else:
            st.info("No suspicious users to alert")

with col4:
    if st.button("🚪 Logout"):
        st.session_state.admin_authenticated = False
        st.session_state.admin_user = None
        st.session_state.admin_details = {}
        st.rerun()

# Suspicious users section
if suspicious_users:
    st.subheader("🔴 Suspicious Users Detected")
    
    for user_id in suspicious_users[:5]:  # Show first 5 suspicious users
        is_suspicious, red_flags = detect_potential_criminal(user_id)
        user_profile = get_user_profile(user_id)
        
        with st.expander(f"🚨 SUSPICIOUS USER: {user_id} | {len(red_flags)} Red Flags"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**User ID:** {user_id}")
                st.write(f"**Full Name:** {user_profile['user_data'].get('full_name', 'N/A')}")
                st.write(f"**Email:** {user_profile['user_data'].get('email', 'N/A')}")
                st.write(f"**Phone:** {user_profile['user_data'].get('phone', 'N/A')}")
                
            with col2:
                st.write(f"**Account Age:** {user_profile['account_age']} days" if user_profile['account_age'] else "**Account Age:** New")
                st.write(f"**Total Transactions:** {user_profile['total_transactions']}")
                st.write(f"**Pending Transactions:** {user_profile['pending_transactions']}")
                st.write(f"**High Risk Count:** {user_profile['high_risk_count']}")
            
            st.subheader("Red Flags:")
            for flag in red_flags:
                st.error(f"• {flag}")
            
            # Action buttons for suspicious users
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"Freeze Account", key=f"freeze_{user_id}"):
                    # In real system, this would freeze the user's account
                    users[user_id]['account_status'] = 'frozen'
                    with open('data/users.json', 'w') as f:
                        json.dump(users, f, indent=2)
                    st.error(f"Account {user_id} frozen!")
                    st.rerun()
            
            with col2:
                if st.button(f"Notify Authorities", key=f"notify_{user_id}"):
                    st.error(f"🚓 Law enforcement notified about user {user_id}")
                    # Create comprehensive alert
                    alert_data = {
                        'user_id': user_id,
                        'red_flags': red_flags,
                        'user_profile': user_profile,
                        'timestamp': str(datetime.now())
                    }
                    # This would integrate with actual law enforcement systems
            
            with col3:
                if st.button(f"View All Transactions", key=f"view_{user_id}"):
                    user_txs = transactions.get(user_id, [])
                    st.write(f"**Transaction History for {user_id}:**")
                    for tx in user_txs[-5:]:  # Show last 5 transactions
                        st.write(f"- ${tx['amount']} to {tx['merchant_name']} - {tx.get('status', 'unknown')}")

# Pending transactions for approval
st.subheader("⏳ Pending Transaction Approvals")

if not pending_approvals:
    st.info("No pending transactions for approval")
else:
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        risk_filter = st.selectbox("Filter by Risk Level", ["All", "HIGH_RISK", "MEDIUM_RISK", "LOW_RISK"])
    with col2:
        sort_by = st.selectbox("Sort Transactions By", ["Risk Level", "Amount", "Date"])
    
    filtered_approvals = [p for p in pending_approvals if p['status'] == 'pending']
    
    if risk_filter != "All":
        filtered_approvals = [p for p in filtered_approvals if p['risk_level'] == risk_filter]
    
    # Sort approvals
    if sort_by == "Risk Level":
        risk_order = {"HIGH_RISK": 3, "MEDIUM_RISK": 2, "LOW_RISK": 1}
        filtered_approvals.sort(key=lambda x: risk_order.get(x['risk_level'], 0), reverse=True)
    elif sort_by == "Amount":
        filtered_approvals.sort(key=lambda x: x['transaction_data']['amount'], reverse=True)
    elif sort_by == "Date":
        filtered_approvals.sort(key=lambda x: x['timestamp'], reverse=True)
    
    for approval in filtered_approvals:
        # Criminal detection for each transaction
        is_suspicious, red_flags = detect_potential_criminal(approval['user_id'])
        
        with st.expander(f"TX: {approval['transaction_id']} | ${approval['transaction_data']['amount']} | {approval['risk_level'].replace('_', ' ')} {'🚨 SUSPICIOUS' if is_suspicious else ''}"):
            
            if is_suspicious:
                st.error("🚨 **POTENTIAL CRIMINAL ACTIVITY DETECTED**")
                for flag in red_flags[:3]:  # Show first 3 red flags
                    st.write(f"• {flag}")
                st.warning("**Recommendation:** Immediate law enforcement notification recommended")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**User:** {approval['user_id']}")
                st.write(f"**Amount:** ${approval['transaction_data']['amount']:,.2f}")
                st.write(f"**Merchant:** {approval['transaction_data']['merchant_name']}")
                st.write(f"**Category:** {approval['transaction_data']['category']}")
                st.write(f"**Fraud Probability:** {approval['fraud_probability']:.2%}")
                
            with col2:
                st.write(f"**Submitted:** {approval['timestamp']}")
                st.write(f"**Risk Level:** {approval['risk_level']}")
                st.write(f"**Recipient:** {approval['transaction_data']['recipient_name']}")
                st.write(f"**Description:** {approval['transaction_data']['description']}")
            
            # Location information
            tx_data = approval['transaction_data']
            if tx_data.get('user_lat') and tx_data.get('user_lon'):
                st.write("**📍 Location Analysis:**")
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"User Location: {tx_data['user_lat']:.4f}, {tx_data['user_lon']:.4f}")
                with col2:
                    st.write(f"Merchant Location: {tx_data['merch_lat']:.4f}, {tx_data['merch_lon']:.4f}")
                
                # Calculate distance
                distance = ((tx_data['merch_lat'] - tx_data['user_lat'])**2 + (tx_data['merch_lon'] - tx_data['user_lon'])**2)**0.5
                if distance > 1.0:
                    st.warning(f"⚠️ Unusual distance between locations: {distance:.2f} units")
            
            # Admin actions
            st.subheader("Admin Decision")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button(f"✅ Approve", key=f"approve_{approval['transaction_id']}"):
                    update_transaction_status(approval['transaction_id'], 'approved', 'Transaction approved by security team')
                    st.success("Transaction approved successfully!")
                    st.rerun()
            
            with col2:
                if st.button(f"❌ Reject", key=f"reject_{approval['transaction_id']}"):
                    update_transaction_status(approval['transaction_id'], 'rejected', 'Transaction rejected by security team')
                    st.error("Transaction rejected!")
                    st.rerun()
            
            with col3:
                if st.button(f"🚨 Flag as Fraud", key=f"flag_{approval['transaction_id']}"):
                    update_transaction_status(approval['transaction_id'], 'fraud', 'Flagged as fraudulent activity')
                    create_fraud_alert(approval['transaction_data'], approval['fraud_probability'])
                    st.error("Transaction flagged as fraud! Authorities notified.")
                    st.rerun()
            
            with col4:
                if is_suspicious and st.button(f"👮 Notify Police", key=f"police_{approval['transaction_id']}"):
                    st.error("🚓 **Law enforcement notified of potential criminal activity**")
                    # Create comprehensive criminal alert
                    criminal_alert = {
                        'alert_id': f"CRIMINAL_{int(datetime.now().timestamp())}",
                        'user_id': approval['user_id'],
                        'transaction_id': approval['transaction_id'],
                        'red_flags': red_flags,
                        'fraud_probability': approval['fraud_probability'],
                        'amount': approval['transaction_data']['amount'],
                        'timestamp': str(datetime.now()),
                        'priority': 'URGENT'
                    }
                    st.json(criminal_alert)

# Fraud alerts management
st.subheader("🚨 Active Fraud Alerts")

active_alerts = [alert for alert in fraud_alerts if alert['status'] == 'new']
if not active_alerts:
    st.success("🎉 No active fraud alerts!")
else:
    for alert in active_alerts:
        with st.expander(f"ALERT: {alert['alert_id']} | Priority: {alert['priority']} | ${alert['amount']:,.2f}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Alert ID:** {alert['alert_id']}")
                st.write(f"**Transaction ID:** {alert['transaction_id']}")
                st.write(f"**User ID:** {alert['user_id']}")
                st.write(f"**Amount:** ${alert['amount']:,.2f}")
                
            with col2:
                st.write(f"**Merchant:** {alert['merchant']}")
                st.write(f"**Fraud Probability:** {alert['fraud_probability']:.2%}")
                st.write(f"**Timestamp:** {alert['timestamp']}")
                st.write(f"**Priority:** {alert['priority']}")
            
            # Get user profile for context
            user_profile = get_user_profile(alert['user_id'])
            st.write(f"**User Context:** {user_profile['total_transactions']} total transactions, {user_profile['pending_transactions']} pending")
            
            # Action buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button(f"Mark as Resolved", key=f"resolve_{alert['alert_id']}"):
                    alert['status'] = 'resolved'
                    alert['resolved_by'] = st.session_state.admin_user
                    alert['resolved_at'] = str(datetime.now())
                    with open('data/fraud_alerts.json', 'w') as f:
                        json.dump(fraud_alerts, f, indent=2)
                    st.success("Alert marked as resolved!")
                    st.rerun()
            
            with col2:
                if st.button(f"Escalate", key=f"escalate_{alert['alert_id']}"):
                    alert['priority'] = 'URGENT'
                    with open('data/fraud_alerts.json', 'w') as f:
                        json.dump(fraud_alerts, f, indent=2)
                    st.error("Alert escalated to URGENT priority!")
                    st.rerun()
            
            with col3:
                if st.button(f"View User Profile", key=f"profile_{alert['alert_id']}"):
                    st.write("**User Profile Details:**")
                    st.json(user_profile['user_data'])

# System statistics
st.subheader("📈 System Statistics")

if users and transactions:
    total_users = len(users)
    total_transactions = sum(len(txs) for txs in transactions.values())
    avg_transactions_per_user = total_transactions / total_users if total_users > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Users", total_users)
    col2.metric("Total Transactions", total_transactions)
    col3.metric("Avg Transactions/User", f"{avg_transactions_per_user:.1f}")

# Footer
st.divider()
st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Logged in as: {st.session_state.admin_user}")