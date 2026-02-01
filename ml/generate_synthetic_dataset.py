"""
Generate a synthetic smartfin dataset for local training/testing.
Saves CSV at ../data/smartfin_dataset.csv
"""
import numpy as np
import pandas as pd

np.random.seed(42)
N = 1000

# Income in currency units per month
income = np.random.normal(loc=60000, scale=20000, size=N).clip(8000, 250000)

# Expenses as proportions of income
rent = (np.random.beta(2, 5, size=N) * income * 0.5).clip(500, None)
food = (np.random.beta(2, 3, size=N) * income * 0.15).clip(200, None)
travel = (np.random.exponential(scale=0.05, size=N) * income).clip(0, None)
shopping = (np.random.beta(1.5, 5, size=N) * income * 0.1).clip(0, None)
emi = (np.random.beta(1.2, 6, size=N) * income * 0.12).clip(0, None)
savings = (income - (rent + food + travel + shopping + emi)).clip(0, None)

# Compute a synthetic score: higher savings ratio and income -> higher score
savings_ratio = np.divide(savings, income, out=np.zeros_like(savings), where=income>0)
score = (50 + 40 * savings_ratio + 0.0001 * (income - 60000)) + np.random.normal(0, 5, size=N)
score = np.clip(score, 0, 100)

df = pd.DataFrame({
    'income': income.round(2),
    'rent': rent.round(2),
    'food': food.round(2),
    'travel': travel.round(2),
    'shopping': shopping.round(2),
    'emi': emi.round(2),
    'savings': savings.round(2),
    'score': score.round(2),
})

out_path = 'data/smartfin_dataset.csv'
print(f"Generating synthetic dataset ({N} rows) -> {out_path}")
df.to_csv(out_path, index=False)
print("Dataset generated.")
