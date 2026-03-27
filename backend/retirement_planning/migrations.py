"""
Database migrations for Retirement Planning Calculator

Creates tables for:
- retirement_plans
- retirement_scenarios
- retirement_action_plans
- retirement_plan_history
"""

import sqlite3
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class RetirementPlanningMigrations:
    """Manages database schema for retirement planning"""
    
    @staticmethod
    def create_tables(db_path: str = 'auth.db') -> None:
        """
        Create all retirement planning tables
        
        Args:
            db_path: Path to SQLite database
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Create retirement_plans table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS retirement_plans (
                    plan_id TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    plan_name TEXT NOT NULL,
                    
                    -- Input Parameters
                    current_age INTEGER NOT NULL CHECK (current_age >= 18 AND current_age <= 75),
                    retirement_age INTEGER NOT NULL CHECK (retirement_age > current_age AND retirement_age <= 75),
                    current_salary REAL NOT NULL CHECK (current_salary > 0),
                    current_monthly_expenses REAL NOT NULL CHECK (current_monthly_expenses > 0),
                    desired_retirement_lifestyle REAL,
                    current_savings REAL NOT NULL CHECK (current_savings >= 0),
                    inflation_rate REAL DEFAULT 0.06 CHECK (inflation_rate >= 0 AND inflation_rate <= 0.15),
                    investment_return_rate REAL DEFAULT 0.10 CHECK (investment_return_rate >= 0 AND investment_return_rate <= 0.30),
                    life_expectancy INTEGER DEFAULT 85,
                    
                    -- Calculated Results (JSON)
                    calculation_results TEXT NOT NULL,
                    
                    -- Readiness Assessment (JSON)
                    readiness_assessment TEXT NOT NULL,
                    
                    -- Metadata
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    is_primary INTEGER DEFAULT 0,
                    deleted_at TEXT,
                    
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            ''')
            
            # Create retirement_scenarios table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS retirement_scenarios (
                    scenario_id TEXT PRIMARY KEY,
                    plan_id TEXT NOT NULL,
                    scenario_name TEXT NOT NULL,
                    
                    -- Modified Parameters (JSON)
                    parameters TEXT NOT NULL,
                    
                    -- Calculated Results (JSON)
                    results TEXT NOT NULL,
                    
                    -- Metadata
                    created_at TEXT NOT NULL,
                    is_primary INTEGER DEFAULT 0,
                    
                    FOREIGN KEY (plan_id) REFERENCES retirement_plans(plan_id) ON DELETE CASCADE
                )
            ''')
            
            # Create retirement_action_plans table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS retirement_action_plans (
                    action_id TEXT PRIMARY KEY,
                    plan_id TEXT NOT NULL,
                    
                    -- Action Plan (JSON)
                    actions TEXT NOT NULL,
                    
                    -- Metadata
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    
                    FOREIGN KEY (plan_id) REFERENCES retirement_plans(plan_id) ON DELETE CASCADE
                )
            ''')
            
            # Create retirement_plan_history table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS retirement_plan_history (
                    history_id TEXT PRIMARY KEY,
                    plan_id TEXT NOT NULL,
                    
                    -- Snapshot of plan at this point in time
                    plan_snapshot TEXT NOT NULL,
                    
                    -- Metadata
                    created_at TEXT NOT NULL,
                    change_reason TEXT,
                    
                    FOREIGN KEY (plan_id) REFERENCES retirement_plans(plan_id) ON DELETE CASCADE
                )
            ''')
            
            # Create indexes for performance
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_retirement_plans_user_id ON retirement_plans(user_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_retirement_plans_created_at ON retirement_plans(created_at)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_retirement_scenarios_plan_id ON retirement_scenarios(plan_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_retirement_action_plans_plan_id ON retirement_action_plans(plan_id)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_retirement_plan_history_plan_id ON retirement_plan_history(plan_id)')
            
            conn.commit()
            logger.info("Retirement planning tables created successfully")
        except sqlite3.Error as e:
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def drop_tables(db_path: str = 'auth.db') -> None:
        """
        Drop all retirement planning tables (for testing/cleanup)
        
        Args:
            db_path: Path to SQLite database
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute('DROP TABLE IF EXISTS retirement_plan_history')
            cursor.execute('DROP TABLE IF EXISTS retirement_action_plans')
            cursor.execute('DROP TABLE IF EXISTS retirement_scenarios')
            cursor.execute('DROP TABLE IF EXISTS retirement_plans')
            
            conn.commit()
            logger.info("Retirement planning tables dropped successfully")
        except sqlite3.Error as e:
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            if conn:
                conn.close()
    
    @staticmethod
    def verify_tables(db_path: str = 'auth.db') -> bool:
        """
        Verify that all retirement planning tables exist
        
        Args:
            db_path: Path to SQLite database
        
        Returns:
            True if all tables exist, False otherwise
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            required_tables = [
                'retirement_plans',
                'retirement_scenarios',
                'retirement_action_plans',
                'retirement_plan_history'
            ]
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row[0] for row in cursor.fetchall()]
            
            for table in required_tables:
                if table not in existing_tables:
                    logger.warning(f"Table {table} not found")
                    return False
            
            logger.info("All retirement planning tables verified")
            return True
        except sqlite3.Error as e:
            logger.error(f"Database error: {str(e)}")
            return False
        finally:
            if conn:
                conn.close()
