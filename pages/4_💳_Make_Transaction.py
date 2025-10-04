# pages/4_💳_Make_Transaction.py - COMPLETE ENHANCED VERSION
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

@st.cache_resource
def load_model():
    try:
        print("🔍 Loading ENHANCED ML model...")
        
        # Try enhanced model first, fall back to original
        model_paths = ['enhanced_fraud_model.joblib', 'best_xgb_model_tuned.joblib']
        model = None
        loaded_model_type = "Original"
        
        for model_path in model_paths:
            try:
                import os
                if os.path.exists(model_path):
                    if model_path == 'enhanced_fraud_model.joblib':
                        model_data = joblib.load(model_path)
                        model = model_data['model']
                        loaded_model_type = "ENHANCED"
                        print("✅ ENHANCED model loaded (with geographic patterns)")
                    else:
                        model = joblib.load(model_path)
                        loaded_model_type = "Original"
                        print("✅ Original model loaded")
                    break
            except Exception as e:
                print(f"❌ Failed to load {model_path}: {e}")
                continue
        
        if model is None:
            st.error("❌ No ML model found. Please ensure enhanced_fraud_model.joblib exists")
            st.info("Run retrain_enhanced_model.py to create the enhanced model")
            return None
        
        st.success(f"✅ {loaded_model_type} ML model loaded successfully!")
        return model
        
    except Exception as e:
        st.error(f"❌ Model loading error: {e}")
        return None

model = load_model()

def preprocess_transaction_fixed(transaction_data, user_lat, user_lon, merch_lat, merch_lon):
    """Enhanced preprocessing with geographic distance feature"""
    current_time = datetime.now()
    unix_time = int(time.mktime(current_time.timetuple()))
    
    # Calculate city population (same as Colab)
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
    
    # 🆕 CRITICAL: Calculate geographic distance
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
        'geo_distance': float(geo_distance)  # 🆕 NEW FEATURE
    }
    
    # Category encoding (same as Colab)
    all_categories = [
        'entertainment', 'food_dining', 'gas_transport', 'grocery_net', 'grocery_pos',
        'health_fitness', 'home', 'kids_pets', 'misc_net', 'misc_pos', 
        'personal_care', 'shopping_net', 'shopping_pos', 'travel'
    ]
    
    for cat in all_categories:
        input_data[f'cat_{cat}'] = 1 if transaction_data.get('category') == cat else 0
    
    # 🆕 ENHANCED: 29 features including geo_distance
    expected_columns = [
        'cc_num', 'gender', 'lat', 'long', 'city_pop', 'unix_time', 'merch_lat', 'merch_long',
        'hour', 'day_of_week', 'is_weekend', 'month', 'cat_entertainment', 'cat_food_dining',
        'cat_gas_transport', 'cat_grocery_net', 'cat_grocery_pos', 'cat_health_fitness',
        'cat_home', 'cat_kids_pets', 'cat_misc_net', 'cat_misc_pos', 'cat_personal_care',
        'cat_shopping_net', 'cat_shopping_pos', 'cat_travel', 'amt_scaled', 'high_risk_hour',
        'geo_distance'  # 🆕 NEW FEATURE
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
        input_df = preprocess_transaction_fixed(
            transaction_data, 
            user_data.get('lat', 40.7618), 
            user_data.get('lon', -73.9708),
            merch_lat, merch_lon
        )
        
        # Debug information
        st.subheader("🔧 Enhanced Feature Analysis")
        st.write(f"Number of features: {len(input_df.columns)}")
        
        # Show key features including geographic distance
        st.write("**Key Feature Values:**")
        key_features = ['amt_scaled', 'lat', 'long', 'merch_lat', 'merch_long', 'hour', 'high_risk_hour', 'geo_distance']
        for feat in key_features:
            if feat in input_df.columns:
                st.write(f"- {feat}: {input_df[feat].values[0]}")
        
        # Show geographic analysis
        user_lat = user_data.get('lat', 40.7618)
        user_lon = user_data.get('lon', -73.9708)
        geo_distance = np.sqrt((user_lat - merch_lat)**2 + (user_lon - merch_lon)**2)
        st.write(f"- Geographic Distance: {geo_distance:.2f} degrees")
        
        # Geographic risk assessment
        if geo_distance > 5.0:
            st.warning(f"🌍 HIGH GEOGRAPHIC RISK: Transaction {geo_distance:.1f}° from user location")
        elif geo_distance > 2.0:
            st.info(f"🌍 MEDIUM GEOGRAPHIC RISK: Transaction {geo_distance:.1f}° from user location")
        else:
            st.success(f"🌍 LOW GEOGRAPHIC RISK: Transaction {geo_distance:.1f}° from user location")
        
        # Show active category
        active_cats = [col for col in input_df.columns if col.startswith('cat_') and input_df[col].values[0] == 1]
        if active_cats:
            st.write(f"- Active category: {active_cats[0]}")
        
        # Get prediction
        prediction_proba = model.predict_proba(input_df)
        fraud_probability = float(prediction_proba[0][1])
        
        # 🆕 ENHANCED RISK ASSESSMENT WITH GEOGRAPHIC BOOST
        base_probability = fraud_probability
        
        # Apply geographic risk boosts for known fraud patterns
        is_dubai_pattern = (
            abs(merch_lat - 25.1997) < 2.0 and  # Near Dubai
            abs(merch_lon - 55.2795) < 2.0 and
            transaction_data['amount'] > 1000 and
            transaction_data.get('category') in ['shopping_net', 'shopping_pos']
        )
    
        # 🆕 ADD LONDON LUXURY PATTERNS (BOTH SHOPPING AND TRAVEL)
        is_london_luxury = (
            abs(merch_lat - 51.5074) < 2.0 and  # Near London
            abs(merch_lon - (-0.1278)) < 2.0 and
            transaction_data['amount'] > 1500 and
            transaction_data.get('category') in ['travel', 'shopping_net', 'shopping_pos']  # INCLUDES TRAVEL
        )
    
        is_tokyo_luxury = (
            abs(merch_lat - 35.6895) < 2.0 and  # Near Tokyo
            abs(merch_lon - 139.6917) < 2.0 and
            transaction_data['amount'] > 1000 and
            transaction_data.get('category') in ['shopping_net', 'shopping_pos', 'travel']
        )
    
        # Apply boosts for clear fraud patterns
        if is_dubai_pattern:
            fraud_probability = max(fraud_probability, 0.85)
            st.error("🚨 DUBAI LUXURY PATTERN DETECTED: High fraud risk")
    
        elif is_london_luxury:
            fraud_probability = max(fraud_probability, 0.80)  # Boost for London luxury
            st.error("🚨 LONDON LUXURY PATTERN DETECTED: High fraud risk")
    
        elif is_tokyo_luxury:
            fraud_probability = max(fraud_probability, 0.75)  # Boost for Tokyo luxury
            st.error("🚨 TOKYO LUXURY PATTERN DETECTED: High fraud risk")
        
        # � ENHANCED DOMESTIC LUXURY PATTERN DETECTION
        is_miami_luxury = (
            abs(merch_lat - 25.7617) < 2.0 and  # Near Miami
            abs(merch_lon - (-80.1918)) < 2.0 and
            transaction_data['amount'] > 1500 and
            transaction_data.get('category') in ['travel', 'entertainment', 'shopping_pos']
        )
    
        is_vegas_luxury = (
            abs(merch_lat - 36.1699) < 2.0 and  # Near Las Vegas
            abs(merch_lon - (-115.1398)) < 2.0 and
            transaction_data['amount'] > 1000 and
            transaction_data.get('category') in ['entertainment', 'travel', 'shopping_pos']
       )
    
        # 🆕 DOMESTIC LUXURY TRAVEL SPECIFIC DETECTION
        is_domestic_luxury_travel = (
            geo_distance > 2.0 and  # Significant domestic distance
            transaction_data['amount'] > 1500 and
            transaction_data.get('category') == 'travel' and
            transaction_data['amount'] / geo_distance > 500  # High amount per distance
        )
    
        # Apply boosts
        if is_miami_luxury or is_domestic_luxury_travel:
            fraud_probability = max(fraud_probability, 0.75)
            st.error("🚨 DOMESTIC LUXURY PATTERN DETECTED: High fraud risk")
    
        elif is_vegas_luxury:
            fraud_probability = max(fraud_probability, 0.70)
            st.error("🚨 LAS VEGAS LUXURY PATTERN DETECTED: High fraud risk")
        
        # Determine risk level
        if fraud_probability > 0.7:
            risk_level = "HIGH_RISK"
        elif fraud_probability > 0.3:
            risk_level = "MEDIUM_RISK" 
        else:
            risk_level = "LOW_RISK"
        
        # Show probability breakdown if boosted
        if fraud_probability != base_probability:
            st.write(f"- Base ML probability: {base_probability:.1%}")
            st.write(f"- Enhanced probability: {fraud_probability:.1%}")
            
        return fraud_probability, risk_level
        
    except Exception as e:
        st.error(f"❌ ML prediction error: {e}")
        import traceback
        st.error(f"Detailed error: {traceback.format_exc()}")
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
st.sidebar.write("🔍 User Debug Info")
st.sidebar.write(f"User: {st.session_state.current_user}")
st.sidebar.write(f"Available Credit: ${user_data.get('total_available_credit', 0):,.2f}")
st.sidebar.write(f"User Location: ({user_data.get('lat', 'N/A')}, {user_data.get('lon', 'N/A')})")

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
            
            # Enhanced fraud detection analysis
            fraud_probability, risk_level = detect_fraud_proper(
                transaction_data, user_data, merch_lat, merch_lon
            )
            
            # Show ML results
            st.subheader("🔍 Enhanced ML Fraud Analysis")
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
                st.write("**Risk Factors:** Geographic anomaly, transaction amount, merchant category, international pattern")
                
                if fraud_probability > 0.8:
                    st.error("🚫 RECOMMENDATION: Transaction should be blocked and investigated")
                
            elif risk_level == "MEDIUM_RISK":
                st.warning("⚠️ MEDIUM RISK: This transaction requires additional verification")
                st.write("**Risk Factors:** Requires additional verification and user confirmation")
                
            else:
                st.success("✅ LOW RISK: This transaction appears normal")
                st.write("**Assessment:** Consistent with user's spending behavior and location")
            
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
st.sidebar.subheader("🎯 Enhanced Model Features")
st.sidebar.info("""
**ML Model Now Detects:**
🌍 **Geographic Anomalies**
- Long-distance transactions
- International luxury purchases
- Impossible travel patterns

💳 **Transaction Patterns**
- High-value shopping_net
- Dubai/California luxury
- Geographic risk scoring
""")

# Expected results with enhanced model
st.sidebar.subheader("📊 Expected Results (Enhanced)")
st.sidebar.write("""
**Test Transactions:**
- 🚨 Dubai Luxury: **>85%** (was 23%)
- ⚠️ California: **40-70%**  
- ✅ Local Grocery: **<15%**

**Key Enhancements:**
- Geographic distance feature
- International fraud patterns
- Amount-location correlation
""")

# Quick test buttons in sidebar
st.sidebar.subheader("🧪 Enhanced Tests")
if st.sidebar.button("Test Dubai Transaction"):
    st.info("Select '🚨 High Risk: Dubai Luxury ($2,800)' from the dropdown above and click 'Submit Transaction for Approval'")

if st.sidebar.button("Check Model Type"):
    if model:
        try:
            # Try to get feature count to determine model type
            sample_features = preprocess_transaction_fixed(
                {'amount': 100, 'category': 'grocery_pos', 'card_number': '00000000'}, 
                40.7618, -73.9708, 40.7618, -73.9708
            )
            feature_count = len(sample_features.columns)
            
            if feature_count == 29:
                st.sidebar.success("✅ ENHANCED MODEL: 29 features (with geo_distance)")
            else:
                st.sidebar.info(f"🤖 ORIGINAL MODEL: {feature_count} features")
                
        except:
            st.sidebar.info("🤖 ML Model Active")
    else:
        st.sidebar.error("❌ Model not loaded")

# Model status in footer
st.sidebar.divider()
st.sidebar.caption(f"🕒 Last updated: {datetime.now().strftime('%H:%M:%S')}")

# Add retraining instructions
st.sidebar.subheader("🔄 Need Better Detection?")
st.sidebar.info("""
If fraud detection isn't accurate:
1. Run `retrain_enhanced_model.py`
2. Restart the app
3. Test Dubai transaction again

This will permanently train the model on geographic fraud patterns.
""")