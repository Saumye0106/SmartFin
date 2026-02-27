"""
Database Utilities for SmartFin
Provides helper functions for database operations and initialization
"""

import sqlite3
import os
from typing import Optional, List, Dict, Any, Tuple


def get_db_path() -> str:
    """Get the absolute path to the database file"""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auth.db')


def init_loan_tables(db_path: Optional[str] = None) -> None:
    """
    Initialize loan-related tables in the database
    
    Args:
        db_path: Path to database file (defaults to auth.db in backend directory)
    
    Creates:
        - loans table: stores loan information
        - loan_payments table: tracks payment history
        - loan_metrics table: caches calculated metrics
        - indexes for performance optimization
    """
    if db_path is None:
        db_path = get_db_path()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Create loans table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS loans (
                loan_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                loan_type TEXT NOT NULL CHECK (loan_type IN ('personal', 'home', 'auto', 'education')),
                loan_amount REAL NOT NULL CHECK (loan_amount > 0),
                loan_tenure INTEGER NOT NULL CHECK (loan_tenure > 0),
                monthly_emi REAL NOT NULL CHECK (monthly_emi > 0),
                interest_rate REAL NOT NULL CHECK (interest_rate >= 0 AND interest_rate <= 50),
                loan_start_date TEXT NOT NULL,
                loan_maturity_date TEXT NOT NULL,
                default_status INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                deleted_at TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Create loan_payments table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS loan_payments (
                payment_id TEXT PRIMARY KEY,
                loan_id TEXT NOT NULL,
                payment_date TEXT NOT NULL,
                payment_amount REAL NOT NULL CHECK (payment_amount > 0),
                payment_status TEXT NOT NULL CHECK (payment_status IN ('on-time', 'late', 'missed')),
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (loan_id) REFERENCES loans(loan_id) ON DELETE CASCADE
            )
        ''')
        
        # Create loan_metrics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS loan_metrics (
                user_id INTEGER PRIMARY KEY,
                loan_diversity_score REAL CHECK (loan_diversity_score >= 0 AND loan_diversity_score <= 100),
                payment_history_score REAL CHECK (payment_history_score >= 0 AND payment_history_score <= 100),
                loan_maturity_score REAL CHECK (loan_maturity_score >= 0 AND loan_maturity_score <= 100),
                payment_statistics TEXT,
                loan_statistics TEXT,
                calculated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_loans_user_id ON loans(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_loans_loan_type ON loans(loan_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_loans_default_status ON loans(default_status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_loans_deleted_at ON loans(deleted_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_loan_payments_loan_id ON loan_payments(loan_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_loan_payments_payment_date ON loan_payments(payment_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_loan_payments_payment_status ON loan_payments(payment_status)')
        
        conn.commit()
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def verify_loan_tables(db_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Verify that loan tables exist and have correct structure
    
    Args:
        db_path: Path to database file
    
    Returns:
        Dictionary with verification results
    """
    if db_path is None:
        db_path = get_db_path()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    results = {
        'success': True,
        'tables': {},
        'indexes': [],
        'errors': []
    }
    
    try:
        # Check tables
        expected_tables = ['loans', 'loan_payments', 'loan_metrics']
        for table in expected_tables:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            exists = cursor.fetchone() is not None
            
            if exists:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = cursor.fetchall()
                results['tables'][table] = {
                    'exists': True,
                    'column_count': len(columns),
                    'columns': [col[1] for col in columns]
                }
            else:
                results['tables'][table] = {'exists': False}
                results['errors'].append(f"Table {table} does not exist")
                results['success'] = False
        
        # Check indexes
        cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_loan%'")
        indexes = cursor.fetchall()
        results['indexes'] = [idx[0] for idx in indexes]
        
    except Exception as e:
        results['success'] = False
        results['errors'].append(str(e))
    finally:
        conn.close()
    
    return results


def execute_loan_query(
    query: str,
    params: Tuple = (),
    fetch_one: bool = False,
    fetch_all: bool = False,
    commit: bool = False,
    db_path: Optional[str] = None
) -> Any:
    """
    Execute a database query for loan operations
    
    Args:
        query: SQL query string
        params: Query parameters tuple
        fetch_one: Return single row
        fetch_all: Return all rows
        commit: Commit transaction
        db_path: Path to database file
    
    Returns:
        Query result or None
    """
    if db_path is None:
        db_path = get_db_path()
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute(query, params)
        
        if commit:
            conn.commit()
            return cursor.lastrowid
        
        if fetch_one:
            result = cursor.fetchone()
            return dict(result) if result else None
        
        if fetch_all:
            results = cursor.fetchall()
            return [dict(row) for row in results]
        
        return None
        
    except sqlite3.Error as e:
        if commit:
            conn.rollback()
        raise e
    finally:
        conn.close()


def get_loan_table_stats(db_path: Optional[str] = None) -> Dict[str, int]:
    """
    Get statistics about loan tables
    
    Args:
        db_path: Path to database file
    
    Returns:
        Dictionary with row counts for each table
    """
    if db_path is None:
        db_path = get_db_path()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    stats = {}
    
    try:
        tables = ['loans', 'loan_payments', 'loan_metrics']
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            stats[table] = count
    finally:
        conn.close()
    
    return stats


if __name__ == '__main__':
    """Test database utilities"""
    print("Testing database utilities...")
    
    # Initialize tables
    print("\n1. Initializing loan tables...")
    init_loan_tables()
    print("   ✓ Tables initialized")
    
    # Verify tables
    print("\n2. Verifying loan tables...")
    results = verify_loan_tables()
    if results['success']:
        print("   ✓ All tables verified")
        for table, info in results['tables'].items():
            if info['exists']:
                print(f"     - {table}: {info['column_count']} columns")
    else:
        print("   ✗ Verification failed:")
        for error in results['errors']:
            print(f"     - {error}")
    
    # Get stats
    print("\n3. Getting table statistics...")
    stats = get_loan_table_stats()
    for table, count in stats.items():
        print(f"   - {table}: {count} rows")
    
    print("\n✅ Database utilities test complete!")
