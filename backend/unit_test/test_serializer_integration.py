"""
Integration test to verify Loan_Data_Parser & Serializer works with existing services
"""

import pytest
import json
import os
import sys
import tempfile
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from loan_data_serializer import LoanDataSerializer
from loan_history_service import LoanHistoryService
from loan_metrics_engine import LoanMetricsEngine


class TestSerializerIntegration:
    """Test that serializer integrates correctly with existing services"""
    
    @pytest.fixture
    def db_path(self):
        """Create a temporary database for testing"""
        fd, path = tempfile.mkstemp(suffix='.db')
        os.close(fd)
        
        # Initialize database schema
        import sqlite3
        conn = sqlite3.connect(path)
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
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
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
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (loan_id) REFERENCES loans(loan_id)
            )
        ''')
        
        conn.commit()
        conn.close()
        
        yield path
        
        # Cleanup
        os.unlink(path)
    
    def test_parse_and_create_loan(self, db_path):
        """Test parsing JSON and creating loan via service"""
        service = LoanHistoryService(db_path)
        
        # Create loan JSON (using correct EMI calculation)
        loan_json = json.dumps({
            'loan_type': 'personal',
            'loan_amount': 50000.00,
            'loan_tenure': 36,
            'monthly_emi': 1672.68,  # Correct EMI for 50000 @ 12.5% for 36 months
            'interest_rate': 12.5,
            'loan_start_date': '2024-01-01T00:00:00',
            'loan_maturity_date': '2027-01-01T00:00:00'
        })
        
        # Parse JSON
        loan_data = LoanDataSerializer.parseLoanJSON(loan_json)
        
        # Create loan using service
        created_loan = service.createLoan(user_id=1, loan_data=loan_data)
        
        assert created_loan is not None
        assert created_loan['loan_type'] == 'personal'
        assert created_loan['loan_amount'] == 50000.00
    
    def test_retrieve_and_serialize_loan(self, db_path):
        """Test retrieving loan from service and serializing"""
        service = LoanHistoryService(db_path)
        
        # Create a loan (using correct EMI calculation)
        loan_data = {
            'loan_type': 'home',
            'loan_amount': 250000.00,
            'loan_tenure': 240,
            'monthly_emi': 2169.56,  # Correct EMI for 250000 @ 8.5% for 240 months
            'interest_rate': 8.5,
            'loan_start_date': '2024-01-01T00:00:00',
            'loan_maturity_date': '2044-01-01T00:00:00'
        }
        
        created_loan = service.createLoan(user_id=1, loan_data=loan_data)
        loan_id = created_loan['loan_id']
        
        # Retrieve loan
        retrieved_loan = service.getLoan(loan_id)
        
        # Serialize loan
        serialized = LoanDataSerializer.serializeLoan(retrieved_loan)
        parsed = json.loads(serialized)
        
        assert parsed['loan_type'] == 'home'
        assert parsed['loan_amount'] == 250000.00
        assert 'months_remaining' in parsed
    
    def test_parse_and_record_payment(self, db_path):
        """Test parsing payment JSON and recording via service"""
        service = LoanHistoryService(db_path)
        
        # Create a loan first (using correct EMI calculation)
        loan_data = {
            'loan_type': 'auto',
            'loan_amount': 30000.00,
            'loan_tenure': 60,
            'monthly_emi': 637.41,  # Correct EMI for 30000 @ 10% for 60 months
            'interest_rate': 10.0,
            'loan_start_date': '2024-01-01T00:00:00',
            'loan_maturity_date': '2029-01-01T00:00:00'
        }
        
        created_loan = service.createLoan(user_id=1, loan_data=loan_data)
        loan_id = created_loan['loan_id']
        
        # Create payment JSON (using correct EMI amount)
        payment_json = json.dumps({
            'payment_date': '2024-02-01T00:00:00',
            'payment_amount': 637.41
        })
        
        # Parse JSON
        payment_data = LoanDataSerializer.parsePaymentJSON(payment_json)
        
        # Record payment using service
        created_payment = service.recordPayment(loan_id, payment_data)
        
        assert created_payment is not None
        assert created_payment['payment_amount'] == 637.41
        assert created_payment['payment_status'] in ['on-time', 'late', 'missed']
    
    def test_serialize_loan_metrics(self, db_path):
        """Test serializing metrics from metrics engine"""
        loan_service = LoanHistoryService(db_path)
        metrics_engine = LoanMetricsEngine(db_path)
        
        # Create multiple loans (using correct EMI calculations)
        loans_data = [
            {
                'loan_type': 'personal',
                'loan_amount': 50000.00,
                'loan_tenure': 36,
                'monthly_emi': 1672.68,  # Correct EMI
                'interest_rate': 12.5,
                'loan_start_date': '2024-01-01T00:00:00',
                'loan_maturity_date': '2027-01-01T00:00:00'
            },
            {
                'loan_type': 'home',
                'loan_amount': 250000.00,
                'loan_tenure': 240,
                'monthly_emi': 2169.56,  # Correct EMI
                'interest_rate': 8.5,
                'loan_start_date': '2024-01-01T00:00:00',
                'loan_maturity_date': '2044-01-01T00:00:00'
            }
        ]
        
        for loan_data in loans_data:
            loan_service.createLoan(user_id=1, loan_data=loan_data)
        
        # Calculate metrics
        diversity_score = metrics_engine.calculateLoanDiversityScore(user_id=1)
        payment_score = metrics_engine.calculatePaymentHistoryScore(user_id=1)
        maturity_score = metrics_engine.calculateLoanMaturityScore(user_id=1)
        payment_stats = metrics_engine.getPaymentStatistics(user_id=1)
        loan_stats = metrics_engine.getLoanStatistics(user_id=1)
        
        # Create metrics object
        metrics = {
            'loan_diversity_score': diversity_score,
            'payment_history_score': payment_score,
            'loan_maturity_score': maturity_score,
            'payment_statistics': payment_stats,
            'loan_statistics': loan_stats,
            'calculated_at': datetime.utcnow()
        }
        
        # Serialize metrics
        serialized = LoanDataSerializer.serializeLoanMetrics(metrics)
        parsed = json.loads(serialized)
        
        assert 'loan_diversity_score' in parsed
        assert 'payment_history_score' in parsed
        assert 'loan_maturity_score' in parsed
        assert 'payment_statistics' in parsed
        assert 'loan_statistics' in parsed
        assert parsed['loan_statistics']['total_active_loans'] == 2
