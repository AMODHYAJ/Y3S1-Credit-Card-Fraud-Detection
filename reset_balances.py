# reset_balances.py - Run this if data gets corrupted
import json
import streamlit as st

def reset_user_balances():
    """Reset all user balances to their credit limits"""
    try:
        with open('data/users.json', 'r') as f:
            users = json.load(f)
        
        for username, user_data in users.items():
            credit_limit = user_data.get('total_credit_limit', 2000.00)
            user_data['total_available_credit'] = credit_limit
            user_data['total_current_balance'] = 0.00
            
            if 'credit_cards' in user_data and 'primary' in user_data['credit_cards']:
                user_data['credit_cards']['primary']['available_balance'] = credit_limit
                user_data['credit_cards']['primary']['current_balance'] = 0.00
        
        with open('data/users.json', 'w') as f:
            json.dump(users, f, indent=2)
        
        st.success("✅ All user balances reset successfully!")
        
    except Exception as e:
        st.error(f"Error resetting balances: {e}")

# Add a reset button to your admin panel or run this separately
if st.button("🔄 Reset All Balances (Admin Only)"):
    reset_user_balances()