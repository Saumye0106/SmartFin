"""
Feature definitions shared by training and serving.

Only inputs SmartFin can actually supply for a user are used, and only ones
whose meaning carries over from the training population (US borrowers) to
SmartFin's users:

  age                    years
  debt_ratio             monthly debt payments + living costs, divided by monthly income
  times_late             payments 30-89 days late in the last 2 years
  times_seriously_late   payments 90+ days late in the last 2 years
  utilization            credit-card balance / credit limit (optional; NaN = no card or unknown)

Deliberately left out of the training data's columns:
  - MonthlyIncome: it is in US dollars, so its absolute level means nothing for
    rupee incomes. Income still enters through debt_ratio, which has no currency.
  - NumberOfOpenCreditLinesAndLoans / NumberRealEstateLoansOrLines: in the US
    data "lines" include credit cards and almost everyone has several, so zero
    lines marks an unusual, high-risk group (21% distress). A SmartFin user with
    no loans is not that person, and the model would advise taking on credit.
  - NumberOfDependents: adds nothing measurable (AUC +0.001).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

FEATURES = ["age", "debt_ratio", "times_late", "times_seriously_late", "utilization"]

# +1 = risk may only rise with the feature. Keeps what-if answers sane: paying
# late or taking on more debt can never be scored as an improvement.
MONOTONE = {"age": 0, "debt_ratio": 1, "times_late": 1, "times_seriously_late": 1, "utilization": 1}

LABELS = {
    "age": "Age",
    "debt_ratio": "EMIs and housing cost vs income",
    "times_late": "Late payments (last 2 years)",
    "times_seriously_late": "Missed payments, 90+ days (last 2 years)",
    "utilization": "Credit-card utilization",
}
# Things the user can act on (age isn't one).
ACTIONABLE = ("debt_ratio", "times_late", "times_seriously_late", "utilization")

RAW_COLUMNS = ["distress", "util", "age", "late30", "debt_ratio", "income", "open_lines",
               "late90", "re_loans", "late60", "dependents"]
_UNKNOWN_CODE = 96  # 96 and 98 in the past-due columns mean "not known", not a count

# The score ranks a user against reference borrowers in the same age band. The
# training population is much older than SmartFin's users (median 52), and young
# borrowers are riskier as a group, so ranking against everyone would give every
# young user a poor score for something they can't change.
AGE_BANDS = (30, 40, 50, 60)  # upper edges: 18-29, 30-39, 40-49, 50-59, 60+
# The training data has no missing ages, so the model must never be given one.
DEFAULT_AGE = 30.0


def age_band(age: float) -> str:
    lower = 18
    for upper in AGE_BANDS:
        if age < upper:
            return f"{lower}-{upper - 1}"
        lower = upper
    return f"{lower}+"


def prepare_training_frame(raw: pd.DataFrame) -> tuple[pd.DataFrame, np.ndarray]:
    """Give Me Some Credit, as downloaded -> (features, label)."""
    df = raw.copy()
    df.columns = RAW_COLUMNS
    df["y"] = (df["distress"].astype(str).str.lower().isin(("yes", "1", "true"))).astype(int)
    df = df[df["age"] >= 18].copy()
    for c in ("late30", "late60", "late90"):
        df.loc[df[c] >= _UNKNOWN_CODE, c] = np.nan
    # The dataset stores the absolute debt figure in DebtRatio when income is missing or zero.
    df.loc[~(df["income"] > 0), "debt_ratio"] = np.nan
    X = pd.DataFrame({
        "age": df["age"].astype(float),
        "debt_ratio": df["debt_ratio"],
        "times_late": df["late30"] + df["late60"],
        "times_seriously_late": df["late90"],
        "utilization": df["util"],
    })[FEATURES]
    return X.reset_index(drop=True), df["y"].to_numpy()


def build_features(*, age=None, monthly_income=None, monthly_debt_payments=0.0, monthly_living_costs=0.0,
                   times_late=0, times_seriously_late=0, card_balance=None, card_limit=None) -> dict:
    """One user's inputs -> model features. Unknown values become NaN, which the model handles natively."""
    def num(v):
        try:
            return float(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    income = num(monthly_income)
    debt_ratio = np.nan
    if income and income > 0:
        debt_ratio = max(0.0, (num(monthly_debt_payments) or 0.0) + (num(monthly_living_costs) or 0.0)) / income

    limit, balance = num(card_limit), num(card_balance)
    utilization = np.nan
    if limit and limit > 0 and balance is not None:
        utilization = max(0.0, balance) / limit

    a = num(age)
    return {
        "age": a if a and a >= 18 else DEFAULT_AGE,
        "debt_ratio": debt_ratio,
        "times_late": float(max(0, int(num(times_late) or 0))),
        "times_seriously_late": float(max(0, int(num(times_seriously_late) or 0))),
        "utilization": utilization,
    }
