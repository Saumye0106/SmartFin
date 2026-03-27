#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, 'backend')
os.chdir('backend')

from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
import requests
import json

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', 'your-secret-key-change-this-in-production')
jwt = JWTManager(app)

with app.app_context():
    token = create_access_token(identity=1)

headers = {
    'Authorization': 'Bearer ' + token,
    'Content-Type': 'application/json'
}

payload = {'message': 'Hello, what is financial health?'}

print('Testing Bedrock chat endpoint...')
print('Sending: ' + payload["message"])
print()

try:
    response = requests.post('http://127.0.0.1:5000/api/chat', headers=headers, json=payload, timeout=120)
    print('Status: ' + str(response.status_code))
    
    result = response.json()
    if response.status_code == 200:
        print('SUCCESS')
        resp_msg = result.get('response', 'N/A')
        print('\nResponse:')
        print(resp_msg[:500])
        
        if result.get('widgets'):
            print('\nTools used: ' + str(len(result["widgets"])))
            for widget in result['widgets']:
                print('  - ' + widget.get("tool"))
    else:
        print('ERROR')
        print('Error: ' + result.get("error", "Unknown"))
        print('\nFull response:')
        print(json.dumps(result, indent=2))
        
except Exception as e:
    print('Exception: ' + str(e))
    import traceback
    traceback.print_exc()
