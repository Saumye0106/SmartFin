#!/usr/bin/env python3
"""
Extended Bedrock integration test - multiple message types
"""
import requests
import json
import sys

backend_url = "http://localhost:5000"

# Use the same user from previous test
test_email = "bedrock-test@smartfin.local"
test_password = "TestPassword123!"

print("=" * 80)
print("EXTENDED BEDROCK CHAT TEST")
print("=" * 80)

# Login
print("\n[1] Logging in...")
login_response = requests.post(
    f"{backend_url}/login",
    json={"email": test_email, "password": test_password},
    timeout=10
)

if login_response.status_code != 200:
    print(f"✗ Login failed: {login_response.status_code}")
    sys.exit(1)

token = login_response.json()['token']
print(f"✓ Login successful")

# Test multiple questions
test_questions = [
    "What are the key components of financial health?",
    "How can I improve my financial situation?",
    "What's the importance of emergency savings?",
]

conversation_id = "extended-test-1"

for i, question in enumerate(test_questions, 1):
    print(f"\n[{i+1}] Question: {question}")
    
    response = requests.post(
        f"{backend_url}/api/chat",
        json={
            "message": question,
            "conversation_id": conversation_id
        },
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"    ✗ Failed: {response.status_code}")
        print(f"    {response.text}")
        continue
    
    response_data = response.json()
    if 'response' in response_data:
        answer = response_data['response']
        print(f"    ✓ Response: {answer[:150]}...")
    else:
        print(f"    ? Unexpected format: {response_data}")

print("\n" + "=" * 80)
print("✓ ALL TESTS COMPLETED")
print("=" * 80)
