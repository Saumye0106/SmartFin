"""
API Integration Tests for Profile Management
Tests all profile and goals endpoints with authentication
"""

import sys
import json
import sqlite3
import tempfile
import os
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash


def create_test_app():
    """Create a test Flask app with test database"""
    # Create temporary database
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    # Initialize database
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Create users table
    cur.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    # Create users_profile table
    cur.execute('''
        CREATE TABLE users_profile (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER NOT NULL CHECK (age >= 18 AND age <= 120),
            location TEXT NOT NULL,
            risk_tolerance INTEGER CHECK (risk_tolerance >= 1 AND risk_tolerance <= 10),
            profile_picture_url TEXT,
            notification_preferences TEXT DEFAULT '{"email": true, "push": false, "in_app": true, "frequency": "daily"}',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # Create financial_goals table
    cur.execute('''
        CREATE TABLE financial_goals (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            goal_type TEXT NOT NULL CHECK (goal_type IN ('short-term', 'long-term')),
            target_amount REAL NOT NULL CHECK (target_amount > 0),
            target_date TEXT NOT NULL,
            priority TEXT NOT NULL CHECK (priority IN ('low', 'medium', 'high')),
            status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users_profile(user_id) ON DELETE CASCADE
        )
    ''')
    
    # Create test user
    password_hash = generate_password_hash('testpass123')
    cur.execute(
        'INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)',
        ('testuser@example.com', password_hash, datetime.utcnow().isoformat())
    )
    
    conn.commit()
    conn.close()
    
    # Import app and configure for testing
    import app as flask_app
    flask_app.DB_PATH = db_path
    flask_app.app.config['TESTING'] = True
    flask_app.app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    
    # Reinitialize services with test database
    from profile_service import ProfileService
    from goals_service import GoalsService
    flask_app.profile_service = ProfileService(db_path)
    flask_app.goals_service = GoalsService(db_path)
    
    return flask_app.app, db_path


def get_auth_token(client):
    """Login and get JWT token"""
    response = client.post('/login', 
        data=json.dumps({
            'email': 'testuser@example.com',
            'password': 'testpass123'
        }),
        content_type='application/json'
    )
    data = json.loads(response.data)
    return data['token']


def test_create_profile_success():
    """Test POST /api/profile/create with valid data"""
    print("\nTest: POST /api/profile/create (success)...")
    
    app, db_path = create_test_app()
    client = app.test_client()
    
    try:
        token = get_auth_token(client)
        
        response = client.post('/api/profile/create',
            headers={'Authorization': f'Bearer {token}'},
            data=json.dumps({
                'name': 'John Doe',
                'age': 30,
                'location': 'New York',
                'risk_tolerance': 7
            }),
            content_type='application/json'
        )
        
        if response.status_code != 201:
            print(f"Response: {response.data}")
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
        data = json.loads(response.data)
        assert 'profile' in data
        assert data['profile']['name'] == 'John Doe'
        assert data['profile']['age'] == 30
        print("✓ PASSED")
        
    finally:
        os.unlink(db_path)


def test_create_profile_without_auth():
    """Test POST /api/profile/create without authentication"""
    print("\nTest: POST /api/profile/create (no auth)...")
    
    app, db_path = create_test_app()
    client = app.test_client()
    
    try:
        response = client.post('/api/profile/create',
            data=json.dumps({
                'name': 'John Doe',
                'age': 30,
                'location': 'New York'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ PASSED")
        
    finally:
        os.unlink(db_path)


def test_create_profile_invalid_data():
    """Test POST /api/profile/create with invalid data"""
    print("\nTest: POST /api/profile/create (invalid data)...")
    
    app, db_path = create_test_app()
    client = app.test_client()
    
    try:
        token = get_auth_token(client)
        
        # Invalid age (below minimum)
        response = client.post('/api/profile/create',
            headers={'Authorization': f'Bearer {token}'},
            data=json.dumps({
                'name': 'John Doe',
                'age': 17,
                'location': 'New York'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        print("✓ PASSED")
        
    finally:
        os.unlink(db_path)


def test_create_profile_duplicate():
    """Test POST /api/profile/create duplicate profile"""
    print("\nTest: POST /api/profile/create (duplicate)...")
    
    app, db_path = create_test_app()
    client = app.test_client()
    
    try:
        token = get_auth_token(client)
        
        profile_data = {
            'name': 'John Doe',
            'age': 30,
            'location': 'New York'
        }
        
        # Create first profile
        response1 = client.post('/api/profile/create',
            headers={'Authorization': f'Bearer {token}'},
            data=json.dumps(profile_data),
            content_type='application/json'
        )
        assert response1.status_code == 201
        
        # Try to create duplicate
        response2 = client.post('/api/profile/create',
            headers={'Authorization': f'Bearer {token}'},
            data=json.dumps(profile_data),
            content_type='application/json'
        )
        
        assert response2.status_code == 409, f"Expected 409, got {response2.status_code}"
        print("✓ PASSED")
        
    finally:
        os.unlink(db_path)


def test_get_profile_success():
    """Test GET /api/profile with existing profile"""
    print("\nTest: GET /api/profile (success)...")
    
    app, db_path = create_test_app()
    client = app.test_client()
    
    try:
        token = get_auth_token(client)
        
        # Create profile first
        client.post('/api/profile/create',
            headers={'Authorization': f'Bearer {token}'},
            data=json.dumps({
                'name': 'John Doe',
                'age': 30,
                'location': 'New York'
            }),
            content_type='application/json'
        )
        
        # Get profile
        response = client.get('/api/profile',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = json.loads(response.data)
        assert 'profile' in data
        assert data['profile']['name'] == 'John Doe'
        print("✓ PASSED")
        
    finally:
        os.unlink(db_path)


def test_get_profile_not_found():
    """Test GET /api/profile when profile doesn't exist"""
    print("\nTest: GET /api/profile (not found)...")
    
    app, db_path = create_test_app()
    client = app.test_client()
    
    try:
        token = get_auth_token(client)
        
        response = client.get('/api/profile',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ PASSED")
        
    finally:
        os.unlink(db_path)


def test_update_profile_success():
    """Test PUT /api/profile/update with valid data"""
    print("\nTest: PUT /api/profile/update (success)...")
    
    app, db_path = create_test_app()
    client = app.test_client()
    
    try:
        token = get_auth_token(client)
        
        # Create profile first
        client.post('/api/profile/create',
            headers={'Authorization': f'Bearer {token}'},
            data=json.dumps({
                'name': 'John Doe',
                'age': 30,
                'location': 'New York'
            }),
            content_type='application/json'
        )
        
        # Update profile
        response = client.put('/api/profile/update',
            headers={'Authorization': f'Bearer {token}'},
            data=json.dumps({
                'name': 'Jane Doe',
                'age': 32
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = json.loads(response.data)
        assert data['profile']['name'] == 'Jane Doe'
        assert data['profile']['age'] == 32
        assert data['profile']['location'] == 'New York'  # Unchanged
        print("✓ PASSED")
        
    finally:
        os.unlink(db_path)


def test_create_goal_success():
    """Test POST /api/profile/goals with valid data"""
    print("\nTest: POST /api/profile/goals (success)...")
    
    app, db_path = create_test_app()
    client = app.test_client()
    
    try:
        token = get_auth_token(client)
        
        # Create profile first
        client.post('/api/profile/create',
            headers={'Authorization': f'Bearer {token}'},
            data=json.dumps({
                'name': 'John Doe',
                'age': 30,
                'location': 'New York'
            }),
            content_type='application/json'
        )
        
        # Create goal
        future_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        response = client.post('/api/profile/goals',
            headers={'Authorization': f'Bearer {token}'},
            data=json.dumps({
                'goal_type': 'long-term',
                'target_amount': 50000,
                'target_date': future_date,
                'priority': 'high',
                'description': 'Save for house down payment'
            }),
            content_type='application/json'
        )
        
        assert response.status_code == 201, f"Expected 201, got {response.status_code}"
        data = json.loads(response.data)
        assert 'goal' in data
        assert data['goal']['target_amount'] == 50000
        print("✓ PASSED")
        
    finally:
        os.unlink(db_path)


def test_get_goals_success():
    """Test GET /api/profile/goals"""
    print("\nTest: GET /api/profile/goals (success)...")
    
    app, db_path = create_test_app()
    client = app.test_client()
    
    try:
        token = get_auth_token(client)
        
        # Create profile first
        client.post('/api/profile/create',
            headers={'Authorization': f'Bearer {token}'},
            data=json.dumps({
                'name': 'John Doe',
                'age': 30,
                'location': 'New York'
            }),
            content_type='application/json'
        )
        
        # Create two goals
        future_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        client.post('/api/profile/goals',
            headers={'Authorization': f'Bearer {token}'},
            data=json.dumps({
                'goal_type': 'long-term',
                'target_amount': 50000,
                'target_date': future_date,
                'priority': 'high'
            }),
            content_type='application/json'
        )
        
        client.post('/api/profile/goals',
            headers={'Authorization': f'Bearer {token}'},
            data=json.dumps({
                'goal_type': 'short-term',
                'target_amount': 5000,
                'target_date': future_date,
                'priority': 'medium'
            }),
            content_type='application/json'
        )
        
        # Get goals
        response = client.get('/api/profile/goals',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = json.loads(response.data)
        assert 'goals' in data
        assert data['count'] == 2
        # Verify sorting (high priority first)
        assert data['goals'][0]['priority'] == 'high'
        print("✓ PASSED")
        
    finally:
        os.unlink(db_path)


if __name__ == '__main__':
    print("Running Profile API integration tests...")
    
    try:
        test_create_profile_success()
        test_create_profile_without_auth()
        test_create_profile_invalid_data()
        test_create_profile_duplicate()
        test_get_profile_success()
        test_get_profile_not_found()
        test_update_profile_success()
        test_create_goal_success()
        test_get_goals_success()
        
        print("\n✅ All Profile API tests passed!")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
