# app.py - REALISTIC Fraud Detection Demo
import streamlit as st
import pandas as pd
import numpy as np
import joblib
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings('ignore')

# Load your trained model
@st.cache_resource
def load_model():
    return joblib.load('best_xgb_model_tuned.joblib')

model = load_model()

# Title and description
st.title('💳 Credit Card Fraud Detection System')
st.write("Enter transaction details to check for potential fraud risk")

# Create input form
st.header("Transaction Details")

# SIMPLIFIED INPUTS - Only ask for realistic information
col1, col2 = st.columns(2)

with col1:
    amt = st.number_input('Transaction Amount ($)', min_value=0.0, value=150.0, step=1.0)
    category = st.selectbox('Transaction Category', 
                           ['shopping_pos', 'shopping_net', 'gas_transport', 'food_dining',
                            'entertainment', 'travel', 'misc_pos', 'misc_net',
                            'grocery_pos', 'personal_care', 'home', 'kids_pets'])
    
with col2:
    gender = st.selectbox('Cardholder Gender', ['M', 'F'])
    hour = st.slider('Time of Day (Hour)', 0, 23, 14)
    day_of_week = st.selectbox('Day of Week', 
                              ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 
                               'Friday', 'Saturday', 'Sunday'])

# Convert inputs to model format
day_map = {'Monday': 0, 'Tuesday': 1, 'Wednesday': 2, 'Thursday': 3, 
           'Friday': 4, 'Saturday': 5, 'Sunday': 6}
day_numeric = day_map[day_of_week]
is_weekend = 1 if day_numeric >= 5 else 0

# Define high-risk hours based on your EDA findings
high_risk_hour = 1 if hour in [2, 3, 4, 22, 23, 0] else 0

# Use DEFAULT VALUES for features users shouldn't need to input
# These represent "average" or "typical" values from your training data
DEFAULT_VALUES = {
    'cc_num': 123456789,  # dummy value
    'lat': 40.7128,       # New York approximate
    'long': -74.0060,     # New York approximate
    'city_pop': 100000,   # Medium city population
    'unix_time': 1609459200,  # Reasonable timestamp
    'merch_lat': 40.7128,     # Same as customer location (typical)
    'merch_long': -74.0060,   # Same as customer location
    'month': 6,           # June (middle of year)
}

# Scale amount using same logic as training (you should use your actual scaler)
def scale_amount(amount):
    # Replace this with your actual scaling logic from training
    return (amount - 70.0) / 200.0  # Simplified scaling

amt_scaled = scale_amount(amt)

def preprocess_input(amount, category, gender, hour, day_of_week, is_weekend, high_risk_hour):
    """Preprocess user input with smart defaults"""
    
    # Start with default values
    input_data = DEFAULT_VALUES.copy()
    
    # Add user-provided values
    input_data.update({
        'hour': hour,
        'day_of_week': day_of_week,
        'is_weekend': is_weekend,
        'gender': 1 if gender == 'M' else 0,
        'amt_scaled': scale_amount(amount),
        'high_risk_hour': high_risk_hour
    })
    
    # Add category encoding
    all_categories = [
        'entertainment', 'food_dining', 'gas_transport', 'grocery_net', 'grocery_pos',
        'health_fitness', 'home', 'kids_pets', 'misc_net', 'misc_pos', 
        'personal_care', 'shopping_net', 'shopping_pos', 'travel'
    ]
    
    for cat in all_categories:
        input_data[f'cat_{cat}'] = 1 if category == cat else 0
    
    # Create DataFrame with exact column order expected by model
    expected_columns = [
        'cc_num', 'gender', 'lat', 'long', 'city_pop', 'unix_time', 'merch_lat', 'merch_long',
        'hour', 'day_of_week', 'is_weekend', 'month', 'cat_entertainment', 'cat_food_dining',
        'cat_gas_transport', 'cat_grocery_net', 'cat_grocery_pos', 'cat_health_fitness',
        'cat_home', 'cat_kids_pets', 'cat_misc_net', 'cat_misc_pos', 'cat_personal_care',
        'cat_shopping_net', 'cat_shopping_pos', 'cat_travel', 'amt_scaled', 'high_risk_hour'
    ]
    
    df = pd.DataFrame([input_data])
    
    # Ensure correct column order
    return df[expected_columns]

# Make prediction
if st.button('🔍 Check for Fraud Risk'):
    input_df = preprocess_input(amt, category, gender, hour, day_numeric, is_weekend, high_risk_hour)
    
    try:
        prediction = model.predict(input_df)
        prediction_proba = model.predict_proba(input_df)
        fraud_probability = prediction_proba[0][1]
        
        # Display results
        st.header("📊 Risk Assessment Results")
        
        risk_level = "HIGH RISK" if fraud_probability > 0.7 else "MEDIUM RISK" if fraud_probability > 0.3 else "LOW RISK"
        
        if risk_level == "HIGH RISK":
            st.error(f'🚨 **{risk_level}: Potential Fraud Detected!**')
            st.warning(f"Fraud Probability: {fraud_probability:.2%}")
            st.info("Recommendation: Verify transaction with cardholder")
        elif risk_level == "MEDIUM RISK":
            st.warning(f'⚠️ **{risk_level}: Suspicious Activity**')
            st.write(f"Fraud Probability: {fraud_probability:.2%}")
            st.info("Recommendation: Additional verification recommended")
        else:
            st.success(f'✅ **{risk_level}: Transaction Appears Legitimate**')
            st.write(f"Fraud Probability: {fraud_probability:.2%}")
        
        # Visual indicators
        st.subheader("Risk Meter")
        st.progress(float(fraud_probability))
        st.write(f"Risk Score: {fraud_probability:.1%}")
        
        # Explanation based on inputs
        st.subheader("Key Risk Factors")
        if high_risk_hour:
            st.write("• ⚠️ Transaction during high-risk hours")
        if amt > 500:
            st.write("• ⚠️ Unusually high transaction amount")
        if category in ['misc_net', 'shopping_net']:
            st.write("• ⚠️ Online transaction category")
            
    except Exception as e:
        st.error(f"Error processing request: {str(e)}")

# Educational information
st.sidebar.header("ℹ️ About This Demo")
st.sidebar.write("""
This system analyzes transaction patterns using machine learning to identify potential fraud.

**How it works:**
- Analyzes transaction amount, category, timing, and demographics
- Compares against patterns learned from historical fraud data
- Provides real-time risk assessment

**Note:** This is a demonstration for educational purposes.
""")

# Add model performance metrics from your evaluation
st.sidebar.header("📈 Model Performance")
st.sidebar.write("""
- **AUC-ROC:** 0.98+ (Excellent)
- **Precision:** 85%+ 
- **Recall:** 80%+
- **Trained on:** 1M+ transactions
""")