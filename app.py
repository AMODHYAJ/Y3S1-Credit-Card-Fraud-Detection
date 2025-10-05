# app.py - Main Application with User/Admin Routing - UPDATED FOR HYBRID SYSTEM
import streamlit as st
import os

# Import deployment setup
try:
    from setup_deployment import setup_deployment_environment
    
    # Check if we need to run setup (simpler check for hybrid system)
    model_files_exist = (
        os.path.exists('enhanced_fraud_model.joblib') or 
        os.path.exists('models/sri_lanka_wide_model.joblib') or
        os.path.exists('models/deployment_model.joblib')
    )
    
    if not model_files_exist:
        st.info("🔄 Setting up Hybrid ML environment...")
        setup_deployment_environment()
        
except ImportError as e:
    st.warning(f"⚠️ Deployment setup import issue: {e}")
except Exception as e:
    st.warning(f"⚠️ Setup check issue: {e}")

# Ensure data directory exists
try:
    from utils.helpers import ensure_data_directory
    ensure_data_directory()
except ImportError:
    st.error("❌ Could not import utils.helpers - check file structure")

st.set_page_config(
    page_title="SecureBank - Hybrid ML Fraud Detection",
    page_icon="🏦",
    layout="wide"
)

# Import session utilities
try:
    from utils.session_utils import initialize_session_state
    initialize_session_state()
except ImportError:
    st.error("❌ Could not import session utilities")

def main():
    """Main application with hybrid ML system"""
    
    # Show system status in sidebar
    with st.sidebar:
        st.subheader("🔧 System Status")
        
        # Check hybrid system status
        try:
            from hybrid_model_manager import get_hybrid_prediction
            # Test the hybrid system
            test_result = get_hybrid_prediction(
                {'amount': 100}, 
                {}, 
                6.9271, 
                79.8612
            )
            st.success("✅ Hybrid ML System: ACTIVE")
            st.info(f"🤖 Models: Sri Lanka + Original")
            
        except Exception as e:
            st.error("❌ Hybrid ML System: OFFLINE")
            st.warning("🔄 Using rule-based fallback")
        
        st.divider()
    
    st.title("🏦 SecureBank - Hybrid ML Banking Platform")
    
    # Show appropriate interface based on authentication
    if st.session_state.user_authenticated:
        st.switch_page("pages/3_🏠_User_Dashboard.py")
    elif st.session_state.admin_authenticated:
        st.switch_page("pages/7_🛡️_Admin_Dashboard.py")
    else:
        show_landing_page()

def show_landing_page():
    """Show landing page with hybrid ML information"""
    
    st.markdown("""
    <div style='text-align: center; padding: 50px 0;'>
        <h1>🏦 Welcome to SecureBank</h1>
        <p style='font-size: 1.2em;'>Hybrid ML-Powered Secure Banking with Real-time Fraud Detection</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Hybrid ML System Info
    st.subheader("🤖 Advanced Fraud Detection System")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **🇱🇰 Sri Lanka Model**
        - Local transaction patterns
        - Sri Lanka geographic context  
        - Regional spending behavior
        - Cultural spending insights
        """)
    
    with col2:
        st.markdown("""
        **🌍 Original Model**
        - International fraud patterns
        - Global fraud detection
        - Established risk patterns
        - Cross-border intelligence
        """)
    
    st.info("""
    **🔍 Smart Hybrid System:** Automatically selects the best model based on transaction context, 
    geographic location, and spending patterns for optimal fraud detection accuracy.
    """)
    
    # Portal selection
    st.subheader("🚪 Access Portals")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("👤 Customer Portal")
        st.page_link("pages/1_👤_User_Login.py", label="Customer Login", icon="🔐")
        st.page_link("pages/2_📝_User_Register.py", label="Open New Account", icon="📝")
        st.write("Access your banking services with enhanced ML protection")
    
    with col2:
        st.subheader("👨💼 Bank Staff Portal")
        st.page_link("pages/6_👨💼_Admin_Login.py", label="Bank Staff Login", icon="🛡️")
        st.write("Monitor transactions and manage hybrid ML fraud detection")
    
    # Demo information
    st.divider()
    st.subheader("🧪 Demo Features")
    
    demo_col1, demo_col2, demo_col3 = st.columns(3)
    
    with demo_col1:
        st.write("**🇱🇰 Local Transactions**")
        st.write("• Low risk detection")
        st.write("• Sri Lanka context")
        
    with demo_col2:
        st.write("**🌍 International**") 
        st.write("• Appropriate risk levels")
        st.write("• Global patterns")
        
    with demo_col3:
        st.write("**🚨 High Risk**")
        st.write("• Dubai luxury goods")
        st.write("• Card testing patterns")

def show_account_settings():
    """Account settings page"""
    st.header("Account Settings")
    
    if st.button("🚪 Logout"):
        st.session_state.user_authenticated = False
        st.session_state.current_user = None
        st.session_state.user_data = {}
        st.rerun()

if __name__ == "__main__":
    main()