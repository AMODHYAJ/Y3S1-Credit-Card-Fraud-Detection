import streamlit as st
import json
import pandas as pd
import numpy as np
from datetime import datetime
import time
from utils.helpers import geocode_address, add_pending_approval, convert_to_serializable, create_fraud_alert

from utils.session_utils import initialize_session_state
initialize_session_state()

st.title("💳 Make New Transaction")

# Hybrid system import
from hybrid_model_manager import get_hybrid_prediction

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
        
        if transaction_amount > current_available:
            st.error(f"Insufficient credit: ${current_available} available, ${transaction_amount} requested")
            return False
        
        user['total_available_credit'] = current_available - transaction_amount
        user['total_current_balance'] = user.get('total_current_balance', 0) + transaction_amount
        
        if 'credit_cards' in user and 'primary' in user['credit_cards']:
            card = user['credit_cards']['primary']
            card_available = card.get('available_balance', current_available)
            card['available_balance'] = card_available - transaction_amount
            card['current_balance'] = card.get('current_balance', 0) + transaction_amount
        
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

def detect_fraud_proper(transaction_data, user_data, merch_lat, merch_lon):
    """Enhanced fraud detection using balanced hybrid system"""
    st.subheader("🔍 Balanced Hybrid ML Fraud Analysis")
    
    try:
        # Use the balanced hybrid prediction system
        fraud_probability, risk_level = get_hybrid_prediction(
            transaction_data,
            user_data,
            merch_lat,
            merch_lon
        )
        
        # Display results
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
        
        return fraud_probability, risk_level
        
    except Exception as e:
        st.error(f"❌ Hybrid prediction error: {e}")
        return 0.05, "LOW_RISK"

# Safe authentication check
if not st.session_state.get('user_authenticated', False):
    st.warning("Please login to make a transaction")
    st.page_link("pages/1_👤_User_Login.py", label="Go to Login", icon="🔐")
    st.stop()

user_data = load_user_data()

# Balanced sidebar information
st.sidebar.subheader("⚖️ Balanced Hybrid System")
st.sidebar.info("""
**Fair Model Selection:**
- 🇱🇰 **Sri Lanka Model**: Local patterns & regional context
- 🌍 **Original Model**: Global patterns & international fraud  
- **Balanced Weights**: No geographic bias

**Weighting Strategy:**
- Local Sri Lanka: 70% Sri Lanka / 30% Original
- Mixed locations: 50% / 50% balanced
- International: 80% Original / 20% Sri Lanka
""")

# Model status in sidebar
st.sidebar.subheader("🔍 System Status")
st.sidebar.success("✅ Balanced Hybrid System Active")
st.sidebar.info("⚖️ Using fair model weighting")

# Check if we just submitted a transaction
if st.session_state.get('transaction_submitted', False):
    st.success("""
    ✅ **Transaction Submitted for Approval**
    
    Your transaction has been received and is pending admin approval.
    Credit has been temporarily reserved for this transaction.
    """)
    
    updated_user_data = load_user_data()
    new_available = updated_user_data.get('total_available_credit', 0)
    st.info(f"**Available Credit (Reserved):** ${new_available:,.2f}")
    
    st.info("💡 You can check the status of this transaction in 'My Transactions' section.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Make Another Transaction", width='stretch'):
            st.session_state.transaction_submitted = False
            st.rerun()
    with col2:
        st.page_link("pages/5_📊_My_Transactions.py", label="📊 View My Transactions", width='stretch')
    
    st.stop()

# Credit information
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

# Credit utilization warning
if total_limit > 0:
    if utilization > 80:
        st.error(f"🚨 High Credit Utilization: {utilization:.1f}% - Consider paying down your balance")
    elif utilization > 50:
        st.warning(f"⚠️ Moderate Credit Utilization: {utilization:.1f}%")

# Transaction form
with st.form("transaction_form", clear_on_submit=True):
    st.subheader("Payment Details")
    
    test_transaction = st.selectbox("Quick Test Transactions", 
                                   ["Custom Transaction", 
                                    "🇱🇰 Low Risk: Local Grocery ($25)",
                                    "🌍 Medium Risk: Colombo to Galle Travel ($80)",
                                    "🚨 High Risk: Dubai Luxury ($2,800)",
                                    "⚠️ High Risk: Local Card Testing ($2)"])
    
    if test_transaction == "🇱🇰 Low Risk: Local Grocery ($25)":
        amount = 25.00
        recipient_name = "Cargills Food City"
        recipient_account = "CARGILLS123"
        category = "grocery_pos"
        merchant_name = "Cargills Supermarket"
        merchant_address = "123 Galle Road, Colombo, Sri Lanka"
        description = "Weekly grocery shopping"
    elif test_transaction == "🌍 Medium Risk: Colombo to Galle Travel ($80)":
        amount = 80.00
        recipient_name = "Sri Lanka Transport Board"
        recipient_account = "SLTB456"
        category = "travel"
        merchant_name = "Intercity Bus Service"
        merchant_address = "Colombo Fort, Colombo, Sri Lanka"
        description = "Bus ticket to Galle"
    elif test_transaction == "🚨 High Risk: Dubai Luxury ($2,800)":
        amount = 2800.00
        recipient_name = "Luxury Watches Dubai"
        recipient_account = "DUBAI12345"
        category = "shopping_net"
        merchant_name = "Dubai Luxury Timepieces"
        merchant_address = "Dubai Mall, Financial Center Rd, Dubai, UAE"
        description = "Rolex watch purchase"
    elif test_transaction == "⚠️ High Risk: Local Card Testing ($2)":
        amount = 2.00
        recipient_name = "Quick Mart"
        recipient_account = "QM789"
        category = "grocery_pos"
        merchant_name = "24 Hour Convenience Store"
        merchant_address = "Colombo City Center, Sri Lanka"
        description = "Small purchase"
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
            st.success(f"✅ Credit will be reserved: ${remaining_after:,.2f} available after transaction")
    
    submitted = st.form_submit_button("Submit Transaction for Approval")
    
    if submitted:
        can_afford, current_available, credit_limit = check_credit_limit(st.session_state.current_user, amount)
        
        if not can_afford:
            st.error(f"❌ Declined: Transaction amount (${amount:,.2f}) exceeds available credit (${current_available:,.2f})")
        elif not all([amount, recipient_name, merchant_address]):
            st.error("Please fill in all required fields")
        else:
            # Enhanced location detection
            with st.spinner("📍 Verifying transaction details with balanced location detection..."):
                user_lat = user_data.get('lat')
                user_lon = user_data.get('lon')
                
                if user_lat is None or user_lon is None:
                    user_address = user_data.get('address', '')
                    if user_address:
                        user_lat, user_lon = geocode_address(user_address)
                        st.info(f"📍 Detected user location from address: ({user_lat:.4f}, {user_lon:.4f})")
                    else:
                        user_lat, user_lon = 40.7128, -74.0060  # Default international
                        st.warning("Using default international coordinates for user")
                
                merch_lat, merch_lon = geocode_address(merchant_address)
                
                # Show balanced model selection info
                from hybrid_model_manager import HybridModelManager
                manager = HybridModelManager()
                is_sri_lanka_user = manager.is_in_sri_lanka(user_lat, user_lon)
                is_sri_lanka_merchant = manager.is_in_sri_lanka(merch_lat, merch_lon)
                
                if is_sri_lanka_user and is_sri_lanka_merchant:
                    st.success("🇱🇰 Local Sri Lanka transaction: Balanced hybrid approach (70% Sri Lanka model)")
                elif is_sri_lanka_user and not is_sri_lanka_merchant:
                    st.info("🌍 Mixed transaction: Equal weighting (50% Sri Lanka + 50% Original models)")
                elif not is_sri_lanka_user and is_sri_lanka_merchant:
                    st.info("🌍 Mixed transaction: Equal weighting (50% Original + 50% Sri Lanka models)")
                else:
                    st.info("🌐 International transaction: Original model focus (80% Original + 20% Sri Lanka)")
                
                geo_distance = np.sqrt((user_lat - merch_lat)**2 + (user_lon - merch_lon)**2)
                st.info(f"🌍 Geographic distance: {geo_distance:.2f} degrees from your location")
            
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
            
            # Balanced fraud detection
            fraud_probability, risk_level = detect_fraud_proper(
                transaction_data, user_data, merch_lat, merch_lon
            )
            
            # Reserve credit
            reserve_success = reserve_credit(st.session_state.current_user, amount)
            
            if not reserve_success:
                st.error("❌ Failed to reserve credit for transaction")
                st.stop()
            
            # Add to pending approvals
            transaction_id = add_pending_approval(transaction_data, fraud_probability, risk_level)
            transaction_data['transaction_id'] = transaction_id
            
            # Save to user transactions
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
            
            st.session_state.transaction_submitted = True
            st.rerun()

# Location debug
st.sidebar.subheader("🔍 Location Debug")
st.sidebar.write(f"**Username:** {st.session_state.current_user}")
st.sidebar.write(f"**User Lat/Lon:** {user_data.get('lat', 'Not set')} / {user_data.get('lon', 'Not set')}")

# Model file check
import os
st.sidebar.subheader("🔍 Model File Check")
model_files = [
    'enhanced_fraud_model.joblib',
    'models/sri_lanka_wide_model.joblib'
]

for model_file in model_files:
    exists = os.path.exists(model_file)
    status = "✅ EXISTS" if exists else "❌ MISSING"
    st.sidebar.write(f"{status} {model_file}")

# Expected results
st.sidebar.subheader("📊 Expected Results")
st.sidebar.write("""
**Balanced Testing:**
- 🇱🇰 Local Grocery: **<10%** (LOW RISK)
- 🌍 Inter-city Travel: **<15%** (LOW RISK)  
- 🚨 Dubai Luxury: **>90%** (HIGH RISK)
- ⚠️ Card Testing: **>90%** (HIGH RISK)
""")

# Footer
st.sidebar.divider()
st.sidebar.caption(f"🕒 Last updated: {datetime.now().strftime('%H:%M:%S')}")