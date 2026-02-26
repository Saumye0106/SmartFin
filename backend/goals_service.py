"""
GoalsService - Business logic for financial goals management
"""

import sqlite3
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any


class GoalsService:
    """Service class for managing financial goals"""
    
    def __init__(self, db_path: str):
        """
        Initialize GoalsService
        
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
    
    def create_goal(self, user_id: int, goal_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a new financial goal
        
        Args:
            user_id: ID of the user
            goal_data: Dictionary containing goal information
                - goal_type: str ('short-term' or 'long-term')
                - target_amount: float (> 0)
                - target_date: str (ISO format date)
                - priority: str ('low', 'medium', or 'high')
                - description: str (optional)
        
        Returns:
            Dictionary containing the created goal
        
        Raises:
            sqlite3.Error: For database errors
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            # Generate unique goal ID
            goal_id = str(uuid.uuid4())
            
            # Get current timestamp
            now = datetime.utcnow().isoformat()
            
            # Insert goal with default status 'active'
            cur.execute('''
                INSERT INTO financial_goals 
                (id, user_id, goal_type, target_amount, target_date, priority, status, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                goal_id,
                user_id,
                goal_data['goal_type'],
                goal_data['target_amount'],
                goal_data['target_date'],
                goal_data['priority'],
                'active',  # Default status
                goal_data.get('description'),
                now,
                now
            ))
            
            conn.commit()
            
            # Retrieve and return the created goal
            return self.get_goal(goal_id)
            
        except sqlite3.Error as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_goal(self, goal_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific goal by ID
        
        Args:
            goal_id: ID of the goal
        
        Returns:
            Dictionary containing goal data, or None if not found
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute('''
                SELECT id, user_id, goal_type, target_amount, target_date,
                       priority, status, description, created_at, updated_at
                FROM financial_goals
                WHERE id = ?
            ''', (goal_id,))
            
            row = cur.fetchone()
            return self._row_to_dict(row)
            
        finally:
            conn.close()
    
    def get_goals(self, user_id: int, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Retrieve all goals for a user with optional filtering
        Goals are sorted by priority (high > medium > low) then by target_date (earliest first)
        
        Args:
            user_id: ID of the user
            filters: Optional dictionary with filter criteria
                - status: str (filter by status)
                - goal_type: str (filter by type)
        
        Returns:
            List of goal dictionaries, sorted by priority then date
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            # Build query with filters
            query = '''
                SELECT id, user_id, goal_type, target_amount, target_date,
                       priority, status, description, created_at, updated_at
                FROM financial_goals
                WHERE user_id = ?
            '''
            params = [user_id]
            
            if filters:
                if 'status' in filters:
                    query += ' AND status = ?'
                    params.append(filters['status'])
                if 'goal_type' in filters:
                    query += ' AND goal_type = ?'
                    params.append(filters['goal_type'])
            
            # Add sorting: priority (high > medium > low) then target_date (earliest first)
            # Use CASE to convert priority to numeric for sorting
            query += '''
                ORDER BY 
                    CASE priority
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low' THEN 3
                    END,
                    target_date ASC
            '''
            
            cur.execute(query, params)
            rows = cur.fetchall()
            
            return [self._row_to_dict(row) for row in rows]
            
        finally:
            conn.close()
    
    def update_goal(self, goal_id: str, user_id: int, updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update an existing goal with ownership check
        
        Args:
            goal_id: ID of the goal
            user_id: ID of the user (for ownership verification)
            updates: Dictionary containing fields to update
        
        Returns:
            Dictionary containing the updated goal
        
        Raises:
            ValueError: If goal doesn't exist or user doesn't own it
            sqlite3.Error: For database errors
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            # Check if goal exists and belongs to user
            existing_goal = self.get_goal(goal_id)
            if existing_goal is None:
                raise ValueError(f'Goal not found: {goal_id}')
            
            if existing_goal['user_id'] != user_id:
                raise ValueError(f'User {user_id} does not own goal {goal_id}')
            
            # Build UPDATE query dynamically
            update_fields = []
            update_values = []
            
            allowed_fields = ['target_amount', 'target_date', 'priority', 'status', 'description']
            
            for field in allowed_fields:
                if field in updates:
                    update_fields.append(f'{field} = ?')
                    update_values.append(updates[field])
            
            if not update_fields:
                # No fields to update, return existing goal
                return existing_goal
            
            # Always update the updated_at timestamp
            update_fields.append('updated_at = ?')
            update_values.append(datetime.utcnow().isoformat())
            
            # Add goal_id to values for WHERE clause
            update_values.append(goal_id)
            
            # Execute update
            query = f'''
                UPDATE financial_goals
                SET {', '.join(update_fields)}
                WHERE id = ?
            '''
            
            cur.execute(query, update_values)
            conn.commit()
            
            # Retrieve and return updated goal
            return self.get_goal(goal_id)
            
        except sqlite3.Error as e:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def delete_goal(self, goal_id: str, user_id: int) -> bool:
        """
        Delete a goal with ownership check
        
        Args:
            goal_id: ID of the goal
            user_id: ID of the user (for ownership verification)
        
        Returns:
            True if goal was deleted, False if not found
        
        Raises:
            ValueError: If user doesn't own the goal
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            # Check if goal exists and belongs to user
            existing_goal = self.get_goal(goal_id)
            if existing_goal is None:
                return False
            
            if existing_goal['user_id'] != user_id:
                raise ValueError(f'User {user_id} does not own goal {goal_id}')
            
            # Delete goal
            cur.execute('DELETE FROM financial_goals WHERE id = ?', (goal_id,))
            conn.commit()
            
            return cur.rowcount > 0
            
        finally:
            conn.close()
    
    def goal_exists(self, goal_id: str) -> bool:
        """
        Check if a goal exists
        
        Args:
            goal_id: ID of the goal
        
        Returns:
            True if goal exists, False otherwise
        """
        return self.get_goal(goal_id) is not None
    
    def get_user_goals_count(self, user_id: int) -> int:
        """
        Get count of goals for a user
        
        Args:
            user_id: ID of the user
        
        Returns:
            Number of goals
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute('SELECT COUNT(*) FROM financial_goals WHERE user_id = ?', (user_id,))
            return cur.fetchone()[0]
            
        finally:
            conn.close()
