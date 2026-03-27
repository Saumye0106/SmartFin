"""
Integration Manager

Integrates retirement planning with existing SmartFin systems:
- Financial Health Scorer (ML model)
- Loan History System
- Goals Manager
"""

from typing import Dict, List, Optional, Tuple
import logging
from .exceptions import IntegrationError

logger = logging.getLogger(__name__)


class IntegrationManager:
    """
    Manages integration with existing SmartFin systems
    
    Provides interfaces to retrieve data from and update other systems
    while handling failures gracefully.
    """
    
    @staticmethod
    def get_financial_health_score(
        user_id: int,
        financial_health_scorer=None
    ) -> float:
        """
        Retrieve user's financial health score from ML model
        
        Args:
            user_id: User ID
            financial_health_scorer: Financial health scorer service (injected)
        
        Returns:
            Financial health score (0-100)
        
        Raises:
            IntegrationError: If retrieval fails
        """
        try:
            if financial_health_scorer is None:
                # Import here to avoid circular imports
                try:
                    from backend.financial_health_scorer import FinancialHealthScorer
                except ImportError:
                    # Handle being run from backend directory
                    from financial_health_scorer import FinancialHealthScorer
                import os
                db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'auth.db')
                financial_health_scorer = FinancialHealthScorer(db_path)
            
            score = financial_health_scorer.calculate_score(user_id)
            logger.info(f"Retrieved financial health score for user {user_id}: {score}")
            return score
        except Exception as e:
            logger.error(f"Failed to retrieve financial health score for user {user_id}: {str(e)}")
            raise IntegrationError('Financial Health Scorer', str(e))
    
    @staticmethod
    def get_user_loans(
        user_id: int,
        loan_service=None
    ) -> List[Dict]:
        """
        Retrieve user's active loans from Loan History System
        
        Args:
            user_id: User ID
            loan_service: Loan service (injected)
        
        Returns:
            List of active loans with details
        
        Raises:
            IntegrationError: If retrieval fails
        """
        try:
            if loan_service is None:
                # Import here to avoid circular imports
                from backend.loan_history_service import LoanHistoryService
                loan_service = LoanHistoryService()
            
            loans = loan_service.get_active_loans(user_id)
            logger.info(f"Retrieved {len(loans)} active loans for user {user_id}")
            return loans
        except Exception as e:
            logger.error(f"Failed to retrieve loans for user {user_id}: {str(e)}")
            raise IntegrationError('Loan History System', str(e))
    
    @staticmethod
    def get_financial_goals(
        user_id: int,
        goals_service=None
    ) -> List[Dict]:
        """
        Retrieve user's financial goals from Goals Manager
        
        Args:
            user_id: User ID
            goals_service: Goals service (injected)
        
        Returns:
            List of financial goals
        
        Raises:
            IntegrationError: If retrieval fails
        """
        try:
            if goals_service is None:
                # Import here to avoid circular imports
                from backend.goals_service import GoalsService
                goals_service = GoalsService()
            
            goals = goals_service.get_goals(user_id)
            logger.info(f"Retrieved {len(goals)} goals for user {user_id}")
            return goals
        except Exception as e:
            logger.error(f"Failed to retrieve goals for user {user_id}: {str(e)}")
            raise IntegrationError('Goals Manager', str(e))
    
    @staticmethod
    def create_retirement_goal(
        user_id: int,
        corpus_target: float,
        retirement_age: int,
        goals_service=None
    ) -> str:
        """
        Create retirement goal in Goals Manager
        
        Args:
            user_id: User ID
            corpus_target: Target retirement corpus
            retirement_age: Target retirement age
            goals_service: Goals service (injected)
        
        Returns:
            Goal ID
        
        Raises:
            IntegrationError: If creation fails
        """
        try:
            if goals_service is None:
                from backend.goals_service import GoalsService
                goals_service = GoalsService()
            
            goal_data = {
                'goal_type': 'long-term',
                'target_amount': corpus_target,
                'target_date': f'{retirement_age}-12-31',  # Simplified
                'priority': 'high',
                'description': f'Retirement corpus target: ₹{corpus_target:,.0f}'
            }
            
            goal_id = goals_service.create_goal(user_id, goal_data)
            logger.info(f"Created retirement goal {goal_id} for user {user_id}")
            return goal_id
        except Exception as e:
            logger.error(f"Failed to create retirement goal for user {user_id}: {str(e)}")
            raise IntegrationError('Goals Manager', str(e))
    
    @staticmethod
    def update_retirement_goal(
        goal_id: str,
        corpus_target: float,
        goals_service=None
    ) -> None:
        """
        Update retirement goal with new corpus target
        
        Args:
            goal_id: Goal ID
            corpus_target: New target corpus
            goals_service: Goals service (injected)
        
        Raises:
            IntegrationError: If update fails
        """
        try:
            if goals_service is None:
                from backend.goals_service import GoalsService
                goals_service = GoalsService()
            
            goal_data = {
                'target_amount': corpus_target,
                'description': f'Retirement corpus target: ₹{corpus_target:,.0f}'
            }
            
            goals_service.update_goal(goal_id, goal_data)
            logger.info(f"Updated retirement goal {goal_id} with new corpus target")
        except Exception as e:
            logger.error(f"Failed to update retirement goal {goal_id}: {str(e)}")
            raise IntegrationError('Goals Manager', str(e))
    
    @staticmethod
    def calculate_goal_impact_on_retirement(
        goal: Dict,
        retirement_plan: Dict
    ) -> Dict:
        """
        Calculate how a goal impacts retirement savings capacity
        
        Args:
            goal: Goal dictionary
            retirement_plan: Retirement plan dictionary
        
        Returns:
            Impact analysis dictionary
        """
        goal_target = goal.get('target_amount', 0)
        goal_date = goal.get('target_date', '')
        
        # Parse goal date to get years until goal
        try:
            goal_year = int(goal_date.split('-')[0])
            retirement_year = retirement_plan.get('retirement_age', 60)
            years_until_goal = goal_year - retirement_plan.get('current_age', 30)
        except:
            years_until_goal = 0
        
        # Calculate impact on retirement savings
        if years_until_goal > 0 and years_until_goal < retirement_plan.get('retirement_age', 60) - retirement_plan.get('current_age', 30):
            # Goal is before retirement - impacts available savings
            impact_percentage = (goal_target / retirement_plan.get('corpus_target', 1)) * 100
        else:
            # Goal is after retirement or invalid - no impact
            impact_percentage = 0
        
        return {
            'goal_id': goal.get('id'),
            'goal_name': goal.get('goal_type'),
            'goal_amount': goal_target,
            'years_until_goal': years_until_goal,
            'impact_on_retirement_savings_percentage': impact_percentage,
            'reduces_available_savings': impact_percentage > 0
        }
    
    @staticmethod
    def aggregate_loan_data(loans: List[Dict]) -> Dict:
        """
        Aggregate loan data for retirement planning
        
        Args:
            loans: List of loan dictionaries
        
        Returns:
            Aggregated loan data
        """
        total_amount = sum(loan.get('outstanding_amount', 0) for loan in loans)
        total_emi = sum(loan.get('emi', 0) for loan in loans)
        total_interest = sum(loan.get('interest_amount', 0) for loan in loans)
        
        return {
            'total_loan_amount': total_amount,
            'total_monthly_emi': total_emi,
            'total_interest': total_interest,
            'number_of_loans': len(loans),
            'loans': loans
        }
    
    @staticmethod
    def get_user_profile_data(
        user_id: int,
        profile_service=None
    ) -> Dict:
        """
        Retrieve user profile data
        
        Args:
            user_id: User ID
            profile_service: Profile service (injected)
        
        Returns:
            User profile data
        
        Raises:
            IntegrationError: If retrieval fails
        """
        try:
            if profile_service is None:
                from backend.profile_service import ProfileService
                profile_service = ProfileService()
            
            profile = profile_service.get_profile(user_id)
            logger.info(f"Retrieved profile data for user {user_id}")
            return profile
        except Exception as e:
            logger.error(f"Failed to retrieve profile for user {user_id}: {str(e)}")
            raise IntegrationError('Profile Service', str(e))
    
    @staticmethod
    def validate_integration_health() -> Dict:
        """
        Validate that all integrated systems are accessible
        
        Returns:
            Health status dictionary
        """
        health = {
            'financial_health_scorer': 'unknown',
            'loan_history_system': 'unknown',
            'goals_manager': 'unknown',
            'profile_service': 'unknown'
        }
        
        # Try to import each service
        try:
            from backend.financial_health_scorer import FinancialHealthScorer
            health['financial_health_scorer'] = 'ok'
        except:
            health['financial_health_scorer'] = 'error'
        
        try:
            from backend.loan_history_service import LoanHistoryService
            health['loan_history_system'] = 'ok'
        except:
            health['loan_history_system'] = 'error'
        
        try:
            from backend.goals_service import GoalsService
            health['goals_manager'] = 'ok'
        except:
            health['goals_manager'] = 'error'
        
        try:
            from backend.profile_service import ProfileService
            health['profile_service'] = 'ok'
        except:
            health['profile_service'] = 'error'
        
        return health
