"""
Repository layer for Retirement Planning Calculator

Provides data access abstraction for:
- Retirement plans
- Retirement scenarios
- Action plans
- Plan history
"""

import sqlite3
import json
import uuid
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from .models import RetirementPlan, RetirementScenario, ActionPlanItem

logger = logging.getLogger(__name__)

# Compute absolute path to auth.db in the backend directory
_DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'auth.db')


class BaseRepository:
    """Base repository with common database operations"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or _DEFAULT_DB_PATH
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute SELECT query"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            results = cursor.fetchall()
            conn.close()
            return results
        except sqlite3.Error as e:
            logger.error(f"Query error: {str(e)}")
            raise
    
    def _execute_update(self, query: str, params: tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE query"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            rows_affected = cursor.rowcount
            conn.close()
            return rows_affected
        except sqlite3.Error as e:
            logger.error(f"Update error: {str(e)}")
            raise


class PlanRepository(BaseRepository):
    """Repository for retirement plans"""
    
    def create(self, plan: RetirementPlan) -> str:
        """Create new retirement plan"""
        query = '''
            INSERT INTO retirement_plans (
                plan_id, user_id, plan_name, current_age, retirement_age,
                current_salary, current_monthly_expenses, current_savings,
                desired_retirement_lifestyle, inflation_rate, investment_return_rate,
                life_expectancy, calculation_results, readiness_assessment,
                created_at, updated_at, is_primary, deleted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''
        
        calc_results = {
            'retirement_corpus': plan.retirement_corpus,
            'monthly_expenses_at_retirement': plan.monthly_expenses_at_retirement,
            'required_monthly_savings': plan.required_monthly_savings,
            'projected_savings': plan.projected_savings,
            'gap': plan.gap,
            'gap_percentage': plan.gap_percentage
        }
        
        readiness = {
            'readiness_score': plan.readiness_score,
            'readiness_classification': plan.readiness_classification,
            'financial_health_factor': plan.financial_health_factor,
            'savings_adequacy_factor': plan.savings_adequacy_factor,
            'savings_rate_factor': plan.savings_rate_factor,
            'debt_burden_factor': plan.debt_burden_factor,
            'time_horizon_factor': plan.time_horizon_factor
        }
        
        params = (
            plan.plan_id, plan.user_id, plan.plan_name, plan.current_age,
            plan.retirement_age, plan.current_salary, plan.current_monthly_expenses,
            plan.current_savings, plan.desired_retirement_lifestyle,
            plan.inflation_rate, plan.investment_return_rate, plan.life_expectancy,
            json.dumps(calc_results), json.dumps(readiness),
            plan.created_at, plan.updated_at, int(plan.is_primary), plan.deleted_at
        )
        
        self._execute_update(query, params)
        logger.info(f"Created plan {plan.plan_id}")
        return plan.plan_id
    
    def read(self, plan_id: str) -> Optional[RetirementPlan]:
        """Read retirement plan by ID"""
        query = 'SELECT * FROM retirement_plans WHERE plan_id = ? AND deleted_at IS NULL'
        results = self._execute_query(query, (plan_id,))
        
        if not results:
            return None
        
        return self._row_to_plan(results[0])
    
    def update(self, plan: RetirementPlan) -> bool:
        """Update retirement plan"""
        query = '''
            UPDATE retirement_plans SET
                plan_name = ?, current_age = ?, retirement_age = ?,
                current_salary = ?, current_monthly_expenses = ?,
                current_savings = ?, desired_retirement_lifestyle = ?,
                inflation_rate = ?, investment_return_rate = ?,
                life_expectancy = ?, calculation_results = ?,
                readiness_assessment = ?, updated_at = ?, is_primary = ?
            WHERE plan_id = ? AND deleted_at IS NULL
        '''
        
        calc_results = {
            'retirement_corpus': plan.retirement_corpus,
            'monthly_expenses_at_retirement': plan.monthly_expenses_at_retirement,
            'required_monthly_savings': plan.required_monthly_savings,
            'projected_savings': plan.projected_savings,
            'gap': plan.gap,
            'gap_percentage': plan.gap_percentage
        }
        
        readiness = {
            'readiness_score': plan.readiness_score,
            'readiness_classification': plan.readiness_classification,
            'financial_health_factor': plan.financial_health_factor,
            'savings_adequacy_factor': plan.savings_adequacy_factor,
            'savings_rate_factor': plan.savings_rate_factor,
            'debt_burden_factor': plan.debt_burden_factor,
            'time_horizon_factor': plan.time_horizon_factor
        }
        
        params = (
            plan.plan_name, plan.current_age, plan.retirement_age,
            plan.current_salary, plan.current_monthly_expenses,
            plan.current_savings, plan.desired_retirement_lifestyle,
            plan.inflation_rate, plan.investment_return_rate,
            plan.life_expectancy, json.dumps(calc_results),
            json.dumps(readiness), plan.updated_at, int(plan.is_primary),
            plan.plan_id
        )
        
        rows = self._execute_update(query, params)
        logger.info(f"Updated plan {plan.plan_id}")
        return rows > 0
    
    def delete(self, plan_id: str) -> bool:
        """Soft delete retirement plan"""
        query = '''
            UPDATE retirement_plans SET deleted_at = ?
            WHERE plan_id = ? AND deleted_at IS NULL
        '''
        rows = self._execute_update(query, (datetime.utcnow().isoformat(), plan_id))
        logger.info(f"Deleted plan {plan_id}")
        return rows > 0
    
    def list_by_user(self, user_id: int) -> List[RetirementPlan]:
        """List all plans for a user"""
        query = '''
            SELECT * FROM retirement_plans
            WHERE user_id = ? AND deleted_at IS NULL
            ORDER BY created_at DESC
        '''
        results = self._execute_query(query, (user_id,))
        return [self._row_to_plan(row) for row in results]
    
    def get_primary_plan(self, user_id: int) -> Optional[RetirementPlan]:
        """Get primary plan for user"""
        query = '''
            SELECT * FROM retirement_plans
            WHERE user_id = ? AND is_primary = 1 AND deleted_at IS NULL
            LIMIT 1
        '''
        results = self._execute_query(query, (user_id,))
        return self._row_to_plan(results[0]) if results else None
    
    def set_primary_plan(self, plan_id: str, user_id: int) -> bool:
        """Set plan as primary for user"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Unset all other primary plans for user
            cursor.execute(
                'UPDATE retirement_plans SET is_primary = 0 WHERE user_id = ?',
                (user_id,)
            )
            
            # Set this plan as primary
            cursor.execute(
                'UPDATE retirement_plans SET is_primary = 1 WHERE plan_id = ?',
                (plan_id,)
            )
            
            conn.commit()
            logger.info(f"Set plan {plan_id} as primary")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error setting primary plan: {str(e)}")
            return False
        finally:
            conn.close()
    
    def _row_to_plan(self, row: sqlite3.Row) -> RetirementPlan:
        """Convert database row to RetirementPlan object"""
        calc_results = json.loads(row['calculation_results'])
        readiness = json.loads(row['readiness_assessment'])
        
        return RetirementPlan(
            plan_id=row['plan_id'],
            user_id=row['user_id'],
            plan_name=row['plan_name'],
            current_age=row['current_age'],
            retirement_age=row['retirement_age'],
            current_salary=row['current_salary'],
            current_monthly_expenses=row['current_monthly_expenses'],
            current_savings=row['current_savings'],
            desired_retirement_lifestyle=row['desired_retirement_lifestyle'],
            inflation_rate=row['inflation_rate'],
            investment_return_rate=row['investment_return_rate'],
            life_expectancy=row['life_expectancy'],
            retirement_corpus=calc_results['retirement_corpus'],
            monthly_expenses_at_retirement=calc_results['monthly_expenses_at_retirement'],
            required_monthly_savings=calc_results['required_monthly_savings'],
            projected_savings=calc_results['projected_savings'],
            gap=calc_results['gap'],
            gap_percentage=calc_results['gap_percentage'],
            readiness_score=readiness['readiness_score'],
            readiness_classification=readiness['readiness_classification'],
            financial_health_factor=readiness['financial_health_factor'],
            savings_adequacy_factor=readiness['savings_adequacy_factor'],
            savings_rate_factor=readiness['savings_rate_factor'],
            debt_burden_factor=readiness['debt_burden_factor'],
            time_horizon_factor=readiness['time_horizon_factor'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
            is_primary=bool(row['is_primary']),
            deleted_at=row['deleted_at']
        )


class ScenarioRepository(BaseRepository):
    """Repository for retirement scenarios"""
    
    def create(self, scenario: RetirementScenario) -> str:
        """Create new scenario"""
        query = '''
            INSERT INTO retirement_scenarios (
                scenario_id, plan_id, scenario_name, parameters, results, created_at, is_primary
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        '''
        
        params_json = {
            'retirement_age': scenario.retirement_age,
            'monthly_savings': scenario.monthly_savings,
            'investment_return_rate': scenario.investment_return_rate,
            'inflation_rate': scenario.inflation_rate,
            'desired_retirement_lifestyle': scenario.desired_retirement_lifestyle
        }
        
        results_json = {
            'retirement_corpus': scenario.retirement_corpus,
            'required_monthly_savings': scenario.required_monthly_savings,
            'projected_savings': scenario.projected_savings,
            'gap': scenario.gap,
            'readiness_score': scenario.readiness_score
        }
        
        params = (
            scenario.scenario_id, scenario.plan_id, scenario.scenario_name,
            json.dumps(params_json), json.dumps(results_json),
            scenario.created_at, int(scenario.is_primary)
        )
        
        self._execute_update(query, params)
        logger.info(f"Created scenario {scenario.scenario_id}")
        return scenario.scenario_id
    
    def read(self, scenario_id: str) -> Optional[RetirementScenario]:
        """Read scenario by ID"""
        query = 'SELECT * FROM retirement_scenarios WHERE scenario_id = ?'
        results = self._execute_query(query, (scenario_id,))
        
        if not results:
            return None
        
        return self._row_to_scenario(results[0])
    
    def update(self, scenario: RetirementScenario) -> bool:
        """Update scenario"""
        query = '''
            UPDATE retirement_scenarios SET
                scenario_name = ?, parameters = ?, results = ?, is_primary = ?
            WHERE scenario_id = ?
        '''
        
        params_json = {
            'retirement_age': scenario.retirement_age,
            'monthly_savings': scenario.monthly_savings,
            'investment_return_rate': scenario.investment_return_rate,
            'inflation_rate': scenario.inflation_rate,
            'desired_retirement_lifestyle': scenario.desired_retirement_lifestyle
        }
        
        results_json = {
            'retirement_corpus': scenario.retirement_corpus,
            'required_monthly_savings': scenario.required_monthly_savings,
            'projected_savings': scenario.projected_savings,
            'gap': scenario.gap,
            'readiness_score': scenario.readiness_score
        }
        
        params = (
            scenario.scenario_name, json.dumps(params_json),
            json.dumps(results_json), int(scenario.is_primary),
            scenario.scenario_id
        )
        
        rows = self._execute_update(query, params)
        logger.info(f"Updated scenario {scenario.scenario_id}")
        return rows > 0
    
    def delete(self, scenario_id: str) -> bool:
        """Delete scenario"""
        query = 'DELETE FROM retirement_scenarios WHERE scenario_id = ?'
        rows = self._execute_update(query, (scenario_id,))
        logger.info(f"Deleted scenario {scenario_id}")
        return rows > 0
    
    def list_by_plan(self, plan_id: str) -> List[RetirementScenario]:
        """List all scenarios for a plan"""
        query = '''
            SELECT * FROM retirement_scenarios
            WHERE plan_id = ?
            ORDER BY created_at DESC
        '''
        results = self._execute_query(query, (plan_id,))
        return [self._row_to_scenario(row) for row in results]
    
    def get_primary_scenario(self, plan_id: str) -> Optional[RetirementScenario]:
        """Get primary scenario for plan"""
        query = '''
            SELECT * FROM retirement_scenarios
            WHERE plan_id = ? AND is_primary = 1
            LIMIT 1
        '''
        results = self._execute_query(query, (plan_id,))
        return self._row_to_scenario(results[0]) if results else None
    
    def set_primary_scenario(self, scenario_id: str, plan_id: str) -> bool:
        """Set scenario as primary for plan"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Unset all other primary scenarios for plan
            cursor.execute(
                'UPDATE retirement_scenarios SET is_primary = 0 WHERE plan_id = ?',
                (plan_id,)
            )
            
            # Set this scenario as primary
            cursor.execute(
                'UPDATE retirement_scenarios SET is_primary = 1 WHERE scenario_id = ?',
                (scenario_id,)
            )
            
            conn.commit()
            logger.info(f"Set scenario {scenario_id} as primary")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error setting primary scenario: {str(e)}")
            return False
        finally:
            conn.close()
    
    def _row_to_scenario(self, row: sqlite3.Row) -> RetirementScenario:
        """Convert database row to RetirementScenario object"""
        params = json.loads(row['parameters'])
        results = json.loads(row['results'])
        
        return RetirementScenario(
            scenario_id=row['scenario_id'],
            plan_id=row['plan_id'],
            scenario_name=row['scenario_name'],
            retirement_age=params['retirement_age'],
            monthly_savings=params['monthly_savings'],
            investment_return_rate=params['investment_return_rate'],
            inflation_rate=params['inflation_rate'],
            desired_retirement_lifestyle=params.get('desired_retirement_lifestyle'),
            retirement_corpus=results['retirement_corpus'],
            required_monthly_savings=results['required_monthly_savings'],
            projected_savings=results['projected_savings'],
            gap=results['gap'],
            readiness_score=results['readiness_score'],
            created_at=row['created_at'],
            is_primary=bool(row['is_primary'])
        )


class ActionPlanRepository(BaseRepository):
    """Repository for action plans"""
    
    def create(self, plan_id: str, actions: List[ActionPlanItem]) -> str:
        """Create action plan for a plan"""
        action_id = str(uuid.uuid4())
        query = '''
            INSERT INTO retirement_action_plans (
                action_id, plan_id, actions, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?)
        '''
        
        actions_json = [action.to_dict() for action in actions]
        now = datetime.utcnow().isoformat()
        
        params = (action_id, plan_id, json.dumps(actions_json), now, now)
        self._execute_update(query, params)
        logger.info(f"Created action plan {action_id}")
        return action_id
    
    def read(self, action_id: str) -> Optional[List[ActionPlanItem]]:
        """Read action plan by ID"""
        query = 'SELECT * FROM retirement_action_plans WHERE action_id = ?'
        results = self._execute_query(query, (action_id,))
        
        if not results:
            return None
        
        actions_json = json.loads(results[0]['actions'])
        return [ActionPlanItem(**action) for action in actions_json]
    
    def get_by_plan(self, plan_id: str) -> Optional[List[ActionPlanItem]]:
        """Get action plan for a plan"""
        query = '''
            SELECT * FROM retirement_action_plans
            WHERE plan_id = ?
            ORDER BY created_at DESC
            LIMIT 1
        '''
        results = self._execute_query(query, (plan_id,))
        
        if not results:
            return None
        
        actions_json = json.loads(results[0]['actions'])
        return [ActionPlanItem(**action) for action in actions_json]
    
    def update(self, action_id: str, actions: List[ActionPlanItem]) -> bool:
        """Update action plan"""
        query = '''
            UPDATE retirement_action_plans SET
                actions = ?, updated_at = ?
            WHERE action_id = ?
        '''
        
        actions_json = [action.to_dict() for action in actions]
        now = datetime.utcnow().isoformat()
        
        params = (json.dumps(actions_json), now, action_id)
        rows = self._execute_update(query, params)
        logger.info(f"Updated action plan {action_id}")
        return rows > 0
    
    def delete(self, action_id: str) -> bool:
        """Delete action plan"""
        query = 'DELETE FROM retirement_action_plans WHERE action_id = ?'
        rows = self._execute_update(query, (action_id,))
        logger.info(f"Deleted action plan {action_id}")
        return rows > 0


class HistoryRepository(BaseRepository):
    """Repository for plan history and versioning"""
    
    def create_snapshot(self, plan_id: str, plan: RetirementPlan, reason: str = '') -> str:
        """Create a snapshot of plan at a point in time"""
        history_id = str(uuid.uuid4())
        query = '''
            INSERT INTO retirement_plan_history (
                history_id, plan_id, plan_snapshot, created_at, change_reason
            ) VALUES (?, ?, ?, ?, ?)
        '''
        
        snapshot = plan.to_json()
        now = datetime.utcnow().isoformat()
        
        params = (history_id, plan_id, snapshot, now, reason)
        self._execute_update(query, params)
        logger.info(f"Created history snapshot {history_id}")
        return history_id
    
    def get_snapshot(self, history_id: str) -> Optional[RetirementPlan]:
        """Get a specific history snapshot"""
        query = 'SELECT * FROM retirement_plan_history WHERE history_id = ?'
        results = self._execute_query(query, (history_id,))
        
        if not results:
            return None
        
        plan_json = results[0]['plan_snapshot']
        return RetirementPlan.from_json(plan_json)
    
    def list_by_plan(self, plan_id: str) -> List[Dict[str, Any]]:
        """List all history snapshots for a plan"""
        query = '''
            SELECT history_id, created_at, change_reason
            FROM retirement_plan_history
            WHERE plan_id = ?
            ORDER BY created_at DESC
        '''
        results = self._execute_query(query, (plan_id,))
        
        return [
            {
                'history_id': row['history_id'],
                'created_at': row['created_at'],
                'change_reason': row['change_reason']
            }
            for row in results
        ]
    
    def delete_old_snapshots(self, plan_id: str, keep_count: int = 10) -> int:
        """Delete old snapshots, keeping only the most recent ones"""
        # Get IDs of snapshots to delete
        query = '''
            SELECT history_id FROM retirement_plan_history
            WHERE plan_id = ?
            ORDER BY created_at DESC
            LIMIT -1 OFFSET ?
        '''
        results = self._execute_query(query, (plan_id, keep_count))
        
        if not results:
            return 0
        
        history_ids = [row['history_id'] for row in results]
        
        # Delete old snapshots
        placeholders = ','.join('?' * len(history_ids))
        delete_query = f'DELETE FROM retirement_plan_history WHERE history_id IN ({placeholders})'
        rows = self._execute_update(delete_query, tuple(history_ids))
        
        logger.info(f"Deleted {rows} old snapshots for plan {plan_id}")
        return rows
