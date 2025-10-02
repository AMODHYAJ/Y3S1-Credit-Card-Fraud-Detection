# pages/6_👨💼_Admin_Login.py
import streamlit as st

from utils.session_utils import initialize_session_state
initialize_session_state()

st.title("👨💼 Bank Staff Portal")

# Admin credentials (in real app, this would be in a secure database)
ADMIN_CREDENTIALS = {
    "admin": "admin123",
    "security_team": "secure456",
    "fraud_dept": "fraud789"
}

ADMIN_DETAILS = {
    "admin": {"name": "System Administrator", "role": "Full Access"},
    "security_team": {"name": "Security Team Member", "role": "Transaction Review"},
    "fraud_dept": {"name": "Fraud Department", "role": "Fraud Analysis"}
}

def verify_admin_credentials(username, password):
    return username in ADMIN_CREDENTIALS and ADMIN_CREDENTIALS[username] == password

# Login form
with st.form("admin_login_form"):
    st.subheader("Bank Staff Authentication")
    
    username = st.text_input("Staff ID")
    password = st.text_input("Password", type="password")
    
    login_submitted = st.form_submit_button("🛡️ Login as Staff")
    
    if login_submitted:
        if not username or not password:
            st.error("Please enter both Staff ID and password")
        elif verify_admin_credentials(username, password):
            st.session_state.admin_authenticated = True
            st.session_state.admin_user = username
            st.session_state.admin_details = ADMIN_DETAILS[username]
            st.success(f"Welcome, {ADMIN_DETAILS[username]['name']}!")
            
            import time
            time.sleep(1)
            st.switch_page("pages/7_🛡️_Admin_Dashboard.py")
        else:
            st.error("Invalid Staff ID or password")

# Security notice
st.divider()
st.subheader("🔒 Security Notice")
st.warning("""
This portal is for authorized bank staff only. All activities are logged and monitored.

**Access Levels:**
- **System Administrator:** Full system access
- **Security Team:** Transaction review and approval
- **Fraud Department:** Fraud analysis and reporting

Unauthorized access is strictly prohibited and may result in legal action.
""")

# Demo credentials
st.info("""
**Demo Credentials:**
- **Staff ID:** admin
- **Password:** admin123
""")