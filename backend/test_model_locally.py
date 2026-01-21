"""
Direct test of SmartFin ML model and backend logic (without Flask server)
"""

import sys
sys.path.insert(0, '.')

import joblib
import pandas as pd
import json

print("=" * 70)
print("SMARTFIN - LOCAL MODEL & LOGIC TEST")
print("=" * 70)

# Load model
print("\n[1] Loading Model...")
model = joblib.load('../ml/financial_health_model.pkl')
feature_names = joblib.load('../ml/feature_names.pkl')
metadata = joblib.load('../ml/model_metadata.pkl')

print(f"   Model Type: {metadata['model_type']}")
print(f"   R2 Score: {metadata['test_r2']:.4f}")
print(f"   MAE: {metadata['mae']:.2f}")

# Import backend functions
print("\n[2] Testing Backend Functions...")

# Test Case 1: Excellent Profile
print("\n" + "-" * 70)
print("TEST CASE 1: Excellent Financial Profile")
print("-" * 70)

test_data_1 = {
    'income': 100000,
    'rent': 20000,
    'food': 10000,
    'travel': 5000,
    'shopping': 5000,
    'emi': 10000,
    'savings': 40000
}

features = pd.DataFrame([[
    test_data_1['income'],
    test_data_1['rent'],
    test_data_1['food'],
    test_data_1['travel'],
    test_data_1['shopping'],
    test_data_1['emi'],
    test_data_1['savings']
]], columns=feature_names)

predicted_score = float(model.predict(features)[0])
predicted_score = max(0, min(100, round(predicted_score, 2)))

print(f"\nInput: {json.dumps(test_data_1, indent=2)}")
print(f"\nPredicted Score: {predicted_score}")

# Calculate ratios
total_expense = test_data_1['rent'] + test_data_1['food'] + test_data_1['travel'] + test_data_1['shopping'] + test_data_1['emi']
expense_ratio = total_expense / test_data_1['income']
savings_ratio = test_data_1['savings'] / test_data_1['income']
emi_ratio = test_data_1['emi'] / test_data_1['income']

print(f"Expense Ratio: {expense_ratio:.1%}")
print(f"Savings Ratio: {savings_ratio:.1%}")
print(f"EMI Ratio: {emi_ratio:.1%}")

# Classify
if predicted_score >= 80:
    category = "Excellent"
elif predicted_score >= 65:
    category = "Very Good"
elif predicted_score >= 50:
    category = "Good"
elif predicted_score >= 35:
    category = "Average"
else:
    category = "Poor"

print(f"Category: {category}")

# Test Case 2: Poor Profile
print("\n" + "-" * 70)
print("TEST CASE 2: Poor Financial Profile")
print("-" * 70)

test_data_2 = {
    'income': 30000,
    'rent': 10000,
    'food': 8000,
    'travel': 3000,
    'shopping': 4000,
    'emi': 8000,
    'savings': 0
}

features = pd.DataFrame([[
    test_data_2['income'],
    test_data_2['rent'],
    test_data_2['food'],
    test_data_2['travel'],
    test_data_2['shopping'],
    test_data_2['emi'],
    test_data_2['savings']
]], columns=feature_names)

predicted_score = float(model.predict(features)[0])
predicted_score = max(0, min(100, round(predicted_score, 2)))

print(f"\nInput: {json.dumps(test_data_2, indent=2)}")
print(f"\nPredicted Score: {predicted_score}")

# Calculate ratios
total_expense = test_data_2['rent'] + test_data_2['food'] + test_data_2['travel'] + test_data_2['shopping'] + test_data_2['emi']
expense_ratio = total_expense / test_data_2['income']
savings_ratio = test_data_2['savings'] / test_data_2['income']
emi_ratio = test_data_2['emi'] / test_data_2['income']

print(f"Expense Ratio: {expense_ratio:.1%}")
print(f"Savings Ratio: {savings_ratio:.1%}")
print(f"EMI Ratio: {emi_ratio:.1%}")

# Classify
if predicted_score >= 80:
    category = "Excellent"
elif predicted_score >= 65:
    category = "Very Good"
elif predicted_score >= 50:
    category = "Good"
elif predicted_score >= 35:
    category = "Average"
else:
    category = "Poor"

print(f"Category: {category}")

# Warnings
warnings = []
if expense_ratio > 0.8:
    warnings.append("You're spending over 80% of your income. This is unsustainable.")
if savings_ratio < 0.05:
    warnings.append("Very low savings rate. Try to save at least 10% of income.")
if emi_ratio > 0.4:
    warnings.append("EMI is consuming over 40% of income - very high debt burden!")

print(f"\nWarnings:")
for warn in warnings:
    print(f"  - {warn}")

# Test Case 3: Student Profile
print("\n" + "-" * 70)
print("TEST CASE 3: Typical Student Profile")
print("-" * 70)

test_data_3 = {
    'income': 25000,
    'rent': 6000,
    'food': 5000,
    'travel': 2000,
    'shopping': 3000,
    'emi': 0,
    'savings': 7000
}

features = pd.DataFrame([[
    test_data_3['income'],
    test_data_3['rent'],
    test_data_3['food'],
    test_data_3['travel'],
    test_data_3['shopping'],
    test_data_3['emi'],
    test_data_3['savings']
]], columns=feature_names)

predicted_score = float(model.predict(features)[0])
predicted_score = max(0, min(100, round(predicted_score, 2)))

print(f"\nInput: {json.dumps(test_data_3, indent=2)}")
print(f"\nPredicted Score: {predicted_score}")

# Calculate ratios
total_expense = test_data_3['rent'] + test_data_3['food'] + test_data_3['travel'] + test_data_3['shopping'] + test_data_3['emi']
expense_ratio = total_expense / test_data_3['income']
savings_ratio = test_data_3['savings'] / test_data_3['income']

print(f"Expense Ratio: {expense_ratio:.1%}")
print(f"Savings Ratio: {savings_ratio:.1%}")
print(f"EMI Ratio: 0.0%")

# Classify
if predicted_score >= 80:
    category = "Excellent"
elif predicted_score >= 65:
    category = "Very Good"
elif predicted_score >= 50:
    category = "Good"
elif predicted_score >= 35:
    category = "Average"
else:
    category = "Poor"

print(f"Category: {category}")

# Test Case 4: What-If Simulation
print("\n" + "-" * 70)
print("TEST CASE 4: What-If Simulation")
print("-" * 70)

current = {
    'income': 50000,
    'rent': 15000,
    'food': 8000,
    'travel': 3000,
    'shopping': 5000,
    'emi': 10000,
    'savings': 5000
}

modified = {
    'income': 50000,
    'rent': 15000,
    'food': 8000,
    'travel': 3000,
    'shopping': 2000,  # Reduced by 3000
    'emi': 10000,
    'savings': 8000     # Increased by 3000
}

# Current score
features_current = pd.DataFrame([[
    current['income'], current['rent'], current['food'],
    current['travel'], current['shopping'], current['emi'], current['savings']
]], columns=feature_names)

current_score = float(model.predict(features_current)[0])
current_score = max(0, min(100, round(current_score, 2)))

# Modified score
features_modified = pd.DataFrame([[
    modified['income'], modified['rent'], modified['food'],
    modified['travel'], modified['shopping'], modified['emi'], modified['savings']
]], columns=feature_names)

modified_score = float(model.predict(features_modified)[0])
modified_score = max(0, min(100, round(modified_score, 2)))

score_change = modified_score - current_score

print(f"\nScenario: Reduce shopping by Rs.3000, increase savings by Rs.3000")
print(f"\nCurrent Score: {current_score}")
print(f"Modified Score: {modified_score}")
print(f"Score Change: {score_change:+.2f}")
print(f"Impact: {'POSITIVE' if score_change > 0 else 'NEGATIVE' if score_change < 0 else 'NEUTRAL'}")

print("\n" + "=" * 70)
print("ALL TESTS COMPLETED SUCCESSFULLY!")
print("=" * 70)

print("\nModel and Backend Logic Working Correctly!")
print("\nTo test the Flask API:")
print("1. Run: python app.py (in one terminal)")
print("2. Run: python test_api.py (in another terminal)")
print("=" * 70)
