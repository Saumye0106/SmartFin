"""
Test payment validation enhancements
Tests the new validation for payment exceeding remaining balance
"""

import pytest
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from loan_history_service import LoanHistoryService, ValidationError


@pytest.fixture
def service():
    """Create LoanHistoryService with in-memory database"""
    import tempfile
    import os
    
    # Use a temporary file instead of :memory: so connections share the same database
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    
    service = LoanHistoryService(db_path)
    
    # Initialize database schema
    conn = service._get_connection()
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE loans (
            loan_id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            loan_type TEXT NOT NULL,
            loan_amount REAL NOT NULL,
            loan_tenure INTEGER NOT NULL,
            monthly_emi REAL NOT NULL,
            interest_rate REAL NOT NULL,
            loan_start_date TEXT NOT NULL,
            loan_maturity_date TEXT NOT NULL,
            default_status INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            deleted_at TEXT
        )
    ''')
    
    cur.execute('''
        CREATE TABLE loan_payments (
            payment_id TEXT PRIMARY KEY,
            loan_id TEXT NOT NULL,
            payment_date TEXT NOT NULL,
            payment_amount REAL NOT NULL,
            payment_status TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (loan_id) REFERENCES loans(loan_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    yield service
    
    # Cleanup
    os.unlink(db_path)


def test_payment_exceeds_remaining_balance(service):
    """Test that payment cannot exceed remaining loan balance"""
    # Create a loan
    start_date = datetime.utcnow()
    maturity_date = start_date + timedelta(days=365 * 2)
    
    loan_data = {
        'loan_type': 'personal',
        'loan_amount': 100000,
        'loan_tenure': 24,
        'monthly_emi': 4622.24,
        'interest_rate': 10.5,
        'loan_start_date': start_date.isoformat(),
        'loan_maturity_date': maturity_date.isoformat()
    }
    
    loan = service.createLoan(1, loan_data)
    
    # Record a payment of 50000
    payment_data_1 = {
        'payment_date': datetime.utcnow().isoformat(),
        'payment_amount': 50000
    }
    service.recordPayment(loan['loan_id'], payment_data_1)
    
    # Try to record another payment of 60000 (exceeds remaining 50000)
    payment_data_2 = {
        'payment_date': datetime.utcnow().isoformat(),
        'payment_amount': 60000
    }
    
    with pytest.raises(ValidationError) as exc_info:
        service.recordPayment(loan['loan_id'], payment_data_2)
    
    assert exc_info.value.field == 'payment_amount'
    assert 'exceeds remaining balance' in exc_info.value.message.lower()
    assert exc_info.value.code == 'EXCEEDS_BALANCE'


def test_payment_exactly_remaining_balance(service):
    """Test that payment can exactly match remaining balance"""
    # Create a loan
    start_date = datetime.utcnow()
    maturity_date = start_date + timedelta(days=365 * 2)
    
    loan_data = {
        'loan_type': 'personal',
        'loan_amount': 100000,
        'loan_tenure': 24,
        'monthly_emi': 4622.24,
        'interest_rate': 10.5,
        'loan_start_date': start_date.isoformat(),
        'loan_maturity_date': maturity_date.isoformat()
    }
    
    loan = service.createLoan(1, loan_data)
    
    # Record a payment of 50000
    payment_data_1 = {
        'payment_date': datetime.utcnow().isoformat(),
        'payment_amount': 50000
    }
    service.recordPayment(loan['loan_id'], payment_data_1)
    
    # Record another payment of exactly 50000 (remaining balance)
    payment_data_2 = {
        'payment_date': datetime.utcnow().isoformat(),
        'payment_amount': 50000
    }
    
    # Should succeed
    payment = service.recordPayment(loan['loan_id'], payment_data_2)
    assert payment is not None
    assert payment['payment_amount'] == 50000


def test_payment_within_remaining_balance(service):
    """Test that payment within remaining balance succeeds"""
    # Create a loan
    start_date = datetime.utcnow()
    maturity_date = start_date + timedelta(days=365 * 2)
    
    loan_data = {
        'loan_type': 'personal',
        'loan_amount': 100000,
        'loan_tenure': 24,
        'monthly_emi': 4622.24,
        'interest_rate': 10.5,
        'loan_start_date': start_date.isoformat(),
        'loan_maturity_date': maturity_date.isoformat()
    }
    
    loan = service.createLoan(1, loan_data)
    
    # Record a payment of 30000
    payment_data_1 = {
        'payment_date': datetime.utcnow().isoformat(),
        'payment_amount': 30000
    }
    service.recordPayment(loan['loan_id'], payment_data_1)
    
    # Record another payment of 40000 (within remaining 70000)
    payment_data_2 = {
        'payment_date': datetime.utcnow().isoformat(),
        'payment_amount': 40000
    }
    
    # Should succeed
    payment = service.recordPayment(loan['loan_id'], payment_data_2)
    assert payment is not None
    assert payment['payment_amount'] == 40000
