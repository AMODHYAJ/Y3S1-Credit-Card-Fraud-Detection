# pages/4_💳_Make_Transaction.py - UPDATED SECURITY VERSION
import streamlit as st
import json
import joblib
from datetime import datetime
from utils.helpers import geocode_address, preprocess_transaction, add_pending_approval, create_fraud_alert, convert_to_serializable

from utils.session_utils import initialize_session_state
initialize_session_state()

st.title("💳 Make New Transaction")

@st.cache_resource
def load_model():
    return joblib.load('best_xgb_model_tuned.joblib')

model = load_model()

def load_user_data():
    try:
        with open('data/users.json', 'r') as f:
            users = json.load(f)
        return users.get(st.session_state.current_user, {})
    except:
        return {}

def analyze_user_behavior(user_id, current_transaction):
    """Analyze user behavior patterns to detect potential criminal activity"""
    try:
        with open('data/transactions.json', 'r') as f:
            all_transactions = json.load(f)
    except:
        return "normal"  # Default if no history
    
    user_transactions = all_transactions.get(user_id, [])
    
    if len(user_transactions) < 3:
        return "new_user"  # Not enough data
    
    # Behavioral analysis
    recent_transactions = user_transactions[-10:]  # Last 10 transactions
    
    # Check for suspicious patterns
    suspicious_patterns = []
    
    # 1. Rapid succession transactions
    if len(recent_transactions) >= 3:
        time_diff = []
        for i in range(1, len(recent_transactions)):
            prev_time = datetime.fromisoformat(recent_transactions[i-1].get('submitted_at', '').replace('Z', '+00:00'))
            curr_time = datetime.fromisoformat(recent_transactions[i].get('submitted_at', '').replace('Z', '+00:00'))
            time_diff.append((curr_time - prev_time).total_seconds())
        
        if any(diff < 300 for diff in time_diff):  # Less than 5 minutes between transactions
            suspicious_patterns.append("rapid_transactions")
    
    # 2. Unusual amount patterns
    amounts = [tx['amount'] for tx in recent_transactions]
    avg_amount = sum(amounts) / len(amounts)
    if current_transaction['amount'] > avg_amount * 5:  # 5x average amount
        suspicious_patterns.append("unusual_amount")
    
    # 3. Geographic anomalies
    user_locations = [(tx.get('user_lat', 0), tx.get('user_lon', 0)) for tx in recent_transactions if tx.get('user_lat')]
    if user_locations:
        avg_lat = sum(lat for lat, lon in user_locations) / len(user_locations)
        avg_lon = sum(lon for lat, lon in user_locations) / len(user_locations)
        
        current_lat = current_transaction.get('user_lat', avg_lat)
        current_lon = current_transaction.get('user_lon', avg_lon)
        
        # Calculate distance from average location
        distance = ((current_lat - avg_lat)**2 + (current_lon - avg_lon)**2)**0.5
        if distance > 1.0:  # Significant location change
            suspicious_patterns.append("geographic_anomaly")
    
    # Determine risk level based on patterns
    if len(suspicious_patterns) >= 2:
        return "high_risk_behavior"
    elif len(suspicious_patterns) >= 1:
        return "medium_risk_behavior"
    else:
        return "normal_behavior"

# Safe authentication check
if not st.session_state.get('user_authenticated', False):
    st.warning("Please login to make a transaction")
    st.page_link("pages/1_👤_User_Login.py", label="Go to Login", icon="🔐")
    st.stop()

user_data = load_user_data()

with st.form("transaction_form"):
    st.subheader("Payment Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write(f"**Account Balance:** ${user_data.get('balance', 0):,.2f}")
        amount = st.number_input("Transaction Amount ($)", min_value=1.0, value=50.0, step=1.0)
        recipient_name = st.text_input("Recipient Name")
        recipient_account = st.text_input("Recipient Account Number")
    
    with col2:
        category = st.selectbox("Transaction Type", 
                               ['shopping_pos', 'shopping_net', 'gas_transport', 'food_dining',
                                'bill_payment', 'transfer', 'entertainment', 'travel'])
        merchant_name = st.text_input("Merchant/Business Name")
        merchant_address = st.text_area("Merchant Address")
        description = st.text_input("Transaction Description")
    
    submitted = st.form_submit_button("Submit Transaction for Approval")
    
    if submitted:
        if amount > user_data.get('balance', 0):
            st.error("❌ Insufficient funds for this transaction")
        elif not all([amount, recipient_name, merchant_address]):
            st.error("Please fill in all required fields")
        else:
            # Geocode addresses
            with st.spinner("📍 Verifying transaction details..."):
                user_lat, user_lon = user_data.get('lat', 40.7128), user_data.get('lon', -74.0060)
                merch_lat, merch_lon = geocode_address(merchant_address)
            
            # Prepare transaction data
            transaction_data = {
                'transaction_id': f"TX{int(datetime.now().timestamp())}",
                'user_id': st.session_state.current_user,
                'amount': amount,
                'recipient_name': recipient_name,
                'recipient_account': recipient_account,
                'category': category,
                'merchant_name': merchant_name,
                'merchant_address': merchant_address,
                'description': description,
                'user_lat': user_lat,
                'user_lon': user_lon,
                'merch_lat': merch_lat,
                'merch_lon': merch_lon,
                'submitted_at': str(datetime.now()),
                'status': 'under_review'
            }
            
            # Behavioral analysis (HIDDEN FROM USER)
            with st.spinner("🛡️ Analyzing transaction patterns..."):
                behavior_risk = analyze_user_behavior(st.session_state.current_user, transaction_data)
                
                # Fraud detection analysis
                input_df = preprocess_transaction(
                    {**transaction_data, 'gender': user_data.get('gender', 'M'), 'card_number': '0000000000000000'},
                    user_lat, user_lon, merch_lat, merch_lon
                )
                
                prediction_proba = model.predict_proba(input_df)
                fraud_probability = float(prediction_proba[0][1])
                
                # Combine fraud probability with behavioral analysis
                if behavior_risk == "high_risk_behavior":
                    fraud_probability = max(fraud_probability, 0.8)  # Boost risk score
                elif behavior_risk == "medium_risk_behavior":
                    fraud_probability = max(fraud_probability, 0.5)  # Moderate boost
                
                # Determine risk level (INTERNAL ONLY - NOT SHOWN TO USER)
                if fraud_probability > 0.7:
                    risk_level = "HIGH_RISK"
                    user_message = "high_risk"
                elif fraud_probability > 0.3:
                    risk_level = "MEDIUM_RISK" 
                    user_message = "medium_risk"
                else:
                    risk_level = "LOW_RISK"
                    user_message = "low_risk"
            
            # 🚨 SECURITY FIX: DON'T SHOW RISK DETAILS TO USER 🚨
            # Only show generic status messages
            
            if user_message == "high_risk":
                st.error("""
                ⚠️ **Transaction Under Security Review**
                
                Your transaction requires additional verification for security purposes.
                Our security team will review this transaction and contact you if needed.
                
                **What happens next:**
                - Transaction is being reviewed
                - You may be contacted for verification
                - This is a standard security procedure
                """)
                
            elif user_message == "medium_risk":
                st.warning("""
                🔍 **Transaction Being Processed**
                
                Your transaction is undergoing standard security checks.
                This may take slightly longer than usual.
                
                **Expected timeline:** 2-4 hours
                """)
                
            else:
                st.success("""
                ✅ **Transaction Submitted Successfully**
                
                Your transaction has been received and is being processed.
                
                **Expected completion:** Within 30 minutes
                """)
            
            # Add to pending approvals (INTERNAL RISK DATA)
            transaction_id = add_pending_approval(transaction_data, fraud_probability, risk_level)
            transaction_data['transaction_id'] = transaction_id
            transaction_data['internal_risk_score'] = fraud_probability  # Hidden from user
            transaction_data['behavior_analysis'] = behavior_risk  # Hidden from user
            
            # Save to user transactions (without internal risk data)
            try:
                with open('data/transactions.json', 'r') as f:
                    transactions = json.load(f)
            except:
                transactions = {}
            
            if st.session_state.current_user not in transactions:
                transactions[st.session_state.current_user] = []
            
            # Remove internal risk data before saving to user-facing records
            user_facing_transaction = transaction_data.copy()
            user_facing_transaction.pop('internal_risk_score', None)
            user_facing_transaction.pop('behavior_analysis', None)
            
            serializable_transaction = convert_to_serializable(user_facing_transaction)
            transactions[st.session_state.current_user].append(serializable_transaction)
            
            with open('data/transactions.json', 'w') as f:
                json.dump(transactions, f, indent=2, default=str)
            
            # Auto-create fraud alert for high-risk cases
            if risk_level == "HIGH_RISK":
                alert_id = create_fraud_alert(transaction_data, fraud_probability)
                st.info("📞 Our security team may contact you for verification.")
            
            st.info("💡 You can check the status of this transaction in 'My Transactions' section.")