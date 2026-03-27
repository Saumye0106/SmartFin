#!/usr/bin/env python3
import requests
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app import app, get_jwt_token

# Create test client
client = app.test_client()

# Get JWT token
token = get_jwt_token("test@example.com")
print(f"✓ Got JWT token: {token[:20]}...")

# Test chat endpoint
chat_data = {
    "message": "Hello, what is financial health?",
    "conversation_id": "test-conv-1"
}

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

print("\nTesting /api/chat endpoint...")
response = client.post(
    "/api/chat",
    data=json.dumps(chat_data),
    headers=headers,
    content_type="application/json"
)

print(f"Status Code: {response.status_code}")
print(f"Response Headers: {dict(response.headers)}")

try:
    response_data = response.get_json()
    print(f"Response Data: {json.dumps(response_data, indent=2)}")
except Exception as e:
    print(f"Raw Response: {response.data}")
    print(f"Error parsing JSON: {e}")

# Check for Bedrock API errors
if response.status_code != 200:
    print(f"\nERROR: Expected 200, got {response.status_code}")
    if 'error' in str(response.data):
        print("API Error detected")
else:
    print("\n✓ Chat endpoint working!")
