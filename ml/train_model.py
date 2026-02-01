"""
SmartFin - Financial Health Score Prediction Model Training
ML-based regression model to predict financial health scores (0-100)
"""

import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import sys
import io

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 70)
print("SMARTFIN - FINANCIAL HEALTH SCORE PREDICTION MODEL")
print("=" * 70)

# ==================== 1. LOAD DATASET ====================
print("\n[1] Loading Dataset...")
df = pd.read_csv('data/smartfin_dataset.csv')
print(f"   Loaded {len(df)} rows, {len(df.columns)} columns")
print(f"   Columns: {list(df.columns)}")

# ==================== 2. PREPARE DATA ====================
print("\n[2] Preparing Data...")

# Features (X) and Target (y)
X = df[['income', 'rent', 'food', 'travel', 'shopping', 'emi', 'savings']]
y = df['score']

print(f"   Features (X): {X.shape}")
print(f"   Target (y): {y.shape}")

# Split into training and testing sets (80-20 split)
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

print(f"   Training set: {X_train.shape[0]} samples")
print(f"   Testing set: {X_test.shape[0]} samples")

# ==================== 3. TRAIN MULTIPLE MODELS ====================
print("\n[3] Training Models...")

models = {
    'Linear Regression': LinearRegression(),
    'Random Forest': RandomForestRegressor(n_estimators=100, random_state=42, max_depth=10),
    'Gradient Boosting': GradientBoostingRegressor(n_estimators=100, random_state=42, max_depth=5)
}

results = {}

for name, model in models.items():
    print(f"\n   Training {name}...")

    # Train
    model.fit(X_train, y_train)

    # Predict
    y_pred_train = model.predict(X_train)
    y_pred_test = model.predict(X_test)

    # Evaluate
    train_r2 = r2_score(y_train, y_pred_train)
    test_r2 = r2_score(y_test, y_pred_test)
    mae = mean_absolute_error(y_test, y_pred_test)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))

    results[name] = {
        'model': model,
        'train_r2': train_r2,
        'test_r2': test_r2,
        'mae': mae,
        'rmse': rmse
    }

    print(f"      Train R2: {train_r2:.4f}")
    print(f"      Test R2:  {test_r2:.4f}")
    print(f"      MAE:      {mae:.2f}")
    print(f"      RMSE:     {rmse:.2f}")

# ==================== 4. SELECT BEST MODEL ====================
print("\n[4] Model Comparison...")

print("\n   Model Performance Summary:")
print("   " + "-" * 66)
print(f"   {'Model':<20} {'Train R2':<12} {'Test R2':<12} {'MAE':<10} {'RMSE':<10}")
print("   " + "-" * 66)

for name, metrics in results.items():
    print(f"   {name:<20} {metrics['train_r2']:<12.4f} {metrics['test_r2']:<12.4f} "
          f"{metrics['mae']:<10.2f} {metrics['rmse']:<10.2f}")

print("   " + "-" * 66)

# Select best model based on test R2 score
best_model_name = max(results, key=lambda x: results[x]['test_r2'])
best_model = results[best_model_name]['model']

print(f"\n   Best Model: {best_model_name}")
print(f"   Test R2 Score: {results[best_model_name]['test_r2']:.4f}")

# ==================== 5. FEATURE IMPORTANCE ====================
if hasattr(best_model, 'feature_importances_'):
    print("\n[5] Feature Importance Analysis...")

    feature_importance = pd.DataFrame({
        'feature': X.columns,
        'importance': best_model.feature_importances_
    }).sort_values('importance', ascending=False)

    print("\n   Feature Importance Ranking:")
    for idx, row in feature_importance.iterrows():
        print(f"      {row['feature']:<12} {row['importance']:.4f}")

# ==================== 6. TEST PREDICTIONS ====================
print("\n[6] Sample Predictions on Test Set...")

y_pred = best_model.predict(X_test)

print("\n   First 10 predictions vs actual:")
print("   " + "-" * 45)
print(f"   {'Actual':<12} {'Predicted':<12} {'Difference':<12}")
print("   " + "-" * 45)

for i in range(min(10, len(y_test))):
    actual = y_test.iloc[i]
    predicted = y_pred[i]
    diff = actual - predicted
    print(f"   {actual:<12.0f} {predicted:<12.2f} {diff:<12.2f}")

print("   " + "-" * 45)

# ==================== 7. SAVE MODEL ====================
print("\n[7] Saving Model...")

model_filename = 'financial_health_model.pkl'
joblib.dump(best_model, model_filename)
print(f"   Model saved as: {model_filename}")

# Save feature names for later use
feature_names = X.columns.tolist()
joblib.dump(feature_names, 'feature_names.pkl')
print(f"   Feature names saved as: feature_names.pkl")

# Save model metadata
metadata = {
    'model_type': best_model_name,
    'train_r2': results[best_model_name]['train_r2'],
    'test_r2': results[best_model_name]['test_r2'],
    'mae': results[best_model_name]['mae'],
    'rmse': results[best_model_name]['rmse'],
    'features': feature_names,
    'n_samples': len(df)
}
joblib.dump(metadata, 'model_metadata.pkl')
print(f"   Metadata saved as: model_metadata.pkl")

# ==================== 8. VISUALIZE RESULTS ====================
print("\n[8] Generating Visualizations...")

# Create figure with subplots
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle('SmartFin - Model Performance Analysis', fontsize=16, fontweight='bold')

# Plot 1: Actual vs Predicted
axes[0, 0].scatter(y_test, y_pred, alpha=0.5)
axes[0, 0].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2)
axes[0, 0].set_xlabel('Actual Score')
axes[0, 0].set_ylabel('Predicted Score')
axes[0, 0].set_title(f'Actual vs Predicted (R2={results[best_model_name]["test_r2"]:.3f})')
axes[0, 0].grid(True, alpha=0.3)

# Plot 2: Residuals
residuals = y_test - y_pred
axes[0, 1].scatter(y_pred, residuals, alpha=0.5)
axes[0, 1].axhline(y=0, color='r', linestyle='--', lw=2)
axes[0, 1].set_xlabel('Predicted Score')
axes[0, 1].set_ylabel('Residuals')
axes[0, 1].set_title('Residual Plot')
axes[0, 1].grid(True, alpha=0.3)

# Plot 3: Model Comparison
model_names = list(results.keys())
test_r2_scores = [results[name]['test_r2'] for name in model_names]
colors = ['lightblue', 'lightgreen', 'lightcoral']
bars = axes[1, 0].bar(model_names, test_r2_scores, color=colors)
axes[1, 0].set_ylabel('R2 Score')
axes[1, 0].set_title('Model Comparison (Test R2)')
axes[1, 0].set_ylim([0, 1])
axes[1, 0].grid(True, alpha=0.3, axis='y')

# Add value labels on bars
for bar in bars:
    height = bar.get_height()
    axes[1, 0].text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.3f}', ha='center', va='bottom')

# Plot 4: Feature Importance
if hasattr(best_model, 'feature_importances_'):
    feature_imp_sorted = feature_importance.sort_values('importance', ascending=True)
    axes[1, 1].barh(feature_imp_sorted['feature'], feature_imp_sorted['importance'])
    axes[1, 1].set_xlabel('Importance')
    axes[1, 1].set_title(f'Feature Importance ({best_model_name})')
    axes[1, 1].grid(True, alpha=0.3, axis='x')
else:
    axes[1, 1].text(0.5, 0.5, 'Feature importance\nnot available\nfor this model',
                    ha='center', va='center', fontsize=12)
    axes[1, 1].set_title('Feature Importance')

plt.tight_layout()
plt.savefig('model_performance.png', dpi=150, bbox_inches='tight')
print(f"   Visualization saved as: model_performance.png")

# ==================== 9. SUMMARY ====================
print("\n" + "=" * 70)
print("TRAINING COMPLETE - SUMMARY")
print("=" * 70)
print(f"\nBest Model: {best_model_name}")
print(f"Test R2 Score: {results[best_model_name]['test_r2']:.4f} (Higher is better, max=1.0)")
print(f"Mean Absolute Error: {results[best_model_name]['mae']:.2f} points")
print(f"Root Mean Squared Error: {results[best_model_name]['rmse']:.2f} points")
print(f"\nInterpretation:")
print(f"  - Model explains {results[best_model_name]['test_r2']*100:.1f}% of score variance")
print(f"  - Average prediction error: ~{results[best_model_name]['mae']:.0f} points")
print(f"  - Predictions are within +/- {results[best_model_name]['mae']:.0f} points on average")

if hasattr(best_model, 'feature_importances_'):
    top_feature = feature_importance.iloc[0]
    print(f"\nMost Important Feature: {top_feature['feature']} ({top_feature['importance']:.3f})")

print("\nFiles Generated:")
print("  - financial_health_model.pkl (trained model)")
print("  - feature_names.pkl (feature list)")
print("  - model_metadata.pkl (performance metrics)")
print("  - model_performance.png (visualizations)")

print("\n" + "=" * 70)
print("Ready for integration with Flask backend!")
print("=" * 70)
