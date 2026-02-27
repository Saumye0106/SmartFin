"""
Unit tests for Loan_Data_Parser & Serializer
Tests JSON parsing and serialization for loan data
"""

import pytest
import json
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from loan_data_serializer import LoanDataSerializer, ParseError


class TestParseLoanJSON:
    """Test parseLoanJSON method"""
    
    def test_parse_valid_loan_json(self):
        """Test parsing valid loan JSON"""
        loan_json = json.dumps({
            'loan_type': 'personal',
            'loan_amount': 50000.00,
            'loan_tenure': 36,
            'monthly_emi': 1500.00,
            'interest_rate': 12.5,
            'loan_start_date': '2024-01-01T00:00:00',
            'loan_maturity_date': '2027-01-01T00:00:00'
        })
        
        result = LoanDataSerializer.parseLoanJSON(loan_json)
        
        assert result['loan_type'] == 'personal'
        assert result['loan_amount'] == 50000.00
        assert result['loan_tenure'] == 36
        assert result['monthly_emi'] == 1500.00
        assert result['interest_rate'] == 12.5
        assert '2024-01-01' in result['loan_start_date']
        assert '2027-01-01' in result['loan_maturity_date']
    
    def test_parse_loan_with_string_numbers(self):
        """Test parsing loan JSON with numeric strings"""
        loan_json = json.dumps({
            'loan_type': 'home',
            'loan_amount': '250000.50',
            'loan_tenure': '240',
            'monthly_emi': '2500.75',
            'interest_rate': '8.5',
            'loan_start_date': '2024-01-01T00:00:00',
            'loan_maturity_date': '2044-01-01T00:00:00'
        })
        
        result = LoanDataSerializer.parseLoanJSON(loan_json)
        
        assert result['loan_amount'] == 250000.50
        assert result['loan_tenure'] == 240
        assert result['monthly_emi'] == 2500.75
        assert result['interest_rate'] == 8.5
    
    def test_parse_loan_with_iso_dates_with_z(self):
        """Test parsing loan JSON with ISO dates ending in Z"""
        loan_json = json.dumps({
            'loan_type': 'auto',
            'loan_amount': 30000,
            'loan_tenure': 60,
            'monthly_emi': 600,
            'interest_rate': 10.0,
            'loan_start_date': '2024-01-01T00:00:00Z',
            'loan_maturity_date': '2029-01-01T00:00:00Z'
        })
        
        result = LoanDataSerializer.parseLoanJSON(loan_json)
        
        assert '2024-01-01' in result['loan_start_date']
        assert '2029-01-01' in result['loan_maturity_date']
    
    def test_parse_loan_with_default_status(self):
        """Test parsing loan JSON with default_status field"""
        loan_json = json.dumps({
            'loan_type': 'education',
            'loan_amount': 20000,
            'loan_tenure': 48,
            'monthly_emi': 500,
            'interest_rate': 6.5,
            'loan_start_date': '2024-01-01T00:00:00',
            'loan_maturity_date': '2028-01-01T00:00:00',
            'default_status': False
        })
        
        result = LoanDataSerializer.parseLoanJSON(loan_json)
        
        assert result['default_status'] is False
    
    def test_parse_loan_with_default_status_as_int(self):
        """Test parsing loan JSON with default_status as integer"""
        loan_json = json.dumps({
            'loan_type': 'personal',
            'loan_amount': 10000,
            'loan_tenure': 24,
            'monthly_emi': 450,
            'interest_rate': 11.0,
            'loan_start_date': '2024-01-01T00:00:00',
            'loan_maturity_date': '2026-01-01T00:00:00',
            'default_status': 0
        })
        
        result = LoanDataSerializer.parseLoanJSON(loan_json)
        
        assert result['default_status'] is False
    
    def test_parse_loan_missing_required_field(self):
        """Test parsing loan JSON with missing required field"""
        loan_json = json.dumps({
            'loan_type': 'personal',
            'loan_amount': 50000,
            # Missing loan_tenure
            'monthly_emi': 1500,
            'interest_rate': 12.5,
            'loan_start_date': '2024-01-01T00:00:00',
            'loan_maturity_date': '2027-01-01T00:00:00'
        })
        
        with pytest.raises(ParseError) as exc_info:
            LoanDataSerializer.parseLoanJSON(loan_json)
        
        assert 'Missing required fields' in str(exc_info.value)
        assert exc_info.value.field == 'loan_tenure'
    
    def test_parse_loan_invalid_json(self):
        """Test parsing malformed JSON"""
        loan_json = '{"loan_type": "personal", invalid json}'
        
        with pytest.raises(ParseError) as exc_info:
            LoanDataSerializer.parseLoanJSON(loan_json)
        
        assert 'Invalid JSON' in str(exc_info.value)
    
    def test_parse_loan_invalid_loan_amount(self):
        """Test parsing loan JSON with invalid loan_amount"""
        loan_json = json.dumps({
            'loan_type': 'personal',
            'loan_amount': 'not-a-number',
            'loan_tenure': 36,
            'monthly_emi': 1500,
            'interest_rate': 12.5,
            'loan_start_date': '2024-01-01T00:00:00',
            'loan_maturity_date': '2027-01-01T00:00:00'
        })
        
        with pytest.raises(ParseError) as exc_info:
            LoanDataSerializer.parseLoanJSON(loan_json)
        
        assert 'loan_amount must be a valid number' in str(exc_info.value)
        assert exc_info.value.field == 'loan_amount'
    
    def test_parse_loan_invalid_date_format(self):
        """Test parsing loan JSON with invalid date format"""
        loan_json = json.dumps({
            'loan_type': 'personal',
            'loan_amount': 50000,
            'loan_tenure': 36,
            'monthly_emi': 1500,
            'interest_rate': 12.5,
            'loan_start_date': '01/01/2024',  # Invalid format
            'loan_maturity_date': '2027-01-01T00:00:00'
        })
        
        with pytest.raises(ParseError) as exc_info:
            LoanDataSerializer.parseLoanJSON(loan_json)
        
        assert 'ISO 8601 format' in str(exc_info.value)
        assert exc_info.value.field == 'loan_start_date'


class TestParsePaymentJSON:
    """Test parsePaymentJSON method"""
    
    def test_parse_valid_payment_json(self):
        """Test parsing valid payment JSON"""
        payment_json = json.dumps({
            'payment_date': '2024-02-01T00:00:00',
            'payment_amount': 1500.00
        })
        
        result = LoanDataSerializer.parsePaymentJSON(payment_json)
        
        assert '2024-02-01' in result['payment_date']
        assert result['payment_amount'] == 1500.00
    
    def test_parse_payment_with_string_amount(self):
        """Test parsing payment JSON with string amount"""
        payment_json = json.dumps({
            'payment_date': '2024-02-01T00:00:00',
            'payment_amount': '1500.50'
        })
        
        result = LoanDataSerializer.parsePaymentJSON(payment_json)
        
        assert result['payment_amount'] == 1500.50
    
    def test_parse_payment_with_z_date(self):
        """Test parsing payment JSON with Z in date"""
        payment_json = json.dumps({
            'payment_date': '2024-02-01T00:00:00Z',
            'payment_amount': 1500
        })
        
        result = LoanDataSerializer.parsePaymentJSON(payment_json)
        
        assert '2024-02-01' in result['payment_date']
    
    def test_parse_payment_missing_required_field(self):
        """Test parsing payment JSON with missing required field"""
        payment_json = json.dumps({
            'payment_date': '2024-02-01T00:00:00'
            # Missing payment_amount
        })
        
        with pytest.raises(ParseError) as exc_info:
            LoanDataSerializer.parsePaymentJSON(payment_json)
        
        assert 'Missing required fields' in str(exc_info.value)
        assert exc_info.value.field == 'payment_amount'
    
    def test_parse_payment_invalid_date(self):
        """Test parsing payment JSON with invalid date"""
        payment_json = json.dumps({
            'payment_date': 'invalid-date',
            'payment_amount': 1500
        })
        
        with pytest.raises(ParseError) as exc_info:
            LoanDataSerializer.parsePaymentJSON(payment_json)
        
        assert 'ISO 8601 format' in str(exc_info.value)
        assert exc_info.value.field == 'payment_date'
    
    def test_parse_payment_invalid_amount(self):
        """Test parsing payment JSON with invalid amount"""
        payment_json = json.dumps({
            'payment_date': '2024-02-01T00:00:00',
            'payment_amount': 'not-a-number'
        })
        
        with pytest.raises(ParseError) as exc_info:
            LoanDataSerializer.parsePaymentJSON(payment_json)
        
        assert 'payment_amount must be a valid number' in str(exc_info.value)
        assert exc_info.value.field == 'payment_amount'


class TestSerializeLoan:
    """Test serializeLoan method"""
    
    def test_serialize_basic_loan(self):
        """Test serializing basic loan object"""
        loan = {
            'loan_id': 'test-loan-id',
            'user_id': 1,
            'loan_type': 'personal',
            'loan_amount': 50000.123,
            'loan_tenure': 36,
            'monthly_emi': 1500.456,
            'interest_rate': 12.567,
            'loan_start_date': '2024-01-01T00:00:00',
            'loan_maturity_date': '2027-01-01T00:00:00',
            'default_status': False
        }
        
        result = LoanDataSerializer.serializeLoan(loan)
        parsed = json.loads(result)
        
        assert parsed['loan_id'] == 'test-loan-id'
        assert parsed['loan_type'] == 'personal'
        assert parsed['loan_amount'] == 50000.12  # Rounded to 2 decimals
        assert parsed['monthly_emi'] == 1500.46  # Rounded to 2 decimals
        assert parsed['interest_rate'] == 12.57  # Rounded to 2 decimals
    
    def test_serialize_loan_with_datetime_objects(self):
        """Test serializing loan with datetime objects"""
        loan = {
            'loan_id': 'test-loan-id',
            'user_id': 1,
            'loan_type': 'home',
            'loan_amount': 250000,
            'loan_tenure': 240,
            'monthly_emi': 2500,
            'interest_rate': 8.5,
            'loan_start_date': datetime(2024, 1, 1),
            'loan_maturity_date': datetime(2044, 1, 1),
            'created_at': datetime(2024, 1, 1, 10, 30, 0),
            'updated_at': datetime(2024, 1, 1, 10, 30, 0),
            'default_status': False
        }
        
        result = LoanDataSerializer.serializeLoan(loan)
        parsed = json.loads(result)
        
        assert '2024-01-01' in parsed['loan_start_date']
        assert '2044-01-01' in parsed['loan_maturity_date']
        assert '2024-01-01' in parsed['created_at']
        assert '2024-01-01' in parsed['updated_at']
    
    def test_serialize_loan_calculates_months_remaining(self):
        """Test that serializeLoan calculates months_remaining"""
        # Create a loan that matures in the future
        future_date = datetime.utcnow()
        future_date = future_date.replace(year=future_date.year + 2)
        
        loan = {
            'loan_id': 'test-loan-id',
            'user_id': 1,
            'loan_type': 'auto',
            'loan_amount': 30000,
            'loan_tenure': 60,
            'monthly_emi': 600,
            'interest_rate': 10.0,
            'loan_start_date': '2024-01-01T00:00:00',
            'loan_maturity_date': future_date.isoformat(),
            'default_status': False
        }
        
        result = LoanDataSerializer.serializeLoan(loan)
        parsed = json.loads(result)
        
        assert 'months_remaining' in parsed
        assert parsed['months_remaining'] >= 0
    
    def test_serialize_loan_with_null_deleted_at(self):
        """Test serializing loan with null deleted_at"""
        loan = {
            'loan_id': 'test-loan-id',
            'user_id': 1,
            'loan_type': 'education',
            'loan_amount': 20000,
            'loan_tenure': 48,
            'monthly_emi': 500,
            'interest_rate': 6.5,
            'loan_start_date': '2024-01-01T00:00:00',
            'loan_maturity_date': '2028-01-01T00:00:00',
            'deleted_at': None,
            'default_status': False
        }
        
        result = LoanDataSerializer.serializeLoan(loan)
        parsed = json.loads(result)
        
        assert parsed['deleted_at'] is None
    
    def test_serialize_loan_does_not_modify_original(self):
        """Test that serializeLoan doesn't modify the original object"""
        loan = {
            'loan_id': 'test-loan-id',
            'loan_amount': 50000.123,
            'loan_start_date': '2024-01-01T00:00:00'
        }
        
        original_amount = loan['loan_amount']
        LoanDataSerializer.serializeLoan(loan)
        
        assert loan['loan_amount'] == original_amount


class TestSerializePayment:
    """Test serializePayment method"""
    
    def test_serialize_basic_payment(self):
        """Test serializing basic payment object"""
        payment = {
            'payment_id': 'test-payment-id',
            'loan_id': 'test-loan-id',
            'payment_date': '2024-02-01T00:00:00',
            'payment_amount': 1500.456,
            'payment_status': 'on-time'
        }
        
        result = LoanDataSerializer.serializePayment(payment)
        parsed = json.loads(result)
        
        assert parsed['payment_id'] == 'test-payment-id'
        assert parsed['payment_amount'] == 1500.46  # Rounded to 2 decimals
        assert parsed['payment_status'] == 'on-time'
    
    def test_serialize_payment_with_datetime_objects(self):
        """Test serializing payment with datetime objects"""
        payment = {
            'payment_id': 'test-payment-id',
            'loan_id': 'test-loan-id',
            'payment_date': datetime(2024, 2, 1),
            'payment_amount': 1500,
            'payment_status': 'late',
            'created_at': datetime(2024, 2, 1, 10, 30, 0),
            'updated_at': datetime(2024, 2, 1, 10, 30, 0)
        }
        
        result = LoanDataSerializer.serializePayment(payment)
        parsed = json.loads(result)
        
        assert '2024-02-01' in parsed['payment_date']
        assert '2024-02-01' in parsed['created_at']
        assert '2024-02-01' in parsed['updated_at']
    
    def test_serialize_payment_does_not_modify_original(self):
        """Test that serializePayment doesn't modify the original object"""
        payment = {
            'payment_id': 'test-payment-id',
            'payment_amount': 1500.456,
            'payment_date': '2024-02-01T00:00:00'
        }
        
        original_amount = payment['payment_amount']
        LoanDataSerializer.serializePayment(payment)
        
        assert payment['payment_amount'] == original_amount


class TestSerializeLoanMetrics:
    """Test serializeLoanMetrics method"""
    
    def test_serialize_basic_metrics(self):
        """Test serializing basic loan metrics"""
        metrics = {
            'loan_diversity_score': 75.456,
            'payment_history_score': 85.789,
            'loan_maturity_score': 70.123
        }
        
        result = LoanDataSerializer.serializeLoanMetrics(metrics)
        parsed = json.loads(result)
        
        assert parsed['loan_diversity_score'] == 75.46
        assert parsed['payment_history_score'] == 85.79
        assert parsed['loan_maturity_score'] == 70.12
    
    def test_serialize_metrics_with_payment_statistics(self):
        """Test serializing metrics with payment statistics"""
        metrics = {
            'loan_diversity_score': 75.0,
            'payment_history_score': 85.0,
            'loan_maturity_score': 70.0,
            'payment_statistics': {
                'on_time_payment_percentage': 92.567,
                'late_payment_count': 2,
                'missed_payment_count': 0,
                'total_payments': 24
            }
        }
        
        result = LoanDataSerializer.serializeLoanMetrics(metrics)
        parsed = json.loads(result)
        
        assert parsed['payment_statistics']['on_time_payment_percentage'] == 92.57
        assert parsed['payment_statistics']['late_payment_count'] == 2
    
    def test_serialize_metrics_with_loan_statistics(self):
        """Test serializing metrics with loan statistics"""
        metrics = {
            'loan_diversity_score': 75.0,
            'payment_history_score': 85.0,
            'loan_maturity_score': 70.0,
            'loan_statistics': {
                'total_active_loans': 3,
                'total_loan_amount': 100000.456,
                'average_loan_tenure': 48.789,
                'weighted_average_tenure': 52.123,
                'loan_type_distribution': {
                    'personal': 33.333,
                    'home': 50.000,
                    'auto': 16.667
                }
            }
        }
        
        result = LoanDataSerializer.serializeLoanMetrics(metrics)
        parsed = json.loads(result)
        
        assert parsed['loan_statistics']['total_loan_amount'] == 100000.46
        assert parsed['loan_statistics']['average_loan_tenure'] == 48.79
        assert parsed['loan_statistics']['weighted_average_tenure'] == 52.12
        assert parsed['loan_statistics']['loan_type_distribution']['personal'] == 33.33
    
    def test_serialize_metrics_with_datetime_calculated_at(self):
        """Test serializing metrics with datetime calculated_at"""
        metrics = {
            'loan_diversity_score': 75.0,
            'payment_history_score': 85.0,
            'loan_maturity_score': 70.0,
            'calculated_at': datetime(2024, 2, 1, 10, 30, 0)
        }
        
        result = LoanDataSerializer.serializeLoanMetrics(metrics)
        parsed = json.loads(result)
        
        assert '2024-02-01' in parsed['calculated_at']
    
    def test_serialize_metrics_does_not_modify_original(self):
        """Test that serializeLoanMetrics doesn't modify the original object"""
        metrics = {
            'loan_diversity_score': 75.456,
            'payment_statistics': {
                'on_time_payment_percentage': 92.567
            }
        }
        
        original_score = metrics['loan_diversity_score']
        original_percentage = metrics['payment_statistics']['on_time_payment_percentage']
        
        LoanDataSerializer.serializeLoanMetrics(metrics)
        
        assert metrics['loan_diversity_score'] == original_score
        assert metrics['payment_statistics']['on_time_payment_percentage'] == original_percentage


class TestRoundTripProperty:
    """Test round-trip property: parse(serialize(parse(x))) == parse(x)"""
    
    def test_loan_round_trip(self):
        """Test that loan data survives round-trip conversion"""
        original_json = json.dumps({
            'loan_type': 'personal',
            'loan_amount': 50000.00,
            'loan_tenure': 36,
            'monthly_emi': 1500.00,
            'interest_rate': 12.5,
            'loan_start_date': '2024-01-01T00:00:00',
            'loan_maturity_date': '2027-01-01T00:00:00'
        })
        
        # Parse -> Serialize -> Parse
        parsed1 = LoanDataSerializer.parseLoanJSON(original_json)
        serialized = LoanDataSerializer.serializeLoan(parsed1)
        parsed2 = LoanDataSerializer.parseLoanJSON(serialized)
        
        # Compare key fields (ignoring calculated fields like months_remaining)
        assert parsed1['loan_type'] == parsed2['loan_type']
        assert parsed1['loan_amount'] == parsed2['loan_amount']
        assert parsed1['loan_tenure'] == parsed2['loan_tenure']
        assert parsed1['monthly_emi'] == parsed2['monthly_emi']
        assert parsed1['interest_rate'] == parsed2['interest_rate']
    
    def test_payment_round_trip(self):
        """Test that payment data survives round-trip conversion"""
        original_json = json.dumps({
            'payment_date': '2024-02-01T00:00:00',
            'payment_amount': 1500.00
        })
        
        # Parse -> Serialize -> Parse
        parsed1 = LoanDataSerializer.parsePaymentJSON(original_json)
        serialized = LoanDataSerializer.serializePayment(parsed1)
        parsed2 = LoanDataSerializer.parsePaymentJSON(serialized)
        
        # Compare fields
        assert parsed1['payment_amount'] == parsed2['payment_amount']
        # Dates should be equivalent (may have different formats but same value)
        date1 = datetime.fromisoformat(parsed1['payment_date'].replace('Z', '+00:00'))
        date2 = datetime.fromisoformat(parsed2['payment_date'].replace('Z', '+00:00'))
        assert date1 == date2
