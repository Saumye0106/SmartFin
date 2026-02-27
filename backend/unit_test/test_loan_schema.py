"""
Unit tests for loan database schema
Tests table creation, constraints, and basic operations
"""

import pytest
import sqlite3
import os
import sys
from datetime import datetime, timedelta
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_utils import init_loan_tables, verify_loan_tables, get_loan_table_stats


@pytest.fixture
def test_db():
    """Create a temporary test database"""
    test_db_path = os.path.join(os.path.dirname(__file__), 'test_loans.db')
    
    # Create test database with users table (required for foreign keys)
    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    # Insert test user
    cursor.execute(
        "INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)",
        ('test@example.com', 'hash123', datetime.utcnow().isoformat())
    )
    conn.commit()
    conn.close()
    
    # Initialize loan tables
    init_loan_tables(test_db_path)
    
    yield test_db_path
    
    # Cleanup
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


def test_loan_tables_created(test_db):
    """Test that all loan tables are created"""
    results = verify_loan_tables(test_db)
    
    assert results['success'], f"Verification failed: {results['errors']}"
    assert 'loans' in results['tables']
    assert 'loan_payments' in results['tables']
    assert 'loan_metrics' in results['tables']
    
    assert results['tables']['loans']['exists']
    assert results['tables']['loan_payments']['exists']
    assert results['tables']['loan_metrics']['exists']


def test_loan_table_columns(test_db):
    """Test that loans table has correct columns"""
    results = verify_loan_tables(test_db)
    
    expected_columns = [
        'loan_id', 'user_id', 'loan_type', 'loan_amount', 'loan_tenure',
        'monthly_emi', 'interest_rate', 'loan_start_date', 'loan_maturity_date',
        'default_status', 'created_at', 'updated_at', 'deleted_at'
    ]
    
    actual_columns = results['tables']['loans']['columns']
    
    for col in expected_columns:
        assert col in actual_columns, f"Column {col} missing from loans table"


def test_insert_valid_loan(test_db):
    """Test inserting a valid loan record"""
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    loan_id = str(uuid.uuid4())
    start_date = datetime.now().isoformat()
    maturity_date = (datetime.now() + timedelta(days=730)).isoformat()
    
    cursor.execute('''
        INSERT INTO loans (
            loan_id, user_id, loan_type, loan_amount, loan_tenure,
            monthly_emi, interest_rate, loan_start_date, loan_maturity_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (loan_id, 1, 'personal', 50000.0, 24, 2291.67, 10.5, start_date, maturity_date))
    
    conn.commit()
    
    # Verify insertion
    cursor.execute('SELECT * FROM loans WHERE loan_id = ?', (loan_id,))
    loan = cursor.fetchone()
    
    assert loan is not None
    assert loan[2] == 'personal'  # loan_type
    assert loan[3] == 50000.0  # loan_amount
    
    conn.close()


def test_loan_type_constraint(test_db):
    """Test that invalid loan types are rejected"""
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    loan_id = str(uuid.uuid4())
    start_date = datetime.now().isoformat()
    maturity_date = (datetime.now() + timedelta(days=730)).isoformat()
    
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute('''
            INSERT INTO loans (
                loan_id, user_id, loan_type, loan_amount, loan_tenure,
                monthly_emi, interest_rate, loan_start_date, loan_maturity_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (loan_id, 1, 'invalid_type', 50000.0, 24, 2291.67, 10.5, start_date, maturity_date))
        conn.commit()
    
    conn.close()


def test_loan_amount_constraint(test_db):
    """Test that negative loan amounts are rejected"""
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    loan_id = str(uuid.uuid4())
    start_date = datetime.now().isoformat()
    maturity_date = (datetime.now() + timedelta(days=730)).isoformat()
    
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute('''
            INSERT INTO loans (
                loan_id, user_id, loan_type, loan_amount, loan_tenure,
                monthly_emi, interest_rate, loan_start_date, loan_maturity_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (loan_id, 1, 'personal', -50000.0, 24, 2291.67, 10.5, start_date, maturity_date))
        conn.commit()
    
    conn.close()


def test_interest_rate_constraint(test_db):
    """Test that interest rates outside 0-50 range are rejected"""
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    loan_id = str(uuid.uuid4())
    start_date = datetime.now().isoformat()
    maturity_date = (datetime.now() + timedelta(days=730)).isoformat()
    
    # Test rate > 50
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute('''
            INSERT INTO loans (
                loan_id, user_id, loan_type, loan_amount, loan_tenure,
                monthly_emi, interest_rate, loan_start_date, loan_maturity_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (loan_id, 1, 'personal', 50000.0, 24, 2291.67, 55.0, start_date, maturity_date))
        conn.commit()
    
    conn.close()


def test_insert_payment(test_db):
    """Test inserting a payment record"""
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    # First insert a loan
    loan_id = str(uuid.uuid4())
    start_date = datetime.now().isoformat()
    maturity_date = (datetime.now() + timedelta(days=730)).isoformat()
    
    cursor.execute('''
        INSERT INTO loans (
            loan_id, user_id, loan_type, loan_amount, loan_tenure,
            monthly_emi, interest_rate, loan_start_date, loan_maturity_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (loan_id, 1, 'personal', 50000.0, 24, 2291.67, 10.5, start_date, maturity_date))
    
    # Insert payment
    payment_id = str(uuid.uuid4())
    payment_date = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO loan_payments (
            payment_id, loan_id, payment_date, payment_amount, payment_status
        ) VALUES (?, ?, ?, ?, ?)
    ''', (payment_id, loan_id, payment_date, 2291.67, 'on-time'))
    
    conn.commit()
    
    # Verify insertion
    cursor.execute('SELECT * FROM loan_payments WHERE payment_id = ?', (payment_id,))
    payment = cursor.fetchone()
    
    assert payment is not None
    assert payment[4] == 'on-time'  # payment_status
    
    conn.close()


def test_payment_status_constraint(test_db):
    """Test that invalid payment statuses are rejected"""
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    # First insert a loan
    loan_id = str(uuid.uuid4())
    start_date = datetime.now().isoformat()
    maturity_date = (datetime.now() + timedelta(days=730)).isoformat()
    
    cursor.execute('''
        INSERT INTO loans (
            loan_id, user_id, loan_type, loan_amount, loan_tenure,
            monthly_emi, interest_rate, loan_start_date, loan_maturity_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (loan_id, 1, 'personal', 50000.0, 24, 2291.67, 10.5, start_date, maturity_date))
    conn.commit()
    
    # Try to insert payment with invalid status
    payment_id = str(uuid.uuid4())
    payment_date = datetime.now().isoformat()
    
    with pytest.raises(sqlite3.IntegrityError):
        cursor.execute('''
            INSERT INTO loan_payments (
                payment_id, loan_id, payment_date, payment_amount, payment_status
            ) VALUES (?, ?, ?, ?, ?)
        ''', (payment_id, loan_id, payment_date, 2291.67, 'invalid_status'))
        conn.commit()
    
    conn.close()


def test_foreign_key_cascade(test_db):
    """Test that deleting a loan cascades to payments"""
    conn = sqlite3.connect(test_db)
    conn.execute('PRAGMA foreign_keys = ON')  # Enable foreign keys
    cursor = conn.cursor()
    
    # Insert loan
    loan_id = str(uuid.uuid4())
    start_date = datetime.now().isoformat()
    maturity_date = (datetime.now() + timedelta(days=730)).isoformat()
    
    cursor.execute('''
        INSERT INTO loans (
            loan_id, user_id, loan_type, loan_amount, loan_tenure,
            monthly_emi, interest_rate, loan_start_date, loan_maturity_date
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (loan_id, 1, 'personal', 50000.0, 24, 2291.67, 10.5, start_date, maturity_date))
    
    # Insert payment
    payment_id = str(uuid.uuid4())
    payment_date = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO loan_payments (
            payment_id, loan_id, payment_date, payment_amount, payment_status
        ) VALUES (?, ?, ?, ?, ?)
    ''', (payment_id, loan_id, payment_date, 2291.67, 'on-time'))
    
    conn.commit()
    
    # Delete loan
    cursor.execute('DELETE FROM loans WHERE loan_id = ?', (loan_id,))
    conn.commit()
    
    # Verify payment was also deleted
    cursor.execute('SELECT * FROM loan_payments WHERE payment_id = ?', (payment_id,))
    payment = cursor.fetchone()
    
    assert payment is None, "Payment should be deleted when loan is deleted"
    
    conn.close()


def test_loan_metrics_insert(test_db):
    """Test inserting loan metrics"""
    conn = sqlite3.connect(test_db)
    cursor = conn.cursor()
    
    import json
    
    payment_stats = json.dumps({
        'on_time_payment_percentage': 95.5,
        'late_payment_count': 2,
        'missed_payment_count': 0,
        'total_payments': 44
    })
    
    loan_stats = json.dumps({
        'total_active_loans': 3,
        'total_loan_amount': 150000.0,
        'average_loan_tenure': 36,
        'weighted_average_tenure': 42.5
    })
    
    cursor.execute('''
        INSERT INTO loan_metrics (
            user_id, loan_diversity_score, payment_history_score,
            loan_maturity_score, payment_statistics, loan_statistics
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (1, 75.5, 88.2, 65.0, payment_stats, loan_stats))
    
    conn.commit()
    
    # Verify insertion
    cursor.execute('SELECT * FROM loan_metrics WHERE user_id = ?', (1,))
    metrics = cursor.fetchone()
    
    assert metrics is not None
    assert metrics[1] == 75.5  # loan_diversity_score
    assert metrics[2] == 88.2  # payment_history_score
    
    # Verify JSON parsing
    parsed_payment_stats = json.loads(metrics[4])
    assert parsed_payment_stats['on_time_payment_percentage'] == 95.5
    
    conn.close()


def test_indexes_created(test_db):
    """Test that all indexes are created"""
    results = verify_loan_tables(test_db)
    
    expected_indexes = [
        'idx_loans_user_id',
        'idx_loans_loan_type',
        'idx_loans_default_status',
        'idx_loans_deleted_at',
        'idx_loan_payments_loan_id',
        'idx_loan_payments_payment_date',
        'idx_loan_payments_payment_status'
    ]
    
    for idx in expected_indexes:
        assert idx in results['indexes'], f"Index {idx} not found"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
