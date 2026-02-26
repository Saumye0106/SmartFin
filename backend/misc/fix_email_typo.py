"""
Fix email typo in database
Changes: saumye.singh2004@gmaill.com -> saumye.singh2004@gmail.com
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auth.db')

def fix_email_typo():
    """Update email with typo to correct email"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        old_email = 'saumye.singh2004@gmaill.com'  # Typo email
        new_email = 'saumye.singh2004@gmail.com'   # Correct email
        
        # Check if old email exists
        cursor.execute('SELECT id, username, phone FROM users WHERE username = ?', (old_email,))
        user = cursor.fetchone()
        
        if not user:
            print(f"❌ Email '{old_email}' not found in database")
            conn.close()
            return
        
        user_id, username, phone = user
        print(f"\n✓ Found user:")
        print(f"  ID: {user_id}")
        print(f"  Email: {username}")
        print(f"  Phone: {phone}")
        
        # Check if new email already exists
        cursor.execute('SELECT id FROM users WHERE username = ?', (new_email,))
        existing = cursor.fetchone()
        
        if existing:
            print(f"\n⚠️  Email '{new_email}' already exists (User ID: {existing[0]})")
            print("\nOptions:")
            print("1. Delete the old typo account and keep the correct one")
            print("2. Merge data from typo account to correct account")
            print("3. Cancel")
            
            choice = input("\nEnter choice (1/2/3): ").strip()
            
            if choice == '1':
                # Delete typo account
                cursor.execute('DELETE FROM users WHERE username = ?', (old_email,))
                conn.commit()
                print(f"\n✅ Deleted typo account: {old_email}")
            elif choice == '2':
                # Merge phone number if typo account has one
                if phone:
                    cursor.execute('UPDATE users SET phone = ? WHERE username = ?', (phone, new_email))
                    conn.commit()
                    print(f"\n✅ Merged phone number to correct account")
                # Delete typo account
                cursor.execute('DELETE FROM users WHERE username = ?', (old_email,))
                conn.commit()
                print(f"✅ Deleted typo account: {old_email}")
            else:
                print("\n❌ Cancelled")
        else:
            # Simply update the email
            cursor.execute('UPDATE users SET username = ? WHERE username = ?', (new_email, old_email))
            conn.commit()
            print(f"\n✅ Email updated successfully!")
            print(f"   Old: {old_email}")
            print(f"   New: {new_email}")
        
        # Show final state
        print("\n" + "="*60)
        print("Current users in database:")
        print("="*60)
        cursor.execute('SELECT id, username, phone FROM users ORDER BY id')
        users = cursor.fetchall()
        for user in users:
            print(f"ID: {user[0]}, Email: {user[1]}, Phone: {user[2]}")
        
        conn.close()
        print("\n✅ Done!")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        raise

if __name__ == '__main__':
    print("=" * 60)
    print("Fix Email Typo")
    print("=" * 60)
    print(f"Database: {DB_PATH}\n")
    
    fix_email_typo()
