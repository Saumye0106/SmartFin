"""
Test script for SmartFin Backend API
Tests all endpoints with sample data
"""

import requests
import json

BASE_URL = "http://localhost:5000"

def test_health_check():
    """Test the health check endpoint"""
    print("\n" + "="*60)
    print("TEST 1: Health Check")
    print("="*60)

    response = requests.get(f"{BASE_URL}/")
    print(f"Status Code: {response.status_code}")
    print(json.dumps(response.json(), indent=2))

    assert response.status_code == 200
    print("✓ PASSED")


def test_predict_excellent():
    """Test prediction with excellent financial profile"""
    print("\n" + "="*60)
    print("TEST 2: Predict Score - Excellent Profile")
    print("="*60)

    data = {
        "income": 100000,
        "rent": 20000,
        "food": 10000,
        "travel": 5000,
        "shopping": 5000,
        "emi": 10000,
        "savings": 40000
    }

    print(f"Input: {json.dumps(data, indent=2)}")

    response = requests.post(f"{BASE_URL}/api/predict", json=data)
    print(f"\nStatus Code: {response.status_code}")

    result = response.json()
    print(f"\nScore: {result['score']}")
    print(f"Category: {result['classification']['category']}")
    print(f"Savings Ratio: {result['patterns']['savings_ratio']:.1%}")
    print(f"Expense Ratio: {result['patterns']['expense_ratio']:.1%}")

    print(f"\nRecommendations ({len(result['guidance']['recommendations'])}):")
    for rec in result['guidance']['recommendations'][:3]:
        print(f"  - {rec}")

    print(f"\nInvestment Eligible: {result['investments']['eligible_for_investment']}")

    assert response.status_code == 200
    assert result['score'] >= 70
    print("\n✓ PASSED")


def test_predict_poor():
    """Test prediction with poor financial profile"""
    print("\n" + "="*60)
    print("TEST 3: Predict Score - Poor Profile")
    print("="*60)

    data = {
        "income": 30000,
        "rent": 10000,
        "food": 8000,
        "travel": 3000,
        "shopping": 4000,
        "emi": 8000,
        "savings": 0
    }

    print(f"Input: {json.dumps(data, indent=2)}")

    response = requests.post(f"{BASE_URL}/api/predict", json=data)
    print(f"\nStatus Code: {response.status_code}")

    result = response.json()
    print(f"\nScore: {result['score']}")
    print(f"Category: {result['classification']['category']}")
    print(f"Savings Ratio: {result['patterns']['savings_ratio']:.1%}")
    print(f"Expense Ratio: {result['patterns']['expense_ratio']:.1%}")

    print(f"\nWarnings ({len(result['guidance']['warnings'])}):")
    for warn in result['guidance']['warnings']:
        print(f"  - {warn}")

    print(f"\nAnomalies ({len(result['anomalies'])}):")
    for anomaly in result['anomalies']:
        print(f"  - [{anomaly['severity'].upper()}] {anomaly['message']}")

    assert response.status_code == 200
    assert result['score'] < 50
    print("\n✓ PASSED")


def test_whatif():
    """Test what-if simulation"""
    print("\n" + "="*60)
    print("TEST 4: What-If Simulation")
    print("="*60)

    data = {
        "current": {
            "income": 50000,
            "rent": 15000,
            "food": 8000,
            "travel": 3000,
            "shopping": 5000,
            "emi": 10000,
            "savings": 5000
        },
        "modified": {
            "income": 50000,
            "rent": 15000,
            "food": 8000,
            "travel": 3000,
            "shopping": 2000,  # Reduced shopping
            "emi": 10000,
            "savings": 8000    # Increased savings
        }
    }

    print("Scenario: Reduce shopping by 3000, increase savings by 3000")

    response = requests.post(f"{BASE_URL}/api/whatif", json=data)
    print(f"\nStatus Code: {response.status_code}")

    result = response.json()
    print(f"\nCurrent Score: {result['current_score']}")
    print(f"Modified Score: {result['modified_score']}")
    print(f"Score Change: {result['score_change']:+.2f}")
    print(f"Impact: {result['impact'].upper()}")

    print(f"\nCurrent Category: {result['current_classification']['category']}")
    print(f"Modified Category: {result['modified_classification']['category']}")

    assert response.status_code == 200
    assert result['score_change'] > 0  # Should improve
    print("\n✓ PASSED")


def test_model_info():
    """Test model info endpoint"""
    print("\n" + "="*60)
    print("TEST 5: Model Information")
    print("="*60)

    response = requests.get(f"{BASE_URL}/api/model-info")
    print(f"Status Code: {response.status_code}")

    result = response.json()
    print(f"\nModel Type: {result['model_type']}")
    print(f"Features: {', '.join(result['features'])}")
    print(f"R2 Score: {result['performance']['r2_score']:.4f}")
    print(f"MAE: {result['performance']['mae']:.2f}")
    print(f"Training Samples: {result['training_samples']}")

    assert response.status_code == 200
    print("\n✓ PASSED")


def test_student_profile():
    """Test with typical student financial profile"""
    print("\n" + "="*60)
    print("TEST 6: Student Profile (Realistic)")
    print("="*60)

    data = {
        "income": 25000,  # Pocket money + part-time
        "rent": 6000,     # Hostel/PG
        "food": 5000,     # Meals
        "travel": 2000,   # Local travel
        "shopping": 3000, # Clothes, misc
        "emi": 0,         # No loans yet
        "savings": 7000   # Saving from pocket money
    }

    print(f"Input: {json.dumps(data, indent=2)}")

    response = requests.post(f"{BASE_URL}/api/predict", json=data)
    result = response.json()

    print(f"\nScore: {result['score']}")
    print(f"Category: {result['classification']['category']}")

    print(f"\nSpending Breakdown:")
    for category, percentage in result['patterns']['breakdown'].items():
        print(f"  {category.capitalize()}: {percentage:.1f}%")

    print(f"\nTop Recommendations:")
    for rec in result['guidance']['recommendations'][:3]:
        print(f"  - {rec}")

    assert response.status_code == 200
    print("\n✓ PASSED")


if __name__ == '__main__':
    print("\n" + "="*60)
    print("SMARTFIN BACKEND API TESTS")
    print("="*60)
    print("Make sure the Flask server is running on port 5000")
    print("Run: python app.py")
    print("="*60)

    try:
        test_health_check()
        test_predict_excellent()
        test_predict_poor()
        test_whatif()
        test_model_info()
        test_student_profile()

        print("\n" + "="*60)
        print("ALL TESTS PASSED!")
        print("="*60)

    except requests.exceptions.ConnectionError:
        print("\n❌ ERROR: Cannot connect to server")
        print("Make sure Flask server is running: python app.py")

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
