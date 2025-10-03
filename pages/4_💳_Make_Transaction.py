# pages/4_💳_Make_Transaction.py - FIXED VERSION
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
    try:
        return joblib.load('best_xgb_model_tuned.joblib')
    except:
        st.info("🔧 Using demo fraud detection mode")
        return None

model = load_model()

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

# Safe authentication check
if not st.session_state.get('user_authenticated', False):
    st.warning("Please login to make a transaction")
    st.page_link("pages/1_👤_User_Login.py", label="Go to Login", icon="🔐")
    st.stop()

user_data = load_user_data()

# Debug: Show current user data
st.sidebar.write("🔍 Debug Info")
st.sidebar.write(f"User: {st.session_state.current_user}")
st.sidebar.write(f"Available Credit: ${user_data.get('total_available_credit', 0):,.2f}")

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

# Regular transaction form (only shows if no recent submission)
with st.form("transaction_form", clear_on_submit=True):
    st.subheader("Payment Details")
    
    amount = st.number_input("Transaction Amount ($)", min_value=0.01, value=50.0, step=1.0)
    
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
    
    col1, col2 = st.columns(2)
    
    with col1:
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
                'status': 'pending'  # ✅ Always start as pending
            }
            
            # Fraud detection analysis
            fraud_probability = 0.1
            risk_level = "LOW_RISK"
            
            if model is not None:
                try:
                    with st.spinner("🛡️ Running security checks..."):
                        input_df = preprocess_transaction(
                            {**transaction_data, 'gender': user_data.get('gender', 'M'), 'card_number': '0000000000000000'},
                            user_lat, user_lon, merch_lat, merch_lon
                        )
                        
                        prediction_proba = model.predict_proba(input_df)
                        fraud_probability = float(prediction_proba[0][1])
                        
                        # Determine risk level
                        if fraud_probability > 0.7:
                            risk_level = "HIGH_RISK"
                        elif fraud_probability > 0.3:
                            risk_level = "MEDIUM_RISK" 
                        else:
                            risk_level = "LOW_RISK"
                except Exception as e:
                    st.warning(f"Using demo mode due to model error: {e}")
            
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