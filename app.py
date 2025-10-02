# app.py - Main Application with User/Admin Routing
import streamlit as st

from utils.helpers import ensure_data_directory
ensure_data_directory()

st.set_page_config(
    page_title="SecureBank - Fraud Detection",
    page_icon="🏦",
    layout="wide"
)

# Initialize session state with proper error handling
def initialize_session_state():
    if 'user_authenticated' not in st.session_state:
        st.session_state.user_authenticated = False
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    if 'current_user' not in st.session_state:
        st.session_state.current_user = None
    if 'user_data' not in st.session_state:
        st.session_state.user_data = {}
    if 'admin_user' not in st.session_state:
        st.session_state.admin_user = None
    if 'admin_details' not in st.session_state:
        st.session_state.admin_details = {}
    if 'pending_notifications' not in st.session_state:
        st.session_state.pending_notifications = []

def main():
    # Initialize session state first
    initialize_session_state()
    
    st.title("🏦 SecureBank - Intelligent Banking Platform")
    
    # Show appropriate interface based on authentication
    if st.session_state.user_authenticated:
        st.switch_page("pages/3_🏠_User_Dashboard.py")
    elif st.session_state.admin_authenticated:
        st.switch_page("pages/7_🛡️_Admin_Dashboard.py")
    else:
        show_landing_page()

def show_landing_page():
    st.markdown("""
    <div style='text-align: center; padding: 50px 0;'>
        <h1>🏦 Welcome to SecureBank</h1>
        <p style='font-size: 1.2em;'>AI-Powered Secure Banking with Real-time Fraud Detection</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👤 Customer Portal")
        st.page_link("pages/1_👤_User_Login.py", label="Customer Login", icon="🔐")
        st.page_link("pages/2_📝_User_Register.py", label="Open New Account", icon="📝")
        st.write("Access your banking services and make secure transactions")
    
    with col2:
        st.subheader("👨💼 Bank Staff Portal")
        st.page_link("pages/6_👨💼_Admin_Login.py", label="Bank Staff Login", icon="🛡️")
        st.write("Monitor transactions and manage fraud detection system")

def show_account_settings():
    st.header("Account Settings")
    
    if st.button("🚪 Logout"):
        st.session_state.user_authenticated = False
        st.session_state.current_user = None
        st.session_state.user_data = {}
        st.rerun()

if __name__ == "__main__":
    main()