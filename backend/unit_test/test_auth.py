import os
import tempfile
import json
import importlib

import pytest


def setup_module(module):
    # create a temporary DB file and set environment before importing the app
    tmp = tempfile.NamedTemporaryFile(delete=False)
    os.environ['AUTH_DB'] = tmp.name
    # use a sufficiently long secret in tests to avoid InsecureKeyLengthWarning
    os.environ['AUTH_JWT_SECRET'] = 'a' * 64
    # import the app after env is set
    global auth_app
    auth_app = importlib.import_module('services.auth.app')
    auth_app.init_db()


def teardown_module(module):
    # remove temp DB
    db_path = os.environ.get('AUTH_DB')
    try:
        os.unlink(db_path)
    except Exception:
        pass


def test_register_and_login():
    client = auth_app.app.test_client()
    # register
    r = client.post('/register', json={'email': 'a@b.com', 'password': 'pass'})
    assert r.status_code == 200
    data = r.get_json()
    assert 'token' in data

    # login (should return access + refresh)
    r2 = client.post('/login', json={'email': 'a@b.com', 'password': 'pass'})
    assert r2.status_code == 200
    data2 = r2.get_json()
    assert 'token' in data2 and 'refresh_token' in data2

    token = data2['token']
    refresh = data2['refresh_token']

    # protected endpoint with access token
    r3 = client.get('/protected', headers={'Authorization': f'Bearer {token}'})
    assert r3.status_code == 200
    assert r3.get_json().get('user_id') is not None

    # use refresh to rotate and get a new access token
    r4 = client.post('/refresh', json={'refresh_token': refresh})
    assert r4.status_code == 200
    data4 = r4.get_json()
    assert 'token' in data4 and 'refresh_token' in data4

    # old refresh token should be invalid now
    r5 = client.post('/refresh', json={'refresh_token': refresh})
    assert r5.status_code == 401

    # logout with the new refresh token
    r6 = client.post('/logout', json={'refresh_token': data4['refresh_token']})
    assert r6.status_code == 200

    # refreshing after logout should fail
    r7 = client.post('/refresh', json={'refresh_token': data4['refresh_token']})
    assert r7.status_code == 401
