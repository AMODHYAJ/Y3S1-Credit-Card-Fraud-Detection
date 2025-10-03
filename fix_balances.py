# fix_balances.py - One-time balance reset script
import json
from datetime import datetime

def fix_all_user_balances():
    """Fix all user balances with proper credit limits"""
    try:
        with open('data/users.json', 'r') as f:
            users = json.load(f)
    except Exception as e:
        print(f"Error loading users: {e}")
        return
    
    fixed_count = 0
    
    for username, user_data in users.items():
        print(f"Fixing balances for user: {username}")
        
        # Calculate age and credit limit
        age = 30  # Default age
        if 'dob' in user_data:
            try:
                dob_str = user_data['dob']
                if 'T' in dob_str:
                    dob = datetime.fromisoformat(dob_str.replace('Z', '+00:00'))
                else:
                    dob = datetime.strptime(dob_str, '%Y-%m-%d')
                
                today = datetime.now()
                age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
                print(f"  - Age calculated: {age}")
            except Exception as e:
                print(f"  - Error calculating age: {e}")
                age = 30
        
        # Set credit limit based on age
        if age < 25:
            credit_limit = 2000.00
        elif age < 35:
            credit_limit = 5000.00
        elif age < 50:
            credit_limit = 10000.00
        else:
            credit_limit = 8000.00
        
        print(f"  - Credit limit set: ${credit_limit:,.2f}")
        
        # Update user balances
        user_data['total_credit_limit'] = credit_limit
        user_data['total_available_credit'] = credit_limit
        user_data['total_current_balance'] = 0.00
        
        # Ensure credit cards structure exists
        if 'credit_cards' not in user_data:
            user_data['credit_cards'] = {}
        
        user_data['credit_cards']['primary'] = {
            'last_four': '0000',
            'card_type': 'Visa',
            'credit_limit': credit_limit,
            'available_balance': credit_limit,
            'current_balance': 0.00,
            'min_payment': 0.00,
            'payment_due_date': str(datetime.now().replace(day=15).date()),
            'is_active': True
        }
        
        fixed_count += 1
    
    # Save fixed data
    try:
        with open('data/users.json', 'w') as f:
            json.dump(users, f, indent=2, default=str)
        print(f"\n✅ Successfully fixed balances for {fixed_count} users!")
        print("All users now have proper credit limits based on their age.")
    except Exception as e:
        print(f"❌ Error saving fixed data: {e}")

if __name__ == "__main__":
    print("🔄 Fixing user balances...")
    fix_all_user_balances()