"""
Financial_Health_Scorer - Enhanced 8-factor financial health scoring model
Integrates loan metrics with existing 5-factor model for comprehensive assessment
"""

import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
from loan_metrics_engine import LoanMetricsEngine


class FinancialHealthScorer:
    """Enhanced 8-factor financial health scoring system"""
    
    # Factor weights for 8-factor model
    WEIGHTS = {
        'savings': 0.25,      # Reduced from 0.30
        'debt': 0.20,         # Reduced from 0.25
        'expense': 0.18,      # Reduced from 0.20
        'balance': 0.12,      # Reduced from 0.15
        'life_stage': 0.08,   # Reduced from 0.10
        'loan_diversity': 0.10,    # NEW
        'payment_history': 0.05,   # NEW
        'loan_maturity': 0.02      # NEW
    }
    
    # Default values for users without loan history (backward compatibility)
    LOAN_DEFAULTS = {
        'loan_diversity': 50.0,      # Neutral
        'payment_history': 70.0,     # Neutral for new loans
        'loan_maturity': 50.0        # Neutral
    }
    
    def __init__(self, db_path: str):
        """
        Initialize FinancialHealthScorer
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.loan_metrics_engine = LoanMetricsEngine(db_path)
    
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _calculate_savings_score(self, financial_data: Dict[str, float]) -> float:
        """
        Calculate savings score (25% weight)
        
        Args:
            financial_data: Dictionary with income and savings
        
        Returns:
            Savings score (0-100)
        """
        income = financial_data.get('income', 0)
        savings = financial_data.get('savings', 0)
        
        if income <= 0:
            return 0.0
        
        savings_ratio = savings / income
        
        if savings_ratio >= 0.30:
            return 100.0
        elif savings_ratio >= 0.20:
            return 85.0
        elif savings_ratio >= 0.15:
            return 70.0
        elif savings_ratio >= 0.10:
            return 55.0
        elif savings_ratio >= 0.05:
            return 40.0
        else:
            return 20.0
    
    def _calculate_debt_score(self, financial_data: Dict[str, float]) -> float:
        """
        Calculate debt management score (20% weight)
        
        Args:
            financial_data: Dictionary with income and emi
        
        Returns:
            Debt score (0-100)
        """
        income = financial_data.get('income', 0)
        emi = financial_data.get('emi', 0)
        
        if income <= 0:
            return 0.0
        
        emi_ratio = emi / income
        
        if emi_ratio == 0:
            return 100.0
        elif emi_ratio <= 0.20:
            return 85.0
        elif emi_ratio <= 0.30:
            return 70.0
        elif emi_ratio <= 0.40:
            return 50.0
        elif emi_ratio <= 0.50:
            return 30.0
        else:
            return 10.0
    
    def _calculate_expense_score(self, financial_data: Dict[str, float]) -> float:
        """
        Calculate expense control score (18% weight)
        
        Args:
            financial_data: Dictionary with income and expenses
        
        Returns:
            Expense score (0-100)
        """
        income = financial_data.get('income', 0)
        
        # Calculate total expenses
        rent = financial_data.get('rent', 0)
        food = financial_data.get('food', 0)
        travel = financial_data.get('travel', 0)
        shopping = financial_data.get('shopping', 0)
        emi = financial_data.get('emi', 0)
        
        total_expenses = rent + food + travel + shopping + emi
        
        if income <= 0:
            return 0.0
        
        expense_ratio = total_expenses / income
        
        if expense_ratio <= 0.50:
            return 100.0
        elif expense_ratio <= 0.60:
            return 85.0
        elif expense_ratio <= 0.70:
            return 70.0
        elif expense_ratio <= 0.80:
            return 50.0
        elif expense_ratio <= 0.90:
            return 30.0
        else:
            return 10.0
    
    def _calculate_balance_score(self, financial_data: Dict[str, float]) -> float:
        """
        Calculate balance score (12% weight)
        
        Args:
            financial_data: Dictionary with income, expenses, and savings
        
        Returns:
            Balance score (0-100)
        """
        income = financial_data.get('income', 0)
        savings = financial_data.get('savings', 0)
        
        # Calculate total expenses
        rent = financial_data.get('rent', 0)
        food = financial_data.get('food', 0)
        travel = financial_data.get('travel', 0)
        shopping = financial_data.get('shopping', 0)
        emi = financial_data.get('emi', 0)
        
        total_expenses = rent + food + travel + shopping + emi
        
        if income <= 0:
            return 0.0
        
        # Check if income covers expenses + savings
        balance = income - total_expenses - savings
        
        if balance >= 0 and savings > 0:
            return 100.0
        elif balance >= 0:
            return 70.0
        elif balance >= -income * 0.10:
            return 50.0
        else:
            return 20.0
    
    def _calculate_life_stage_score(self, financial_data: Dict[str, float]) -> float:
        """
        Calculate life stage score (8% weight)
        
        Args:
            financial_data: Dictionary with age
        
        Returns:
            Life stage score (0-100)
        """
        age = financial_data.get('age', 30)
        
        if age < 25:
            return 75.0  # Early career
        elif age < 35:
            return 85.0  # Prime earning years
        elif age < 50:
            return 80.0  # Peak earning years
        elif age < 60:
            return 75.0  # Pre-retirement
        else:
            return 70.0  # Retirement
    
    def calculateFinancialHealthScore(self, user_id: int, financial_data: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculate overall financial health score using 8-factor model
        
        Integrates existing 5 factors with 3 new loan factors:
        - Savings Score (25%)
        - Debt Score (20%)
        - Expense Score (18%)
        - Balance Score (12%)
        - Life Stage Score (8%)
        - Loan Diversity Score (10%)
        - Payment History Score (5%)
        - Loan Maturity Score (2%)
        
        Args:
            user_id: ID of the user
            financial_data: Dictionary with financial information
        
        Returns:
            Dictionary containing:
            - overall_score: float (0-100, 2 decimal places)
            - savings_score: float
            - debt_score: float
            - expense_score: float
            - balance_score: float
            - life_stage_score: float
            - loan_diversity_score: float
            - payment_history_score: float
            - loan_maturity_score: float
            - calculated_at: str (ISO 8601 timestamp)
        """
        # Calculate existing 5 factors
        savings_score = self._calculate_savings_score(financial_data)
        debt_score = self._calculate_debt_score(financial_data)
        expense_score = self._calculate_expense_score(financial_data)
        balance_score = self._calculate_balance_score(financial_data)
        life_stage_score = self._calculate_life_stage_score(financial_data)
        
        # Calculate new 3 loan factors
        # Check if user has loan history
        try:
            loan_diversity_score = self.loan_metrics_engine.calculateLoanDiversityScore(user_id)
            payment_history_score = self.loan_metrics_engine.calculatePaymentHistoryScore(user_id)
            loan_maturity_score = self.loan_metrics_engine.calculateLoanMaturityScore(user_id)
        except Exception:
            # Use defaults if loan metrics calculation fails
            loan_diversity_score = self.LOAN_DEFAULTS['loan_diversity']
            payment_history_score = self.LOAN_DEFAULTS['payment_history']
            loan_maturity_score = self.LOAN_DEFAULTS['loan_maturity']
        
        # Calculate weighted overall score
        overall_score = (
            savings_score * self.WEIGHTS['savings'] +
            debt_score * self.WEIGHTS['debt'] +
            expense_score * self.WEIGHTS['expense'] +
            balance_score * self.WEIGHTS['balance'] +
            life_stage_score * self.WEIGHTS['life_stage'] +
            loan_diversity_score * self.WEIGHTS['loan_diversity'] +
            payment_history_score * self.WEIGHTS['payment_history'] +
            loan_maturity_score * self.WEIGHTS['loan_maturity']
        )
        
        # Normalize to 0-100 and round to 2 decimal places
        overall_score = max(0.0, min(100.0, round(overall_score, 2)))
        
        return {
            'overall_score': overall_score,
            'savings_score': round(savings_score, 2),
            'debt_score': round(debt_score, 2),
            'expense_score': round(expense_score, 2),
            'balance_score': round(balance_score, 2),
            'life_stage_score': round(life_stage_score, 2),
            'loan_diversity_score': round(loan_diversity_score, 2),
            'payment_history_score': round(payment_history_score, 2),
            'loan_maturity_score': round(loan_maturity_score, 2),
            'calculated_at': datetime.utcnow().isoformat() + 'Z'
        }
    
    def getScoreBreakdown(self, user_id: int, financial_data: Dict[str, float]) -> Dict[str, Any]:
        """
        Get detailed score breakdown with individual factor contributions
        
        Args:
            user_id: ID of the user
            financial_data: Dictionary with financial information
        
        Returns:
            Dictionary containing:
            - overall_score: float
            - factors: list of factor dictionaries with name, score, weight, contribution
        """
        score_result = self.calculateFinancialHealthScore(user_id, financial_data)
        
        factors = [
            {
                'name': 'Savings',
                'score': score_result['savings_score'],
                'weight': self.WEIGHTS['savings'],
                'contribution': round(score_result['savings_score'] * self.WEIGHTS['savings'], 2)
            },
            {
                'name': 'Debt Management',
                'score': score_result['debt_score'],
                'weight': self.WEIGHTS['debt'],
                'contribution': round(score_result['debt_score'] * self.WEIGHTS['debt'], 2)
            },
            {
                'name': 'Expense Control',
                'score': score_result['expense_score'],
                'weight': self.WEIGHTS['expense'],
                'contribution': round(score_result['expense_score'] * self.WEIGHTS['expense'], 2)
            },
            {
                'name': 'Balance',
                'score': score_result['balance_score'],
                'weight': self.WEIGHTS['balance'],
                'contribution': round(score_result['balance_score'] * self.WEIGHTS['balance'], 2)
            },
            {
                'name': 'Life Stage',
                'score': score_result['life_stage_score'],
                'weight': self.WEIGHTS['life_stage'],
                'contribution': round(score_result['life_stage_score'] * self.WEIGHTS['life_stage'], 2)
            },
            {
                'name': 'Loan Diversity',
                'score': score_result['loan_diversity_score'],
                'weight': self.WEIGHTS['loan_diversity'],
                'contribution': round(score_result['loan_diversity_score'] * self.WEIGHTS['loan_diversity'], 2)
            },
            {
                'name': 'Payment History',
                'score': score_result['payment_history_score'],
                'weight': self.WEIGHTS['payment_history'],
                'contribution': round(score_result['payment_history_score'] * self.WEIGHTS['payment_history'], 2)
            },
            {
                'name': 'Loan Maturity',
                'score': score_result['loan_maturity_score'],
                'weight': self.WEIGHTS['loan_maturity'],
                'contribution': round(score_result['loan_maturity_score'] * self.WEIGHTS['loan_maturity'], 2)
            }
        ]
        
        return {
            'overall_score': score_result['overall_score'],
            'factors': factors
        }

    
    def getScoreHistory(self, user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get historical financial health scores for a user
        
        Args:
            user_id: ID of the user
            limit: Maximum number of historical records to return
        
        Returns:
            List of score history dictionaries with:
            - score: float
            - calculated_at: str (ISO 8601 timestamp)
            - factors: list of factor scores
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            # Query score history from database
            # Note: This assumes a score_history table exists
            # For now, return empty list as placeholder
            cur.execute('''
                SELECT overall_score, savings_score, debt_score, expense_score,
                       balance_score, life_stage_score, loan_diversity_score,
                       payment_history_score, loan_maturity_score, calculated_at
                FROM score_history
                WHERE user_id = ?
                ORDER BY calculated_at DESC
                LIMIT ?
            ''', (user_id, limit))
            
            rows = cur.fetchall()
            
            history = []
            for row in rows:
                history.append({
                    'score': row['overall_score'],
                    'calculated_at': row['calculated_at'],
                    'factors': [
                        {'name': 'Savings', 'score': row['savings_score']},
                        {'name': 'Debt Management', 'score': row['debt_score']},
                        {'name': 'Expense Control', 'score': row['expense_score']},
                        {'name': 'Balance', 'score': row['balance_score']},
                        {'name': 'Life Stage', 'score': row['life_stage_score']},
                        {'name': 'Loan Diversity', 'score': row['loan_diversity_score']},
                        {'name': 'Payment History', 'score': row['payment_history_score']},
                        {'name': 'Loan Maturity', 'score': row['loan_maturity_score']}
                    ]
                })
            
            return history
            
        except sqlite3.OperationalError:
            # Table doesn't exist yet, return empty list
            return []
        finally:
            conn.close()
    
    def calculateScoreDelta(self, user_id: int, financial_data: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculate score delta comparing with and without loan data
        
        Shows the impact of loan history on the overall score.
        Ensures delta is within bounds (-12 to +8 points as per requirements).
        
        Args:
            user_id: ID of the user
            financial_data: Dictionary with financial information
        
        Returns:
            Dictionary containing:
            - score_with_loans: float
            - score_without_loans: float
            - delta: float (change in score)
            - percentage_change: float
        """
        # Calculate score with actual loan data
        score_with_loans_result = self.calculateFinancialHealthScore(user_id, financial_data)
        score_with_loans = score_with_loans_result['overall_score']
        
        # Calculate score without loan data (using defaults)
        # Temporarily override loan metrics to use defaults
        savings_score = self._calculate_savings_score(financial_data)
        debt_score = self._calculate_debt_score(financial_data)
        expense_score = self._calculate_expense_score(financial_data)
        balance_score = self._calculate_balance_score(financial_data)
        life_stage_score = self._calculate_life_stage_score(financial_data)
        
        # Use default loan scores
        loan_diversity_score = self.LOAN_DEFAULTS['loan_diversity']
        payment_history_score = self.LOAN_DEFAULTS['payment_history']
        loan_maturity_score = self.LOAN_DEFAULTS['loan_maturity']
        
        # Calculate score without loans
        score_without_loans = (
            savings_score * self.WEIGHTS['savings'] +
            debt_score * self.WEIGHTS['debt'] +
            expense_score * self.WEIGHTS['expense'] +
            balance_score * self.WEIGHTS['balance'] +
            life_stage_score * self.WEIGHTS['life_stage'] +
            loan_diversity_score * self.WEIGHTS['loan_diversity'] +
            payment_history_score * self.WEIGHTS['payment_history'] +
            loan_maturity_score * self.WEIGHTS['loan_maturity']
        )
        
        score_without_loans = max(0.0, min(100.0, round(score_without_loans, 2)))
        
        # Calculate delta
        delta = round(score_with_loans - score_without_loans, 2)
        
        # Calculate percentage change
        if score_without_loans > 0:
            percentage_change = round((delta / score_without_loans) * 100, 2)
        else:
            percentage_change = 0.0
        
        return {
            'score_with_loans': score_with_loans,
            'score_without_loans': score_without_loans,
            'delta': delta,
            'percentage_change': percentage_change
        }
