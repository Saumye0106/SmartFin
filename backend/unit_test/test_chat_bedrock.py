#!/usr/bin/env python3
"""
Test script for Bedrock chat integration
Tests the /api/chat endpoint with authentication
"""

import requests
import json
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from flask_jwt_extended import create_access_token
from flask import Flask

# Create minimal Flask app context for JWT token generation
app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-this-in-production')

BASE_URL = 'http://127.0.0.1:5000'

def generate_token(user_id='test_user', user_email='test@example.com'):
    """Generate a test JWT token"""
    with app.app_context():
        token = create_access_token(
            identity={'user_id': user_id, 'email': user_email}
        )
    return token

def test_chat():
    """Test the chat endpoint"""
    token = generate_token()
    
    print("=" * 60)
    print("Testing SmartFin Chat Agent with Bedrock")
    print("=" * 60)
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    # Test message
    payload = {
        'message': 'Hello! Can you tell me about financial health scores?'
    }
    
    print(f"\nSending message: {payload['message']}")
    print(f"Token: {token[:50]}...")
    
    try:
        response = requests.post(
            f'{BASE_URL}/api/chat',
            headers=headers,
            json=payload,
            timeout=60
        )
        
        print(f"\nResponse Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ SUCCESS!")
            print(f"\nAssistant Response:")
            print(f"{result.get('message', 'N/A')}")
            
            if result.get('widgets'):
                print(f"\n📊 Tools Used: {len(result['widgets'])}")
                for widget in result['widgets']:
                    print(f"  - {widget.get('tool', 'unknown')}")
            
            return True
        else:
            print(f"\n❌ ERROR (HTTP {response.status_code})")
            print(f"Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Connection Error: {str(e)}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_chat()
    sys.exit(0 if success else 1)
