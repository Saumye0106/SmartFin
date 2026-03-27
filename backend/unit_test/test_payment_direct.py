#!/usr/bin/env python
"""Direct test of payment recording without HTTP"""

from datetime import datetime, timezone, timedelta
from backend.loan_history_service import LoanHistoryService
import tempfile
import os
import sqlite3

# Create a temporary database
with tempfile.TemporaryDirectory() as tmpdir:
    db_path = os.path.join(tmpdir, 'test.db')
    
    # Initialize the service
    service = LoanHistoryService(db_path)
    
    # Create tables
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # Create loans table
    cur.execute('''
        CREATE TABLE loans (
            loan_id TEXT PRIMARY KEY,
            user_id INTEGER,
            loan_type TEXT,
            loan_amount REAL,
            loan_tenure INTEGER,
            monthly_emi REAL,
            interest_rate REAL,
            loan_start_date TEXT,
            loan_maturity_date TEXT,
            default_status INTEGER,
            created_at TEXT,
            updated_at TEXT,
            deleted_at TEXT
        )
    ''')
    
    # Create loan_payments table
    cur.execute('''
        CREATE TABLE loan_payments (
            payment_id TEXT PRIMARY KEY,
            loan_id TEXT,
            payment_date TEXT,
            payment_amount REAL,
            payment_status TEXT,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (loan_id) REFERENCES loans(loan_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    # Create a loan
    loan_data = {
        'loan_type': 'personal',
        'loan_amount': 100000,
        'loan_tenure': 24,
        'interest_rate': 10.0,
        'loan_start_date': '2026-02-27T00:00:00Z',
        'loan_maturity_date': '2028-02-27T00:00:00Z',
        'monthly_emi': 4614.49
    }
    
    loan = service.createLoan(1, loan_data)
    print(f'Loan created: {loan["loan_id"]}')
    
    # Try to record a payment with today's date
    today = datetime.now(timezone.utc).date()
    payment_date_iso = f'{today.isoformat()}T00:00:00Z'
    
    payment_data = {
        'payment_date': payment_date_iso,
        'payment_amount': 5000
    }
    
    print(f'Recording payment with date: {payment_date_iso}')
    
    try:
        payment = service.recordPayment(loan['loan_id'], payment_data)
        print(f'✓ Payment recorded: {payment["payment_id"]}')
        print(f'  Status: {payment["payment_status"]}')
    except Exception as e:
        print(f'✗ Error: {str(e)}')
        import traceback
        traceback.print_exc()
