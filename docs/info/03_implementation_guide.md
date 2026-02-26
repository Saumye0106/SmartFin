# Implementation Guide

**Document Version:** 1.0  
**Date:** February 26, 2026  
**Status:** Complete

---

## Quick Start

This guide provides step-by-step instructions to implement the financial health scoring model using Dataset 2.

---

## Table of Contents

1. [Setup](#setup)
2. [Data Loading](#data-loading)
3. [Feature Mapping](#feature-mapping)
4. [Scoring Implementation](#scoring-implementation)
5. [Model Training](#model-training)
6. [Validation](#validation)
7. [Integration](#integration)

---

## Setup

### Prerequisites

```bash
# Python 3.8+
python --version

# Install required packages
pip install pandas numpy scikit-learn matplotlib seaborn joblib
```

### Project Structure

```
smartfin/
├── data/
│   ├── india_personal_finance.csv
│   └── smartfin_training_data.csv
├── ml/
│   ├── financial_health_model.pkl
│   ├── feature_names.pkl
│   └── train_model.py
├── backend/
│   └── app.py
└── docs/
    └── info/
        ├── 01_financial_health_scoring_model.md
        ├── 02_dataset_selection_analysis.md
        └── 03_implementation_guide.md
```

---

## Data Loading

### Step 1: Load Dataset 2

```python
import pandas as pd
import numpy as np

# Load the dataset
df = pd.read_csv('data/india_personal_finance.csv')

# Display basic info
print(f"Dataset shape: {df.shape}")
print(f"Columns: {df.columns.tolist()}")
print(f"\nFirst few rows:")
print(df.head())

# Check data types
print(f"\nData types:")
print(df.dtypes)

# Check for missing values
print(f"\nMissing values:")
print(df.isnull().sum())
```

### Step 2: Explore the Data

```python
# Statistical summary
print(df.describe())

# Check unique values in categorical columns
print(f"\nCity Tiers: {df['City_Tier'].unique()}")
print(f"Occupations: {df['Occupation'].unique()}")

# Income distribution
print(f"\nIncome Statistics:")
print(f"Min: ₹{df['Income'].min():,.0f}")
print(f"Max: ₹{df['Income'].max():,.0f}")
print(f"Mean: ₹{df['Income'].mean():,.0f}")
print(f"Median: ₹{df['Income'].median():,.0f}")
```

---

## Feature Mapping

### Step 1: Create SmartFin Features

```python
# Create a new dataframe with SmartFin features
smartfin_df = pd.DataFrame({
    'income': df['Income'],
    'rent': df['Rent'],
    'food': df['Groceries'],
    'travel': df['Transport'],
    'shopping': df['Eating_Out'] + df['Entertainment'],
    'emi': df['Loan_Repayment'],
    'savings': df['Disposable_Income'],
    'age': df['Age'],
    'dependents': df['Dependents'],
    'city_tier': df['City_Tier']
})

print(f"SmartFin features shape: {smartfin_df.shape}")
print(smartfin_df.head())
```

### Step 2: Validate Mapping

```python
# Verify savings calculation
total_expenses = (df['Rent'] + df['Loan_Repayment'] + df['Insurance'] +
                  df['Groceries'] + df['Transport'] + df['Eating_Out'] +
                  df['Entertainment'] + df['Utilities'] + df['Healthcare'] +
                  df['Education'] + df['Miscellaneous'])

calculated_savings = df['Income'] - total_expenses
actual_savings = df['Disposable_Income']

# Check correlation
correlation = calculated_savings.corr(actual_savings)
print(f"Savings correlation: {correlation:.4f}")

# Should be very close to 1.0
if correlation > 0.95:
    print("✓ Savings mapping is correct")
else:
    print("✗ Savings mapping needs review")

# Check for negative savings
negative_savings = (smartfin_df['savings'] < 0).sum()
print(f"Records with negative savings: {negative_savings}")

# Remove invalid records if needed
smartfin_df = smartfin_df[smartfin_df['savings'] >= 0]
print(f"Final dataset shape: {smartfin_df.shape}")
```

### Step 3: Data Cleaning

```python
# Remove outliers (optional)
# Keep records where income is within reasonable range
smartfin_df = smartfin_df[
    (smartfin_df['income'] > 0) &
    (smartfin_df['income'] < smartfin_df['income'].quantile(0.99))
]

# Check for any remaining issues
print(f"Final dataset shape: {smartfin_df.shape}")
print(f"Missing values: {smartfin_df.isnull().sum().sum()}")
print(f"Data types:\n{smartfin_df.dtypes}")
```

---

## Scoring Implementation

### Step 1: Create Scoring Functions

```python
def calculate_savings_score(row):
    """Calculate savings score (0-100)"""
    savings_ratio = row['savings'] / row['income'] if row['income'] > 0 else 0
    
    if savings_ratio >= 0.20:
        return 100
    elif savings_ratio >= 0.15:
        return 85
    elif savings_ratio >= 0.10:
        return 70
    elif savings_ratio >= 0.05:
        return 50
    else:
        return 30

def calculate_debt_score(row):
    """Calculate debt management score (0-100)"""
    emi_ratio = row['emi'] / row['income'] if row['income'] > 0 else 0
    
    if emi_ratio <= 0.10:
        return 100
    elif emi_ratio <= 0.20:
        return 85
    elif emi_ratio <= 0.30:
        return 65
    elif emi_ratio <= 0.40:
        return 45
    else:
        return 25

def calculate_expense_score(row):
    """Calculate expense control score (0-100)"""
    total_expenses = (row['rent'] + row['emi'] + row['food'] + 
                      row['travel'] + row['shopping'])
    expense_ratio = total_expenses / row['income'] if row['income'] > 0 else 0
    
    if expense_ratio <= 0.70:
        return 100
    elif expense_ratio <= 0.80:
        return 85
    elif expense_ratio <= 0.90:
        return 65
    elif expense_ratio <= 1.00:
        return 40
    else:
        return 20

def calculate_balance_score(row):
    """Calculate balance score (0-100)"""
    essential = row['rent'] + row['food'] + row['travel']
    discretionary = row['shopping']
    
    essential_ratio = essential / row['income'] if row['income'] > 0 else 0
    discretionary_ratio = discretionary / row['income'] if row['income'] > 0 else 0
    
    if essential_ratio <= 0.60 and discretionary_ratio <= 0.20:
        return 100
    elif essential_ratio <= 0.70 and discretionary_ratio <= 0.25:
        return 85
    elif essential_ratio <= 0.80 and discretionary_ratio <= 0.30:
        return 65
    elif essential_ratio <= 0.90 and discretionary_ratio <= 0.35:
        return 45
    else:
        return 25

def calculate_life_stage_score(row):
    """Calculate life stage score (0-100)"""
    age = row['age']
    dependents = row['dependents']
    savings_ratio = row['savings'] / row['income'] if row['income'] > 0 else 0
    
    base_score = 70
    
    # Age adjustment
    if age < 25:
        if savings_ratio >= 0.25:
            base_score += 20
        elif savings_ratio >= 0.15:
            base_score += 10
    elif age < 40:
        if savings_ratio >= 0.20:
            base_score += 20
        elif savings_ratio >= 0.15:
            base_score += 10
    elif age < 55:
        if savings_ratio >= 0.25:
            base_score += 20
        elif savings_ratio >= 0.20:
            base_score += 10
    else:
        if savings_ratio >= 0.30:
            base_score += 20
        elif savings_ratio >= 0.25:
            base_score += 10
    
    # Dependent adjustment
    if dependents > 3:
        base_score -= 10
    
    return min(base_score, 100)

def calculate_financial_health_score(row):
    """
    Calculate comprehensive financial health score (0-100)
    
    Weights:
    - Savings: 30%
    - Debt: 25%
    - Expenses: 20%
    - Balance: 15%
    - Life Stage: 10%
    """
    savings_score = calculate_savings_score(row)
    debt_score = calculate_debt_score(row)
    expense_score = calculate_expense_score(row)
    balance_score = calculate_balance_score(row)
    life_stage_score = calculate_life_stage_score(row)
    
    overall_score = (
        savings_score * 0.30 +
        debt_score * 0.25 +
        expense_score * 0.20 +
        balance_score * 0.15 +
        life_stage_score * 0.10
    )
    
    return round(overall_score, 2)

def classify_financial_health(score):
    """Classify score into categories"""
    if score >= 80:
        return {
            'category': 'Excellent',
            'emoji': '🌟',
            'color': '#10b981',
            'description': 'Outstanding financial health. Keep up the great work!'
        }
    elif score >= 65:
        return {
            'category': 'Very Good',
            'emoji': '👍',
            'color': '#3b82f6',
            'description': 'Strong financial position. Minor improvements possible.'
        }
    elif score >= 50:
        return {
            'category': 'Good',
            'emoji': '✓',
            'color': '#f59e0b',
            'description': 'Decent financial health. Focus on savings and debt.'
        }
    elif score >= 35:
        return {
            'category': 'Average',
            'emoji': '⚠️',
            'color': '#f97316',
            'description': 'Moderate concerns. Review spending and increase savings.'
        }
    else:
        return {
            'category': 'Poor',
            'emoji': '🚨',
            'color': '#ef4444',
            'description': 'Critical issues. Immediate action needed.'
        }
```

### Step 2: Apply Scoring

```python
# Apply scoring functions
smartfin_df['savings_score'] = smartfin_df.apply(calculate_savings_score, axis=1)
smartfin_df['debt_score'] = smartfin_df.apply(calculate_debt_score, axis=1)
smartfin_df['expense_score'] = smartfin_df.apply(calculate_expense_score, axis=1)
smartfin_df['balance_score'] = smartfin_df.apply(calculate_balance_score, axis=1)
smartfin_df['life_stage_score'] = smartfin_df.apply(calculate_life_stage_score, axis=1)

# Calculate overall score
smartfin_df['financial_health_score'] = smartfin_df.apply(
    calculate_financial_health_score, axis=1
)

# Classify
smartfin_df['classification'] = smartfin_df['financial_health_score'].apply(
    classify_financial_health
)

print("Scoring complete!")
print(f"\nScore distribution:")
print(smartfin_df['financial_health_score'].describe())
```

### Step 3: Analyze Results

```python
# Score distribution
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.hist(smartfin_df['financial_health_score'], bins=20, edgecolor='black')
plt.xlabel('Financial Health Score')
plt.ylabel('Number of Individuals')
plt.title('Distribution of Financial Health Scores')
plt.grid(True, alpha=0.3)
plt.savefig('score_distribution.png')
plt.show()

# Category distribution
category_counts = smartfin_df['classification'].apply(lambda x: x['category']).value_counts()
print(f"\nCategory Distribution:")
print(category_counts)

# Average scores by category
print(f"\nAverage Scores by Category:")
for category in ['Excellent', 'Very Good', 'Good', 'Average', 'Poor']:
    mask = smartfin_df['classification'].apply(lambda x: x['category'] == category)
    avg_score = smartfin_df[mask]['financial_health_score'].mean()
    count = mask.sum()
    print(f"{category}: {avg_score:.1f} ({count} individuals)")
```

---

## Model Training

### Step 1: Prepare Data for ML Model

```python
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Prepare features and target
X = smartfin_df[['income', 'rent', 'food', 'travel', 'shopping', 'emi', 'savings']]
y = smartfin_df['financial_health_score']

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"Training set size: {len(X_train)}")
print(f"Test set size: {len(X_test)}")

# Optional: Scale features
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)
```

### Step 2: Train Model

```python
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error

# Train Gradient Boosting model
model = GradientBoostingRegressor(
    n_estimators=200,
    max_depth=10,
    learning_rate=0.1,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    verbose=1
)

print("Training model...")
model.fit(X_train, y_train)
print("Training complete!")

# Make predictions
y_pred_train = model.predict(X_train)
y_pred_test = model.predict(X_test)

# Evaluate
r2_train = r2_score(y_train, y_pred_train)
r2_test = r2_score(y_test, y_pred_test)
mae = mean_absolute_error(y_test, y_pred_test)
rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))

print(f"\n{'='*50}")
print(f"Model Performance")
print(f"{'='*50}")
print(f"Training R² Score: {r2_train:.4f}")
print(f"Test R² Score: {r2_test:.4f}")
print(f"MAE: {mae:.2f} points")
print(f"RMSE: {rmse:.2f} points")
```

### Step 3: Feature Importance

```python
# Get feature importance
feature_importance = pd.DataFrame({
    'feature': X.columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print(f"\nFeature Importance:")
print(feature_importance)

# Visualize
plt.figure(figsize=(10, 6))
plt.barh(feature_importance['feature'], feature_importance['importance'])
plt.xlabel('Importance')
plt.title('Feature Importance in Financial Health Score Prediction')
plt.tight_layout()
plt.savefig('feature_importance.png')
plt.show()
```

---

## Validation

### Step 1: Cross-Validation

```python
from sklearn.model_selection import cross_val_score

# Perform 5-fold cross-validation
cv_scores = cross_val_score(model, X, y, cv=5, scoring='r2')

print(f"Cross-Validation R² Scores: {cv_scores}")
print(f"Mean CV R² Score: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")
```

### Step 2: Error Analysis

```python
# Analyze prediction errors
errors = y_test - y_pred_test

print(f"\nError Statistics:")
print(f"Mean Error: {errors.mean():.2f}")
print(f"Std Dev: {errors.std():.2f}")
print(f"Min Error: {errors.min():.2f}")
print(f"Max Error: {errors.max():.2f}")

# Accuracy within thresholds
within_5 = (np.abs(errors) <= 5).sum() / len(errors) * 100
within_10 = (np.abs(errors) <= 10).sum() / len(errors) * 100

print(f"\nAccuracy:")
print(f"Within ±5 points: {within_5:.1f}%")
print(f"Within ±10 points: {within_10:.1f}%")

# Visualize errors
plt.figure(figsize=(10, 6))
plt.scatter(y_test, errors, alpha=0.5)
plt.axhline(y=0, color='r', linestyle='--')
plt.xlabel('Actual Score')
plt.ylabel('Prediction Error')
plt.title('Prediction Errors')
plt.grid(True, alpha=0.3)
plt.savefig('prediction_errors.png')
plt.show()
```

### Step 3: Scenario Testing

```python
# Test with known scenarios
test_scenarios = [
    {
        'name': 'Excellent Profile',
        'income': 100000,
        'rent': 20000,
        'food': 8000,
        'travel': 4000,
        'shopping': 5000,
        'emi': 5000,
        'savings': 25000,
        'age': 35,
        'dependents': 1,
        'city_tier': 'Tier 1'
    },
    {
        'name': 'Good Profile',
        'income': 50000,
        'rent': 15000,
        'food': 8000,
        'travel': 3000,
        'shopping': 5000,
        'emi': 3000,
        'savings': 10000,
        'age': 28,
        'dependents': 0,
        'city_tier': 'Tier 2'
    },
    {
        'name': 'Poor Profile',
        'income': 30000,
        'rent': 12000,
        'food': 6000,
        'travel': 2000,
        'shopping': 4000,
        'emi': 8000,
        'savings': 500,
        'age': 25,
        'dependents': 2,
        'city_tier': 'Tier 3'
    }
]

print(f"\nScenario Testing:")
print(f"{'='*60}")

for scenario in test_scenarios:
    # Create dataframe for prediction
    scenario_df = pd.DataFrame([scenario])
    
    # Get score
    score = calculate_financial_health_score(scenario_df.iloc[0])
    classification = classify_financial_health(score)
    
    # Get ML prediction
    X_scenario = scenario_df[['income', 'rent', 'food', 'travel', 'shopping', 'emi', 'savings']]
    ml_score = model.predict(X_scenario)[0]
    
    print(f"\n{scenario['name']}:")
    print(f"  Rule-based Score: {score:.1f}")
    print(f"  ML Model Score: {ml_score:.1f}")
    print(f"  Category: {classification['category']} {classification['emoji']}")
    print(f"  Description: {classification['description']}")
```

---

## Integration

### Step 1: Save Model

```python
import joblib

# Save model
joblib.dump(model, 'ml/financial_health_model.pkl')

# Save feature names
joblib.dump(X.columns.tolist(), 'ml/feature_names.pkl')

# Save metadata
metadata = {
    'model_type': 'GradientBoostingRegressor',
    'r2_score': r2_test,
    'mae': mae,
    'rmse': rmse,
    'features': X.columns.tolist(),
    'n_samples': len(X),
    'n_features': len(X.columns),
    'training_date': pd.Timestamp.now().isoformat()
}

joblib.dump(metadata, 'ml/model_metadata.pkl')

print("Model saved successfully!")
```

### Step 2: Load and Use Model

```python
# Load model
model = joblib.load('ml/financial_health_model.pkl')
feature_names = joblib.load('ml/feature_names.pkl')
metadata = joblib.load('ml/model_metadata.pkl')

print(f"Model loaded!")
print(f"Features: {feature_names}")
print(f"R² Score: {metadata['r2_score']:.4f}")

# Make prediction
new_data = pd.DataFrame({
    'income': [50000],
    'rent': [15000],
    'food': [8000],
    'travel': [3000],
    'shopping': [5000],
    'emi': [3000],
    'savings': [10000]
})

prediction = model.predict(new_data)[0]
print(f"\nPredicted Score: {prediction:.1f}")
```

### Step 3: Backend Integration

```python
# In backend/app.py
from flask import Flask, request, jsonify
import joblib
import pandas as pd

app = Flask(__name__)

# Load model
model = joblib.load('ml/financial_health_model.pkl')

@app.route('/api/predict', methods=['POST'])
def predict():
    """Predict financial health score"""
    data = request.json
    
    # Create dataframe
    df = pd.DataFrame([data])
    
    # Make prediction
    score = model.predict(df)[0]
    
    # Classify
    classification = classify_financial_health(score)
    
    return jsonify({
        'score': round(score, 2),
        'classification': classification
    })

if __name__ == '__main__':
    app.run(debug=True)
```

---

## Summary

This implementation guide provides:

1. ✅ Data loading and exploration
2. ✅ Feature mapping from Dataset 2
3. ✅ Scoring function implementation
4. ✅ ML model training
5. ✅ Validation and testing
6. ✅ Backend integration

Expected Results:
- R² Score: 65-70%
- MAE: <10 points
- Implementation time: 2-3 hours

---

**Document Status:** Complete  
**Last Updated:** February 26, 2026  
**Next Review:** March 15, 2026
