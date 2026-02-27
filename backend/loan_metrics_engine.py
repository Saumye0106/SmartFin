"""
Loan_Metrics_Engine - Calculate loan diversity, payment history, and maturity scores
Provides comprehensive loan metrics for financial health scoring
"""

import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
from collections import defaultdict


class LoanMetricsEngine:
    """Engine for calculating loan-related metrics and scores"""
    
    def __init__(self, db_path: str):
        """
        Initialize LoanMetricsEngine
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
    
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _get_active_loans(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all active (non-deleted) loans for a user
        
        Args:
            user_id: ID of the user
        
        Returns:
            List of loan dictionaries
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute('''
                SELECT loan_id, user_id, loan_type, loan_amount, loan_tenure,
                       monthly_emi, interest_rate, loan_start_date, loan_maturity_date,
                       default_status, created_at, updated_at
                FROM loans
                WHERE user_id = ? AND deleted_at IS NULL
            ''', (user_id,))
            
            rows = cur.fetchall()
            return [dict(row) for row in rows]
            
        finally:
            conn.close()
    
    def _get_all_payments(self, user_id: int) -> List[Dict[str, Any]]:
        """
        Get all payments for all loans of a user
        
        Args:
            user_id: ID of the user
        
        Returns:
            List of payment dictionaries
        """
        conn = self._get_connection()
        cur = conn.cursor()
        
        try:
            cur.execute('''
                SELECT p.payment_id, p.loan_id, p.payment_date, p.payment_amount,
                       p.payment_status, p.created_at, p.updated_at
                FROM loan_payments p
                INNER JOIN loans l ON p.loan_id = l.loan_id
                WHERE l.user_id = ? AND l.deleted_at IS NULL
            ''', (user_id,))
            
            rows = cur.fetchall()
            return [dict(row) for row in rows]
            
        finally:
            conn.close()
    
    def calculateLoanDiversityScore(self, user_id: int) -> float:
        """
        Calculate loan diversity score (0-100)
        
        Based on:
        - Loan type diversity (40% weight): Number of distinct loan types
        - Type distribution (35% weight): Balance of loan amounts across types
        - Loan count diversity (25% weight): Number of active loans
        
        Scoring logic:
        - 0 loans: 50 (neutral baseline)
        - 1 loan: 60
        - 2 loans: 75
        - 3+ loans: 85-100 (depending on diversity and distribution)
        
        Penalties:
        - Single loan type: -20 points
        - Imbalanced distribution (one type >80%): -15 points
        - More than 5 active loans: -10 points
        
        Args:
            user_id: ID of the user
        
        Returns:
            Loan diversity score (0-100)
        """
        loans = self._get_active_loans(user_id)
        
        # No active loans: return neutral baseline
        if not loans:
            return 50.0
        
        # Calculate loan type diversity (distinct types)
        loan_types = set(loan['loan_type'] for loan in loans)
        num_types = len(loan_types)
        
        # Calculate type distribution (percentage per type)
        total_amount = sum(loan['loan_amount'] for loan in loans)
        type_amounts = defaultdict(float)
        for loan in loans:
            type_amounts[loan['loan_type']] += loan['loan_amount']
        
        type_percentages = {
            loan_type: (amount / total_amount) * 100
            for loan_type, amount in type_amounts.items()
        }
        
        # Calculate loan count
        loan_count = len(loans)
        
        # Base score calculation
        # Type diversity component (40% weight)
        if num_types == 1:
            type_diversity_score = 50
        elif num_types == 2:
            type_diversity_score = 75
        elif num_types == 3:
            type_diversity_score = 90
        else:  # 4 types
            type_diversity_score = 100
        
        # Distribution component (35% weight)
        # Check if distribution is balanced (no single type dominates)
        max_percentage = max(type_percentages.values())
        if max_percentage > 80:
            distribution_score = 50
        elif max_percentage > 60:
            distribution_score = 70
        elif max_percentage > 40:
            distribution_score = 85
        else:
            distribution_score = 100
        
        # Count component (25% weight)
        if loan_count == 1:
            count_score = 60
        elif loan_count == 2:
            count_score = 75
        elif loan_count == 3:
            count_score = 90
        elif loan_count == 4:
            count_score = 100
        else:  # 5 or more
            count_score = 85  # Slight penalty for too many loans
        
        # Weighted score
        base_score = (
            type_diversity_score * 0.40 +
            distribution_score * 0.35 +
            count_score * 0.25
        )
        
        # Apply penalties (but don't double-penalize)
        penalties = 0
        
        # Single loan type penalty (only if not already reflected in type_diversity_score)
        if num_types == 1 and loan_count > 1:
            penalties += 10  # Reduced penalty since already reflected in type_diversity_score
        
        # Imbalanced distribution penalty (only if multiple types)
        if num_types > 1 and max_percentage > 80:
            penalties += 10  # Reduced penalty
        
        # Too many loans penalty
        if loan_count > 5:
            penalties += 10
        
        # Calculate final score
        final_score = max(0, min(100, base_score - penalties))
        
        return round(final_score, 2)
    
    def calculatePaymentHistoryScore(self, user_id: int) -> float:
        """
        Calculate payment history score (0-100)
        
        Based on:
        - On-time payment percentage (primary factor)
        - Late payment count (deduction)
        - Missed payment count (larger deduction)
        
        Scoring logic:
        - 95-100% on-time: 95 base score
        - 85-94% on-time: 80 base score
        - 75-84% on-time: 65 base score
        - 60-74% on-time: 45 base score
        - <60% on-time: 25 base score
        
        Deductions:
        - Late payments: -2 points each (max -15)
        - Missed payments: -5 points each (max -25)
        
        Args:
            user_id: ID of the user
        
        Returns:
            Payment history score (0-100)
        """
        payments = self._get_all_payments(user_id)
        
        # No payment history: return neutral baseline for new loans
        if not payments:
            return 70.0
        
        # Count payment statuses
        on_time_count = sum(1 for p in payments if p['payment_status'] == 'on-time')
        late_count = sum(1 for p in payments if p['payment_status'] == 'late')
        missed_count = sum(1 for p in payments if p['payment_status'] == 'missed')
        total_count = len(payments)
        
        # Calculate on-time percentage
        on_time_percentage = (on_time_count / total_count) * 100
        
        # Assign base score based on on-time percentage
        if on_time_percentage >= 95:
            base_score = 95
        elif on_time_percentage >= 85:
            base_score = 80
        elif on_time_percentage >= 75:
            base_score = 65
        elif on_time_percentage >= 60:
            base_score = 45
        else:
            base_score = 25
        
        # Calculate deductions
        late_deduction = min(15, late_count * 2)
        missed_deduction = min(25, missed_count * 5)
        
        # Calculate final score
        final_score = max(0, min(100, base_score - late_deduction - missed_deduction))
        
        return round(final_score, 2)
    
    def calculateLoanMaturityScore(self, user_id: int) -> float:
        """
        Calculate loan maturity score (0-100)
        
        Based on:
        - Average loan tenure (primary factor)
        - Weighted average tenure by loan amount
        - Loans maturing soon (bonus)
        - Loans maturing very late (penalty)
        
        Scoring logic:
        - <12 months: 85 base score (short-term, lower risk)
        - 12-36 months: 75 base score (medium-term)
        - 36-60 months: 65 base score (long-term)
        - >60 months: 50 base score (very long-term, higher commitment)
        
        Adjustments:
        - Loans maturing within 6 months: +10 points
        - Loans maturing beyond 10 years: -10 points
        
        Args:
            user_id: ID of the user
        
        Returns:
            Loan maturity score (0-100)
        """
        loans = self._get_active_loans(user_id)
        
        # No active loans: return neutral baseline
        if not loans:
            return 50.0
        
        # Calculate average loan tenure
        total_tenure = sum(loan['loan_tenure'] for loan in loans)
        average_tenure = total_tenure / len(loans)
        
        # Calculate weighted average tenure
        total_amount = sum(loan['loan_amount'] for loan in loans)
        weighted_tenure = sum(
            loan['loan_amount'] * loan['loan_tenure']
            for loan in loans
        ) / total_amount
        
        # Use weighted average for scoring (more representative)
        tenure_months = weighted_tenure
        
        # Assign base score based on tenure
        if tenure_months < 12:
            base_score = 85
        elif tenure_months < 36:
            base_score = 75
        elif tenure_months < 60:
            base_score = 65
        else:
            base_score = 50
        
        # Calculate adjustments
        adjustments = 0
        current_date = datetime.utcnow()
        
        for loan in loans:
            # Parse maturity date
            maturity_date = datetime.fromisoformat(
                loan['loan_maturity_date'].replace('Z', '+00:00')
            )
            
            # Calculate months remaining
            months_remaining = (
                (maturity_date.year - current_date.year) * 12 +
                (maturity_date.month - current_date.month)
            )
            
            # Bonus for loans maturing within 6 months
            if 0 < months_remaining <= 6:
                adjustments += 10
                break  # Only apply bonus once
        
        for loan in loans:
            # Parse maturity date
            maturity_date = datetime.fromisoformat(
                loan['loan_maturity_date'].replace('Z', '+00:00')
            )
            
            # Calculate months remaining
            months_remaining = (
                (maturity_date.year - current_date.year) * 12 +
                (maturity_date.month - current_date.month)
            )
            
            # Penalty for loans maturing beyond 10 years
            if months_remaining > 120:
                adjustments -= 10
                break  # Only apply penalty once
        
        # Calculate final score
        final_score = max(0, min(100, base_score + adjustments))
        
        return round(final_score, 2)
    
    def getPaymentStatistics(self, user_id: int) -> Dict[str, Any]:
        """
        Get payment statistics for a user
        
        Args:
            user_id: ID of the user
        
        Returns:
            Dictionary containing:
            - on_time_payment_percentage: float (0-100)
            - late_payment_count: int
            - missed_payment_count: int
            - total_payments: int
        """
        payments = self._get_all_payments(user_id)
        
        if not payments:
            return {
                'on_time_payment_percentage': 0.0,
                'late_payment_count': 0,
                'missed_payment_count': 0,
                'total_payments': 0
            }
        
        # Count payment statuses
        on_time_count = sum(1 for p in payments if p['payment_status'] == 'on-time')
        late_count = sum(1 for p in payments if p['payment_status'] == 'late')
        missed_count = sum(1 for p in payments if p['payment_status'] == 'missed')
        total_count = len(payments)
        
        # Calculate on-time percentage
        on_time_percentage = (on_time_count / total_count) * 100
        
        return {
            'on_time_payment_percentage': round(on_time_percentage, 2),
            'late_payment_count': late_count,
            'missed_payment_count': missed_count,
            'total_payments': total_count
        }
    
    def getLoanStatistics(self, user_id: int) -> Dict[str, Any]:
        """
        Get loan statistics for a user
        
        Args:
            user_id: ID of the user
        
        Returns:
            Dictionary containing:
            - total_active_loans: int
            - total_loan_amount: float
            - average_loan_tenure: float (months)
            - weighted_average_tenure: float (months)
            - loan_type_distribution: dict (type -> percentage)
        """
        loans = self._get_active_loans(user_id)
        
        if not loans:
            return {
                'total_active_loans': 0,
                'total_loan_amount': 0.0,
                'average_loan_tenure': 0.0,
                'weighted_average_tenure': 0.0,
                'loan_type_distribution': {}
            }
        
        # Calculate total active loans
        total_active_loans = len(loans)
        
        # Calculate total loan amount
        total_loan_amount = sum(loan['loan_amount'] for loan in loans)
        
        # Calculate average loan tenure
        total_tenure = sum(loan['loan_tenure'] for loan in loans)
        average_loan_tenure = total_tenure / total_active_loans
        
        # Calculate weighted average tenure
        weighted_average_tenure = sum(
            loan['loan_amount'] * loan['loan_tenure']
            for loan in loans
        ) / total_loan_amount
        
        # Calculate loan type distribution
        type_amounts = defaultdict(float)
        for loan in loans:
            type_amounts[loan['loan_type']] += loan['loan_amount']
        
        loan_type_distribution = {
            loan_type: round((amount / total_loan_amount) * 100, 2)
            for loan_type, amount in type_amounts.items()
        }
        
        return {
            'total_active_loans': total_active_loans,
            'total_loan_amount': round(total_loan_amount, 2),
            'average_loan_tenure': round(average_loan_tenure, 2),
            'weighted_average_tenure': round(weighted_average_tenure, 2),
            'loan_type_distribution': loan_type_distribution
        }
