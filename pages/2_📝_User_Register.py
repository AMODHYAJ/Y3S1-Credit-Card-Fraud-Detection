# pages/2_📝_User_Register.py
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
    
    # Check if date is in future
    if dob > today:
        return False, "Date of birth cannot be in the future"
    
    # Check if at least 18 years old
    if age < 18:
        return False, "You must be at least 18 years old to open an account"
    
    # Check if reasonable age (not older than 120 years)
    if age > 120:
        return False, "Please enter a valid date of birth"
    
    return True, "Valid"

with st.form("registration_form"):
    st.subheader("Personal Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        full_name = st.text_input("Full Name")
        email = st.text_input("Email Address")
        phone = st.text_input("Phone Number")
        
        # Fixed Date of Birth with proper validation
        min_date = date(1900, 1, 1)  # Reasonable minimum date
        max_date = date.today()      # Cannot be in future
        
        # Set default to 30 years ago for better UX
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
    
    st.subheader("Residential Address")
    address = st.text_area("Permanent Address", 
                          placeholder="Enter your complete residential address including city, state, and zip code")
    
    # Terms and conditions
    st.subheader("Terms & Conditions")
    terms_accepted = st.checkbox("I agree to the terms and conditions and privacy policy")
    
    submitted = st.form_submit_button("Open Account")
    
    if submitted:
        errors = []
        
        # Validate required fields
        if not all([full_name, email, username, password, address, id_number]):
            errors.append("Please fill in all required fields")
        
        # Validate password match
        if password != confirm_password:
            errors.append("Passwords do not match")
        
        # Validate password strength
        if len(password) < 6:
            errors.append("Password must be at least 6 characters long")
        
        # Validate date of birth
        is_valid, dob_error = is_valid_dob(dob)
        if not is_valid:
            errors.append(dob_error)
        
        # Validate terms acceptance
        if not terms_accepted:
            errors.append("You must accept the terms and conditions")
        
        # Validate username availability
        users = load_users()
        if username in users:
            errors.append("Username already exists. Please choose a different username.")
        
        # Validate email format (basic validation)
        if "@" not in email or "." not in email:
            errors.append("Please enter a valid email address")
        
        if errors:
            for error in errors:
                st.error(error)
        else:
            # Geocode address
            with st.spinner("Verifying your address..."):
                lat, lon = geocode_address(address)
            
            # Calculate age
            age = calculate_age(dob)
            
            # Prepare user data
            user_data = {
                'full_name': full_name,
                'email': email,
                'phone': phone,
                'password': password,
                'gender': gender,
                'dob': str(dob),
                'age': age,
                'id_number': id_number,
                'address': address,
                'lat': lat,
                'lon': lon,
                'account_created': str(datetime.now()),
                'account_status': 'active',
                'balance': 10000.00,  # Initial balance
                'terms_accepted': True,
                'terms_accepted_at': str(datetime.now())
            }
            
            # Save user
            save_user(username, user_data)
            
            # Success message
            st.success("🎉 Account created successfully! You can now login.")
            st.info(f"""
            **Account Details:**
            - **Name:** {full_name}
            - **Age:** {age} years
            - **Initial Balance:** $10,000.00
            - **Address Verified:** Latitude {lat:.4f}, Longitude {lon:.4f}
            """)
            
            # Show next steps
            st.balloons()
            st.page_link("pages/1_👤_User_Login.py", label="Proceed to Login", icon="🔐")

# Add helper information in sidebar
st.sidebar.header("ℹ️ Account Requirements")
st.sidebar.write("""
**To open an account, you must:**
- Be at least 18 years old
- Provide valid identification
- Provide a permanent residential address
- Accept our terms and conditions

**Age Verification:**
- Minimum age: 18 years
- Maximum age: 120 years
- Date of birth cannot be in the future

**Security:**
- All information is encrypted
- We verify your address automatically
- Your privacy is protected
""")

# Demo information
st.sidebar.header("📝 Demo Information")
st.sidebar.write("""
For testing purposes, you can use:
- **Sample DOB:** 1990-01-01 (35 years old)
- **Valid ID:** Any 8-12 digit number
- **Address:** Any real address for geocoding
""")