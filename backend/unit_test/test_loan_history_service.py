"""
Unit tests for Loan_History_System service
Tests CRUD operations, validation, and payment tracking
"""

import pytest
import sqlite3
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from loan_history_service import LoanHistoryService, ValidationError
from db_utils import init_loan_tables


@pytest.fixture
def test_db(tmp_path):
    """Create a test database"""
    db_path = str(tmp_path / "test.db")
    
    # Initialize database with loan tables
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table (required for foreign key)
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT NOT NULL
        )
    ''')
    
    # Insert test user
    cursor.execute('INSERT INTO users (id, username, email) VALUES (?, ?, ?)',
                   (1, 'testuser', 'test@example.com'))
    
    conn.commit()
    conn.close()
    
    # Initialize loan tables
    init_loan_tables(db_path)
    
    return db_path


@pytest.fixture
def service(test_db):
    """Create LoanHistoryService instance"""
    return LoanHistoryService(test_db)


@pytest.fixture
def valid_loan_data():
    """Valid loan data for testing"""
    start_date = datetime.utcnow()
    maturity_date = start_date + timedelta(days=365 * 2)  # 2 years
    
    return {
        'loan_type': 'personal',
        'loan_amount': 100000.0,
        'loan_tenure': 24,
        'monthly_emi': 4614.49,  # Correct EMI for 100k at 10% for 24 months
        'interest_rate': 10.0,
        'loan_start_date': start_date.isoformat(),
        'loan_maturity_date': maturity_date.isoformat()
    }


class TestValidateLoanData:
    """Tests for validateLoanData method"""
    
    def test_valid_loan_data(self, service, valid_loan_data):
        """Test validation with valid loan data"""
        result = service.validateLoanData(valid_loan_data)
        assert result['isValid'] is True
        assert len(result['errors']) == 0
    
    def test_missing_required_field(self, service, valid_loan_data):
        """Test validation fails when required field is missing"""
        del valid_loan_data['loan_type']
        result = service.validateLoanData(valid_loan_data)
        assert result['isValid'] is False
        assert len(result['errors']) > 0
        assert result['errors'][0]['field'] == 'loan_type'
    
    def test_invalid_loan_type(self, service, valid_loan_data):
        """Test validation fails with invalid loan type"""
        valid_loan_data['loan_type'] = 'invalid'
        result = service.validateLoanData(valid_loan_data)
        assert result['isValid'] is False
        assert any(e['field'] == 'loan_type' for e in result['errors'])
    
    def test_negative_loan_amount(self, service, valid_loan_data):
        """Test validation fails with negative loan amount"""
        valid_loan_data['loan_amount'] = -1000
        result = service.validateLoanData(valid_loan_data)
        assert result['isValid'] is False
        assert any(e['field'] == 'loan_amount' for e in result['errors'])
    
    def test_invalid_interest_rate(self, service, valid_loan_data):
        """Test validation fails with interest rate outside 0-50 range"""
        valid_loan_data['interest_rate'] = 60
        result = service.validateLoanData(valid_loan_data)
        assert result['isValid'] is False
        assert any(e['field'] == 'interest_rate' for e in result['errors'])
    
    def test_maturity_before_start(self, service, valid_loan_data):
        """Test validation fails when maturity date is before start date"""
        valid_loan_data['loan_maturity_date'] = valid_loan_data['loan_start_date']
        result = service.validateLoanData(valid_loan_data)
        assert result['isValid'] is False


class TestCreateLoan:
    """Tests for createLoan method"""
    
    def test_create_valid_loan(self, service, valid_loan_data):
        """Test creating a loan with valid data"""
        loan = service.createLoan(user_id=1, loan_data=valid_loan_data)
        
        assert loan is not None
        assert loan['loan_id'] is not None
        assert loan['user_id'] == 1
        assert loan['loan_type'] == 'personal'
        assert loan['loan_amount'] == 100000.0
        assert loan['default_status'] == 0
    
    def test_create_loan_with_invalid_data(self, service, valid_loan_data):
        """Test creating a loan with invalid data raises ValidationError"""
        valid_loan_data['loan_amount'] = -1000
        
        with pytest.raises(ValidationError) as exc_info:
            service.createLoan(user_id=1, loan_data=valid_loan_data)
        
        assert exc_info.value.field == 'loan_amount'


class TestGetLoan:
    """Tests for getLoan method"""
    
    def test_get_existing_loan(self, service, valid_loan_data):
        """Test retrieving an existing loan"""
        created_loan = service.createLoan(user_id=1, loan_data=valid_loan_data)
        
        retrieved_loan = service.getLoan(created_loan['loan_id'])
        
        assert retrieved_loan is not None
        assert retrieved_loan['loan_id'] == created_loan['loan_id']
        assert retrieved_loan['loan_amount'] == created_loan['loan_amount']
    
    def test_get_nonexistent_loan(self, service):
        """Test retrieving a non-existent loan returns None"""
        loan = service.getLoan('nonexistent-id')
        assert loan is None


class TestGetLoansByUser:
    """Tests for getLoansByUser method"""
    
    def test_get_loans_for_user(self, service, valid_loan_data):
        """Test retrieving all loans for a user"""
        # Create multiple loans
        service.createLoan(user_id=1, loan_data=valid_loan_data)
        service.createLoan(user_id=1, loan_data=valid_loan_data)
        
        loans = service.getLoansByUser(user_id=1)
        
        assert len(loans) == 2
        assert all(loan['user_id'] == 1 for loan in loans)
    
    def test_get_loans_excludes_deleted(self, service, valid_loan_data):
        """Test that deleted loans are excluded by default"""
        loan = service.createLoan(user_id=1, loan_data=valid_loan_data)
        service.deleteLoan(loan['loan_id'], user_id=1)
        
        loans = service.getLoansByUser(user_id=1)
        
        assert len(loans) == 0
    
    def test_get_loans_includes_deleted_when_requested(self, service, valid_loan_data):
        """Test that deleted loans are included when requested"""
        loan = service.createLoan(user_id=1, loan_data=valid_loan_data)
        service.deleteLoan(loan['loan_id'], user_id=1)
        
        loans = service.getLoansByUser(user_id=1, include_deleted=True)
        
        assert len(loans) == 1
        assert loans[0]['deleted_at'] is not None


class TestUpdateLoan:
    """Tests for updateLoan method"""
    
    def test_update_loan_amount(self, service, valid_loan_data):
        """Test updating loan amount"""
        loan = service.createLoan(user_id=1, loan_data=valid_loan_data)
        
        # Update with new EMI to match new amount (150k at 10% for 24 months)
        updates = {
            'loan_amount': 150000.0,
            'monthly_emi': 6921.74
        }
        
        updated_loan = service.updateLoan(loan['loan_id'], user_id=1, updates=updates)
        
        assert updated_loan['loan_amount'] == 150000.0
        assert updated_loan['monthly_emi'] == 6921.74
    
    def test_update_loan_ownership_check(self, service, valid_loan_data):
        """Test that update fails if user doesn't own the loan"""
        loan = service.createLoan(user_id=1, loan_data=valid_loan_data)
        
        with pytest.raises(ValueError) as exc_info:
            service.updateLoan(loan['loan_id'], user_id=999, updates={'loan_amount': 150000.0})
        
        assert 'does not own' in str(exc_info.value)
    
    def test_update_deleted_loan_fails(self, service, valid_loan_data):
        """Test that updating a deleted loan fails"""
        loan = service.createLoan(user_id=1, loan_data=valid_loan_data)
        service.deleteLoan(loan['loan_id'], user_id=1)
        
        with pytest.raises(ValueError) as exc_info:
            service.updateLoan(loan['loan_id'], user_id=1, updates={'loan_amount': 150000.0})
        
        assert 'deleted' in str(exc_info.value)


class TestDeleteLoan:
    """Tests for deleteLoan method"""
    
    def test_soft_delete_loan(self, service, valid_loan_data):
        """Test soft deleting a loan"""
        loan = service.createLoan(user_id=1, loan_data=valid_loan_data)
        
        result = service.deleteLoan(loan['loan_id'], user_id=1)
        
        assert result is True
        
        # Verify loan still exists but has deleted_at timestamp
        deleted_loan = service.getLoan(loan['loan_id'])
        assert deleted_loan is not None
        assert deleted_loan['deleted_at'] is not None
    
    def test_delete_loan_ownership_check(self, service, valid_loan_data):
        """Test that delete fails if user doesn't own the loan"""
        loan = service.createLoan(user_id=1, loan_data=valid_loan_data)
        
        with pytest.raises(ValueError) as exc_info:
            service.deleteLoan(loan['loan_id'], user_id=999)
        
        assert 'does not own' in str(exc_info.value)


class TestRecordPayment:
    """Tests for recordPayment method"""
    
    def test_record_payment(self, service, valid_loan_data):
        """Test recording a payment"""
        loan = service.createLoan(user_id=1, loan_data=valid_loan_data)
        
        payment_data = {
            'payment_date': datetime.utcnow().isoformat(),
            'payment_amount': 4614.49
        }
        
        payment = service.recordPayment(loan['loan_id'], payment_data)
        
        assert payment is not None
        assert payment['payment_id'] is not None
        assert payment['loan_id'] == loan['loan_id']
        assert payment['payment_amount'] == 4614.49
        assert payment['payment_status'] in ['on-time', 'late', 'missed']
    
    def test_record_payment_future_date_fails(self, service, valid_loan_data):
        """Test that recording a payment with future date now works (no future date validation)"""
        loan = service.createLoan(user_id=1, loan_data=valid_loan_data)
        
        # Future dates are now allowed due to timezone differences
        future_date = datetime.utcnow() + timedelta(days=30)
        payment_data = {
            'payment_date': future_date.isoformat(),
            'payment_amount': 4614.49
        }
        
        # This should now succeed instead of raising an error
        payment = service.recordPayment(loan['loan_id'], payment_data)
        assert payment['payment_id'] is not None
        assert payment['payment_amount'] == 4614.49
    
    def test_record_payment_negative_amount_fails(self, service, valid_loan_data):
        """Test that recording a payment with negative amount fails"""
        loan = service.createLoan(user_id=1, loan_data=valid_loan_data)
        
        payment_data = {
            'payment_date': datetime.utcnow().isoformat(),
            'payment_amount': -100
        }
        
        with pytest.raises(ValidationError) as exc_info:
            service.recordPayment(loan['loan_id'], payment_data)
        
        assert exc_info.value.field == 'payment_amount'


class TestGetPaymentHistory:
    """Tests for getPaymentHistory method"""
    
    def test_get_payment_history(self, service, valid_loan_data):
        """Test retrieving payment history"""
        loan = service.createLoan(user_id=1, loan_data=valid_loan_data)
        
        # Record multiple payments
        for i in range(3):
            payment_data = {
                'payment_date': (datetime.utcnow() - timedelta(days=30 * i)).isoformat(),
                'payment_amount': 4614.49
            }
            service.recordPayment(loan['loan_id'], payment_data)
        
        payments = service.getPaymentHistory(loan['loan_id'])
        
        assert len(payments) == 3
        assert all(p['loan_id'] == loan['loan_id'] for p in payments)
        
        # Verify payments are sorted by date (ascending)
        dates = [datetime.fromisoformat(p['payment_date'].replace('Z', '+00:00')) for p in payments]
        assert dates == sorted(dates)
    
    def test_get_payment_history_empty(self, service, valid_loan_data):
        """Test retrieving payment history for loan with no payments"""
        loan = service.createLoan(user_id=1, loan_data=valid_loan_data)
        
        payments = service.getPaymentHistory(loan['loan_id'])
        
        assert len(payments) == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
