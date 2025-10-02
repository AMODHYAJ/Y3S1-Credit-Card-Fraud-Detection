# pages/8_🚨_Fraud_Alerts.py
import streamlit as st
import json
import pandas as pd
from datetime import datetime

from utils.session_utils import initialize_session_state
initialize_session_state()

st.title("🚨 Fraud Alert Management")

def load_fraud_alerts():
    try:
        with open('data/fraud_alerts.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def load_users():
    try:
        with open('data/users.json', 'r') as f:
            return json.load(f)
    except:
        return {}

def load_transactions():
    try:
        with open('data/transactions.json', 'r') as f:
            return json.load(f)
    except:
        return {}

# Admin authentication check
if not st.session_state.get('admin_authenticated'):
    st.error("🔒 Access Denied: Admin authentication required")
    st.stop()

fraud_alerts = load_fraud_alerts()
users = load_users()
transactions = load_transactions()

# Alert statistics
st.subheader("📈 Fraud Alert Overview")

active_alerts = [a for a in fraud_alerts if a['status'] == 'new']
resolved_alerts = [a for a in fraud_alerts if a['status'] == 'resolved']
high_priority = [a for a in active_alerts if a['priority'] == 'HIGH']

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Alerts", len(fraud_alerts))
col2.metric("Active Alerts", len(active_alerts))
col3.metric("High Priority", len(high_priority))
col4.metric("Resolved", len(resolved_alerts))

# Quick actions
st.subheader("🛠️ Quick Actions")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Refresh Alerts"):
        st.rerun()

with col2:
    if st.button("📧 Generate Report"):
        st.info("Fraud report generation feature would be implemented here")

with col3:
    if st.button("👮 Notify Authorities"):
        st.warning("This would automatically notify law enforcement of high-priority alerts")

# Active alerts
st.subheader("🔴 Active Fraud Alerts")

if not active_alerts:
    st.success("🎉 No active fraud alerts!")
else:
    # Filter options
    col1, col2 = st.columns(2)
    with col1:
        priority_filter = st.selectbox("Filter by Priority", ["All", "HIGH", "MEDIUM"])
    with col2:
        sort_alerts = st.selectbox("Sort by", ["Newest", "Oldest", "Priority", "Amount"])
    
    # Filter alerts
    filtered_alerts = active_alerts.copy()
    if priority_filter != "All":
        filtered_alerts = [a for a in filtered_alerts if a['priority'] == priority_filter]
    
    # Sort alerts
    if sort_alerts == "Newest":
        filtered_alerts.sort(key=lambda x: x['timestamp'], reverse=True)
    elif sort_alerts == "Oldest":
        filtered_alerts.sort(key=lambda x: x['timestamp'])
    elif sort_alerts == "Priority":
        filtered_alerts.sort(key=lambda x: 0 if x['priority'] == 'HIGH' else 1)
    elif sort_alerts == "Amount":
        filtered_alerts.sort(key=lambda x: x['amount'], reverse=True)
    
    for alert in filtered_alerts:
        # Get user details
        user_data = users.get(alert['user_id'], {})
        
        with st.expander(f"🚨 {alert['alert_id']} | {alert['priority']} Priority | ${alert['amount']:,.2f}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Alert ID:** {alert['alert_id']}")
                st.write(f"**Transaction ID:** {alert['transaction_id']}")
                st.write(f"**User ID:** {alert['user_id']}")
                st.write(f"**User Name:** {user_data.get('full_name', 'N/A')}")
                st.write(f"**User Phone:** {user_data.get('phone', 'N/A')}")
                st.write(f"**User Email:** {user_data.get('email', 'N/A')}")
                
            with col2:
                st.write(f"**Amount:** ${alert['amount']:,.2f}")
                st.write(f"**Merchant:** {alert['merchant']}")
                st.write(f"**Fraud Probability:** {alert['fraud_probability']:.2%}")
                st.write(f"**Timestamp:** {alert['timestamp']}")
                st.write(f"**Priority:** {alert['priority']}")
                st.write(f"**Status:** {alert['status']}")
            
            # Additional user information
            st.subheader("👤 User Profile Information")
            col1, col2 = st.columns(2)
            
            with col1:
                if user_data:
                    st.write(f"**Address:** {user_data.get('address', 'N/A')}")
                    st.write(f"**ID Number:** {user_data.get('id_number', 'N/A')}")
                    st.write(f"**Account Created:** {user_data.get('account_created', 'N/A')}")
            
            with col2:
                if user_data:
                    st.write(f"**Location:** {user_data.get('lat', 'N/A'):.4f}, {user_data.get('lon', 'N/A'):.4f}")
                    st.write(f"**Gender:** {user_data.get('gender', 'N/A')}")
                    st.write(f"**Account Status:** {user_data.get('account_status', 'N/A')}")
            
            # Action buttons
            st.subheader("🛡️ Alert Management")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("✅ Mark as Resolved", key=f"resolve_{alert['alert_id']}"):
                    alert['status'] = 'resolved'
                    alert['resolved_by'] = st.session_state.admin_user
                    alert['resolved_at'] = str(datetime.now())
                    with open('data/fraud_alerts.json', 'w') as f:
                        json.dump(fraud_alerts, f, indent=2)
                    st.success("Alert marked as resolved!")
                    st.rerun()
            
            with col2:
                if st.button("📞 Contact User", key=f"contact_{alert['alert_id']}"):
                    st.info(f"Would initiate contact with user: {user_data.get('phone', 'N/A')}")
            
            with col3:
                if st.button("🚓 Notify Police", key=f"police_{alert['alert_id']}"):
                    st.error(f"🚨 Law enforcement notification sent for alert {alert['alert_id']}")
                    # In real implementation, this would integrate with police systems
            
            with col4:
                if st.button("📋 User History", key=f"history_{alert['alert_id']}"):
                    user_transactions = transactions.get(alert['user_id'], [])
                    st.write(f"**User Transaction History:** {len(user_transactions)} transactions")
                    for tx in user_transactions[-3:]:  # Show last 3 transactions
                        st.write(f"- ${tx['amount']:,.2f} to {tx['merchant_name']} - {tx.get('status', 'unknown')}")

# Resolved alerts section
if resolved_alerts:
    st.subheader("✅ Resolved Alerts")
    
    with st.expander("View Resolved Alerts"):
        for alert in resolved_alerts[-10:]:  # Show last 10 resolved alerts
            st.write(f"**{alert['alert_id']}** - ${alert['amount']:,.2f} - {alert['priority']} - Resolved by: {alert.get('resolved_by', 'Unknown')} - {alert.get('resolved_at', '')[:16]}")

# Reporting section
st.divider()
st.subheader("📊 Reporting & Analytics")

col1, col2 = st.columns(2)

with col1:
    if st.button("Generate Monthly Report"):
        st.info("Monthly fraud report generation would be implemented here")
        
        # Sample report data
        report_data = {
            "Total Alerts": len(fraud_alerts),
            "Active Alerts": len(active_alerts),
            "High Priority Alerts": len(high_priority),
            "Average Fraud Probability": f"{sum(a['fraud_probability'] for a in fraud_alerts) / len(fraud_alerts):.2%}" if fraud_alerts else "0%",
            "Total Amount in Alerts": f"${sum(a['amount'] for a in fraud_alerts):,.2f}"
        }
        
        st.json(report_data)

with col2:
    if st.button("Export Alert Data"):
        st.info("Alert data export would be implemented here")
        df = pd.DataFrame(fraud_alerts)
        csv = df.to_csv(index=False)
        st.download_button(
            label="Download CSV",
            data=csv,
            file_name=f"fraud_alerts_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )