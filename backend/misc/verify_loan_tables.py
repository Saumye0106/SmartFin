"""
Verify loan tables were created successfully
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'auth.db')

def verify():
    """Verify loan tables exist and have correct schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("=" * 70)
    print("Verifying Loan Tables")
    print("=" * 70)
    print(f"Database: {DB_PATH}\n")
    
    # Check all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    all_tables = [t[0] for t in cursor.fetchall()]
    
    print("All tables in database:")
    for table in all_tables:
        print(f"  - {table}")
    
    # Check loan-specific tables
    loan_tables = ['loans', 'loan_payments', 'loan_metrics']
    print("\nLoan-related tables:")
    for table in loan_tables:
        if table in all_tables:
            print(f"  ✓ {table} exists")
            
            # Show column count
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"    Columns: {len(columns)}")
        else:
            print(f"  ✗ {table} MISSING")
    
    # Check indexes
    print("\nLoan-related indexes:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_loan%'")
    indexes = cursor.fetchall()
    for idx in indexes:
        print(f"  ✓ {idx[0]}")
    
    conn.close()
    print("\n✅ Verification complete!")

if __name__ == '__main__':
    verify()
