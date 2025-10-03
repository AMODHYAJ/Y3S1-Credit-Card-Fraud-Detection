# pages/2_📝_User_Register.py - UPDATED
import streamlit as st
import json
import os
from datetime import datetime, date
from utils.helpers import geocode_address

from utils.session_utils import initialize_session_state
initialize_session_state()

st.title("📝 Open New Bank Account")

def load_users():
    try:
        with open('data/users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_user(username, user_data):
    users = load_users()
    users[username] = user_data
    with open('data/users.json', 'w') as f:
        json.dump(users, f, indent=2)

def calculate_age(born):
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))

def is_valid_dob(dob):
    """Validate date of birth - must be at least 18 years old and not in the future"""
    today = date.today()
    age = calculate_age(dob)
    
    if dob > today:
        return False, "Date of birth cannot be in the future"
    
    if age < 18:
        return False, "You must be at least 18 years old to open an account"
    
    if age > 120:
        return False, "Please enter a valid date of birth"
    
    return True, "Valid"

def calculate_credit_limit(age, income=None):
    """Calculate credit limit based on age and other factors"""
    # Base credit limit
    if age < 25:
        base_limit = 2000.00
    elif age < 35:
        base_limit = 5000.00
    elif age < 50:
        base_limit = 10000.00
    else:
        base_limit = 8000.00
    
    return base_limit

with st.form("registration_form"):
    st.subheader("Personal Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        full_name = st.text_input("Full Name")
        email = st.text_input("Email Address")
        phone = st.text_input("Phone Number")
        
        min_date = date(1900, 1, 1)
        max_date = date.today()
        default_dob = date(date.today().year - 30, 1, 1)
        
        dob = st.date_input(
            "Date of Birth",
            value=default_dob,
            min_value=min_date,
            max_value=max_date,
            format="YYYY-MM-DD"
        )
    
    with col2:
        username = st.text_input("Choose Username")
        password = st.text_input("Choose Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        gender = st.selectbox("Gender", ["M", "F"])
        id_number = st.text_input("Government ID Number")
        monthly_income = st.number_input("Monthly Income ($)", min_value=0, value=3000, step=500)
    
    st.subheader("Residential Address")
    address = st.text_area("Permanent Address", 
                          placeholder="Enter your complete residential address including city, state, and zip code")
    
    terms_accepted = st.checkbox("I agree to the terms and conditions and privacy policy")
    
    submitted = st.form_submit_button("Open Account")
    
    if submitted:
        errors = []
        
        if not all([full_name, email, username, password, address, id_number]):
            errors.append("Please fill in all required fields")
        
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        if len(password) < 6:
            errors.append("Password must be at least 6 characters long")
        
        is_valid, dob_error = is_valid_dob(dob)
        if not is_valid:
            errors.append(dob_error)
        
        if not terms_accepted:
            errors.append("You must accept the terms and conditions")
        
        users = load_users()
        if username in users:
            errors.append("Username already exists. Please choose a different username.")
        
        if "@" not in email or "." not in email:
            errors.append("Please enter a valid email address")
        
        if errors:
            for error in errors:
                st.error(error)
        else:
            with st.spinner("Verifying your address..."):
                lat, lon = geocode_address(address)
            
            age = calculate_age(dob)
            
            # DYNAMIC CREDIT LIMIT CALCULATION
            credit_limit = calculate_credit_limit(age, monthly_income)
            available_credit = credit_limit
            
            user_data = {
                'full_name': full_name,
                'email': email,
                'phone': phone,
                'password': password,
                'gender': gender,
                'dob': str(dob),
                'age': age,
                'monthly_income': monthly_income,
                'id_number': id_number,
                'address': address,
                'lat': lat,
                'lon': lon,
                'account_created': str(datetime.now()),
                'account_status': 'active',
                'credit_cards': {
                    'primary': {
                        'last_four': '0000',
                        'card_type': 'Visa',
                        'credit_limit': credit_limit,
                        'available_balance': available_credit,
                        'current_balance': 0.00,
                        'min_payment': 0.00,
                        'payment_due_date': str(date.today().replace(day=15)),
                        'is_active': True
                    }
                },
                'total_credit_limit': credit_limit,
                'total_available_credit': available_credit,
                'total_current_balance': 0.00,
                'terms_accepted': True,
                'terms_accepted_at': str(datetime.now())
            }
            
            save_user(username, user_data)
            
            st.success("🎉 Account created successfully! You can now login.")
            st.info(f"""
            **Account Details:**
            - **Name:** {full_name}
            - **Age:** {age} years
            - **Monthly Income:** ${monthly_income:,.2f}
            - **Credit Limit:** ${credit_limit:,.2f}
            - **Available Credit:** ${available_credit:,.2f}
            """)
            
            st.balloons()
            st.page_link("pages/1_👤_User_Login.py", label="Proceed to Login", icon="🔐")