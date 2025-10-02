# utils/session_utils.py
import streamlit as st

def initialize_session_state():
    """Initialize all session state variables with default values"""
    defaults = {
        'user_authenticated': False,
        'admin_authenticated': False,
        'current_user': None,
        'user_data': {},
        'admin_user': None,
        'admin_details': {},
        'pending_notifications': []
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value