"""
Database Migration: Add phone column to users table
Run this script to add the phone column to existing database
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auth.db')

def migrate():
    """Add phone column to users table"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if phone column already exists
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'phone' in columns:
            print("✓ Phone column already exists in users table")
        else:
            print("Adding phone column to users table...")
            cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
            conn.commit()
            print("✓ Phone column added successfully!")
        
        # Verify the column was added
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
    print("Database Migration: Add Phone Column")
    print("=" * 60)
    print(f"Database: {DB_PATH}\n")
    
    migrate()
