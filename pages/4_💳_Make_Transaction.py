# pages/4_💳_Make_Transaction.py - COMPLETE UPDATED VERSION WITH HYBRID SYSTEM
import streamlit as st
import json
import pandas as pd
import numpy as np
from datetime import datetime
import time
from utils.helpers import geocode_address, add_pending_approval, convert_to_serializable, create_fraud_alert, send_real_time_alert

from utils.session_utils import initialize_session_state
initialize_session_state()

st.title("💳 Make New Transaction")

# 🆕 HYBRID SYSTEM IMPORT
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
    """Reserve credit for pending transaction - DON'T deduct yet"""
    try:
        # Read current users data
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
        
        # ✅ ONLY RESERVE CREDIT, DON'T DEDUCT YET
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

# 🆕 SIMPLIFIED FRAUD DETECTION WITH HYBRID SYSTEM
def detect_fraud_proper(transaction_data, user_data, merch_lat, merch_lon):
    """Enhanced fraud detection using hybrid model system"""
    st.subheader("🔍 Hybrid ML Fraud Analysis")
    
    try:
        # Use the hybrid prediction system
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
        
        # Enhanced risk assessment explanation
        if risk_level == "HIGH_RISK":
            st.error("🚨 HIGH RISK: This transaction shows strong fraud indicators")
            
            if fraud_probability > 0.9:
                st.error("🚫 CRITICAL: Transaction shows clear fraud patterns - recommend immediate block")
            elif fraud_probability > 0.7:
                st.error("🚫 HIGH CONFIDENCE: Strong fraud indicators - recommend block")
            else:
                st.warning("⚠️ SUSPICIOUS: Multiple risk factors detected - requires manual review")
                
        elif risk_level == "MEDIUM_RISK":
            st.warning("⚠️ MEDIUM RISK: This transaction requires additional verification")
            st.write("**Recommendation:** Additional user verification recommended")
            
        else:
            st.success("✅ LOW RISK: This transaction appears normal")
            st.write("**Assessment:** Consistent with expected spending patterns")
        
        return fraud_probability, risk_level
        
    except Exception as e:
        st.error(f"❌ Hybrid prediction error: {e}")
        # Fallback to 5% if hybrid system fails
        return 0.05, "LOW_RISK"

# Safe authentication check
if not st.session_state.get('user_authenticated', False):
    st.warning("Please login to make a transaction")
    st.page_link("pages/1_👤_User_Login.py", label="Go to Login", icon="🔐")
    st.stop()

user_data = load_user_data()

# Enhanced sidebar information
st.sidebar.subheader("🎯 Hybrid Model System")
st.sidebar.info("""
**🤖 Dual Model Intelligence:**
🇱🇰 **Sri Lanka Model**
- Local transaction patterns
- Sri Lanka geographic context
- Regional spending behavior

🌍 **Original Model** 
- International fraud patterns
- Global fraud detection
- Established risk patterns

**🔍 Smart Selection:**
- Automatically chooses best model
- Context-aware predictions
- Geographic intelligence
""")

# Model status in sidebar
st.sidebar.subheader("🔍 System Status")
st.sidebar.success("✅ Hybrid System Active")
st.sidebar.info("🤖 Using both Sri Lanka & Original models")

# Quick test instructions
st.sidebar.subheader("🧪 Test Transactions")
st.sidebar.info("""
**For Testing:**
- 🇱🇰 **Local Sri Lanka**: Should show LOW risk
- 🌍 **International**: Should show appropriate risk
- 🚨 **Dubai Luxury**: Should show HIGH risk
""")

# Check if we just submitted a transaction (using session state)
if st.session_state.get('transaction_submitted', False):
    # Show success message that persists
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
    
    # Navigation options OUTSIDE the form
    st.info("💡 You can check the status of this transaction in 'My Transactions' section.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Make Another Transaction", use_container_width=True):
            # Clear the submission flag and refresh
            st.session_state.transaction_submitted = False
            st.rerun()
    with col2:
        st.page_link("pages/5_📊_My_Transactions.py", 
                    label="📊 View My Transactions", 
                    use_container_width=True)
    
    # Stop execution here to prevent showing the form again
    st.stop()

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

# Regular transaction form (only shows if no recent submission)
with st.form("transaction_form", clear_on_submit=True):
    st.subheader("Payment Details")
    
    # Pre-filled test transactions for quick testing
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
                    user_lat, user_lon = 6.9271, 79.8612  # Default Colombo coordinates
                    st.warning("Using default Colombo coordinates for user")
                
                merch_lat, merch_lon = geocode_address(merchant_address)
                st.info(f"📍 Geocoded merchant location: ({merch_lat:.4f}, {merch_lon:.4f})")
                
                # Show geographic analysis
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
            
            # 🆕 ENHANCED FRAUD DETECTION WITH HYBRID SYSTEM
            fraud_probability, risk_level = detect_fraud_proper(
                transaction_data, user_data, merch_lat, merch_lon
            )
            
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

# Add user location debug to sidebar
st.sidebar.subheader("🔍 User Location Debug")
st.sidebar.write(f"**Username:** {st.session_state.current_user}")
st.sidebar.write(f"**Stored Lat:** {user_data.get('lat', 'Not set')}")
st.sidebar.write(f"**Stored Lon:** {user_data.get('lon', 'Not set')}")

# Add a button to check user data
if st.sidebar.button("Check User Data"):
    st.sidebar.write("**Full User Data:**")
    st.sidebar.json(user_data)

# Model file check in sidebar
import os

st.sidebar.subheader("🔍 Model File Check")
model_files = [
    'enhanced_fraud_model.joblib',
    'models/sri_lanka_wide_model.joblib',
    'models/deployment_model.joblib', 
    'models/fallback_model.joblib'
]

for model_file in model_files:
    exists = os.path.exists(model_file)
    status = "✅ EXISTS" if exists else "❌ MISSING"
    st.sidebar.write(f"{status} {model_file}")

if st.sidebar.button("Check All Model Files"):
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.joblib'):
                st.sidebar.write(f"📁 {os.path.join(root, file)}")

# Expected results with hybrid system
st.sidebar.subheader("📊 Expected Results")
st.sidebar.write("""
**Test Transactions:**
- 🇱🇰 Local Grocery: **<10%** (LOW RISK)
- 🌍 Inter-city Travel: **<15%** (LOW RISK)  
- 🚨 Dubai Luxury: **>90%** (HIGH RISK)
- ⚠️ Card Testing: **>90%** (HIGH RISK)
""")

# Model status in footer
st.sidebar.divider()
st.sidebar.caption(f"🕒 Last updated: {datetime.now().strftime('%H:%M:%S')}")

# Add hybrid system explanation
st.sidebar.subheader("🤖 How Hybrid System Works")
st.sidebar.info("""
**Smart Model Selection:**
- 🇱🇰 **Sri Lanka Model**: Local transactions
- 🌍 **Original Model**: International transactions  
- 🔍 **Context-Aware**: Automatically chooses best model

**Benefits:**
- ✅ Accurate local risk assessment
- ✅ Strong international fraud detection
- ✅ No manual configuration needed
""")