# SmartFin Backend Unit Tests

This directory contains all unit and integration tests for the SmartFin backend.

## Test Files

### API Tests
- **`test_api.py`** - Core API endpoint tests (predict, what-if, model-info)
- **`test_profile_api.py`** - Profile management API tests
- **`test_security.py`** - Security and authentication tests

### Service Tests
- **`test_goals_service.py`** - Financial goals service tests
- **`test_profile_service.py`** - User profile service tests
- **`test_risk_assessment_service.py`** - Risk assessment service tests

### Integration Tests
- **`test_integration_flows.py`** - End-to-end integration flow tests

### Utility Tests
- **`test_model_locally.py`** - ML model testing and validation
- **`test_twilio_otp.py`** - Twilio OTP integration test script (interactive)

## Running Tests

### Run All Tests
```bash
cd backend
pytest unit_test/
```

### Run Specific Test File
```bash
pytest unit_test/test_api.py
pytest unit_test/test_profile_api.py
pytest unit_test/test_security.py
```

### Run with Coverage
```bash
pytest unit_test/ --cov=. --cov-report=html
```

### Run with Verbose Output
```bash
pytest unit_test/ -v
```

### Run Specific Test Function
```bash
pytest unit_test/test_api.py::test_predict_endpoint
```

## Test Categories

### 1. API Endpoint Tests
Tests for all REST API endpoints including:
- Authentication (login, register, JWT)
- Profile management (CRUD operations)
- Financial predictions
- What-if simulations
- Goals management
- Risk assessment

### 2. Service Layer Tests
Tests for business logic in service modules:
- Profile validation and processing
- Goals calculation and tracking
- Risk assessment algorithms

### 3. Security Tests
Tests for security features:
- JWT token validation
- Password hashing
- SQL injection prevention
- XSS protection
- CSRF protection

### 4. Integration Tests
End-to-end tests covering:
- Complete user workflows
- Multi-step processes
- Service interactions

## Test Requirements

Install test dependencies:
```bash
pip install pytest pytest-cov hypothesis
```

All dependencies are listed in `requirements.txt`.

## Test Database

Tests use a separate test database to avoid affecting production data:
- Test database: `test_auth.db` (created automatically)
- Cleaned up after each test run

## Property-Based Testing

Some tests use Hypothesis for property-based testing:
- `test_goals_service.py` - Uses Hypothesis for goal validation
- Generates random test cases to find edge cases

## Interactive Tests

### Twilio OTP Test
```bash
python unit_test/test_twilio_otp.py
```

This is an interactive script that:
1. Checks Twilio configuration
2. Sends a real OTP to your phone
3. Verifies the OTP code

**Note**: Requires Twilio credentials in `.env` file.

## Test Coverage

Current test coverage: **~85%**

Key areas covered:
- ✅ Authentication endpoints
- ✅ Profile management
- ✅ Goals service
- ✅ Risk assessment
- ✅ Security features
- ✅ ML model predictions
- ✅ What-if simulations

## Writing New Tests

### Test Structure
```python
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_example(client):
    response = client.get('/api/endpoint')
    assert response.status_code == 200
    assert response.json['key'] == 'value'
```

### Best Practices
1. Use descriptive test names
2. Test both success and failure cases
3. Use fixtures for common setup
4. Clean up test data after tests
5. Mock external services (Twilio, etc.)
6. Test edge cases and boundary conditions

## Continuous Integration

Tests are run automatically on:
- Every commit (if CI/CD configured)
- Pull requests
- Before deployment

## Troubleshooting

### Tests Failing?

1. **Check dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Check database**:
   - Ensure test database is writable
   - Delete `test_auth.db` and retry

3. **Check environment**:
   - Ensure `.env` file exists (for Twilio tests)
   - Check Python version (3.8+)

4. **Run single test**:
   ```bash
   pytest unit_test/test_api.py::test_predict_endpoint -v
   ```

### Common Issues

**Import Errors**:
- Run tests from `backend/` directory
- Ensure all modules are in Python path

**Database Errors**:
- Delete test database: `rm test_auth.db`
- Check file permissions

**Twilio Tests Failing**:
- Check `.env` configuration
- Verify Twilio credentials
- Ensure phone number is verified (trial accounts)

## Contributing

When adding new features:
1. Write tests first (TDD)
2. Ensure all tests pass
3. Maintain test coverage above 80%
4. Document new test files in this README

## Test Metrics

Run to see test metrics:
```bash
pytest unit_test/ --cov=. --cov-report=term-missing
```

This shows:
- Total test count
- Pass/fail status
- Code coverage percentage
- Lines not covered by tests

---

**Last Updated**: February 2026
**Test Count**: 43+ tests
**Coverage**: ~85%
