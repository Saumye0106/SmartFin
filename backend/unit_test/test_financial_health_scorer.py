"""
Unit tests for Financial_Health_Scorer
Tests the 8-factor financial health scoring model
"""

import unittest
import sqlite3
import os
import sys
import tempfile
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from financial_health_scorer import FinancialHealthScorer


class TestFinancialHealthScorer(unittest.TestCase):
    """Test suite for FinancialHealthScorer"""
    
    def setUp(self):
        """Set up test database and scorer instance"""
        # Create temporary database
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Initialize database with required tables
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Create loans table
        cur.execute('''
            CREATE TABLE loans (
                loan_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                loan_type TEXT NOT NULL,
                loan_amount REAL NOT NULL,
                loan_tenure INTEGER NOT NULL,
                monthly_emi REAL NOT NULL,
                interest_rate REAL NOT NULL,
                loan_start_date TEXT NOT NULL,
                loan_maturity_date TEXT NOT NULL,
                default_status INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                deleted_at TEXT
            )
        ''')
        
        # Create loan_payments table
        cur.execute('''
            CREATE TABLE loan_payments (
                payment_id TEXT PRIMARY KEY,
                loan_id TEXT NOT NULL,
                payment_date TEXT NOT NULL,
                payment_amount REAL NOT NULL,
                payment_status TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (loan_id) REFERENCES loans(loan_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        # Create scorer instance
        self.scorer = FinancialHealthScorer(self.db_path)
    
    def tearDown(self):
        """Clean up test database"""
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_calculate_savings_score_excellent(self):
        """Test savings score calculation for excellent savings (30%+)"""
        financial_data = {
            'income': 100000,
            'savings': 30000,
            'rent': 20000,
            'food': 10000,
            'travel': 5000,
            'shopping': 5000,
            'emi': 10000,
            'age': 30
        }
        
        score = self.scorer._calculate_savings_score(financial_data)
        self.assertEqual(score, 100.0)
    
    def test_calculate_savings_score_good(self):
        """Test savings score calculation for good savings (20%)"""
        financial_data = {
            'income': 100000,
            'savings': 20000,
            'rent': 20000,
            'food': 10000,
            'travel': 5000,
            'shopping': 5000,
            'emi': 10000,
            'age': 30
        }
        
        score = self.scorer._calculate_savings_score(financial_data)
        self.assertEqual(score, 85.0)
    
    def test_calculate_savings_score_poor(self):
        """Test savings score calculation for poor savings (<5%)"""
        financial_data = {
            'income': 100000,
            'savings': 2000,
            'rent': 20000,
            'food': 10000,
            'travel': 5000,
            'shopping': 5000,
            'emi': 10000,
            'age': 30
        }
        
        score = self.scorer._calculate_savings_score(financial_data)
        self.assertEqual(score, 20.0)
    
    def test_calculate_debt_score_no_debt(self):
        """Test debt score calculation with no EMI"""
        financial_data = {
            'income': 100000,
            'emi': 0,
            'savings': 20000,
            'rent': 20000,
            'food': 10000,
            'travel': 5000,
            'shopping': 5000,
            'age': 30
        }
        
        score = self.scorer._calculate_debt_score(financial_data)
        self.assertEqual(score, 100.0)
    
    def test_calculate_debt_score_high_debt(self):
        """Test debt score calculation with high EMI (>50%)"""
        financial_data = {
            'income': 100000,
            'emi': 60000,
            'savings': 5000,
            'rent': 20000,
            'food': 10000,
            'travel': 5000,
            'shopping': 0,
            'age': 30
        }
        
        score = self.scorer._calculate_debt_score(financial_data)
        self.assertEqual(score, 10.0)
    
    def test_calculate_expense_score_low_expenses(self):
        """Test expense score calculation with low expenses (50%)"""
        financial_data = {
            'income': 100000,
            'rent': 20000,
            'food': 10000,
            'travel': 5000,
            'shopping': 5000,
            'emi': 10000,
            'savings': 50000,
            'age': 30
        }
        
        score = self.scorer._calculate_expense_score(financial_data)
        self.assertEqual(score, 100.0)
    
    def test_calculate_expense_score_high_expenses(self):
        """Test expense score calculation with high expenses (>90%)"""
        financial_data = {
            'income': 100000,
            'rent': 40000,
            'food': 20000,
            'travel': 10000,
            'shopping': 10000,
            'emi': 15000,
            'savings': 5000,
            'age': 30
        }
        
        score = self.scorer._calculate_expense_score(financial_data)
        self.assertEqual(score, 10.0)
    
    def test_calculate_balance_score_positive_balance(self):
        """Test balance score with positive balance and savings"""
        financial_data = {
            'income': 100000,
            'rent': 20000,
            'food': 10000,
            'travel': 5000,
            'shopping': 5000,
            'emi': 10000,
            'savings': 20000,
            'age': 30
        }
        
        score = self.scorer._calculate_balance_score(financial_data)
        self.assertEqual(score, 100.0)
    
    def test_calculate_life_stage_score_prime_years(self):
        """Test life stage score for prime earning years (25-35)"""
        financial_data = {
            'income': 100000,
            'age': 30,
            'savings': 20000,
            'rent': 20000,
            'food': 10000,
            'travel': 5000,
            'shopping': 5000,
            'emi': 10000
        }
        
        score = self.scorer._calculate_life_stage_score(financial_data)
        self.assertEqual(score, 85.0)
    
    def test_calculate_financial_health_score_no_loans(self):
        """Test overall score calculation for user without loans"""
        user_id = 1
        financial_data = {
            'income': 100000,
            'rent': 20000,
            'food': 10000,
            'travel': 5000,
            'shopping': 5000,
            'emi': 10000,
            'savings': 30000,
            'age': 30
        }
        
        result = self.scorer.calculateFinancialHealthScore(user_id, financial_data)
        
        # Verify all scores are present
        self.assertIn('overall_score', result)
        self.assertIn('savings_score', result)
        self.assertIn('debt_score', result)
        self.assertIn('expense_score', result)
        self.assertIn('balance_score', result)
        self.assertIn('life_stage_score', result)
        self.assertIn('loan_diversity_score', result)
        self.assertIn('payment_history_score', result)
        self.assertIn('loan_maturity_score', result)
        self.assertIn('calculated_at', result)
        
        # Verify loan scores use defaults
        self.assertEqual(result['loan_diversity_score'], 50.0)
        self.assertEqual(result['payment_history_score'], 70.0)
        self.assertEqual(result['loan_maturity_score'], 50.0)
        
        # Verify overall score is within valid range
        self.assertGreaterEqual(result['overall_score'], 0.0)
        self.assertLessEqual(result['overall_score'], 100.0)
    
    def test_calculate_financial_health_score_with_loans(self):
        """Test overall score calculation for user with loans"""
        user_id = 2
        
        # Add loan data
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Add a personal loan
        loan_start = datetime.utcnow()
        loan_maturity = loan_start + timedelta(days=365 * 2)  # 2 years
        
        cur.execute('''
            INSERT INTO loans (loan_id, user_id, loan_type, loan_amount, loan_tenure,
                             monthly_emi, interest_rate, loan_start_date, loan_maturity_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('loan1', user_id, 'personal', 100000, 24, 5000, 10.0,
              loan_start.isoformat(), loan_maturity.isoformat()))
        
        # Add payment history
        for i in range(10):
            payment_date = loan_start + timedelta(days=30 * i)
            cur.execute('''
                INSERT INTO loan_payments (payment_id, loan_id, payment_date,
                                         payment_amount, payment_status)
                VALUES (?, ?, ?, ?, ?)
            ''', (f'payment{i}', 'loan1', payment_date.isoformat(), 5000, 'on-time'))
        
        conn.commit()
        conn.close()
        
        financial_data = {
            'income': 100000,
            'rent': 20000,
            'food': 10000,
            'travel': 5000,
            'shopping': 5000,
            'emi': 5000,
            'savings': 30000,
            'age': 30
        }
        
        result = self.scorer.calculateFinancialHealthScore(user_id, financial_data)
        
        # Verify loan scores are calculated (not defaults)
        self.assertNotEqual(result['loan_diversity_score'], 50.0)
        self.assertNotEqual(result['payment_history_score'], 70.0)
        
        # Verify overall score is within valid range
        self.assertGreaterEqual(result['overall_score'], 0.0)
        self.assertLessEqual(result['overall_score'], 100.0)
    
    def test_get_score_breakdown(self):
        """Test score breakdown with factor contributions"""
        user_id = 3
        financial_data = {
            'income': 100000,
            'rent': 20000,
            'food': 10000,
            'travel': 5000,
            'shopping': 5000,
            'emi': 10000,
            'savings': 30000,
            'age': 30
        }
        
        result = self.scorer.getScoreBreakdown(user_id, financial_data)
        
        # Verify structure
        self.assertIn('overall_score', result)
        self.assertIn('factors', result)
        
        # Verify all 8 factors are present
        self.assertEqual(len(result['factors']), 8)
        
        # Verify each factor has required fields
        for factor in result['factors']:
            self.assertIn('name', factor)
            self.assertIn('score', factor)
            self.assertIn('weight', factor)
            self.assertIn('contribution', factor)
        
        # Verify weights sum to 1.0
        total_weight = sum(f['weight'] for f in result['factors'])
        self.assertAlmostEqual(total_weight, 1.0, places=2)
    
    def test_calculate_score_delta(self):
        """Test score delta calculation"""
        user_id = 4
        
        # Add loan data
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        loan_start = datetime.utcnow()
        loan_maturity = loan_start + timedelta(days=365 * 2)
        
        cur.execute('''
            INSERT INTO loans (loan_id, user_id, loan_type, loan_amount, loan_tenure,
                             monthly_emi, interest_rate, loan_start_date, loan_maturity_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', ('loan2', user_id, 'home', 500000, 24, 25000, 8.0,
              loan_start.isoformat(), loan_maturity.isoformat()))
        
        # Add excellent payment history
        for i in range(20):
            payment_date = loan_start + timedelta(days=30 * i)
            cur.execute('''
                INSERT INTO loan_payments (payment_id, loan_id, payment_date,
                                         payment_amount, payment_status)
                VALUES (?, ?, ?, ?, ?)
            ''', (f'payment{i}', 'loan2', payment_date.isoformat(), 25000, 'on-time'))
        
        conn.commit()
        conn.close()
        
        financial_data = {
            'income': 100000,
            'rent': 20000,
            'food': 10000,
            'travel': 5000,
            'shopping': 5000,
            'emi': 25000,
            'savings': 20000,
            'age': 30
        }
        
        result = self.scorer.calculateScoreDelta(user_id, financial_data)
        
        # Verify structure
        self.assertIn('score_with_loans', result)
        self.assertIn('score_without_loans', result)
        self.assertIn('delta', result)
        self.assertIn('percentage_change', result)
        
        # Verify delta is calculated
        expected_delta = result['score_with_loans'] - result['score_without_loans']
        self.assertAlmostEqual(result['delta'], expected_delta, places=2)
    
    def test_backward_compatibility_defaults(self):
        """Test that default loan scores are used when no loan data exists"""
        user_id = 5
        financial_data = {
            'income': 100000,
            'rent': 20000,
            'food': 10000,
            'travel': 5000,
            'shopping': 5000,
            'emi': 10000,
            'savings': 30000,
            'age': 30
        }
        
        result = self.scorer.calculateFinancialHealthScore(user_id, financial_data)
        
        # Verify defaults are used
        self.assertEqual(result['loan_diversity_score'], 
                        self.scorer.LOAN_DEFAULTS['loan_diversity'])
        self.assertEqual(result['payment_history_score'], 
                        self.scorer.LOAN_DEFAULTS['payment_history'])
        self.assertEqual(result['loan_maturity_score'], 
                        self.scorer.LOAN_DEFAULTS['loan_maturity'])
    
    def test_score_normalization(self):
        """Test that overall score is normalized to 0-100 range"""
        user_id = 6
        
        # Test with extreme values
        financial_data = {
            'income': 1000000,
            'rent': 10000,
            'food': 5000,
            'travel': 2000,
            'shopping': 1000,
            'emi': 0,
            'savings': 500000,
            'age': 35
        }
        
        result = self.scorer.calculateFinancialHealthScore(user_id, financial_data)
        
        # Verify score is within bounds
        self.assertGreaterEqual(result['overall_score'], 0.0)
        self.assertLessEqual(result['overall_score'], 100.0)
        
        # Verify score is rounded to 2 decimal places
        self.assertEqual(result['overall_score'], round(result['overall_score'], 2))
    
    def test_weight_distribution(self):
        """Test that factor weights sum to 1.0"""
        total_weight = sum(self.scorer.WEIGHTS.values())
        self.assertAlmostEqual(total_weight, 1.0, places=10)
    
    def test_get_score_history_empty(self):
        """Test score history retrieval when no history exists"""
        user_id = 7
        
        history = self.scorer.getScoreHistory(user_id)
        
        # Should return empty list when no history exists
        self.assertEqual(history, [])


if __name__ == '__main__':
    unittest.main()
