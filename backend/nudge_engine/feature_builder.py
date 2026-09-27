"""
feature_builder.py — Build feature matrix from user expense history in SQLite.

For each week in the user's expense history, computes:
  - Total spend by category (normalised by income)
  - Day-of-month effect (week 1 = post-salary, etc.)
  - Lag features: this week vs previous 2 weeks per category
  - Rolling 4-week average per category
  - Ratio of this week vs rolling average (the key anomaly signal)

Requires at least 4 weeks of expense data for meaningful features.
The function is designed to work with the existing SmartFin `expenses` /
`budget_categories` table schema.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd


EXPENSE_CATEGORIES = [
    "Food & Groceries",
    "Travel & Transport",
    "Shopping & Entertainment",
    "Rent & Housing",
    "EMI & Loans",
    "Healthcare",
    "Utilities",
    "Other",
]

# Normalised slugs used as column names
CAT_SLUGS = [c.lower().replace(" & ", "_").replace(" ", "_") for c in EXPENSE_CATEGORIES]


class FeatureBuilder:
    """Builds weekly expense feature matrix from the SmartFin database."""

    def __init__(self, db_path: str = "auth.db"):
        self.db_path = db_path

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _get_user_income(self, user_id: int) -> float:
        """Fetch monthly income from user profile."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute("SELECT income FROM users WHERE id = ?", (user_id,))
            row = cur.fetchone()
            conn.close()
            return float(row["income"]) if row and row["income"] else 50000.0
        except Exception:
            return 50000.0

    def _get_raw_expenses(self, user_id: int, days_back: int = 180) -> pd.DataFrame:
        """
        Fetch raw expense records from the database.

        Returns DataFrame with columns: date, category, amount
        """
        cutoff = (datetime.utcnow() - timedelta(days=days_back)).date().isoformat()
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            # Try the expenses table used by BudgetManager
            cur.execute("""
                SELECT e.date, bc.name as category, e.amount
                FROM expenses e
                LEFT JOIN budget_categories bc ON e.category_id = bc.id
                WHERE e.user_id = ?
                  AND e.date >= ?
                ORDER BY e.date ASC
            """, (user_id, cutoff))
            rows = cur.fetchall()
            conn.close()

            if not rows:
                return pd.DataFrame(columns=["date", "category", "amount"])

            df = pd.DataFrame([dict(r) for r in rows])
            df["date"] = pd.to_datetime(df["date"])
            df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)
            return df

        except Exception:
            return pd.DataFrame(columns=["date", "category", "amount"])

    def _categorise(self, category_name: str) -> str:
        """Map raw category names to standardised slugs."""
        if not category_name:
            return "other"
        name_lower = category_name.lower()
        for i, cat in enumerate(EXPENSE_CATEGORIES):
            if any(keyword in name_lower for keyword in cat.lower().split(" & ")):
                return CAT_SLUGS[i]
        return "other"

    def build(self, user_id: int) -> Tuple[Optional[pd.DataFrame], Dict]:
        """
        Build the weekly feature matrix for a user.

        Returns:
            (feature_df, info_dict) where:
              feature_df: pd.DataFrame, index=week_start, columns=features
                          Returns None if insufficient data
              info_dict: dict with 'weeks_of_data', 'sufficient', 'income'
        """
        income = self._get_user_income(user_id)
        raw = self._get_raw_expenses(user_id, days_back=180)

        if raw.empty or len(raw) < 5:
            return None, {"weeks_of_data": 0, "sufficient": False, "income": income}

        # Assign each expense to its ISO week
        raw["week"] = raw["date"].dt.to_period("W").dt.start_time

        # Pivot: weekly spend per category (normalised by income)
        cat_col = "category_slug"
        raw[cat_col] = raw["category"].apply(self._categorise)

        weekly = (
            raw.groupby(["week", cat_col])["amount"]
            .sum()
            .unstack(fill_value=0)
            .reindex(columns=CAT_SLUGS, fill_value=0)
        )

        # Normalise by monthly income (weekly income ≈ income/4.33)
        weekly_income = income / 4.33
        weekly_norm = weekly / weekly_income

        # Add week-of-month (1-4) — post-salary effect
        weekly_norm["week_of_month"] = [
            min((d.day - 1) // 7 + 1, 4) for d in weekly_norm.index
        ]

        # Rolling 4-week average per category
        for slug in CAT_SLUGS:
            if slug in weekly_norm.columns:
                roll = weekly_norm[slug].rolling(4, min_periods=2).mean()
                weekly_norm[f"{slug}_roll4"] = roll

                # Ratio vs rolling avg (key anomaly signal)
                weekly_norm[f"{slug}_ratio"] = (
                    weekly_norm[slug] / (roll + 1e-6)
                )

                # Lag features
                weekly_norm[f"{slug}_lag1"] = weekly_norm[slug].shift(1)
                weekly_norm[f"{slug}_lag2"] = weekly_norm[slug].shift(2)

        # Drop early rows with too many NaNs
        feature_df = weekly_norm.dropna(thresh=int(weekly_norm.shape[1] * 0.6))
        feature_df = feature_df.fillna(0)

        weeks = len(feature_df)
        info = {
            "weeks_of_data": weeks,
            "sufficient": weeks >= 4,
            "income": income,
            "date_range": {
                "start": feature_df.index[0].isoformat() if weeks > 0 else None,
                "end":   feature_df.index[-1].isoformat() if weeks > 0 else None,
            },
        }

        return feature_df, info
