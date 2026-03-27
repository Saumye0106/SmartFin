"""
Generate Model Performance Chart for Enhanced 8-Factor Model
Produces a 4-panel visualization similar to the original model_performance.png
"""

import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
import os
import sys

# Fix encoding on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

print("=" * 70)
print("SMARTFIN - ENHANCED MODEL PERFORMANCE CHART GENERATOR")
print("=" * 70)

# ==================== 1. LOAD MODEL ====================
print("\n[1] Loading enhanced model...")
model_path = os.path.join(os.path.dirname(__file__), 'enhanced_model.pkl')
model_data = joblib.load(model_path)

model = model_data['model']
metrics = model_data['metrics']
feature_cols = model_data['feature_cols']
model_type = model_data.get('model_type', 'Enhanced GBR')
trained_at = model_data.get('trained_at', 'Unknown')

print(f"   Model type: {model_type}")
print(f"   Features: {feature_cols}")
print(f"   Trained at: {trained_at}")
print(f"   Stored metrics: R2={metrics['r2_test']:.4f}, MAE={metrics['mae_test']:.2f}")

# ==================== 2. LOAD & PREPARE DATA ====================
print("\n[2] Loading dataset and reproducing train/test split...")
data_dir = os.path.dirname(__file__)
df = pd.read_csv(os.path.join(data_dir, 'combined_dataset.csv'))
print(f"   Loaded {len(df):,} records")

# Reproduce the same feature engineering from train_enhanced_model.py
# Calculate 8-factor financial health scores
def calculate_savings_score(row):
    savings_ratio = row['savings'] / row['income'] if row['income'] > 0 else 0
    if savings_ratio >= 0.30: return 100
    elif savings_ratio >= 0.20: return 85
    elif savings_ratio >= 0.10: return 70
    elif savings_ratio >= 0.05: return 50
    else: return 30

def calculate_debt_score(row):
    emi_ratio = row['emi'] / row['income'] if row['income'] > 0 else 0
    if emi_ratio <= 0.10: return 100
    elif emi_ratio <= 0.20: return 85
    elif emi_ratio <= 0.30: return 65
    elif emi_ratio <= 0.40: return 45
    else: return 25

def calculate_expense_score(row):
    expense_ratio = row['expenses'] / row['income'] if row['income'] > 0 else 0
    if expense_ratio <= 0.50: return 100
    elif expense_ratio <= 0.65: return 85
    elif expense_ratio <= 0.80: return 70
    elif expense_ratio <= 0.90: return 50
    else: return 30

def calculate_balance_score(row):
    if 'rent' in row and pd.notna(row.get('rent')):
        essential = row['rent'] + row.get('food', 0) + row.get('emi', 0)
        discretionary = row.get('shopping', 0) + row.get('travel', 0)
        total = essential + discretionary
        if total > 0:
            essential_ratio = essential / total
            if essential_ratio >= 0.70: return 100
            elif essential_ratio >= 0.60: return 85
            elif essential_ratio >= 0.50: return 70
            else: return 50
    return 70

def calculate_life_stage_score(row):
    age = row.get('age', 30)
    if age < 25: return 60
    elif age < 35: return 75
    elif age < 50: return 85
    elif age < 65: return 80
    else: return 70

def calculate_loan_diversity_score(row):
    has_loan = row.get('has_loan', False)
    if not has_loan or row.get('emi', 0) == 0:
        return 50
    if 'loan_type' in row and pd.notna(row.get('loan_type')):
        return 75
    emi_ratio = row['emi'] / row['income'] if row['income'] > 0 else 0
    if emi_ratio < 0.15: return 80
    elif emi_ratio < 0.25: return 70
    else: return 60

def calculate_payment_history_score(row):
    if 'credit_score' in row and pd.notna(row.get('credit_score')):
        credit = row['credit_score']
        if credit >= 750: return 95
        elif credit >= 700: return 85
        elif credit >= 650: return 75
        elif credit >= 600: return 65
        else: return 50
    has_loan = row.get('has_loan', False)
    if not has_loan or row.get('emi', 0) == 0:
        return 70
    emi_ratio = row['emi'] / row['income'] if row['income'] > 0 else 0
    if emi_ratio < 0.20: return 80
    else: return 65

def calculate_loan_maturity_score(row):
    has_loan = row.get('has_loan', False)
    if not has_loan or row.get('emi', 0) == 0:
        return 50
    if 'loan_tenure_months' in row and pd.notna(row.get('loan_tenure_months')):
        tenure = row['loan_tenure_months']
        if tenure <= 12: return 85
        elif tenure <= 36: return 75
        elif tenure <= 60: return 65
        else: return 50
    return 65

def calculate_financial_health_score_8factor(row):
    savings = calculate_savings_score(row)
    debt = calculate_debt_score(row)
    expense = calculate_expense_score(row)
    balance = calculate_balance_score(row)
    life_stage = calculate_life_stage_score(row)
    loan_diversity = calculate_loan_diversity_score(row)
    payment_history = calculate_payment_history_score(row)
    loan_maturity = calculate_loan_maturity_score(row)
    score = (savings * 0.25 + debt * 0.20 + expense * 0.18 + balance * 0.12 +
             life_stage * 0.08 + loan_diversity * 0.10 + payment_history * 0.05 +
             loan_maturity * 0.02)
    return round(score, 2)

# Calculate target scores
df['financial_health_score'] = df.apply(calculate_financial_health_score_8factor, axis=1)

# Prepare features (same logic as training script)
X_cols = ['income', 'expenses', 'savings', 'emi']
if 'age' in df.columns:
    X_cols.append('age')
if 'has_loan' in df.columns:
    df['has_loan_numeric'] = df['has_loan'].astype(int)
    X_cols.append('has_loan_numeric')
if 'loan_amount' in df.columns:
    df['loan_amount_filled'] = df['loan_amount'].fillna(0)
    X_cols.append('loan_amount_filled')
if 'interest_rate' in df.columns:
    df['interest_rate_filled'] = df['interest_rate'].fillna(0)
    X_cols.append('interest_rate_filled')

X = df[X_cols].fillna(0)
y = df['financial_health_score']

# Same split as training (random_state=42, test_size=0.2)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
print(f"   Train: {len(X_train):,} | Test: {len(X_test):,}")

# ==================== 3. GENERATE PREDICTIONS ====================
print("\n[3] Generating predictions...")
y_pred_train = model.predict(X_train)
y_pred_test = model.predict(X_test)

r2_train = r2_score(y_train, y_pred_train)
r2_test = r2_score(y_test, y_pred_test)
mae_test = mean_absolute_error(y_test, y_pred_test)
rmse_test = np.sqrt(mean_squared_error(y_test, y_pred_test))

print(f"   Train R2: {r2_train:.4f}")
print(f"   Test R2:  {r2_test:.4f}")
print(f"   MAE:      {mae_test:.2f}")
print(f"   RMSE:     {rmse_test:.2f}")

# ==================== 4. CREATE VISUALIZATION ====================
print("\n[4] Generating performance chart...")

# Use a clean style
plt.style.use('seaborn-v0_8-whitegrid')
fig, axes = plt.subplots(2, 2, figsize=(14, 11))
fig.suptitle('SmartFin - Enhanced 8-Factor Model Performance', fontsize=16, fontweight='bold', y=0.98)

# Color palette
PRIMARY = '#10B981'     # Emerald green
SECONDARY = '#6366F1'   # Indigo
ACCENT = '#F59E0B'      # Amber
DANGER = '#EF4444'      # Red
BG_DARK = '#1F2937'     # Dark gray

# --- Plot 1: Actual vs Predicted ---
ax1 = axes[0, 0]
scatter = ax1.scatter(y_test, y_pred_test, alpha=0.4, s=20, c=PRIMARY, edgecolors='white', linewidth=0.3)
line_min, line_max = y_test.min(), y_test.max()
ax1.plot([line_min, line_max], [line_min, line_max], 'r--', lw=2, label='Perfect Prediction')
ax1.set_xlabel('Actual Score', fontsize=11)
ax1.set_ylabel('Predicted Score', fontsize=11)
ax1.set_title(f'Actual vs Predicted (R² = {r2_test:.4f})', fontsize=12, fontweight='bold')
ax1.legend(fontsize=9)
ax1.grid(True, alpha=0.3)

# --- Plot 2: Residuals ---
ax2 = axes[0, 1]
residuals = y_test.values - y_pred_test
ax2.scatter(y_pred_test, residuals, alpha=0.4, s=20, c=SECONDARY, edgecolors='white', linewidth=0.3)
ax2.axhline(y=0, color=DANGER, linestyle='--', lw=2)
ax2.set_xlabel('Predicted Score', fontsize=11)
ax2.set_ylabel('Residuals (Actual - Predicted)', fontsize=11)
ax2.set_title('Residual Plot', fontsize=12, fontweight='bold')
ax2.grid(True, alpha=0.3)

# Add residual stats annotation
mean_resid = np.mean(residuals)
std_resid = np.std(residuals)
ax2.annotate(f'Mean: {mean_resid:.2f}\nStd: {std_resid:.2f}',
             xy=(0.95, 0.95), xycoords='axes fraction',
             ha='right', va='top', fontsize=9,
             bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow', alpha=0.8))

# --- Plot 3: Metrics Summary (replacing old model comparison bars) ---
ax3 = axes[1, 0]
metric_names = ['R² Score', 'MAE', 'RMSE']
train_vals = [r2_train, mean_absolute_error(y_train, y_pred_train), np.sqrt(mean_squared_error(y_train, y_pred_train))]
test_vals = [r2_test, mae_test, rmse_test]

x_pos = np.arange(len(metric_names))
width = 0.35

bars_train = ax3.bar(x_pos - width/2, train_vals, width, label='Train', color=PRIMARY, alpha=0.8, edgecolor='white')
bars_test = ax3.bar(x_pos + width/2, test_vals, width, label='Test', color=SECONDARY, alpha=0.8, edgecolor='white')

# Add value labels
for bar in bars_train:
    h = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., h + 0.01,
             f'{h:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')
for bar in bars_test:
    h = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., h + 0.01,
             f'{h:.3f}', ha='center', va='bottom', fontsize=9, fontweight='bold')

ax3.set_xticks(x_pos)
ax3.set_xticklabels(metric_names, fontsize=11)
ax3.set_ylabel('Value', fontsize=11)
ax3.set_title('Train vs Test Metrics', fontsize=12, fontweight='bold')
ax3.legend(fontsize=9)
ax3.grid(True, alpha=0.3, axis='y')

# --- Plot 4: Feature Importance ---
ax4 = axes[1, 1]
importances = model.feature_importances_
feature_importance = pd.DataFrame({
    'feature': feature_cols,
    'importance': importances
}).sort_values('importance', ascending=True)

colors = plt.cm.viridis(np.linspace(0.3, 0.9, len(feature_importance)))
bars = ax4.barh(feature_importance['feature'], feature_importance['importance'],
                color=colors, edgecolor='white', linewidth=0.5)

# Add percentage labels
for bar, imp in zip(bars, feature_importance['importance']):
    ax4.text(bar.get_width() + 0.005, bar.get_y() + bar.get_height()/2.,
             f'{imp*100:.1f}%', va='center', fontsize=9, fontweight='bold')

ax4.set_xlabel('Importance', fontsize=11)
ax4.set_title('Feature Importance (Gradient Boosting)', fontsize=12, fontweight='bold')
ax4.grid(True, alpha=0.3, axis='x')

# Add subtitle with key stats
fig.text(0.5, 0.935, 
         f'Gradient Boosting Regressor  |  8 Features  |  {len(df):,} samples  |  '
         f'R² = {r2_test:.4f}  |  MAE = {mae_test:.2f}  |  RMSE = {rmse_test:.2f}',
         ha='center', fontsize=10, color='gray', style='italic')

plt.tight_layout(rect=[0, 0, 1, 0.92])

# Save
output_path = os.path.join(data_dir, 'model_performance.png')
plt.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='white')
print(f"   Saved: {output_path}")

plt.close()

print("\n" + "=" * 70)
print("CHART GENERATED SUCCESSFULLY")
print("=" * 70)
print(f"\nFile: data/model_performance.png")
print(f"Model: {model_type} (Gradient Boosting, 8 features)")
print(f"R² Score: {r2_test:.4f} ({r2_test*100:.2f}%)")
print(f"MAE: {mae_test:.2f} points")
print(f"RMSE: {rmse_test:.2f} points")
