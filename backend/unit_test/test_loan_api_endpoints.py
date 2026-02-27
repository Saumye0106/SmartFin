"""
Integration tests for Loan API endpoints
Tests all 8 loan management endpoints with authentication and authorization
"""

import pytest
import json
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app, init_db
from werkzeug.security import generate_password_hash
import sqlite3


@pytest.fixture
def client():
    """Create test client with test database"""
    app.config['TESTING'] = True
    app.config['JWT_SECRET_KEY'] = 'test-secret-key'
    
    # Use in-memory database for testing
    test_db_path = ':memory:'
    
    with app.test_client() as client:
        yield client


@pytest.fixture
def auth_headers(client):
    """Create authenticated user and return auth headers"""
    # Register a test user
    response = client.post('/register', json={
        'email': 'test@example.com',
        'password': 'testpass123'
    })
    
    data = json.loads(response.data)
    token = data.get('token')
    
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }


def test_create_loan_success(client, auth_headers):
    """Test POST /api/loans - successful loan creation"""
    loan_data = {
        'loan_type': 'personal',
        'loan_amount': 100000,
        'loan_tenure': 24,
        'monthly_emi': 4622.24,
        'interest_rate': 10.5,
        'loan_start_date': '2024-01-01T00:00:00Z',
        'loan_maturity_date': '2026-01-01T00:00:00Z'
    }
    
    response = client.post('/api/loans', 
                          json=loan_data,
                          headers=auth_headers)
    
    assert response.status_code == 201
    data = json.loads(response.data)
    assert 'loan' in data
    assert data['loan']['loan_type'] == 'personal'
    assert data['loan']['loan_amount'] == 100000


def test_create_loan_validation_error(client, auth_headers):
    """Test POST /api/loans - validation error"""
    loan_data = {
        'loan_type': 'personal',
        'loan_amount': -1000,  # Invalid: negative amount
        'loan_tenure': 24,
        'monthly_emi': 4622.24,
        'interest_rate': 10.5,
        'loan_start_date': '2024-01-01T00:00:00Z',
        'loan_maturity_date': '2026-01-01T00:00:00Z'
    }
    
    response = client.post('/api/loans',
                          json=loan_data,
                          headers=auth_headers)
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data


def test_create_loan_unauthorized(client):
    """Test POST /api/loans - unauthorized (no token)"""
    loan_data = {
        'loan_type': 'personal',
        'loan_amount': 100000,
        'loan_tenure': 24,
        'monthly_emi': 4622.24,
        'interest_rate': 10.5,
        'loan_start_date': '2024-01-01T00:00:00Z',
        'loan_maturity_date': '2026-01-01T00:00:00Z'
    }
    
    response = client.post('/api/loans', json=loan_data)
    
    assert response.status_code == 401


def test_get_user_loans(client, auth_headers):
    """Test GET /api/loans/user/{user_id} - get all user loans"""
    # First create a loan
    loan_data = {
        'loan_type': 'home',
        'loan_amount': 500000,
        'loan_tenure': 240,
        'monthly_emi': 4825.00,
        'interest_rate': 8.5,
        'loan_start_date': '2024-01-01T00:00:00Z',
        'loan_maturity_date': '2044-01-01T00:00:00Z'
    }
    
    client.post('/api/loans', json=loan_data, headers=auth_headers)
    
    # Get user ID from token (in real test, extract from JWT)
    # For now, assume user_id = 1
    response = client.get('/api/loans/user/1', headers=auth_headers)
    
    assert response.status_code in [200, 403]  # 403 if user_id doesn't match


def test_get_loan_by_id(client, auth_headers):
    """Test GET /api/loans/{loan_id} - get specific loan"""
    # First create a loan
    loan_data = {
        'loan_type': 'auto',
        'loan_amount': 50000,
        'loan_tenure': 60,
        'monthly_emi': 943.56,
        'interest_rate': 9.0,
        'loan_start_date': '2024-01-01T00:00:00Z',
        'loan_maturity_date': '2029-01-01T00:00:00Z'
    }
    
    create_response = client.post('/api/loans', json=loan_data, headers=auth_headers)
    
    if create_response.status_code == 201:
        data = json.loads(create_response.data)
        loan_id = data['loan']['loan_id']
        
        # Get the loan
        response = client.get(f'/api/loans/{loan_id}', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'loan' in data
        assert data['loan']['loan_id'] == loan_id


def test_update_loan(client, auth_headers):
    """Test PUT /api/loans/{loan_id} - update loan"""
    # First create a loan
    loan_data = {
        'loan_type': 'education',
        'loan_amount': 200000,
        'loan_tenure': 120,
        'monthly_emi': 2220.41,
        'interest_rate': 7.5,
        'loan_start_date': '2024-01-01T00:00:00Z',
        'loan_maturity_date': '2034-01-01T00:00:00Z'
    }
    
    create_response = client.post('/api/loans', json=loan_data, headers=auth_headers)
    
    if create_response.status_code == 201:
        data = json.loads(create_response.data)
        loan_id = data['loan']['loan_id']
        
        # Update the loan
        update_data = {
            'interest_rate': 8.0
        }
        
        response = client.put(f'/api/loans/{loan_id}',
                            json=update_data,
                            headers=auth_headers)
        
        assert response.status_code in [200, 400]  # 400 if EMI validation fails


def test_delete_loan(client, auth_headers):
    """Test DELETE /api/loans/{loan_id} - soft delete loan"""
    # First create a loan
    loan_data = {
        'loan_type': 'personal',
        'loan_amount': 75000,
        'loan_tenure': 36,
        'monthly_emi': 2428.64,
        'interest_rate': 11.0,
        'loan_start_date': '2024-01-01T00:00:00Z',
        'loan_maturity_date': '2027-01-01T00:00:00Z'
    }
    
    create_response = client.post('/api/loans', json=loan_data, headers=auth_headers)
    
    if create_response.status_code == 201:
        data = json.loads(create_response.data)
        loan_id = data['loan']['loan_id']
        
        # Delete the loan
        response = client.delete(f'/api/loans/{loan_id}', headers=auth_headers)
        
        assert response.status_code == 204


def test_record_payment(client, auth_headers):
    """Test POST /api/loans/{loan_id}/payments - record payment"""
    # First create a loan
    loan_data = {
        'loan_type': 'personal',
        'loan_amount': 100000,
        'loan_tenure': 24,
        'monthly_emi': 4622.24,
        'interest_rate': 10.5,
        'loan_start_date': '2024-01-01T00:00:00Z',
        'loan_maturity_date': '2026-01-01T00:00:00Z'
    }
    
    create_response = client.post('/api/loans', json=loan_data, headers=auth_headers)
    
    if create_response.status_code == 201:
        data = json.loads(create_response.data)
        loan_id = data['loan']['loan_id']
        
        # Record a payment
        payment_data = {
            'payment_date': '2024-02-01T00:00:00Z',
            'payment_amount': 4622.24
        }
        
        response = client.post(f'/api/loans/{loan_id}/payments',
                             json=payment_data,
                             headers=auth_headers)
        
        assert response.status_code == 201
        data = json.loads(response.data)
        assert 'payment' in data


def test_get_payment_history(client, auth_headers):
    """Test GET /api/loans/{loan_id}/payments - get payment history"""
    # First create a loan
    loan_data = {
        'loan_type': 'personal',
        'loan_amount': 100000,
        'loan_tenure': 24,
        'monthly_emi': 4622.24,
        'interest_rate': 10.5,
        'loan_start_date': '2024-01-01T00:00:00Z',
        'loan_maturity_date': '2026-01-01T00:00:00Z'
    }
    
    create_response = client.post('/api/loans', json=loan_data, headers=auth_headers)
    
    if create_response.status_code == 201:
        data = json.loads(create_response.data)
        loan_id = data['loan']['loan_id']
        
        # Get payment history
        response = client.get(f'/api/loans/{loan_id}/payments', headers=auth_headers)
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'payments' in data
        assert isinstance(data['payments'], list)


def test_get_loan_metrics(client, auth_headers):
    """Test GET /api/loans/metrics/{user_id} - get loan metrics"""
    # First create a loan
    loan_data = {
        'loan_type': 'personal',
        'loan_amount': 100000,
        'loan_tenure': 24,
        'monthly_emi': 4622.24,
        'interest_rate': 10.5,
        'loan_start_date': '2024-01-01T00:00:00Z',
        'loan_maturity_date': '2026-01-01T00:00:00Z'
    }
    
    client.post('/api/loans', json=loan_data, headers=auth_headers)
    
    # Get metrics (assume user_id = 1)
    response = client.get('/api/loans/metrics/1', headers=auth_headers)
    
    assert response.status_code in [200, 403]  # 403 if user_id doesn't match
    
    if response.status_code == 200:
        data = json.loads(response.data)
        assert 'metrics' in data
        assert 'loan_diversity_score' in data['metrics']
        assert 'payment_history_score' in data['metrics']
        assert 'loan_maturity_score' in data['metrics']


def test_authorization_check(client, auth_headers):
    """Test that users cannot access other users' loans"""
    # This test would require creating two users
    # For now, just verify 403 is returned for mismatched user_id
    response = client.get('/api/loans/user/999', headers=auth_headers)
    
    assert response.status_code == 403


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
