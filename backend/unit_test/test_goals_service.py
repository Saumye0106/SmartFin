"""
Property-based and unit tests for GoalsService
Feature: user-profile-management
"""

import os
import sqlite3
import tempfile
from datetime import date, timedelta
from hypothesis import given, strategies as st, settings
from goals_service import GoalsService


# Test database setup
def create_test_db():
    """Create a temporary test database"""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    
    # Create users_profile table
    cur.execute('''
        CREATE TABLE users_profile (
            user_id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            location TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
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


# Hypothesis strategies
valid_goal_type_strategy = st.sampled_from(['short-term', 'long-term'])
valid_priority_strategy = st.sampled_from(['low', 'medium', 'high'])
valid_amount_strategy = st.floats(min_value=0.01, max_value=1000000.0)
future_date_strategy = st.dates(
    min_value=date.today() + timedelta(days=1),
    max_value=date.today() + timedelta(days=3650)
)


# Feature: user-profile-management, Property 5: Goal creation round-trip
@given(
    goal_type=valid_goal_type_strategy,
    target_amount=valid_amount_strategy,
    target_date=future_date_strategy,
    priority=valid_priority_strategy
)
@settings(max_examples=100, deadline=None)
def test_property_5_goal_creation_roundtrip(goal_type, target_amount, target_date, priority):
    """
    Property 5: Goal creation round-trip
    For any valid goal data, creating a goal then retrieving it should return 
    an equivalent goal with all fields matching and status defaulting to "active".
    
    Validates: Requirements 2.1, 2.6, 6.4, 6.5
    """
    db_path = create_test_db()
    service = GoalsService(db_path)
    
    try:
        user_id = 1
        goal_data = {
            'goal_type': goal_type,
            'target_amount': target_amount,
            'target_date': target_date.isoformat(),
            'priority': priority,
            'description': 'Test goal'
        }
        
        # Create goal
        created_goal = service.create_goal(user_id, goal_data)
        
        # Retrieve goal
        retrieved_goal = service.get_goal(created_goal['id'])
        
        # Verify equivalence
        assert retrieved_goal is not None
        assert retrieved_goal['goal_type'] == goal_type
        assert abs(retrieved_goal['target_amount'] - target_amount) < 0.01  # Float comparison
        assert retrieved_goal['target_date'] == target_date.isoformat()
        assert retrieved_goal['priority'] == priority
        assert retrieved_goal['status'] == 'active'  # Default status
        assert retrieved_goal['user_id'] == user_id
        
    finally:
        os.unlink(db_path)


# Feature: user-profile-management, Property 7: Goals are sorted by priority then date
def test_property_7_goals_sorted_by_priority_then_date():
    """
    Property 7: Goals are sorted by priority then date
    For any set of goals, retrieving them should return goals ordered first by 
    priority (high > medium > low) and then by target_date (earliest first).
    
    Validates: Requirements 2.7
    """
    db_path = create_test_db()
    service = GoalsService(db_path)
    
    try:
        user_id = 1
        
        # Create goals with different priorities and dates
        goals_data = [
            {'goal_type': 'short-term', 'target_amount': 1000, 'target_date': '2026-06-01', 'priority': 'low'},
            {'goal_type': 'long-term', 'target_amount': 5000, 'target_date': '2026-03-01', 'priority': 'high'},
            {'goal_type': 'short-term', 'target_amount': 2000, 'target_date': '2026-05-01', 'priority': 'medium'},
            {'goal_type': 'long-term', 'target_amount': 3000, 'target_date': '2026-02-01', 'priority': 'high'},
            {'goal_type': 'short-term', 'target_amount': 1500, 'target_date': '2026-04-01', 'priority': 'medium'},
        ]
        
        for goal_data in goals_data:
            service.create_goal(user_id, goal_data)
        
        # Retrieve goals
        goals = service.get_goals(user_id)
        
        # Verify sorting
        assert len(goals) == 5
        
        # First two should be high priority, sorted by date
        assert goals[0]['priority'] == 'high'
        assert goals[0]['target_date'] == '2026-02-01'
        assert goals[1]['priority'] == 'high'
        assert goals[1]['target_date'] == '2026-03-01'
        
        # Next two should be medium priority, sorted by date
        assert goals[2]['priority'] == 'medium'
        assert goals[2]['target_date'] == '2026-04-01'
        assert goals[3]['priority'] == 'medium'
        assert goals[3]['target_date'] == '2026-05-01'
        
        # Last should be low priority
        assert goals[4]['priority'] == 'low'
        assert goals[4]['target_date'] == '2026-06-01'
        
    finally:
        os.unlink(db_path)


# Feature: user-profile-management, Property 8: Goal updates preserve identity
def test_property_8_goal_updates_preserve_identity():
    """
    Property 8: Goal updates preserve identity
    For any existing goal and valid update data, updating the goal should 
    preserve the goal id and created_at timestamp.
    
    Validates: Requirements 2.8
    """
    db_path = create_test_db()
    service = GoalsService(db_path)
    
    try:
        user_id = 1
        goal_data = {
            'goal_type': 'short-term',
            'target_amount': 1000.0,
            'target_date': '2026-12-31',
            'priority': 'medium'
        }
        
        # Create goal
        created_goal = service.create_goal(user_id, goal_data)
        original_id = created_goal['id']
        original_created_at = created_goal['created_at']
        
        # Update goal
        import time
        time.sleep(0.01)
        
        updates = {
            'target_amount': 2000.0,
            'priority': 'high'
        }
        
        updated_goal = service.update_goal(original_id, user_id, updates)
        
        # Verify identity preserved
        assert updated_goal['id'] == original_id
        assert updated_goal['created_at'] == original_created_at
        assert updated_goal['updated_at'] >= original_created_at
        
        # Verify updates applied
        assert updated_goal['target_amount'] == 2000.0
        assert updated_goal['priority'] == 'high'
        assert updated_goal['goal_type'] == 'short-term'  # Unchanged
        
    finally:
        os.unlink(db_path)


# Feature: user-profile-management, Property 9: Goal deletion removes from database
def test_property_9_goal_deletion():
    """
    Property 9: Goal deletion removes from database
    For any existing goal, deleting it should result in subsequent retrieval 
    attempts returning None or the goal being absent from the user's goal list.
    
    Validates: Requirements 2.9
    """
    db_path = create_test_db()
    service = GoalsService(db_path)
    
    try:
        user_id = 1
        goal_data = {
            'goal_type': 'short-term',
            'target_amount': 1000.0,
            'target_date': '2026-12-31',
            'priority': 'low'
        }
        
        # Create goal
        created_goal = service.create_goal(user_id, goal_data)
        goal_id = created_goal['id']
        
        # Verify goal exists
        assert service.get_goal(goal_id) is not None
        assert len(service.get_goals(user_id)) == 1
        
        # Delete goal
        result = service.delete_goal(goal_id, user_id)
        assert result is True
        
        # Verify goal is gone
        assert service.get_goal(goal_id) is None
        assert len(service.get_goals(user_id)) == 0
        
    finally:
        os.unlink(db_path)


# Feature: user-profile-management, Property 10: Goals have unique identifiers
def test_property_10_goal_unique_ids():
    """
    Property 10: Goals have unique identifiers
    For any set of goals created by the system, all goal IDs should be unique.
    
    Validates: Requirements 7.6
    """
    db_path = create_test_db()
    service = GoalsService(db_path)
    
    try:
        user_id = 1
        goal_ids = set()
        
        # Create 100 goals
        for i in range(100):
            goal_data = {
                'goal_type': 'short-term',
                'target_amount': 1000.0 + i,
                'target_date': '2026-12-31',
                'priority': 'medium'
            }
            
            created_goal = service.create_goal(user_id, goal_data)
            goal_ids.add(created_goal['id'])
        
        # Verify all IDs are unique
        assert len(goal_ids) == 100
        
    finally:
        os.unlink(db_path)


# Unit tests for edge cases
def test_edge_case_target_amount_minimum():
    """Test goal with minimum target amount (0.01)"""
    db_path = create_test_db()
    service = GoalsService(db_path)
    
    try:
        goal_data = {
            'goal_type': 'short-term',
            'target_amount': 0.01,
            'target_date': '2026-12-31',
            'priority': 'low'
        }
        
        goal = service.create_goal(1, goal_data)
        assert abs(goal['target_amount'] - 0.01) < 0.001
        
    finally:
        os.unlink(db_path)


def test_edge_case_ownership_check_update():
    """Test that user cannot update another user's goal"""
    db_path = create_test_db()
    service = GoalsService(db_path)
    
    try:
        # User 1 creates goal
        goal_data = {
            'goal_type': 'short-term',
            'target_amount': 1000.0,
            'target_date': '2026-12-31',
            'priority': 'medium'
        }
        
        goal = service.create_goal(1, goal_data)
        goal_id = goal['id']
        
        # User 2 tries to update
        try:
            service.update_goal(goal_id, 2, {'target_amount': 2000.0})
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert 'does not own' in str(e)
        
    finally:
        os.unlink(db_path)


def test_edge_case_ownership_check_delete():
    """Test that user cannot delete another user's goal"""
    db_path = create_test_db()
    service = GoalsService(db_path)
    
    try:
        # User 1 creates goal
        goal_data = {
            'goal_type': 'short-term',
            'target_amount': 1000.0,
            'target_date': '2026-12-31',
            'priority': 'medium'
        }
        
        goal = service.create_goal(1, goal_data)
        goal_id = goal['id']
        
        # User 2 tries to delete
        try:
            service.delete_goal(goal_id, 2)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert 'does not own' in str(e)
        
    finally:
        os.unlink(db_path)


if __name__ == '__main__':
    print("Running GoalsService property-based tests...\n")
    
    print("Property 5: Goal creation round-trip (100 examples)...")
    test_property_5_goal_creation_roundtrip()
    print("✓ PASSED\n")
    
    print("Property 7: Goals sorted by priority then date...")
    test_property_7_goals_sorted_by_priority_then_date()
    print("✓ PASSED\n")
    
    print("Property 8: Goal updates preserve identity...")
    test_property_8_goal_updates_preserve_identity()
    print("✓ PASSED\n")
    
    print("Property 9: Goal deletion...")
    test_property_9_goal_deletion()
    print("✓ PASSED\n")
    
    print("Property 10: Goal unique IDs...")
    test_property_10_goal_unique_ids()
    print("✓ PASSED\n")
    
    print("Edge case: Minimum target amount...")
    test_edge_case_target_amount_minimum()
    print("✓ PASSED\n")
    
    print("Edge case: Ownership check (update)...")
    test_edge_case_ownership_check_update()
    print("✓ PASSED\n")
    
    print("Edge case: Ownership check (delete)...")
    test_edge_case_ownership_check_delete()
    print("✓ PASSED\n")
    
    print("✅ All GoalsService tests passed!")
