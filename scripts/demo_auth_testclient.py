import importlib
import os
import sys
import tempfile
from pathlib import Path

# Make sure project root is on sys.path so `services.auth` can be imported
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Ensure a fresh DB
tmp = tempfile.NamedTemporaryFile(delete=False)
os.environ['AUTH_DB'] = tmp.name
os.environ['AUTH_JWT_SECRET'] = 'demo-secret'

app_mod = importlib.import_module('services.auth.app')
app_mod.init_db()

client = app_mod.app.test_client()

print('Registering user...')
r = client.post('/register', json={'email':'demo@local','password':'pass'})
print('Status:', r.status_code)
print('Body:', r.get_json())

print('\nLogging in...')
r2 = client.post('/login', json={'email':'demo@local','password':'pass'})
print('Status:', r2.status_code)
print('Body:', r2.get_json())

token = r2.get_json().get('token')
print('\nCalling protected with token...')
# Try decoding token locally
try:
	decoded = app_mod.jwt.decode(token, app_mod.JWT_SECRET, algorithms=[app_mod.JWT_ALGO])
	print('Local decode OK:', decoded)
except Exception as e:
	print('Local decode failed:', e)

r3 = client.get('/protected', headers={'Authorization': f'Bearer {token}'})
print('Status:', r3.status_code)
print('Body:', r3.get_json())
