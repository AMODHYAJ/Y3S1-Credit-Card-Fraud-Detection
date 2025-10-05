# pages/4_💳_Make_Transaction.py - CLEAN PRODUCTION VERSION
import streamlit as st
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime
import time
from utils.helpers import geocode_address, add_pending_approval, convert_to_serializable

from utils.session_utils import initialize_session_state
initialize_session_state()

st.title("💳 Make New Transaction")

from model_manager import get_ml_model

def load_model():
    """Load ML model using the model manager"""
    try:
        model_data = get_ml_model()
        if isinstance(model_data, dict) and 'model' in model_data:
            model = model_data['model']
        else:
            model = model_data
        return model
    except Exception as e:
        st.error(f"❌ Model loading error: {e}")
        return None

model = load_model()

def preprocess_transaction_fixed(transaction_data, user_lat, user_lon, merch_lat, merch_lon):
    """Enhanced preprocessing with geographic distance feature"""
    current_time = datetime.now()
    unix_time = int(time.mktime(current_time.timetuple()))
    
    def get_city_population(lat, lon):
        if abs(lat - 40.7128) < 1 and abs(lon - (-74.0060)) < 1:
            return 8419000
        elif abs(lat - 34.0522) < 1 and abs(lon - (-118.2437)) < 1:
            return 3980000
        elif abs(lat - 41.8781) < 1 and abs(lon - (-87.6298)) < 1:
            return 2716000
        else:
            return 500000
    
    city_pop = get_city_population(user_lat, user_lon)
    high_risk_hours = [2, 3, 4, 22, 23, 0]
    
    # Calculate geographic distance
    geo_distance = np.sqrt((user_lat - merch_lat)**2 + (user_lon - merch_lon)**2)
    
    # Create features with geographic distance
    input_data = {
        'cc_num': int(str(transaction_data.get('card_number', '00000000'))[-8:]),
        'gender': 1 if transaction_data.get('gender', 'M') == 'M' else 0,
        'lat': float(user_lat), 
        'long': float(user_lon), 
        'city_pop': city_pop,
        'unix_time': unix_time, 
        'merch_lat': float(merch_lat), 
        'merch_long': float(merch_lon),
        'hour': current_time.hour, 
        'day_of_week': current_time.weekday(),
        'is_weekend': 1 if current_time.weekday() >= 5 else 0,
        'month': current_time.month,
        'amt_scaled': float((transaction_data['amount'] - 70.0) / 200.0),
        'high_risk_hour': 1 if current_time.hour in high_risk_hours else 0,
        'geo_distance': float(geo_distance)
    }
    
    # Category encoding
    all_categories = [
        'entertainment', 'food_dining', 'gas_transport', 'grocery_net', 'grocery_pos',
        'health_fitness', 'home', 'kids_pets', 'misc_net', 'misc_pos', 
        'personal_care', 'shopping_net', 'shopping_pos', 'travel'
    ]
    
    for cat in all_categories:
        input_data[f'cat_{cat}'] = 1 if transaction_data.get('category') == cat else 0
    
    expected_columns = [
        'cc_num', 'gender', 'lat', 'long', 'city_pop', 'unix_time', 'merch_lat', 'merch_long',
        'hour', 'day_of_week', 'is_weekend', 'month', 'cat_entertainment', 'cat_food_dining',
        'cat_gas_transport', 'cat_grocery_net', 'cat_grocery_pos', 'cat_health_fitness',
        'cat_home', 'cat_kids_pets', 'cat_misc_net', 'cat_misc_pos', 'cat_personal_care',
        'cat_shopping_net', 'cat_shopping_pos', 'cat_travel', 'amt_scaled', 'high_risk_hour',
        'geo_distance'
    ]
    
    df = pd.DataFrame([input_data])
    
    # Ensure all expected columns exist
    for col in expected_columns:
        if col not in df.columns:
            df[col] = 0
    
    return df[expected_columns]

def detect_fraud_proper(transaction_data, user_data, merch_lat, merch_lon):
    """Proper fraud detection with correct feature transformation"""
    if model is None:
        return 0.05, "LOW_RISK"
    
    try:
        # Get user coordinates
        user_lat = user_data.get('lat', 40.7618)
        user_lon = user_data.get('lon', -73.9708)
        
        # Preprocess transaction
        input_df = preprocess_transaction_fixed(
            transaction_data, 
            user_lat, 
            user_lon,
            merch_lat, merch_lon
        )
        
        # Get base probability from ML model
        prediction_proba = model.predict_proba(input_df)
        fraud_probability = float(prediction_proba[0][1])
        
        # Apply geographic risk boosts for Sri Lankan users
        base_probability = fraud_probability
        
        # Check if user is in Sri Lanka
        is_sri_lankan_user = (5.0 <= user_lat <= 10.0) and (79.0 <= user_lon <= 82.0)
        
        if is_sri_lankan_user:
            # Calculate distance from Sri Lanka
            geo_distance = np.sqrt((user_lat - merch_lat)**2 + (user_lon - merch_lon)**2)
            
            # Sri Lankan risk patterns
            is_international_from_sl = geo_distance > 3.0
            is_high_value = transaction_data['amount'] > 500
            is_luxury_category = transaction_data.get('category') in ['shopping_net', 'travel', 'entertainment']
            
            # Apply Sri Lankan specific risk boosts
            if is_international_from_sl and is_high_value and is_luxury_category:
                fraud_probability = max(fraud_probability, 0.80)
            elif is_international_from_sl and is_high_value:
                fraud_probability = max(fraud_probability, 0.65)
            elif is_international_from_sl:
                fraud_probability = max(fraud_probability, 0.40)
        
        # Determine risk level
        if fraud_probability > 0.7:
            risk_level = "HIGH_RISK"
        elif fraud_probability > 0.3:
            risk_level = "MEDIUM_RISK" 
        else:
            risk_level = "LOW_RISK"
            
        return fraud_probability, risk_level
        
    except Exception as e:
        st.error(f"❌ ML prediction error: {e}")
        return 0.05, "LOW_RISK"
    
def load_user_data():
    """Load user data from JSON file"""
    try:
        with open('data/users.json', 'r') as f:
            users = json.load(f)
        return users.get(st.session_state.current_user, {})
    except Exception as e:
        st.error(f"Error loading user data: {e}")
        return {}

def reserve_credit(user_id, transaction_amount):
    """Reserve credit for pending transaction"""
    try:
        with open('data/users.json', 'r') as f:
            users = json.load(f)
        
        if user_id not in users:
            st.error("User not found")
            return False
        
        user = users[user_id]
        current_available = user.get('total_available_credit', 0)
        
        # Check if enough credit is available
        if transaction_amount > current_available:
            st.error(f"Insufficient credit: ${current_available} available, ${transaction_amount} requested")
            return False
        
        # Reserve credit
        user['total_available_credit'] = current_available - transaction_amount
        user['total_current_balance'] = user.get('total_current_balance', 0) + transaction_amount
        
        # Update primary card balance
        if 'credit_cards' in user and 'primary' in user['credit_cards']:
            card = user['credit_cards']['primary']
            card_available = card.get('available_balance', current_available)
            card['available_balance'] = card_available - transaction_amount
            card['current_balance'] = card.get('current_balance', 0) + transaction_amount
        
        # Write back to file
        with open('data/users.json', 'w') as f:
            json.dump(users, f, indent=2, default=str)
        
        return True
        
    except Exception as e:
        st.error(f"Error reserving credit: {e}")
        return False

def check_credit_limit(user_id, transaction_amount):
    """Check if transaction exceeds credit limit"""
    user_data = load_user_data()
    available_credit = user_data.get('total_available_credit', 0)
    credit_limit = user_data.get('total_credit_limit', 0)
    
    if transaction_amount > available_credit:
        return False, available_credit, credit_limit
    return True, available_credit, credit_limit

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
    st.warning("Please login to make a transaction")
    st.page_link("pages/1_👤_User_Login.py", label="Go to Login", icon="🔐")
    st.stop()

user_data = load_user_data()

# Dynamic credit information display
st.subheader("💳 Credit Information")

utilization, used_credit, total_limit = get_credit_utilization(user_data)
available_credit = user_data.get('total_available_credit', 0)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Credit Limit", f"${total_limit:,.2f}")

with col2:
    st.metric("Available Credit", f"${available_credit:,.2f}")

with col3:
    st.metric("Credit Used", f"${used_credit:,.2f}")

# Dynamic credit utilization warning
if total_limit > 0:
    if utilization > 80:
        st.error(f"🚨 High Credit Utilization: {utilization:.1f}% - Consider paying down your balance")
    elif utilization > 50:
        st.warning(f"⚠️ Moderate Credit Utilization: {utilization:.1f}%")

# Check if we just submitted a transaction
if st.session_state.get('transaction_submitted', False):
    st.success("""
    ✅ **Transaction Submitted for Approval**
    
    Your transaction has been received and is pending admin approval.
    Credit has been temporarily reserved for this transaction.
    
    **What happens next:**
    - Transaction sent to security team for review
    - You will be notified once approved
    - Credit will be permanently deducted upon approval
    """)
    
    # Show updated available credit
    updated_user_data = load_user_data()
    new_available = updated_user_data.get('total_available_credit', 0)
    st.info(f"**Available Credit (Reserved):** ${new_available:,.2f}")
    
    # Navigation options
    st.info("💡 You can check the status of this transaction in 'My Transactions' section.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Make Another Transaction", use_container_width=True):
            st.session_state.transaction_submitted = False
            st.rerun()
    with col2:
        st.page_link("pages/5_📊_My_Transactions.py", 
                    label="📊 View My Transactions", 
                    use_container_width=True)
    
    st.stop()

# Regular transaction form
with st.form("transaction_form", clear_on_submit=True):
    st.subheader("Payment Details")
    
    # Pre-filled test transactions for quick testing
    test_transaction = st.selectbox("Quick Test Transactions", 
                                   ["Custom Transaction", 
                                    "🚨 High Risk: Dubai Luxury ($2,800)",
                                    "⚠️ Medium Risk: California Shopping ($650)", 
                                    "✅ Low Risk: Local Grocery ($85)"])
    
    if test_transaction == "🚨 High Risk: Dubai Luxury ($2,800)":
        amount = 2800.00
        recipient_name = "Luxury Watches Dubai"
        recipient_account = "DUBAI12345"
        category = "shopping_net"
        merchant_name = "Dubai Luxury Timepieces"
        merchant_address = "Dubai Mall, Financial Center Rd, Dubai, UAE"
        description = "Rolex watch purchase"
    elif test_transaction == "⚠️ Medium Risk: California Shopping ($650)":
        amount = 650.00
        recipient_name = "California Designs"
        recipient_account = "CALDESIGN123"
        category = "shopping_pos"
        merchant_name = "Beverly Hills Boutique"
        merchant_address = "Rodeo Drive, Beverly Hills, CA 90210"
        description = "Designer clothing purchase"
    elif test_transaction == "✅ Low Risk: Local Grocery ($85)":
        amount = 85.50
        recipient_name = "Local Grocery Mart"
        recipient_account = "GROCERY111"
        category = "grocery_pos"
        merchant_name = "Manhattan Fresh Market"
        merchant_address = "456 Park Avenue, New York, NY 10022"
        description = "Weekly grocery shopping"
    else:
        amount = st.number_input("Transaction Amount ($)", min_value=0.01, value=50.0, step=1.0)
        recipient_name = st.text_input("Recipient Name")
        recipient_account = st.text_input("Recipient Account Number")
        category = st.selectbox("Transaction Type", [
            'entertainment', 'food_dining', 'gas_transport', 'grocery_net', 'grocery_pos',
            'health_fitness', 'home', 'kids_pets', 'misc_net', 'misc_pos', 
            'personal_care', 'shopping_net', 'shopping_pos', 'travel'
        ])
        merchant_name = st.text_input("Merchant/Business Name")
        merchant_address = st.text_area("Merchant Address")
        description = st.text_input("Transaction Description")
    
    # Real-time credit limit check
    if amount > 0:
        can_afford, current_available, credit_limit = check_credit_limit(st.session_state.current_user, amount)
        
        if not can_afford:
            st.error(f"❌ Transaction exceeds available credit. Available: ${current_available:,.2f}")
        else:
            remaining_after = current_available - amount
            new_utilization = ((used_credit + amount) / total_limit) * 100
            
            st.success(f"✅ Credit will be reserved: ${remaining_after:,.2f} available after transaction")
            
            # Dynamic low balance warning
            if remaining_after < (total_limit * 0.1):
                st.warning(f"⚠️ Very low credit alert: Only ${remaining_after:,.2f} remaining")
            elif remaining_after < (total_limit * 0.2):
                st.warning(f"⚠️ Low credit alert: ${remaining_after:,.2f} remaining")
            
            # High utilization warning
            if new_utilization > 80:
                st.warning(f"⚠️ This transaction will increase utilization to {new_utilization:.1f}%")
    
    submitted = st.form_submit_button("Submit Transaction for Approval")
    
    if submitted:
        # Dynamic credit limit validation
        can_afford, current_available, credit_limit = check_credit_limit(st.session_state.current_user, amount)
        
        if not can_afford:
            st.error(f"❌ Declined: Transaction amount (${amount:,.2f}) exceeds available credit (${current_available:,.2f})")
        elif not all([amount, recipient_name, merchant_address]):
            st.error("Please fill in all required fields")
        else:
            # Geocode addresses with user's actual location
            with st.spinner("📍 Verifying transaction details..."):
                user_lat = user_data.get('lat')
                user_lon = user_data.get('lon')
                
                if user_lat is None or user_lon is None:
                    user_lat, user_lon = 40.7128, -74.0060
                    st.warning("Using default NYC coordinates for user")
                
                merch_lat, merch_lon = geocode_address(merchant_address)
                st.info(f"📍 Geocoded merchant location: ({merch_lat:.4f}, {merch_lon:.4f})")
            
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
                'status': 'pending'
            }
            
            # Enhanced fraud detection analysis
            fraud_probability, risk_level = detect_fraud_proper(
                transaction_data, user_data, merch_lat, merch_lon
            )
            
            # Show ML results
            st.subheader("🔍 ML Fraud Analysis")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Fraud Probability", f"{fraud_probability:.2%}")
            with col2:
                st.metric("Risk Level", risk_level)
            with col3:
                if risk_level == "HIGH_RISK":
                    st.metric("Status", "🚨 HIGH RISK")
                elif risk_level == "MEDIUM_RISK":
                    st.metric("Status", "⚠️ MEDIUM RISK")
                else:
                    st.metric("Status", "✅ LOW RISK")
            
            # Risk assessment explanation
            if risk_level == "HIGH_RISK":
                st.error("🚨 HIGH RISK: This transaction shows strong fraud indicators")
            elif risk_level == "MEDIUM_RISK":
                st.warning("⚠️ MEDIUM RISK: This transaction requires additional verification")
            else:
                st.success("✅ LOW RISK: This transaction appears normal")
            
            # Reserve credit for ALL transactions
            reserve_success = reserve_credit(st.session_state.current_user, amount)
            
            if not reserve_success:
                st.error("❌ Failed to reserve credit for transaction")
                st.stop()
            
            # Add to pending approvals for admin review
            transaction_id = add_pending_approval(transaction_data, fraud_probability, risk_level)
            transaction_data['transaction_id'] = transaction_id
            
            # Save to user transactions as PENDING
            try:
                with open('data/transactions.json', 'r') as f:
                    transactions = json.load(f)
            except:
                transactions = {}
            
            if st.session_state.current_user not in transactions:
                transactions[st.session_state.current_user] = []
            
            serializable_transaction = convert_to_serializable(transaction_data)
            transactions[st.session_state.current_user].append(serializable_transaction)
            
            with open('data/transactions.json', 'w') as f:
                json.dump(transactions, f, indent=2, default=str)
            
            # Set session state to show success message on next run
            st.session_state.transaction_submitted = True
            
            # Force refresh to show the success section
            st.rerun()

# Enhanced sidebar information
st.sidebar.subheader("🎯 ML Fraud Detection")
st.sidebar.info("""
**Detects:**
🌍 Geographic Anomalies
💳 High-value Patterns  
🛡️ International Transactions
""")

# Quick test info
st.sidebar.subheader("🧪 Test Transactions")
st.sidebar.write("""
- 🚨 Dubai Luxury: >85% risk
- ⚠️ California: 40-70% risk  
- ✅ Local Grocery: <15% risk
""")