#!/usr/bin/env python3
"""
Test the Bedrock chat integration
"""
import requests
import json
import sys

backend_url = "http://localhost:5000"

# Test user
test_email = "bedrock-test@smartfin.local"
test_password = "TestPassword123!"

print("=" * 80)
print("BEDROCK CHAT INTEGRATION TEST")
print("=" * 80)

# Step 1: Try to login (or register if needed)
print("\n[1] Attempting login...")
login_response = requests.post(
    f"{backend_url}/login",
    json={"email": test_email, "password": test_password},
    timeout=10
)

if login_response.status_code == 401:
    # Try register
    print("    User not found, attempting registration...")
    register_response = requests.post(
        f"{backend_url}/register",
        json={"email": test_email, "password": test_password},
        timeout=10
    )
    
    if register_response.status_code == 201:
        print("    ✓ Registration successful")
        # Now login
        login_response = requests.post(
            f"{backend_url}/login",
            json={"email": test_email, "password": test_password},
            timeout=10
        )
    else:
        print(f"    ✗ Registration failed: {register_response.status_code}")
        print(f"    Response: {register_response.text}")
        sys.exit(1)

if login_response.status_code != 200:
    print(f"✗ Login failed: {login_response.status_code}")
    print(f"  Response: {login_response.text}")
    sys.exit(1)

login_data = login_response.json()
token = login_data['token']
print(f"✓ Login successful")
print(f"  Token: {token[:30]}...")

# Step 2: Test chat endpoint
print("\n[2] Testing /api/chat endpoint...")

chat_message = "Hello, what is financial health?"
chat_response = requests.post(
    f"{backend_url}/api/chat",
    json={
        "message": chat_message,
        "conversation_id": "test-bedrock-1"
    },
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    timeout=30
)

print(f"    Status: {chat_response.status_code}")

if chat_response.status_code != 200:
    print(f"    ✗ Request failed")
    print(f"    Response: {chat_response.text}")
    
    # Try to parse JSON for more detail
    try:
        error_data = chat_response.json()
        print(f"    Error Details: {json.dumps(error_data, indent=2)}")
    except:
        pass
    sys.exit(1)

# Parse response
response_data = chat_response.json()
print(f"    ✓ Request successful")

# Check for required fields
if 'response' in response_data:
    response_text = response_data['response']
    print(f"\n[3] Bedrock Response:")
    print(f"    {response_text[:200]}...")
    
    # Check if it's actual content or an error
    if "Error" in response_text or "error" in response_text:
        print("\n    ⚠️ Response contains error text, investigating...")
        print(f"    Full response: {response_text}")
    else:
        print("\n✓ BEDROCK INTEGRATION WORKING!")
else:
    print(f"    ⚠️ Unexpected response format: {response_data}")

print("\n" + "=" * 80)
