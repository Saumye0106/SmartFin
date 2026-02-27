"""
Database Migration: Add loan history tables
Run this script to add loans, loan_payments, and loan_metrics tables
"""

import sqlite3
import os

# Get the correct path to auth.db (one level up from misc/)
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'auth.db')

def migrate():
    """Add loan history tables to database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("Creating loan history tables...\n")
        
        # 1. Create loans table
        print("1. Creating loans table...")
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
        print("   ✓ Loans table created")
        
        # 2. Create loan_payments table
        print("2. Creating loan_payments table...")
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
        print("   ✓ Loan_payments table created")
        
        # 3. Create loan_metrics table (for caching calculated metrics)
        print("3. Creating loan_metrics table...")
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
        print("   ✓ Loan_metrics table created")
        
        # 4. Create indexes for better query performance
        print("4. Creating indexes...")
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_loans_user_id ON loans(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_loans_loan_type ON loans(loan_type)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_loans_default_status ON loans(default_status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_loans_deleted_at ON loans(deleted_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_loan_payments_loan_id ON loan_payments(loan_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_loan_payments_payment_date ON loan_payments(payment_date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_loan_payments_payment_status ON loan_payments(payment_status)')
        print("   ✓ Indexes created")
        
        conn.commit()
        
        # 5. Verify tables were created
        print("\n5. Verifying table creation...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'loan%'")
        tables = cursor.fetchall()
        print("   Loan-related tables in database:")
        for table in tables:
            print(f"     - {table[0]}")
            
            # Show schema for each table
            cursor.execute(f"PRAGMA table_info({table[0]})")
            columns = cursor.fetchall()
            print(f"       Columns:")
            for col in columns:
                print(f"         • {col[1]} ({col[2]})")
        
        conn.close()
        print("\n✅ Migration completed successfully!")
        print("\nNext steps:")
        print("  1. Implement Loan_History_System service")
        print("  2. Implement Loan_Metrics_Engine service")
        print("  3. Create API endpoints for loan operations")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        raise

if __name__ == '__main__':
    print("=" * 70)
    print("Database Migration: Add Loan History Tables")
    print("=" * 70)
    print(f"Database: {DB_PATH}\n")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ Error: Database file not found at {DB_PATH}")
        print("Please ensure the database exists before running this migration.")
        exit(1)
    
    migrate()
