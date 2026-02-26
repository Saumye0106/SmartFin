"""
Utility script to manually add phone number to a user
Useful for testing or fixing accounts
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'auth.db')

def list_users():
    """List all users"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, phone FROM users')
    users = cursor.fetchall()
    conn.close()
    return users

def add_phone_to_user(user_id, phone):
    """Add phone number to a specific user"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET phone = ? WHERE id = ?', (phone, user_id))
    conn.commit()
    conn.close()

if __name__ == '__main__':
    print("=" * 60)
    print("Add Phone Number to User")
    print("=" * 60)
    
    # List all users
    users = list_users()
    print("\nCurrent users:")
    for user in users:
        phone_status = user[2] if user[2] else "No phone"
        print(f"  ID: {user[0]}, Email: {user[1]}, Phone: {phone_status}")
    
    print("\n" + "=" * 60)
    user_id = input("Enter user ID to add phone to: ")
    phone = input("Enter phone number (E.164 format, e.g., +917880308989): ")
    
    try:
        add_phone_to_user(int(user_id), phone)
        print(f"\n✅ Phone number {phone} added to user ID {user_id}")
        
        # Verify
        users = list_users()
        print("\nUpdated users:")
        for user in users:
            phone_status = user[2] if user[2] else "No phone"
            print(f"  ID: {user[0]}, Email: {user[1]}, Phone: {phone_status}")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
