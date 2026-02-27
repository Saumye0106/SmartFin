"""
Enhanced ML Model Training Script
Trains 8-factor financial health scoring model with loan history data
Target: 72-78% R² score (improvement from 65-70% baseline)
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import joblib
from datetime import datetime

# Scoring functions from the design document
def calculate_savings_score(row):
    """Calculate savings score (30% -> 25% weight)"""
    savings_ratio = row['savings'] / row['income'] if row['income'] > 0 else 0
    
    if savings_ratio >= 0.30:
        return 100
    elif savings_ratio >= 0.20:
        return 85
    elif savings_ratio >= 0.10:
        return 70
    elif savings_ratio >= 0.05:
        return 50
    else:
        return 30

def calculate_debt_score(row):
    """Calculate debt management score (25% -> 20% weight)"""
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
    """Calculate expense control score (20% -> 18% weight)"""
    expense_ratio = row['expenses'] / row['income'] if row['income'] > 0 else 0
    
    if expense_ratio <= 0.50:
        return 100
    elif expense_ratio <= 0.65:
        return 85
    elif expense_ratio <= 0.80:
        return 70
    elif expense_ratio <= 0.90:
        return 50
    else:
        return 30

def calculate_balance_score(row):
    """Calculate balance score (15% -> 12% weight)"""
    # For Dataset 2, we have detailed expenses
    if 'rent' in row and pd.notna(row['rent']):
        essential = row['rent'] + row.get('food', 0) + row.get('emi', 0)
        discretionary = row.get('shopping', 0) + row.get('travel', 0)
        total = essential + discretionary
        
        if total > 0:
            essential_ratio = essential / total
            if essential_ratio >= 0.70:
                return 100
            elif essential_ratio >= 0.60:
                return 85
            elif essential_ratio >= 0.50:
                return 70
            else:
                return 50
    
    # For Dataset 1, use a simpler calculation
    return 70  # Neutral baseline

def calculate_life_stage_score(row):
    """Calculate life stage score (10% -> 8% weight)"""
    age = row.get('age', 30)
    
    if age < 25:
        return 60  # Young, building
    elif age < 35:
        return 75  # Establishing
    elif age < 50:
        return 85  # Peak earning
    elif age < 65:
        return 80  # Pre-retirement
    else:
        return 70  # Retirement

def calculate_loan_diversity_score(row):
    """Calculate loan diversity score (NEW - 10% weight)"""
    has_loan = row.get('has_loan', False)
    
    if not has_loan or row.get('emi', 0) == 0:
        return 50  # Neutral - no loans
    
    # If we have loan type information (Dataset 1)
    if 'loan_type' in row and pd.notna(row['loan_type']):
        # Single loan type gets lower score
        return 75  # Moderate diversity
    
    # If we only have EMI (Dataset 2)
    emi_ratio = row['emi'] / row['income'] if row['income'] > 0 else 0
    if emi_ratio < 0.15:
        return 80  # Low debt burden suggests good management
    elif emi_ratio < 0.25:
        return 70
    else:
        return 60

def calculate_payment_history_score(row):
    """Calculate payment history score (NEW - 5% weight)"""
    # Since we don't have actual payment history, estimate based on credit score
    if 'credit_score' in row and pd.notna(row['credit_score']):
        credit = row['credit_score']
        if credit >= 750:
            return 95
        elif credit >= 700:
            return 85
        elif credit >= 650:
            return 75
        elif credit >= 600:
            return 65
        else:
            return 50
    
    # For records without credit score, use EMI ratio as proxy
    has_loan = row.get('has_loan', False)
    if not has_loan or row.get('emi', 0) == 0:
        return 70  # Neutral - no payment history
    
    emi_ratio = row['emi'] / row['income'] if row['income'] > 0 else 0
    if emi_ratio < 0.20:
        return 80  # Manageable debt suggests good payment behavior
    else:
        return 65

def calculate_loan_maturity_score(row):
    """Calculate loan maturity score (NEW - 2% weight)"""
    has_loan = row.get('has_loan', False)
    
    if not has_loan or row.get('emi', 0) == 0:
        return 50  # Neutral - no loans
    
    # If we have loan tenure information (Dataset 1)
    if 'loan_tenure_months' in row and pd.notna(row['loan_tenure_months']):
        tenure = row['loan_tenure_months']
        if tenure <= 12:
            return 85  # Short-term
        elif tenure <= 36:
            return 75  # Medium-term
        elif tenure <= 60:
            return 65  # Long-term
        else:
            return 50  # Very long-term
    
    # Estimate based on loan amount and EMI
    if 'loan_amount' in row and pd.notna(row['loan_amount']) and row['monthly_emi'] > 0:
        estimated_tenure = row['loan_amount'] / row['monthly_emi']
        if estimated_tenure <= 24:
            return 80
        elif estimated_tenure <= 48:
            return 70
        else:
            return 60
    
    return 65  # Default moderate score

def calculate_financial_health_score_8factor(row):
    """Calculate overall financial health score using 8-factor model"""
    savings = calculate_savings_score(row)
    debt = calculate_debt_score(row)
    expense = calculate_expense_score(row)
    balance = calculate_balance_score(row)
    life_stage = calculate_life_stage_score(row)
    loan_diversity = calculate_loan_diversity_score(row)
    payment_history = calculate_payment_history_score(row)
    loan_maturity = calculate_loan_maturity_score(row)
    
    # 8-factor weighted formula
    score = (
        savings * 0.25 +
        debt * 0.20 +
        expense * 0.18 +
        balance * 0.12 +
        life_stage * 0.08 +
        loan_diversity * 0.10 +
        payment_history * 0.05 +
        loan_maturity * 0.02
    )
    
    return round(score, 2)

def load_and_prepare_data():
    """Load combined dataset and prepare features"""
    print("📂 Loading combined dataset...")
    df = pd.read_csv('data/combined_dataset.csv')
    print(f"   ✓ Loaded {len(df):,} records\n")
    
    print("🔧 Calculating financial health scores...")
    df['financial_health_score'] = df.apply(calculate_financial_health_score_8factor, axis=1)
    print(f"   ✓ Calculated scores for all records\n")
    
    print("📊 Score Distribution:")
    print(f"   Mean: {df['financial_health_score'].mean():.2f}")
    print(f"   Median: {df['financial_health_score'].median():.2f}")
    print(f"   Std Dev: {df['financial_health_score'].std():.2f}")
    print(f"   Min: {df['financial_health_score'].min():.2f}")
    print(f"   Max: {df['financial_health_score'].max():.2f}\n")
    
    return df

def prepare_features(df):
    """Prepare feature matrix for ML training"""
    print("🎯 Preparing features for ML training...")
    
    # Select features for training
    feature_cols = ['income', 'expenses', 'savings', 'emi']
    
    # Add age if available
    if 'age' in df.columns:
        feature_cols.append('age')
    
    # Add loan features if available
    if 'has_loan' in df.columns:
        df['has_loan_numeric'] = df['has_loan'].astype(int)
        feature_cols.append('has_loan_numeric')
    
    if 'loan_amount' in df.columns:
        df['loan_amount_filled'] = df['loan_amount'].fillna(0)
        feature_cols.append('loan_amount_filled')
    
    if 'interest_rate' in df.columns:
        df['interest_rate_filled'] = df['interest_rate'].fillna(0)
        feature_cols.append('interest_rate_filled')
    
    X = df[feature_cols].fillna(0)
    y = df['financial_health_score']
    
    print(f"   ✓ Features: {feature_cols}")
    print(f"   ✓ Feature matrix shape: {X.shape}")
    print(f"   ✓ Target shape: {y.shape}\n")
    
    return X, y, feature_cols

def train_model(X_train, y_train):
    """Train Gradient Boosting model"""
    print("🤖 Training Gradient Boosting model...")
    
    model = GradientBoostingRegressor(
        n_estimators=200,
        max_depth=10,
        learning_rate=0.1,
        random_state=42,
        verbose=0
    )
    
    model.fit(X_train, y_train)
    print("   ✓ Model trained successfully\n")
    
    return model

def evaluate_model(model, X_test, y_test, X_train, y_train):
    """Evaluate model performance"""
    print("📈 Evaluating model performance...")
    
    # Predictions
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)
    
    # Metrics
    r2_train = r2_score(y_train, y_pred_train)
    r2_test = r2_score(y_test, y_pred_test)
    mae_train = mean_absolute_error(y_train, y_pred_train)
    mae_test = mean_absolute_error(y_test, y_pred_test)
    rmse_train = np.sqrt(mean_squared_error(y_train, y_pred_train))
    rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_test))
    
    print(f"\n   📊 Training Set:")
    print(f"      R² Score: {r2_train:.4f}")
    print(f"      MAE: {mae_train:.2f} points")
    print(f"      RMSE: {rmse_train:.2f} points")
    
    print(f"\n   📊 Test Set:")
    print(f"      R² Score: {r2_test:.4f} ({r2_test*100:.2f}%)")
    print(f"      MAE: {mae_test:.2f} points")
    print(f"      RMSE: {rmse_test:.2f} points")
    
    # Check if we met the target
    target_r2_min = 0.72
    target_r2_max = 0.78
    
    if target_r2_min <= r2_test <= target_r2_max:
        print(f"\n   ✅ SUCCESS! R² score {r2_test:.4f} is within target range ({target_r2_min}-{target_r2_max})")
    elif r2_test > target_r2_max:
        print(f"\n   🎉 EXCELLENT! R² score {r2_test:.4f} exceeds target range!")
    else:
        print(f"\n   ⚠️  R² score {r2_test:.4f} is below target ({target_r2_min})")
    
    return {
        'r2_train': r2_train,
        'r2_test': r2_test,
        'mae_train': mae_train,
        'mae_test': mae_test,
        'rmse_train': rmse_train,
        'rmse_test': rmse_test
    }

def analyze_feature_importance(model, feature_cols):
    """Analyze feature importance"""
    print("\n🔍 Feature Importance Analysis:")
    
    importances = model.feature_importances_
    feature_importance = pd.DataFrame({
        'feature': feature_cols,
        'importance': importances
    }).sort_values('importance', ascending=False)
    
    print("\n   Top Features:")
    for idx, row in feature_importance.iterrows():
        print(f"      {row['feature']}: {row['importance']:.4f} ({row['importance']*100:.2f}%)")
    
    return feature_importance

def save_model(model, metrics, feature_cols):
    """Save trained model and metadata"""
    print("\n💾 Saving model...")
    
    model_data = {
        'model': model,
        'metrics': metrics,
        'feature_cols': feature_cols,
        'trained_at': datetime.now().isoformat(),
        'model_type': '8-factor enhanced',
        'target_r2': '72-78%'
    }
    
    joblib.dump(model_data, 'data/enhanced_model.pkl')
    print("   ✓ Model saved to data/enhanced_model.pkl")

def main():
    """Main training process"""
    print("="*70)
    print("ENHANCED ML MODEL TRAINING (8-Factor)")
    print("="*70)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    try:
        # Load and prepare data
        df = load_and_prepare_data()
        X, y, feature_cols = prepare_features(df)
        
        # Split data
        print("✂️  Splitting data (80% train, 20% test)...")
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        print(f"   ✓ Training set: {len(X_train):,} records")
        print(f"   ✓ Test set: {len(X_test):,} records\n")
        
        # Train model
        model = train_model(X_train, y_train)
        
        # Evaluate
        metrics = evaluate_model(model, X_test, y_test, X_train, y_train)
        
        # Feature importance
        feature_importance = analyze_feature_importance(model, feature_cols)
        
        # Save model
        save_model(model, metrics, feature_cols)
        
        print("\n" + "="*70)
        print("✅ TRAINING COMPLETE!")
        print("="*70)
        print(f"\nModel Performance:")
        print(f"  R² Score: {metrics['r2_test']:.4f} (Target: 0.72-0.78)")
        print(f"  MAE: {metrics['mae_test']:.2f} points (Target: <7)")
        print(f"\nNext Steps:")
        print("1. Review model performance")
        print("2. Proceed to backend implementation")
        print("3. Integrate model into application")
        
    except Exception as e:
        print(f"\n❌ Error during training: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
