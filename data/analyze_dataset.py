import pandas as pd
import numpy as np
import sys
import io

# Fix Windows encoding issue
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Load dataset
df = pd.read_csv('smartfin_dataset.csv')

print("=" * 60)
print("DATASET ANALYSIS FOR ML MODEL")
print("=" * 60)

# Basic info
print(f"\nDataset Shape: {df.shape[0]} rows x {df.shape[1]} columns")
print(f"\nColumns: {list(df.columns)}")

# Check for missing values
print(f"\nMissing Values: {df.isnull().sum().sum()}")

# Statistical summary
print("\nStatistical Summary:")
print(df.describe().round(2))

# Target variable (score) distribution
print("\nScore Distribution:")
print(df['score'].value_counts().sort_index())

print("\nScore Statistics:")
print(f"  Min Score: {df['score'].min()}")
print(f"  Max Score: {df['score'].max()}")
print(f"  Mean Score: {df['score'].mean():.2f}")
print(f"  Median Score: {df['score'].median():.2f}")
print(f"  Std Dev: {df['score'].std():.2f}")

# Check correlation with target
print("\nCorrelation with Score:")
correlations = df.corr()['score'].sort_values(ascending=False)
print(correlations)

# Check for duplicate rows
duplicates = df.duplicated().sum()
print(f"\nDuplicate Rows: {duplicates}")

# Feature ranges
print(f"\nIncome Range: Rs.{df['income'].min():,} to Rs.{df['income'].max():,}")
print(f"Savings Range: Rs.{df['savings'].min():,} to Rs.{df['savings'].max():,}")

# Check if score follows the rule-based logic
print("\nDataset Quality Assessment:")
print("  - Large enough for ML: ", "YES" if len(df) >= 1000 else "NO")
print("  - No missing values: ", "YES" if df.isnull().sum().sum() == 0 else "NO")
print("  - Score variance: ", "YES" if df['score'].std() > 10 else "NO")
print("  - Feature diversity: ", "YES" if all(df[col].std() > 0 for col in df.columns) else "NO")

print("\n" + "=" * 60)
print("VERDICT: Dataset is", "GOOD" if len(df) >= 1000 and df.isnull().sum().sum() == 0 else "NEEDS IMPROVEMENT")
print("=" * 60)
