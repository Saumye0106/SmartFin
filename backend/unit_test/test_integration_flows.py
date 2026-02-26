"""
Integration tests for complete user flows
Tests end-to-end scenarios across multiple services
Feature: user-profile-management
"""

import os
import sqlite3
import tempfile
from profile_service import ProfileService
from goals_service import GoalsService
from risk_assessment_service import RiskAssessmentService


def create_test_db():
    """Create a temporary test database with all required tables"""
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
            status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'cancelled')),
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    ''')
    
    # Create indexes
    cur.execute('CREATE INDEX idx_profile_user_id ON users_profile(user_id)')
    cur.execute('CREATE INDEX idx_goals_user_id ON financial_goals(user_id)')
    cur.execute('CREATE INDEX idx_goals_priority ON financial_goals(priority)')
    cur.execute('CREATE INDEX idx_goals_target_date ON financial_goals(target_date)')
    
    conn.commit()
    conn.close()
    
    return path


# ==================== INTEGRATION TEST 1: Complete Profile Setup Flow ====================
# Validates: Requirements 1.1, 3.3, 2.1

def test_complete_profile_setup_flow():
    """
    Integration Test 1: Complete profile setup flow
    
    Flow: Create profile → Complete risk assessment → Create goal → Verify all data
    """
    print("\n=== Integration Test 1: Complete Profile Setup Flow ===")
    
    db_path = create_test_db()
    profile_service = ProfileService(db_path)
    goals_service = GoalsService(db_path)
    risk_service = RiskAssessmentService(db_path)
    
    try:
        # Step 1: Create user
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute('INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, datetime("now"))',
                   ('testuser@example.com', 'hash123', ))
        conn.commit()
        user_id = cur.lastrowid
        conn.close()
        
        print(f"✓ Step 1: User created (ID: {user_id})")
        
        # Step 2: Create profile
        profile_data = {
            'name': 'John Doe',
            'age': 30,
            'location': 'New York, USA',
            'notification_preferences': {
                'email': True,
                'push': False,
                'in_app': True,
                'frequency': 'daily'
            }
        }
        
        created_profile = profile_service.create_profile(user_id, profile_data)
        assert created_profile is not None, "Profile should be created"
        assert created_profile['name'] == 'John Doe', "Profile name should match"
        assert created_profile['age'] == 30, "Profile age should match"
        
        print("✓ Step 2: Profile created successfully")
        
        # Step 3: Complete risk assessment
        questionnaire = {
            1: 3,  # Hold steady (moderate)
            2: 2,  # Medium-term (3-10 years)
            3: 2,  # Some experience
            4: 3,  # 10-20% (moderate)
            5: 3   # Neutral
        }
        
        risk_score = risk_service.calculate_risk_score(questionnaire)
        assert 1 <= risk_score <= 10, "Risk score should be in valid range"
        
        # Update profile with risk tolerance
        update_data = {'risk_tolerance': risk_score}
        updated_profile = profile_service.update_profile(user_id, update_data)
        assert updated_profile['risk_tolerance'] == risk_score, "Risk tolerance should be updated"
        
        print(f"✓ Step 3: Risk assessment completed (Score: {risk_score})")
        
        # Step 4: Create financial goal
        goal_data = {
            'goal_type': 'long-term',
            'target_amount': 50000.00,
            'target_date': '2027-12-31',
            'priority': 'high',
            'description': 'Save for house down payment'
        }
        
        created_goal = goals_service.create_goal(user_id, goal_data)
        assert created_goal is not None, "Goal should be created"
        assert created_goal['target_amount'] == 50000.00, "Goal amount should match"
        assert created_goal['priority'] == 'high', "Goal priority should match"
        
        print("✓ Step 4: Financial goal created successfully")
        
        # Step 5: Verify all data is retrievable
        final_profile = profile_service.get_profile(user_id)
        assert final_profile is not None, "Profile should be retrievable"
        assert final_profile['name'] == 'John Doe', "Profile data should persist"
        assert final_profile['risk_tolerance'] == risk_score, "Risk tolerance should persist"
        
        goals = goals_service.get_goals(user_id)
        assert len(goals) == 1, "Should have one goal"
        assert goals[0]['target_amount'] == 50000.00, "Goal data should persist"
        
        print("✓ Step 5: All data verified successfully")
        print("✓ Integration Test 1 PASSED")
        
    finally:
        del profile_service
        del goals_service
        del risk_service
        os.unlink(db_path)


if __name__ == '__main__':
    test_complete_profile_setup_flow()
    print("\n=== All Integration Tests Passed ===")



# ==================== INTEGRATION TEST 2: Profile Update Flow ====================
# Validates: Requirements 1.6, 5.3, 4.1

def test_profile_update_flow():
    """
    Integration Test 2: Profile update flow
    
    Flow: Create profile → Update profile → Update preferences → Verify changes
    Note: Profile picture upload is optional and not implemented yet
    """
    print("\n=== Integration Test 2: Profile Update Flow ===")
    
    db_path = create_test_db()
    profile_service = ProfileService(db_path)
    
    try:
        # Step 1: Create user and initial profile
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute('INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, datetime("now"))',
                   ('updateuser@example.com', 'hash123', ))
        conn.commit()
        user_id = cur.lastrowid
        conn.close()
        
        initial_profile_data = {
            'name': 'Jane Smith',
            'age': 25,
            'location': 'Los Angeles, CA',
            'risk_tolerance': 5
        }
        
        created_profile = profile_service.create_profile(user_id, initial_profile_data)
        assert created_profile is not None, "Initial profile should be created"
        
        print("✓ Step 1: Initial profile created")
        
        # Step 2: Update basic profile information
        update_data = {
            'name': 'Jane Smith-Johnson',
            'age': 26,
            'location': 'San Francisco, CA'
        }
        
        updated_profile = profile_service.update_profile(user_id, update_data)
        assert updated_profile['name'] == 'Jane Smith-Johnson', "Name should be updated"
        assert updated_profile['age'] == 26, "Age should be updated"
        assert updated_profile['location'] == 'San Francisco, CA', "Location should be updated"
        assert updated_profile['risk_tolerance'] == 5, "Risk tolerance should remain unchanged"
        
        print("✓ Step 2: Profile information updated")
        
        # Step 3: Update notification preferences
        prefs_update = {
            'notification_preferences': {
                'email': False,
                'push': True,
                'in_app': True,
                'frequency': 'weekly'
            }
        }
        
        updated_profile = profile_service.update_profile(user_id, prefs_update)
        prefs = updated_profile['notification_preferences']
        assert prefs['email'] == False, "Email preference should be updated"
        assert prefs['push'] == True, "Push preference should be updated"
        assert prefs['frequency'] == 'weekly', "Frequency should be updated"
        
        print("✓ Step 3: Notification preferences updated")
        
        # Step 4: Update risk tolerance
        risk_update = {'risk_tolerance': 8}
        updated_profile = profile_service.update_profile(user_id, risk_update)
        assert updated_profile['risk_tolerance'] == 8, "Risk tolerance should be updated"
        
        print("✓ Step 4: Risk tolerance updated")
        
        # Step 5: Verify all changes persisted
        final_profile = profile_service.get_profile(user_id)
        assert final_profile['name'] == 'Jane Smith-Johnson', "Name should persist"
        assert final_profile['age'] == 26, "Age should persist"
        assert final_profile['location'] == 'San Francisco, CA', "Location should persist"
        assert final_profile['risk_tolerance'] == 8, "Risk tolerance should persist"
        assert final_profile['notification_preferences']['frequency'] == 'weekly', "Preferences should persist"
        
        print("✓ Step 5: All changes verified")
        print("✓ Integration Test 2 PASSED")
        
    finally:
        del profile_service
        os.unlink(db_path)


if __name__ == '__main__':
    test_complete_profile_setup_flow()
    test_profile_update_flow()
    print("\n=== All Integration Tests Passed ===")



# ==================== INTEGRATION TEST 3: Goals Management Flow ====================
# Validates: Requirements 2.1, 2.7, 2.8, 2.9

def test_goals_management_flow():
    """
    Integration Test 3: Goals management flow
    
    Flow: Create multiple goals → Update goal → Delete goal → Verify sorting
    """
    print("\n=== Integration Test 3: Goals Management Flow ===")
    
    db_path = create_test_db()
    profile_service = ProfileService(db_path)
    goals_service = GoalsService(db_path)
    
    try:
        # Step 1: Create user and profile
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute('INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, datetime("now"))',
                   ('goalsuser@example.com', 'hash123', ))
        conn.commit()
        user_id = cur.lastrowid
        conn.close()
        
        profile_data = {
            'name': 'Bob Johnson',
            'age': 35,
            'location': 'Chicago, IL'
        }
        profile_service.create_profile(user_id, profile_data)
        
        print("✓ Step 1: User and profile created")
        
        # Step 2: Create multiple goals with different priorities and dates
        goal1_data = {
            'goal_type': 'short-term',
            'target_amount': 5000.00,
            'target_date': '2026-06-30',
            'priority': 'high',
            'description': 'Emergency fund'
        }
        
        goal2_data = {
            'goal_type': 'long-term',
            'target_amount': 100000.00,
            'target_date': '2030-12-31',
            'priority': 'medium',
            'description': 'Retirement savings'
        }
        
        goal3_data = {
            'goal_type': 'short-term',
            'target_amount': 3000.00,
            'target_date': '2026-03-31',
            'priority': 'high',
            'description': 'Vacation fund'
        }
        
        goal4_data = {
            'goal_type': 'long-term',
            'target_amount': 50000.00,
            'target_date': '2028-12-31',
            'priority': 'low',
            'description': 'Investment portfolio'
        }
        
        goal1 = goals_service.create_goal(user_id, goal1_data)
        goal2 = goals_service.create_goal(user_id, goal2_data)
        goal3 = goals_service.create_goal(user_id, goal3_data)
        goal4 = goals_service.create_goal(user_id, goal4_data)
        
        assert goal1 is not None, "Goal 1 should be created"
        assert goal2 is not None, "Goal 2 should be created"
        assert goal3 is not None, "Goal 3 should be created"
        assert goal4 is not None, "Goal 4 should be created"
        
        print("✓ Step 2: Four goals created")
        
        # Step 3: Verify goals are sorted by priority then date
        goals = goals_service.get_goals(user_id)
        assert len(goals) == 4, "Should have 4 goals"
        
        # Expected order: high priority (earliest date first), then medium, then low
        # Goal 3 (high, 2026-03-31), Goal 1 (high, 2026-06-30), Goal 2 (medium, 2030-12-31), Goal 4 (low, 2028-12-31)
        assert goals[0]['priority'] == 'high', "First goal should be high priority"
        assert goals[1]['priority'] == 'high', "Second goal should be high priority"
        assert goals[0]['target_date'] < goals[1]['target_date'], "High priority goals should be sorted by date"
        assert goals[2]['priority'] == 'medium', "Third goal should be medium priority"
        assert goals[3]['priority'] == 'low', "Fourth goal should be low priority"
        
        print("✓ Step 3: Goals sorted correctly (priority then date)")
        
        # Step 4: Update a goal
        update_data = {
            'target_amount': 6000.00,
            'priority': 'medium',
            'status': 'active'
        }
        
        updated_goal = goals_service.update_goal(goal1['id'], user_id, update_data)
        assert updated_goal['target_amount'] == 6000.00, "Goal amount should be updated"
        assert updated_goal['priority'] == 'medium', "Goal priority should be updated"
        
        print("✓ Step 4: Goal updated successfully")
        
        # Step 5: Delete a goal
        deleted = goals_service.delete_goal(goal4['id'], user_id)
        assert deleted == True, "Goal should be deleted"
        
        remaining_goals = goals_service.get_goals(user_id)
        assert len(remaining_goals) == 3, "Should have 3 goals after deletion"
        assert all(g['id'] != goal4['id'] for g in remaining_goals), "Deleted goal should not be in list"
        
        print("✓ Step 5: Goal deleted successfully")
        
        # Step 6: Verify final state
        final_goals = goals_service.get_goals(user_id)
        assert len(final_goals) == 3, "Final count should be 3"
        
        # Verify sorting is still correct after updates
        for i in range(len(final_goals) - 1):
            current_priority = final_goals[i]['priority']
            next_priority = final_goals[i + 1]['priority']
            priority_order = {'high': 0, 'medium': 1, 'low': 2}
            assert priority_order[current_priority] <= priority_order[next_priority], \
                "Goals should remain sorted by priority"
        
        print("✓ Step 6: Final state verified")
        print("✓ Integration Test 3 PASSED")
        
    finally:
        del profile_service
        del goals_service
        os.unlink(db_path)


if __name__ == '__main__':
    test_complete_profile_setup_flow()
    test_profile_update_flow()
    test_goals_management_flow()
    print("\n=== All Integration Tests Passed ===")
