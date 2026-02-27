#!/usr/bin/env python
"""Test script to verify payment recording works with timezone fixes"""

import requests
import json
from datetime import datetime, timezone, timedelta
import time

BASE_URL = 'http://127.0.0.1:5000'

def test_payment_recording():
    """Test the payment recording endpoint"""
    
    # Wait for server to be ready
    time.sleep(2)
    
    print("=" * 60)
    print("Testing Payment Recording with Timezone Fixes")
    print("=" * 60)
    
    # Step 1: Register a user
    print("\n1. Registering user...")
    register_data = {
        'email': f'test_payment_{int(time.time())}@example.com',
        'password': 'TestPassword123!'
    }
    
    try:
        resp = requests.post(f'{BASE_URL}/register', json=register_data, timeout=5)
        print(f"   Status: {resp.status_code}")
        
        if resp.status_code != 201:
            print(f"   Error: {resp.text}")
            return False
        
        user_data = resp.json()
        token = user_data.get('token')
        user_id = user_data.get('user', {}).get('id')
        print(f"   ✓ User registered: ID={user_id}")
        
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False
    
    # Step 2: Create a loan
    print("\n2. Creating loan...")
    headers = {'Authorization': f'Bearer {token}'}
    loan_data = {
        'loan_type': 'personal',
        'loan_amount': 100000,
        'loan_tenure': 24,
        'interest_rate': 10.0,
        'loan_start_date': '2026-02-27T00:00:00Z',
        'loan_maturity_date': '2028-02-27T00:00:00Z'
    }
    
    try:
        resp = requests.post(f'{BASE_URL}/api/loans', json=loan_data, headers=headers, timeout=5)
        print(f"   Status: {resp.status_code}")
        
        if resp.status_code != 201:
            print(f"   Error: {resp.text}")
            return False
        
        loan = resp.json()
        loan_id = loan.get('loan_id')
        print(f"   ✓ Loan created: ID={loan_id}")
        
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False
    
    # Step 3: Record a payment with today's date
    print("\n3. Recording payment with today's date...")
    
    # Get today's date in ISO format
    today = datetime.now(timezone.utc).date()
    payment_date_iso = f"{today.isoformat()}T00:00:00Z"
    
    payment_data = {
        'payment_date': payment_date_iso,
        'payment_amount': 5000
    }
    
    print(f"   Payment date: {payment_date_iso}")
    print(f"   Payment amount: 5000")
    
    try:
        resp = requests.post(
            f'{BASE_URL}/api/loans/{loan_id}/payments',
            json=payment_data,
            headers=headers,
            timeout=5
        )
        print(f"   Status: {resp.status_code}")
        
        if resp.status_code == 201:
            payment = resp.json().get('payment')
            print(f"   ✓ Payment recorded successfully!")
            print(f"     Payment ID: {payment.get('payment_id')}")
            print(f"     Status: {payment.get('payment_status')}")
            return True
        else:
            print(f"   ✗ Error: {resp.text}")
            return False
        
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
        return False

if __name__ == '__main__':
    success = test_payment_recording()
    print("\n" + "=" * 60)
    if success:
        print("✓ All tests passed!")
    else:
        print("✗ Tests failed!")
    print("=" * 60)
