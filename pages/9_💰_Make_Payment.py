import streamlit as st
import json
from datetime import datetime, timedelta
from utils.session_utils import initialize_session_state

initialize_session_state()

st.title("💰 Make Payment")

def load_user_data():
    """Load user data from JSON file"""
    try:
        with open('data/users.json', 'r') as f:
            users = json.load(f)
        return users.get(st.session_state.current_user, {})
    except Exception as e:
        st.error(f"Error loading user data: {e}")
        return {}

def load_user_transactions():
    """Load user transactions"""
    try:
        with open('data/transactions.json', 'r') as f:
            transactions = json.load(f)
        return transactions.get(st.session_state.current_user, [])
    except:
        return []

def process_payment(user_id, payment_amount, payment_method):
    """Process payment and update user balances"""
    try:
        # Read current users data
        with open('data/users.json', 'r') as f:
            users = json.load(f)
        
        if user_id not in users:
            st.error("User not found")
            return False
        
        user = users[user_id]
        current_balance = user.get('total_current_balance', 0)
        credit_limit = user.get('total_credit_limit', 0)
        
        # Validate payment amount
        if payment_amount <= 0:
            st.error("Payment amount must be greater than 0")
            return False
        
        if payment_amount > current_balance:
            st.error(f"Payment amount (${payment_amount:,.2f}) cannot exceed current balance (${current_balance:,.2f})")
            return False
        
        # Update user balances
        user['total_current_balance'] = current_balance - payment_amount
        user['total_available_credit'] = user.get('total_available_credit', 0) + payment_amount
        
        # Update primary card balance
        if 'credit_cards' in user and 'primary' in user['credit_cards']:
            card = user['credit_cards']['primary']
            card['current_balance'] = max(0, card.get('current_balance', 0) - payment_amount)
            card['available_balance'] = card.get('available_balance', 0) + payment_amount
        
        # Calculate new utilization
        new_balance = user['total_current_balance']
        utilization = (new_balance / credit_limit * 100) if credit_limit > 0 else 0
        
        # Write back to file
        with open('data/users.json', 'w') as f:
            json.dump(users, f, indent=2, default=str)
        
        # Record payment transaction
        record_payment_transaction(user_id, payment_amount, payment_method, new_balance, utilization)
        
        return True
        
    except Exception as e:
        st.error(f"Error processing payment: {e}")
        return False

def record_payment_transaction(user_id, amount, method, new_balance, utilization):
    """Record payment as a transaction"""
    try:
        with open('data/transactions.json', 'r') as f:
            transactions = json.load(f)
    except:
        transactions = {}
    
    if user_id not in transactions:
        transactions[user_id] = []
    
    payment_data = {
        'transaction_id': f"PAY{int(datetime.now().timestamp())}",
        'user_id': user_id,
        'amount': -amount,  # Negative amount indicates payment
        'recipient_name': 'SecureBank Credit Card',
        'recipient_account': 'CREDIT CARD PAYMENT',
        'category': 'payment',
        'merchant_name': 'SecureBank Payment',
        'merchant_address': 'Digital Payment Processing',
        'description': f'Credit card payment via {method}',
        'user_lat': None,
        'user_lon': None,
        'merch_lat': None,
        'merch_lon': None,
        'submitted_at': str(datetime.now()),
        'status': 'approved',
        'payment_method': method,
        'new_balance': new_balance,
        'utilization_after': utilization,
        'type': 'payment'
    }
    
    transactions[user_id].append(payment_data)
    
    with open('data/transactions.json', 'w') as f:
        json.dump(transactions, f, indent=2, default=str)

def get_payment_history(user_id):
    """Get user's payment history"""
    transactions = load_user_transactions()
    payments = [t for t in transactions if t.get('type') == 'payment']
    return sorted(payments, key=lambda x: x.get('submitted_at', ''), reverse=True)

# Safe authentication check
if not st.session_state.get('user_authenticated', False):
    st.warning("Please login to make a payment")
    st.page_link("pages/1_👤_User_Login.py", label="Go to Login", icon="🔐")
    st.stop()

user_data = load_user_data()

# Current balance information
st.subheader("💳 Current Account Status")

current_balance = user_data.get('total_current_balance', 0)
credit_limit = user_data.get('total_credit_limit', 0)
available_credit = user_data.get('total_available_credit', 0)
utilization = (current_balance / credit_limit * 100) if credit_limit > 0 else 0

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Current Balance", f"${current_balance:,.2f}")

with col2:
    st.metric("Credit Limit", f"${credit_limit:,.2f}")

with col3:
    st.metric("Available Credit", f"${available_credit:,.2f}")

with col4:
    st.metric("Utilization", f"{utilization:.1f}%")

# Utilization warning
if utilization > 80:
    st.error(f"🚨 High Credit Utilization: {utilization:.1f}% - Consider paying down your balance")
elif utilization > 50:
    st.warning(f"⚠️ Moderate Credit Utilization: {utilization:.1f}% - Making a payment can improve your credit score")

# Quick Payment Options (OUTSIDE ANY FORM)
st.subheader("💸 Quick Payment Options")

min_payment = max(current_balance * 0.03, 25.00)
suggested_payments = [
    min_payment,
    current_balance * 0.1,  # 10% of balance
    current_balance * 0.25, # 25% of balance
    current_balance         # Full balance
]

quick_col1, quick_col2, quick_col3, quick_col4 = st.columns(4)

with quick_col1:
    if st.button(f"Min Payment\n${min_payment:,.0f}", width='stretch', help="Pay the minimum required amount"):
        st.session_state.quick_pay_amount = min_payment
        st.session_state.show_payment_form = True
        st.rerun()

with quick_col2:
    ten_percent = suggested_payments[1]
    if st.button(f"10% of Balance\n${ten_percent:,.0f}", width='stretch', help="Pay 10% of your current balance"):
        st.session_state.quick_pay_amount = ten_percent
        st.session_state.show_payment_form = True
        st.rerun()

with quick_col3:
    twenty_five_percent = suggested_payments[2]
    if st.button(f"25% of Balance\n${twenty_five_percent:,.0f}", width='stretch', help="Pay 25% of your current balance"):
        st.session_state.quick_pay_amount = twenty_five_percent
        st.session_state.show_payment_form = True
        st.rerun()

with quick_col4:
    if st.button(f"Full Balance\n${current_balance:,.0f}", width='stretch', help="Pay off your entire balance"):
        st.session_state.quick_pay_amount = current_balance
        st.session_state.show_payment_form = True
        st.rerun()

# Initialize session state for payment form
if 'show_payment_form' not in st.session_state:
    st.session_state.show_payment_form = False
if 'quick_pay_amount' not in st.session_state:
    st.session_state.quick_pay_amount = min_payment

# Show payment form when a quick pay option is selected or manually
if st.session_state.show_payment_form:
    st.subheader("📋 Payment Details")
    
    # Custom payment button (OUTSIDE FORM)
    if st.button("← Back to Quick Options"):
        st.session_state.show_payment_form = False
        st.rerun()
    
    with st.form("payment_form"):
        # Pre-fill amount if quick pay was selected
        default_amount = st.session_state.quick_pay_amount
        
        col1, col2 = st.columns(2)
        
        with col1:
            payment_amount = st.number_input(
                "Payment Amount ($)",
                min_value=0.01,
                max_value=float(current_balance),
                value=float(default_amount),
                step=10.0,
                key="payment_amount_input"
            )
        
        with col2:
            payment_method = st.selectbox(
                "Payment Method",
                ["Bank Transfer", "Debit Card", "Savings Account", "External Account"],
                key="payment_method_select"
            )
            
            payment_date = st.date_input(
                "Payment Date",
                value=datetime.now().date(),
                min_value=datetime.now().date(),
                max_value=datetime.now().date() + timedelta(days=30),
                key="payment_date_input"
            )
        
        # Payment summary
        st.write("### Payment Summary")
        
        if payment_amount > 0:
            new_balance = current_balance - payment_amount
            new_utilization = (new_balance / credit_limit * 100) if credit_limit > 0 else 0
            
            summary_col1, summary_col2 = st.columns(2)
            
            with summary_col1:
                st.write(f"**Payment Amount:** ${payment_amount:,.2f}")
                st.write(f"**Current Balance:** ${current_balance:,.2f}")
                st.write(f"**New Balance:** ${new_balance:,.2f}")
            
            with summary_col2:
                st.write(f"**Current Utilization:** {utilization:.1f}%")
                st.write(f"**New Utilization:** {new_utilization:,.1f}%")
                
                # Utilization improvement message
                if new_utilization < utilization:
                    improvement = utilization - new_utilization
                    st.success(f"✅ Utilization will decrease by {improvement:.1f}%")
                
                if new_utilization < 30:
                    st.success("🎉 Excellent! Your utilization will be in the healthy range (<30%)")
        
        # Terms and submission
        terms_accepted = st.checkbox("I authorize SecureBank to process this payment from my selected payment method")
        
        # Use form_submit_button instead of regular button
        submitted = st.form_submit_button("Process Payment")
        
        if submitted:
            if not terms_accepted:
                st.error("Please accept the authorization to process your payment")
            elif payment_amount <= 0:
                st.error("Please enter a valid payment amount")
            else:
                with st.spinner("Processing your payment..."):
                    success = process_payment(
                        st.session_state.current_user, 
                        payment_amount, 
                        payment_method
                    )
                    
                    if success:
                        st.success(f"✅ Payment of ${payment_amount:,.2f} processed successfully!")
                        st.balloons()
                        
                        # Show updated balance
                        updated_user_data = load_user_data()
                        new_balance = updated_user_data.get('total_current_balance', 0)
                        new_available = updated_user_data.get('total_available_credit', 0)
                        new_utilization = (new_balance / credit_limit * 100) if credit_limit > 0 else 0
                        
                        st.info(f"""
                        **Updated Account Status:**
                        - **New Balance:** ${new_balance:,.2f}
                        - **Available Credit:** ${new_available:,.2f}
                        - **Credit Utilization:** {new_utilization:.1f}%
                        """)
                        
                        # Show improvement message
                        if new_utilization < 30:
                            st.success("🎉 Your credit utilization is now in the excellent range!")
                        elif new_utilization < 50:
                            st.success("👍 Your credit utilization is now in the good range!")
                        
                        # Reset form state
                        st.session_state.show_payment_form = False
                        if hasattr(st.session_state, 'quick_pay_amount'):
                            del st.session_state.quick_pay_amount
                        
                        # Store success state to show navigation options
                        st.session_state.payment_success = True

# Show navigation options after successful payment (OUTSIDE FORM)
if st.session_state.get('payment_success', False):
    st.write("---")
    st.write("### What would you like to do next?")
    nav_col1, nav_col2 = st.columns(2)
    with nav_col1:
        if st.button("Make Another Payment", key="another_payment", width='stretch'):
            st.session_state.show_payment_form = True
            st.session_state.payment_success = False
            st.rerun()
    with nav_col2:
        if st.button("Return to Dashboard", key="return_dashboard", width='stretch'):
            st.session_state.payment_success = False
            st.switch_page("pages/3_🏠_User_Dashboard.py")

# Show custom payment option if no form is shown
elif not st.session_state.show_payment_form and not st.session_state.get('payment_success', False):
    if st.button("Custom Payment Amount", width='stretch'):
        st.session_state.show_payment_form = True
        st.session_state.quick_pay_amount = min_payment
        st.rerun()

# Payment history (ALWAYS SHOW - OUTSIDE ANY FORM)
st.subheader("📋 Recent Payment History")

payment_history = get_payment_history(st.session_state.current_user)

if not payment_history:
    st.info("No payment history found. Make your first payment above!")
else:
    for payment in payment_history[:5]:  # Show last 5 payments
        with st.expander(f"💰 ${abs(payment['amount']):,.2f} - {payment['submitted_at'][:16]}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Payment ID:** {payment['transaction_id']}")
                st.write(f"**Amount:** ${abs(payment['amount']):,.2f}")
                st.write(f"**Method:** {payment.get('payment_method', 'N/A')}")
                
            with col2:
                st.write(f"**Date:** {payment['submitted_at'][:16]}")
                st.write(f"**New Balance:** ${payment.get('new_balance', 0):,.2f}")
                st.write(f"**Utilization After:** {payment.get('utilization_after', 0):.1f}%")

# Help section
st.sidebar.header("💡 Payment Tips")
st.sidebar.write("""
**Smart Payment Strategies:**
- Pay more than the minimum to reduce interest
- Keep utilization below 30% for best credit scores
- Set up automatic payments to avoid missed payments
- Make multiple payments throughout the month

**Benefits of Low Utilization:**
- Better credit scores
- Lower interest rates
- Higher credit limit increases
- Improved financial health
""")

# Footer
st.divider()
st.caption(f"SecureBank Payment Portal • Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")