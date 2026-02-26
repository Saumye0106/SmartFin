"""
Unit Tests for Profile Picture Edge Cases
Tests Task 6.5 from the implementation plan
"""

import sys
import os
import tempfile
import sqlite3
import io
from datetime import datetime
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
            email_verified INTEGER DEFAULT 0,
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
    
    # Create test user
    password_hash = generate_password_hash('testpass123')
    cur.execute(
        'INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)',
        ('testuser@example.com', password_hash, datetime.utcnow().isoformat())
    )
    
    # Create profile for test user
    cur.execute('''
        INSERT INTO users_profile (user_id, name, age, location)
        VALUES (1, 'Test User', 30, 'Test City')
    ''')
    
    conn.commit()
    conn.close()
    
    # Import app and configure for testing
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import app as flask_app
    flask_app.DB_PATH = db_path
    flask_app.app.config['TESTING'] = True
    flask_app.app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    
    # Create temporary upload folder
    upload_dir = tempfile.mkdtemp()
    flask_app.app.config['UPLOAD_FOLDER'] = upload_dir
    
    # Reinitialize services with test database
    from profile_service import ProfileService
    flask_app.profile_service = ProfileService(db_path)
    
    return flask_app.app, db_path, upload_dir


def get_auth_token(client):
    """Login and get JWT token"""
    import json
    response = client.post('/login', 
        data=json.dumps({
            'email': 'testuser@example.com',
            'password': 'testpass123'
        }),
        content_type='application/json'
    )
    data = json.loads(response.data)
    return data['token']


def cleanup_test_app(db_path, upload_dir):
    """Clean up test resources"""
    try:
        if os.path.exists(db_path):
            os.unlink(db_path)
    except:
        pass
    
    try:
        if os.path.exists(upload_dir):
            import shutil
            shutil.rmtree(upload_dir)
    except:
        pass


def test_jpeg_upload():
    """Test JPEG upload (should pass) - Requirement 5.1"""
    app, db_path, upload_dir = create_test_app()
    client = app.test_client()
    
    try:
        token = get_auth_token(client)
        
        # Create JPEG file
        file_content = b'fake jpeg content'
        filename = 'test_image.jpeg'
        
        data = {
            'file': (io.BytesIO(file_content), filename)
        }
        
        response = client.post('/api/profile/upload-picture',
            headers={'Authorization': f'Bearer {token}'},
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200, \
            f"JPEG upload should succeed, got {response.status_code}"
        
        import json
        response_data = json.loads(response.data)
        assert 'profile_picture_url' in response_data, \
            "Response should contain profile_picture_url"
        
        print("✓ JPEG upload test passed")
        
    finally:
        cleanup_test_app(db_path, upload_dir)


def test_jpg_upload():
    """Test JPG upload (should pass) - Requirement 5.1"""
    app, db_path, upload_dir = create_test_app()
    client = app.test_client()
    
    try:
        token = get_auth_token(client)
        
        # Create JPG file
        file_content = b'fake jpg content'
        filename = 'test_image.jpg'
        
        data = {
            'file': (io.BytesIO(file_content), filename)
        }
        
        response = client.post('/api/profile/upload-picture',
            headers={'Authorization': f'Bearer {token}'},
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200, \
            f"JPG upload should succeed, got {response.status_code}"
        
        import json
        response_data = json.loads(response.data)
        assert 'profile_picture_url' in response_data, \
            "Response should contain profile_picture_url"
        
        print("✓ JPG upload test passed")
        
    finally:
        cleanup_test_app(db_path, upload_dir)


def test_png_upload():
    """Test PNG upload (should pass) - Requirement 5.1"""
    app, db_path, upload_dir = create_test_app()
    client = app.test_client()
    
    try:
        token = get_auth_token(client)
        
        # Create PNG file
        file_content = b'fake png content'
        filename = 'test_image.png'
        
        data = {
            'file': (io.BytesIO(file_content), filename)
        }
        
        response = client.post('/api/profile/upload-picture',
            headers={'Authorization': f'Bearer {token}'},
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200, \
            f"PNG upload should succeed, got {response.status_code}"
        
        import json
        response_data = json.loads(response.data)
        assert 'profile_picture_url' in response_data, \
            "Response should contain profile_picture_url"
        
        print("✓ PNG upload test passed")
        
    finally:
        cleanup_test_app(db_path, upload_dir)


def test_webp_upload():
    """Test WebP upload (should pass) - Requirement 5.1"""
    app, db_path, upload_dir = create_test_app()
    client = app.test_client()
    
    try:
        token = get_auth_token(client)
        
        # Create WebP file
        file_content = b'fake webp content'
        filename = 'test_image.webp'
        
        data = {
            'file': (io.BytesIO(file_content), filename)
        }
        
        response = client.post('/api/profile/upload-picture',
            headers={'Authorization': f'Bearer {token}'},
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 200, \
            f"WebP upload should succeed, got {response.status_code}"
        
        import json
        response_data = json.loads(response.data)
        assert 'profile_picture_url' in response_data, \
            "Response should contain profile_picture_url"
        
        print("✓ WebP upload test passed")
        
    finally:
        cleanup_test_app(db_path, upload_dir)


def test_gif_upload():
    """Test GIF upload (should fail) - Requirement 5.1"""
    app, db_path, upload_dir = create_test_app()
    client = app.test_client()
    
    try:
        token = get_auth_token(client)
        
        # Create GIF file
        file_content = b'fake gif content'
        filename = 'test_image.gif'
        
        data = {
            'file': (io.BytesIO(file_content), filename)
        }
        
        response = client.post('/api/profile/upload-picture',
            headers={'Authorization': f'Bearer {token}'},
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400, \
            f"GIF upload should fail with 400, got {response.status_code}"
        
        import json
        response_data = json.loads(response.data)
        error_message = response_data.get('error', '').lower()
        assert 'format' in error_message or 'allowed' in error_message, \
            f"Error message should mention format: {error_message}"
        
        print("✓ GIF upload rejection test passed")
        
    finally:
        cleanup_test_app(db_path, upload_dir)


def test_pdf_upload():
    """Test PDF upload (should fail) - Requirement 5.1"""
    app, db_path, upload_dir = create_test_app()
    client = app.test_client()
    
    try:
        token = get_auth_token(client)
        
        # Create PDF file
        file_content = b'fake pdf content'
        filename = 'test_document.pdf'
        
        data = {
            'file': (io.BytesIO(file_content), filename)
        }
        
        response = client.post('/api/profile/upload-picture',
            headers={'Authorization': f'Bearer {token}'},
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400, \
            f"PDF upload should fail with 400, got {response.status_code}"
        
        import json
        response_data = json.loads(response.data)
        error_message = response_data.get('error', '').lower()
        assert 'format' in error_message or 'allowed' in error_message, \
            f"Error message should mention format: {error_message}"
        
        print("✓ PDF upload rejection test passed")
        
    finally:
        cleanup_test_app(db_path, upload_dir)


def test_file_size_4_9mb():
    """Test 4.9MB file upload (should pass) - Requirement 5.2"""
    app, db_path, upload_dir = create_test_app()
    client = app.test_client()
    
    try:
        token = get_auth_token(client)
        
        # Create 4.9MB file
        file_size = int(4.9 * 1024 * 1024)
        file_content = b'x' * file_size
        filename = 'test_large_image.jpg'
        
        data = {
            'file': (io.BytesIO(file_content), filename)
        }
        
        response = client.post('/api/profile/upload-picture',
            headers={'Authorization': f'Bearer {token}'},
            data=data,
            content_type='multipart/form-data'
        )
        
        # Should not be rejected due to size
        if response.status_code == 400:
            import json
            response_data = json.loads(response.data)
            error_message = response_data.get('error', '').lower()
            assert 'size' not in error_message and 'large' not in error_message, \
                f"4.9MB file should not be rejected due to size: {error_message}"
        else:
            assert response.status_code in [200, 500], \
                f"4.9MB file should be accepted or fail for non-size reasons, got {response.status_code}"
        
        print("✓ 4.9MB file size test passed")
        
    finally:
        cleanup_test_app(db_path, upload_dir)


def test_file_size_5_1mb():
    """Test 5.1MB file upload (should fail) - Requirement 5.2"""
    app, db_path, upload_dir = create_test_app()
    client = app.test_client()
    
    try:
        token = get_auth_token(client)
        
        # Create 5.1MB file
        file_size = int(5.1 * 1024 * 1024)
        file_content = b'x' * file_size
        filename = 'test_oversized_image.jpg'
        
        data = {
            'file': (io.BytesIO(file_content), filename)
        }
        
        response = client.post('/api/profile/upload-picture',
            headers={'Authorization': f'Bearer {token}'},
            data=data,
            content_type='multipart/form-data'
        )
        
        # Should be rejected with 400, 413, or 500
        assert response.status_code in [400, 413, 500], \
            f"5.1MB file should be rejected, got {response.status_code}"
        
        print("✓ 5.1MB file size rejection test passed")
        
    finally:
        cleanup_test_app(db_path, upload_dir)


def test_no_file_provided():
    """Test upload without file (should fail)"""
    app, db_path, upload_dir = create_test_app()
    client = app.test_client()
    
    try:
        token = get_auth_token(client)
        
        response = client.post('/api/profile/upload-picture',
            headers={'Authorization': f'Bearer {token}'},
            data={},
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400, \
            f"Upload without file should fail with 400, got {response.status_code}"
        
        import json
        response_data = json.loads(response.data)
        error_message = response_data.get('error', '').lower()
        assert 'file' in error_message or 'no' in error_message, \
            f"Error message should mention missing file: {error_message}"
        
        print("✓ No file provided test passed")
        
    finally:
        cleanup_test_app(db_path, upload_dir)


def test_empty_filename():
    """Test upload with empty filename (should fail)"""
    app, db_path, upload_dir = create_test_app()
    client = app.test_client()
    
    try:
        token = get_auth_token(client)
        
        # Create file with empty filename
        file_content = b'test content'
        
        data = {
            'file': (io.BytesIO(file_content), '')
        }
        
        response = client.post('/api/profile/upload-picture',
            headers={'Authorization': f'Bearer {token}'},
            data=data,
            content_type='multipart/form-data'
        )
        
        assert response.status_code == 400, \
            f"Upload with empty filename should fail with 400, got {response.status_code}"
        
        import json
        response_data = json.loads(response.data)
        error_message = response_data.get('error', '').lower()
        assert 'file' in error_message or 'selected' in error_message, \
            f"Error message should mention file selection: {error_message}"
        
        print("✓ Empty filename test passed")
        
    finally:
        cleanup_test_app(db_path, upload_dir)


def test_delete_nonexistent_picture():
    """Test deleting profile picture when none exists (should fail with 404)"""
    app, db_path, upload_dir = create_test_app()
    client = app.test_client()
    
    try:
        token = get_auth_token(client)
        
        # Try to delete without uploading first
        response = client.delete('/api/profile/delete-picture',
            headers={'Authorization': f'Bearer {token}'}
        )
        
        assert response.status_code == 404, \
            f"Deleting non-existent picture should return 404, got {response.status_code}"
        
        import json
        response_data = json.loads(response.data)
        error_message = response_data.get('error', '').lower()
        assert 'no' in error_message or 'not' in error_message, \
            f"Error message should mention no picture: {error_message}"
        
        print("✓ Delete non-existent picture test passed")
        
    finally:
        cleanup_test_app(db_path, upload_dir)


if __name__ == '__main__':
    print("Running Profile Picture Unit Tests...")
    print("\n" + "="*70)
    
    try:
        print("\nTest 1: JPEG upload (should pass)...")
        test_jpeg_upload()
        
        print("\nTest 2: JPG upload (should pass)...")
        test_jpg_upload()
        
        print("\nTest 3: PNG upload (should pass)...")
        test_png_upload()
        
        print("\nTest 4: WebP upload (should pass)...")
        test_webp_upload()
        
        print("\nTest 5: GIF upload (should fail)...")
        test_gif_upload()
        
        print("\nTest 6: PDF upload (should fail)...")
        test_pdf_upload()
        
        print("\nTest 7: 4.9MB file (should pass)...")
        test_file_size_4_9mb()
        
        print("\nTest 8: 5.1MB file (should fail)...")
        test_file_size_5_1mb()
        
        print("\nTest 9: No file provided (should fail)...")
        test_no_file_provided()
        
        print("\nTest 10: Empty filename (should fail)...")
        test_empty_filename()
        
        print("\nTest 11: Delete non-existent picture (should fail)...")
        test_delete_nonexistent_picture()
        
        print("\n" + "="*70)
        print("✅ All Profile Picture Unit Tests passed!")
        
    except AssertionError as e:
        print(f"\n❌ Unit test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
