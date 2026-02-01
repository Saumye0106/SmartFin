import os
import sqlite3
from datetime import datetime, timedelta, timezone
from functools import wraps

from flask import Flask, request, jsonify, g
from werkzeug.security import generate_password_hash, check_password_hash
import jwt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.environ.get('AUTH_DB', os.path.join(BASE_DIR, 'auth.db'))
JWT_SECRET = os.environ.get('AUTH_JWT_SECRET', 'dev-secret')
JWT_ALGO = 'HS256'

app = Flask(__name__)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db


def init_db():
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute(
        '''CREATE TABLE IF NOT EXISTS users (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             email TEXT UNIQUE NOT NULL,
             password_hash TEXT NOT NULL,
             created_at TEXT NOT NULL
        )'''
    )
    # refresh tokens table
    cur.execute(
        '''CREATE TABLE IF NOT EXISTS refresh_tokens (
             id INTEGER PRIMARY KEY AUTOINCREMENT,
             user_id INTEGER NOT NULL,
             token TEXT NOT NULL,
             issued_at TEXT NOT NULL,
             revoked INTEGER DEFAULT 0,
             FOREIGN KEY(user_id) REFERENCES users(id)
        )'''
    )
    db.commit()
    db.close()


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def generate_token(user_id, expires_minutes=30):
    payload = {
        # subject must be a string per JWT recommendations
        'sub': str(user_id),
        'exp': datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGO)
    # PyJWT may return bytes in some versions; ensure string
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token


def generate_refresh_token(user_id):
    import secrets
    token = secrets.token_urlsafe(64)
    issued_at = datetime.now(timezone.utc).isoformat()
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute('INSERT INTO refresh_tokens (user_id, token, issued_at) VALUES (?, ?, ?)',
                (user_id, token, issued_at))
    db.commit()
    db.close()
    return token


def revoke_refresh_token(token):
    db = sqlite3.connect(DB_PATH)
    cur = db.cursor()
    cur.execute('UPDATE refresh_tokens SET revoked = 1 WHERE token = ?', (token,))
    db.commit()
    db.close()


def find_valid_refresh_token(token):
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    cur = db.cursor()
    cur.execute('SELECT * FROM refresh_tokens WHERE token = ? AND revoked = 0', (token,))
    row = cur.fetchone()
    db.close()
    return row


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', None)
        if not auth or not auth.startswith('Bearer '):
            return jsonify({'message': 'Missing token'}), 401
        token = auth.split(None, 1)[1]
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGO])
            user_id = data.get('sub')
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token expired'}), 401
        except Exception:
            return jsonify({'message': 'Invalid token'}), 401
        # attach user_id to request context
        request.user_id = user_id
        return f(*args, **kwargs)

    return decorated


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'message': 'email and password required'}), 400

    password_hash = generate_password_hash(password)
    created_at = datetime.now(timezone.utc).isoformat()
    db = get_db()
    cur = db.cursor()
    try:
        cur.execute('INSERT INTO users (email, password_hash, created_at) VALUES (?, ?, ?)',
                    (email, password_hash, created_at))
        db.commit()
        user_id = cur.lastrowid
    except sqlite3.IntegrityError:
        return jsonify({'message': 'email already registered'}), 400

    token = generate_token(user_id)
    return jsonify({'id': user_id, 'email': email, 'token': token})


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        return jsonify({'message': 'email and password required'}), 400

    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT id, password_hash FROM users WHERE email = ?', (email,))
    row = cur.fetchone()
    if not row:
        return jsonify({'message': 'invalid credentials'}), 401
    user_id = row['id']
    if not check_password_hash(row['password_hash'], password):
        return jsonify({'message': 'invalid credentials'}), 401

    access_token = generate_token(user_id)
    refresh_token = generate_refresh_token(user_id)
    return jsonify({'id': user_id, 'email': email, 'token': access_token, 'refresh_token': refresh_token})


@app.route('/protected', methods=['GET'])
@token_required
def protected():
    return jsonify({'message': 'access granted', 'user_id': request.user_id})


@app.route('/refresh', methods=['POST'])
def refresh():
    data = request.get_json() or {}
    token = data.get('refresh_token')
    if not token:
        return jsonify({'message': 'refresh_token required'}), 400

    row = find_valid_refresh_token(token)
    if not row:
        return jsonify({'message': 'invalid refresh token'}), 401

    user_id = row['user_id']
    # rotate: revoke old and issue new
    revoke_refresh_token(token)
    new_refresh = generate_refresh_token(user_id)
    access_token = generate_token(user_id)
    return jsonify({'token': access_token, 'refresh_token': new_refresh})


@app.route('/logout', methods=['POST'])
def logout():
    data = request.get_json() or {}
    token = data.get('refresh_token')
    if not token:
        return jsonify({'message': 'refresh_token required'}), 400
    revoke_refresh_token(token)
    return jsonify({'message': 'logged out'})


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=6000, debug=True)
