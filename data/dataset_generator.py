import random
import pandas as pd

def compute_score(income, rent, food, travel, shopping, emi, savings):
    expense = rent + food + travel + shopping + emi

    if income <= 0:
        return 0

    savings_ratio = savings / income
    expense_ratio = expense / income
    emi_ratio = emi / income

    score = 100

    # Penalize high expenses
    if expense_ratio > 0.8:
        score -= 40
    elif expense_ratio > 0.6:
        score -= 25
    elif expense_ratio > 0.5:
        score -= 15

    # Penalize low savings
    if savings_ratio < 0.05:
        score -= 30
    elif savings_ratio < 0.1:
        score -= 20
    elif savings_ratio < 0.2:
        score -= 10

    # Penalize high EMI burden
    if emi_ratio > 0.4:
        score -= 25
    elif emi_ratio > 0.3:
        score -= 15
    elif emi_ratio > 0.2:
        score -= 5

    # Clamp score between 0 and 100
    score = max(0, min(100, score))
    return int(score)

data = []

for _ in range(1500):
    income = random.randint(15000, 150000)

    rent = random.randint(int(0.1 * income), int(0.35 * income))
    food = random.randint(int(0.05 * income), int(0.2 * income))
    travel = random.randint(0, int(0.1 * income))
    shopping = random.randint(0, int(0.15 * income))
    emi = random.randint(0, int(0.4 * income))

    total_expense = rent + food + travel + shopping + emi

    max_savings = max(0, income - total_expense)
    savings = random.randint(0, max_savings) if max_savings > 0 else 0

    score = compute_score(income, rent, food, travel, shopping, emi, savings)

    data.append([income, rent, food, travel, shopping, emi, savings, score])

df = pd.DataFrame(data, columns=[
    "income", "rent", "food", "travel", "shopping", "emi", "savings", "score"
])

df.to_csv("smartfin_dataset.csv", index=False)

print("Dataset generated: smartfin_dataset.csv")
