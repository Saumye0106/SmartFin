import json
import urllib.request

BASE = 'http://127.0.0.1:6000'


def post(path, payload):
    url = BASE + path
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def get(path, token=None):
    url = BASE + path
    headers = {}
    if token:
        headers['Authorization'] = f'Bearer {token}'
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


print('Registering demo user...')
try:
    r = post('/register', {'email': 'demo@local', 'password': 'pass'})
    print('Register response:', r)
except Exception as e:
    print('Register error (might already exist):', e)

print('\nLogging in...')
try:
    l = post('/login', {'email': 'demo@local', 'password': 'pass'})
    print('Login response:', {k: l.get(k) for k in ('id','email')})
    token = l.get('token')
except Exception as e:
    print('Login error:', e)
    raise

print('\nCalling protected endpoint with token...')
try:
    p = get('/protected', token=token)
    print('Protected response:', p)
except Exception as e:
    print('Protected error:', e)
