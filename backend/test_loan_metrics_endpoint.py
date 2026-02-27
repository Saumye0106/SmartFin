"""
Quick test script to verify loan metrics endpoint works
"""
import requests
import json

# Configuration
BASE_URL = "http://127.0.0.1:5000"

def test_loan_metrics():
    print("=" * 60)
    print("Testing Loan Metrics Endpoint")
    print("=" * 60)
    
    # Step 1: Register a test user
    print("\n1. Registering test user...")
    register_data = {
        "email": "test_metrics@example.com",
        "password": "testpass123"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/register", json=register_data)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            token = data.get('token')
            user_id = data.get('user', {}).get('id')
            print(f"   ✓ User registered successfully")
            print(f"   User ID: {user_id}")
            print(f"   Token: {token[:20]}...")
        elif response.status_code == 409:
            # User already exists, try to login
            print("   User already exists, logging in...")
            response = requests.post(f"{BASE_URL}/api/login", json=register_data)
            if response.status_code == 200:
                data = response.json()
                token = data.get('token')
                user_id = data.get('user', {}).get('id')
                print(f"   ✓ Logged in successfully")
                print(f"   User ID: {user_id}")
                print(f"   Token: {token[:20]}...")
            else:
                print(f"   ✗ Login failed: {response.text}")
                return
        else:
            print(f"   ✗ Registration failed: {response.text}")
            return
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    # Step 2: Test loan metrics endpoint
    print(f"\n2. Testing GET /api/loans/metrics/{user_id}...")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/api/loans/metrics/{user_id}", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Metrics retrieved successfully")
            print(f"\n   Response structure:")
            print(f"   {json.dumps(data, indent=2)}")
            
            # Check if metrics are present
            if 'metrics' in data:
                metrics = data['metrics']
                print(f"\n   Metrics values:")
                print(f"   - Loan Diversity Score: {metrics.get('loan_diversity_score')}")
                print(f"   - Payment History Score: {metrics.get('payment_history_score')}")
                print(f"   - Loan Maturity Score: {metrics.get('loan_maturity_score')}")
        else:
            print(f"   ✗ Failed to get metrics")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
        return
    
    # Step 3: Create a test loan
    print(f"\n3. Creating a test loan...")
    loan_data = {
        "user_id": user_id,
        "loan_type": "personal",
        "loan_amount": 50000,
        "loan_tenure": 24,
        "monthly_emi": 2200,
        "interest_rate": 10.5,
        "loan_start_date": "2026-01-01",
        "loan_maturity_date": "2028-01-01"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/loans", json=loan_data, headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 201:
            data = response.json()
            loan_id = data.get('loan', {}).get('loan_id')
            print(f"   ✓ Loan created successfully")
            print(f"   Loan ID: {loan_id}")
        else:
            print(f"   ✗ Failed to create loan")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    # Step 4: Get metrics again (should have loan data now)
    print(f"\n4. Getting metrics again (with loan data)...")
    try:
        response = requests.get(f"{BASE_URL}/api/loans/metrics/{user_id}", headers=headers)
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ Metrics retrieved successfully")
            
            if 'metrics' in data:
                metrics = data['metrics']
                print(f"\n   Updated metrics values:")
                print(f"   - Loan Diversity Score: {metrics.get('loan_diversity_score')}")
                print(f"   - Payment History Score: {metrics.get('payment_history_score')}")
                print(f"   - Loan Maturity Score: {metrics.get('loan_maturity_score')}")
                
                if metrics.get('loan_statistics'):
                    stats = metrics['loan_statistics']
                    print(f"\n   Loan Statistics:")
                    print(f"   - Total Active Loans: {stats.get('total_active_loans')}")
                    print(f"   - Total Loan Amount: {stats.get('total_loan_amount')}")
        else:
            print(f"   ✗ Failed to get metrics")
            print(f"   Response: {response.text}")
    except Exception as e:
        print(f"   ✗ Error: {e}")
    
    print("\n" + "=" * 60)
    print("Test Complete")
    print("=" * 60)

if __name__ == "__main__":
    test_loan_metrics()
