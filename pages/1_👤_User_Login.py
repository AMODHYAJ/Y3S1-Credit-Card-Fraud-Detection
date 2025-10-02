# pages/1_👤_User_Login.py
import streamlit as st
import json

from utils.session_utils import initialize_session_state
initialize_session_state()

st.title("👤 Customer Login")

def load_users():
    try:
        with open('data/users.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def verify_user_credentials(username, password):
    users = load_users()
    if username in users:
        return users[username]['password'] == password
    return False

def get_user_data(username):
    users = load_users()
    return users.get(username, {})

# Login form
with st.form("user_login_form"):
    st.subheader("Access Your Bank Account")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        login_submitted = st.form_submit_button("🔐 Login")
    with col2:
        st.page_link("pages/2_📝_User_Register.py", label="Don't have an account? Register", icon="📝")
    
    if login_submitted:
        if not username or not password:
            st.error("Please enter both username and password")
        elif verify_user_credentials(username, password):
            st.session_state.user_authenticated = True
            st.session_state.current_user = username
            st.session_state.user_data = get_user_data(username)
            st.success(f"Welcome back, {get_user_data(username)['full_name']}!")
            
            # Add a small delay before redirecting
            import time
            time.sleep(2)
            st.switch_page("pages/3_🏠_User_Dashboard.py")
        else:
            st.error("Invalid username or password")

# Demo credentials for testing
st.divider()
st.subheader("Demo Credentials")
st.info("""
For testing purposes, you can use these demo accounts after registration:
- **Username:** john_doe
- **Password:** password123

Or register a new account using the registration page.
""")