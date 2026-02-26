"""
Database Migration: Add email verification to users table
Run this script to add email verification columns to existing database
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auth.db')

def migrate():
    """Add email verification columns to users table"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if email_verified column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'email_verified' not in columns:
            print("Adding email_verified column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN email_verified INTEGER DEFAULT 0")
            conn.commit()
            print("✓ email_verified column added successfully!")
        else:
            print("✓ email_verified column already exists in users table")
        
        if 'email_verification_token' not in columns:
            print("Adding email_verification_token column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN email_verification_token TEXT")
            conn.commit()
            print("✓ email_verification_token column added successfully!")
        else:
            print("✓ email_verification_token column already exists in users table")
        
        if 'email_verification_expires' not in columns:
            print("Adding email_verification_expires column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN email_verification_expires TEXT")
            conn.commit()
            print("✓ email_verification_expires column added successfully!")
        else:
            print("✓ email_verification_expires column already exists in users table")
        
        # Verify the columns were added
        cursor.execute("PRAGMA table_info(users)")
        columns = cursor.fetchall()
        print("\nCurrent users table schema:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        conn.close()
        print("\n✅ Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {str(e)}")
        raise

if __name__ == '__main__':
    print("=" * 60)
    print("Database Migration: Add Email Verification")
    print("=" * 60)
    print(f"Database: {DB_PATH}\n")
    
    migrate()
