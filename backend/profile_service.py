"""
ProfileService - Business logic for user profile management
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, Dict, Any


class ProfileService:
    """Service class for managing user profiles"""
    
    def __init__(self, db_path: str):
        """
        Initialize ProfileService
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
    
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _row_to_dict(self, row) -> Optional[Dict[str, Any]]:
        """Convert SQLite row to dictionary"""
        if row is None:
            return None
        return dict(row)
    
    def create_profile(self, user_id: int, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new user profile
        
        Args:
            user_id: ID of the user
            profile_data: Dictionary containing profile information
                - name: str
                - age: int
                - location: str
                - risk_tolerance: int (optional)
                - notification_preferences: dict (optional)
        
        Returns:
            Dictionary containing the created profile
        
        Raises:
            sqlite3.IntegrityError: If profile already exists for user
            sqlite3.Error: For other database errors
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            # Set default notification preferences if not provided
            notification_prefs = profile_data.get('notification_preferences', {
                'email': True,
                'push': False,
                'in_app': True,
                'frequency': 'daily'
            })
            
            # Convert notification preferences to JSON string
            notification_prefs_json = json.dumps(notification_prefs)
            
            # Get current timestamp
            now = datetime.utcnow().isoformat()
            
            # Insert profile
            cur.execute('''
                INSERT INTO users_profile 
                (user_id, name, age, location, risk_tolerance, notification_preferences, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                profile_data['name'],
                profile_data['age'],
                profile_data['location'],
                profile_data.get('risk_tolerance'),
                notification_prefs_json,
                now,
                now
            ))
            
            conn.commit()
            
            # Retrieve and return the created profile
            return self.get_profile(user_id)
            
        except sqlite3.IntegrityError as e:
            conn.rollback()
            if 'UNIQUE constraint' in str(e) or 'PRIMARY KEY' in str(e):
                raise ValueError(f'Profile already exists for user {user_id}')
            raise
        except sqlite3.Error as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Retrieve a user's profile
        
        Args:
            user_id: ID of the user
        
        Returns:
            Dictionary containing profile data, or None if not found
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute('''
                SELECT user_id, name, age, location, risk_tolerance, 
                       profile_picture_url, notification_preferences,
                       created_at, updated_at
                FROM users_profile
                WHERE user_id = ?
            ''', (user_id,))
            
            row = cur.fetchone()
            
            if row is None:
                return None
            
            profile = self._row_to_dict(row)
            
            # Parse notification preferences JSON
            if profile['notification_preferences']:
                profile['notification_preferences'] = json.loads(profile['notification_preferences'])
            
            return profile
            
        finally:
            conn.close()
    
    def update_profile(self, user_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update a user's profile
        
        Args:
            user_id: ID of the user
            updates: Dictionary containing fields to update
        
        Returns:
            Dictionary containing the updated profile
        
        Raises:
            ValueError: If profile doesn't exist
            sqlite3.Error: For database errors
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            # Check if profile exists
            existing_profile = self.get_profile(user_id)
            if existing_profile is None:
                raise ValueError(f'Profile not found for user {user_id}')
            
            # Build UPDATE query dynamically based on provided fields
            update_fields = []
            update_values = []
            
            allowed_fields = ['name', 'age', 'location', 'risk_tolerance', 'notification_preferences', 'profile_picture_url']
            
            for field in allowed_fields:
                if field in updates:
                    if field == 'notification_preferences':
                        # Convert dict to JSON string
                        update_fields.append(f'{field} = ?')
                        update_values.append(json.dumps(updates[field]))
                    else:
                        update_fields.append(f'{field} = ?')
                        update_values.append(updates[field])
            
            if not update_fields:
                # No fields to update, return existing profile
                return existing_profile
            
            # Always update the updated_at timestamp
            update_fields.append('updated_at = ?')
            update_values.append(datetime.utcnow().isoformat())
            
            # Add user_id to values for WHERE clause
            update_values.append(user_id)
            
            # Execute update
            query = f'''
                UPDATE users_profile
                SET {', '.join(update_fields)}
                WHERE user_id = ?
            '''
            
            cur.execute(query, update_values)
            conn.commit()
            
            # Retrieve and return updated profile
            return self.get_profile(user_id)
            
        except sqlite3.Error as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def delete_profile(self, user_id: int) -> bool:
        """
        Delete a user's profile
        
        Args:
            user_id: ID of the user
        
        Returns:
            True if profile was deleted, False if not found
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute('DELETE FROM users_profile WHERE user_id = ?', (user_id,))
            conn.commit()
            
            return cur.rowcount > 0
            
        finally:
            conn.close()
    
    def profile_exists(self, user_id: int) -> bool:
        """
        Check if a profile exists for a user
        
        Args:
            user_id: ID of the user
        
        Returns:
            True if profile exists, False otherwise
        """
        return self.get_profile(user_id) is not None
