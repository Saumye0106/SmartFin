#!/usr/bin/env python
"""
Quick test script for retirement planning API
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

# Test data
test_plan = {
    "user_id": 1,
    "plan_name": "Test Plan",
    "current_age": 30,
    "retirement_age": 65,
    "current_salary": 500000,
    "current_monthly_expenses": 30000,
    "current_savings": 100000,
    "inflation_rate": 0.06,
    "investment_return_rate": 0.10,
    "life_expectancy": 85
}

print("Testing Retirement Planning API")
print("=" * 50)

try:
    print("\n1. Testing POST /api/retirement/calculate")
    print(f"   Sending: {json.dumps(test_plan, indent=2)}")
    
    response = requests.post(
        f"{BASE_URL}/api/retirement/calculate",
        json=test_plan,
        headers={"Content-Type": "application/json"}
    )
    
    print(f"   Status: {response.status_code}")
    
    if response.status_code == 201:
        data = response.json()
        print(f"   ✓ Success!")
        print(f"   Plan ID: {data.get('plan_id')}")
        print(f"   Readiness Score: {data.get('plan', {}).get('readiness_score')}")
    else:
        print(f"   ✗ Error: {response.text}")
        
except Exception as e:
    print(f"   ✗ Exception: {str(e)}")

print("\n" + "=" * 50)
print("Test complete!")
