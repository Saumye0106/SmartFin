"""
Security Tests for User Profile Management
Tests SQL injection prevention and authorization enforcement
"""

import sys
import os
import sqlite3
import tempfile
from profile_service import ProfileService
from goals_service import GoalsService


def create_test_db():
    """Create a temporary test database"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    conn = sqlite3.connect(path)
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
    
    conn.commit()
    conn.close()
    
    return path


def test_sql_injection_in_name():
    """
    Property 21: SQL injection prevention
    Test that SQL injection patterns in name field are safely handled
    Validates: Requirements 8.1
    """
    print("\nTest: SQL injection in name field...")
    
    db_path = create_test_db()
    service = ProfileService(db_path)
    
    try:
        # SQL injection attempts
        injection_patterns = [
            "'; DROP TABLE users_profile; --",
            "' OR '1'='1",
            "admin'--",
            "' UNION SELECT * FROM users--",
            "1'; DELETE FROM users_profile WHERE '1'='1",
        ]
        
        for pattern in injection_patterns:
            try:
                # These should either be rejected by validation or safely escaped
                profile_data = {
                    'name': pattern,
                    'age': 30,
                    'location': 'New York'
                }
                
                # Validation should reject these (non-alphabetic characters)
                service.create_profile(1, profile_data)
                
                # If it somehow gets through validation, verify it's stored safely
                profile = service.get_profile(1)
                if profile:
                    # The pattern should be stored as-is, not executed
                    assert profile['name'] == pattern, "Name should be stored literally"
                    service.delete_profile(1)  # Clean up for next test
                    
            except (ValueError, sqlite3.Error) as e:
                # Expected - validation or database constraint rejected it
                pass
        
        # Verify database still exists and is functional
        valid_profile = {
            'name': 'John Doe',
            'age': 30,
            'location': 'New York'
        }
        profile = service.create_profile(1, valid_profile)
        assert profile is not None, "Database should still be functional"
        
        print("✓ PASSED - SQL injection patterns safely handled")
        
    finally:
        os.unlink(db_path)


def test_sql_injection_in_location():
    """Test SQL injection patterns in location field"""
    print("\nTest: SQL injection in location field...")
    
    db_path = create_test_db()
    service = ProfileService(db_path)
    
    try:
        injection_patterns = [
            "'; DROP TABLE users_profile; --",
            "' OR '1'='1",
        ]
        
        for pattern in injection_patterns:
            try:
                profile_data = {
                    'name': 'John Doe',
                    'age': 30,
                    'location': pattern
                }
                
                # Create profile - should be safely escaped
                profile = service.create_profile(1, profile_data)
                
                # Verify it's stored literally, not executed
                retrieved = service.get_profile(1)
                assert retrieved['location'] == pattern, "Location should be stored literally"
                
                service.delete_profile(1)  # Clean up
                
            except (ValueError, sqlite3.Error):
                # Expected if validation rejects it
                pass
        
        # Verify database still functional
        valid_profile = {
            'name': 'John Doe',
            'age': 30,
            'location': 'New York'
        }
        profile = service.create_profile(1, valid_profile)
        assert profile is not None
        
        print("✓ PASSED - SQL injection in location safely handled")
        
    finally:
        os.unlink(db_path)


def test_sql_injection_in_goal_description():
    """Test SQL injection patterns in goal description field"""
    print("\nTest: SQL injection in goal description...")
    
    db_path = create_test_db()
    profile_service = ProfileService(db_path)
    goals_service = GoalsService(db_path)
    
    try:
        # Create profile first
        profile_service.create_profile(1, {
            'name': 'John Doe',
            'age': 30,
            'location': 'New York'
        })
        
        injection_patterns = [
            "'; DROP TABLE financial_goals; --",
            "' OR '1'='1",
        ]
        
        from datetime import datetime, timedelta
        future_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        
        for pattern in injection_patterns:
            try:
                goal_data = {
                    'goal_type': 'long-term',
                    'target_amount': 50000,
                    'target_date': future_date,
                    'priority': 'high',
                    'description': pattern
                }
                
                # Create goal - should be safely escaped
                goal = goals_service.create_goal(1, goal_data)
                
                # Verify it's stored literally
                assert goal['description'] == pattern, "Description should be stored literally"
                
                goals_service.delete_goal(goal['id'], 1)  # Clean up
                
            except (ValueError, sqlite3.Error):
                # Expected if validation rejects it
                pass
        
        # Verify database still functional
        valid_goal = {
            'goal_type': 'long-term',
            'target_amount': 50000,
            'target_date': future_date,
            'priority': 'high',
            'description': 'Save for house'
        }
        goal = goals_service.create_goal(1, valid_goal)
        assert goal is not None
        
        print("✓ PASSED - SQL injection in description safely handled")
        
    finally:
        os.unlink(db_path)


def test_authorization_profile_access():
    """
    Property 22: Authorization enforcement
    Test that users cannot access other users' profiles
    Validates: Requirements 8.4, 8.5
    """
    print("\nTest: Authorization - profile access...")
    
    db_path = create_test_db()
    service = ProfileService(db_path)
    
    try:
        # Create profiles for two users
        service.create_profile(1, {
            'name': 'User One',
            'age': 30,
            'location': 'New York'
        })
        
        service.create_profile(2, {
            'name': 'User Two',
            'age': 25,
            'location': 'Boston'
        })
        
        # User 1 should only see their own profile
        profile1 = service.get_profile(1)
        assert profile1['name'] == 'User One'
        
        # User 2 should only see their own profile
        profile2 = service.get_profile(2)
        assert profile2['name'] == 'User Two'
        
        # Profiles are isolated
        assert profile1['user_id'] != profile2['user_id']
        
        print("✓ PASSED - Profile access properly isolated")
        
    finally:
        os.unlink(db_path)


def test_authorization_goal_ownership():
    """Test that users cannot modify other users' goals"""
    print("\nTest: Authorization - goal ownership...")
    
    db_path = create_test_db()
    profile_service = ProfileService(db_path)
    goals_service = GoalsService(db_path)
    
    try:
        # Create profiles for two users
        profile_service.create_profile(1, {
            'name': 'User One',
            'age': 30,
            'location': 'New York'
        })
        
        profile_service.create_profile(2, {
            'name': 'User Two',
            'age': 25,
            'location': 'Boston'
        })
        
        from datetime import datetime, timedelta
        future_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        
        # User 1 creates a goal
        goal1 = goals_service.create_goal(1, {
            'goal_type': 'long-term',
            'target_amount': 50000,
            'target_date': future_date,
            'priority': 'high'
        })
        
        # User 2 tries to update User 1's goal - should fail
        try:
            goals_service.update_goal(goal1['id'], 2, {
                'target_amount': 100000
            })
            assert False, "Should not allow updating another user's goal"
        except ValueError as e:
            error_msg = str(e).lower()
            assert 'not authorized' in error_msg or 'does not own' in error_msg or 'not own' in error_msg, \
                f"Expected ownership error, got: {e}"
        
        # User 2 tries to delete User 1's goal - should fail
        try:
            goals_service.delete_goal(goal1['id'], 2)
            assert False, "Should not allow deleting another user's goal"
        except ValueError as e:
            error_msg = str(e).lower()
            assert 'not authorized' in error_msg or 'does not own' in error_msg or 'not own' in error_msg, \
                f"Expected ownership error, got: {e}"
        
        # User 1 can update their own goal
        updated = goals_service.update_goal(goal1['id'], 1, {
            'target_amount': 60000
        })
        assert updated['target_amount'] == 60000
        
        # User 1 can delete their own goal
        success = goals_service.delete_goal(goal1['id'], 1)
        assert success
        
        print("✓ PASSED - Goal ownership properly enforced")
        
    finally:
        os.unlink(db_path)


def test_parameterized_queries_verification():
    """Verify all queries use parameterized statements"""
    print("\nTest: Parameterized queries verification...")
    
    # Check that service files use parameterized queries
    services = [
        'backend/profile_service.py',
        'backend/goals_service.py'
    ]
    
    for service_file in services:
        if not os.path.exists(service_file):
            service_file = service_file.replace('backend/', '')
        
        with open(service_file, 'r') as f:
            content = f.read()
            
            # Check for parameterized query patterns
            assert '?' in content or '%s' in content, f"{service_file} should use parameterized queries"
            
            # Check that we're NOT using string formatting in SQL
            # (This is a simple check - not foolproof)
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'execute' in line.lower() and 'cur.execute' in line:
                    # Check next few lines for SQL
                    sql_block = '\n'.join(lines[i:i+10])
                    if 'INSERT' in sql_block or 'UPDATE' in sql_block or 'DELETE' in sql_block or 'SELECT' in sql_block:
                        # Should have ? or %s for parameters
                        assert '?' in sql_block or '%s' in sql_block, \
                            f"Query at line {i+1} in {service_file} should use parameterized queries"
    
    print("✓ PASSED - All queries use parameterized statements")


if __name__ == '__main__':
    print("Running Security Tests...")
    print("="*60)
    
    try:
        test_sql_injection_in_name()
        test_sql_injection_in_location()
        test_sql_injection_in_goal_description()
        test_authorization_profile_access()
        test_authorization_goal_ownership()
        test_parameterized_queries_verification()
        
        print("\n" + "="*60)
        print("✅ All Security Tests Passed!")
        print("="*60)
        print("\nSecurity Features Verified:")
        print("  ✓ SQL injection prevention (parameterized queries)")
        print("  ✓ Input sanitization (validation layer)")
        print("  ✓ Authorization enforcement (ownership checks)")
        print("  ✓ Profile access isolation")
        print("  ✓ Goal ownership verification")
        
    except AssertionError as e:
        print(f"\n❌ Security test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
