"""
personalizer.py — User-context adjustments on top of Markowitz allocations

Applies rule-based nudges based on the user's actual financial situation
(loans, goals, EMI burden) drawn from the SmartFin database.

These adjustments shift allocations toward liquidity / safety when the user
has high debt burden or short-term goals, and allow more equity exposure
when the user is in a strong financial position.
"""

from __future__ import annotations

import logging
import sqlite3
from contextlib import closing
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


ASSET_NAMES = [
    "Equity_LargeCap",
    "Equity_MidCap",
    "Equity_SmallCap",
    "International_Equity",
    "Debt_ShortTerm",
    "Gold",
    "Silver",
    "REIT",
    "Fixed_Deposit",
]

# Same-role groupings used to extend the rules below to the expanded asset
# universe: "reduce equity" nudges should pull from ALL equity buckets, not
# just the original two, and "reduce risk/illiquid" nudges should pull from
# Gold's new sibling assets too.
_EQUITY_ASSETS = ["Equity_LargeCap", "Equity_MidCap", "Equity_SmallCap", "International_Equity"]
_RISKY_NONEQUITY_ASSETS = ["Gold", "Silver", "REIT"]


class Personalizer:
    """Apply user-specific adjustments to raw Markowitz portfolio."""

    def __init__(self, db_path: str = "auth.db"):
        self.db_path = db_path

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ── Data fetchers ─────────────────────────────────────────────────────
    # On DB errors each fetcher returns "no adjustment" so optimization still
    # works, but logs it: a silent `except: pass` once hid broken queries here.

    def _latest_budget(self, conn, user_id: int) -> Optional[sqlite3.Row]:
        """Most recent month the user recorded a positive income for."""
        return conn.execute(
            "SELECT month, monthly_income FROM monthly_budgets "
            "WHERE user_id = ? AND monthly_income > 0 ORDER BY month DESC LIMIT 1",
            (user_id,),
        ).fetchone()

    def _get_emi_ratio(self, user_id: int) -> Optional[float]:
        """Total EMI of active loans / latest monthly income from the budget tracker."""
        try:
            with closing(self._get_conn()) as conn:
                budget = self._latest_budget(conn, user_id)
                if not budget:
                    return None
                row = conn.execute(
                    "SELECT COALESCE(SUM(monthly_emi), 0) AS emi FROM loans "
                    "WHERE user_id = ? AND deleted_at IS NULL "
                    "AND (loan_maturity_date IS NULL OR loan_maturity_date >= date('now'))",
                    (user_id,),
                ).fetchone()
                return row["emi"] / budget["monthly_income"]
        except sqlite3.Error as e:
            logger.warning("personalizer: EMI ratio lookup failed for user %s: %s", user_id, e)
            return None

    def _get_active_loans_count(self, user_id: int) -> int:
        """Loans not deleted and not yet past maturity."""
        try:
            with closing(self._get_conn()) as conn:
                row = conn.execute(
                    "SELECT COUNT(*) AS cnt FROM loans "
                    "WHERE user_id = ? AND deleted_at IS NULL "
                    "AND (loan_maturity_date IS NULL OR loan_maturity_date >= date('now'))",
                    (user_id,),
                ).fetchone()
                return row["cnt"]
        except sqlite3.Error as e:
            logger.warning("personalizer: active loan count failed for user %s: %s", user_id, e)
            return 0

    def _get_shortest_goal_months(self, user_id: int) -> Optional[float]:
        """Months until the nearest active financial goal's target date."""
        try:
            with closing(self._get_conn()) as conn:
                rows = conn.execute(
                    "SELECT target_date FROM financial_goals "
                    "WHERE user_id = ? AND status = 'active' AND target_date IS NOT NULL",
                    (user_id,),
                ).fetchall()
        except sqlite3.Error as e:
            logger.warning("personalizer: goal lookup failed for user %s: %s", user_id, e)
            return None

        now = datetime.now()
        months_list = []
        for row in rows:
            try:
                td = datetime.fromisoformat(str(row["target_date"]).replace("Z", ""))
            except ValueError:
                continue
            delta = (td - now).days / 30
            if delta > 0:
                months_list.append(delta)
        return min(months_list) if months_list else None

    def _get_savings_ratio(self, user_id: int) -> Optional[float]:
        """(income - recorded expenses) / income for the latest budget month."""
        try:
            with closing(self._get_conn()) as conn:
                budget = self._latest_budget(conn, user_id)
                if not budget:
                    return None
                row = conn.execute(
                    "SELECT COALESCE(SUM(amount), 0) AS spent FROM expense_entries "
                    "WHERE user_id = ? AND substr(expense_date, 1, 7) = ?",
                    (user_id, budget["month"]),
                ).fetchone()
                income = budget["monthly_income"]
                return (income - row["spent"]) / income
        except sqlite3.Error as e:
            logger.warning("personalizer: savings ratio lookup failed for user %s: %s", user_id, e)
            return None

    # ── Adjustment logic ──────────────────────────────────────────────────

    def adjust(
        self, portfolio: Dict, user_id: int, investable_amount: float
    ) -> Dict:
        """
        Apply user-context adjustments to a Markowitz portfolio dict.

        Args:
            portfolio: Output dict from MarkowitzEngine._portfolio_dict()
            user_id: SmartFin user ID
            investable_amount: Rupee amount the user wants to invest

        Returns:
            Modified portfolio dict with:
              - Adjusted weight arrays
              - Applied adjustments list (for frontend explanation chips)
              - Investable allocation breakdown (in rupees)
        """
        import copy
        p = copy.deepcopy(portfolio)

        weights = {a["asset"]: a["weight"] for a in p["allocations"]}
        applied: List[str] = []

        # Fetch user context
        emi_ratio = self._get_emi_ratio(user_id)
        active_loans = self._get_active_loans_count(user_id)
        min_goal_months = self._get_shortest_goal_months(user_id)
        savings_ratio = self._get_savings_ratio(user_id)

        # Rule 1: High EMI burden → reduce equity (across ALL equity buckets), increase FD/Debt
        if emi_ratio is not None and emi_ratio > 0.40:
            weights = self._shift(weights, from_assets=_EQUITY_ASSETS,
                                  to_assets=["Fixed_Deposit", "Debt_ShortTerm"], amount=0.10)
            applied.append("high_emi_reduced_equity")

        elif emi_ratio is not None and emi_ratio > 0.25:
            weights = self._shift(weights, from_assets=["Equity_MidCap", "Equity_SmallCap"],
                                  to_assets=["Debt_ShortTerm"], amount=0.05)
            applied.append("moderate_emi_reduced_midcap")

        # Rule 2: Active loans → add a liquidity buffer in FD (pull from mid-cap
        # and the higher-volatility non-equity assets: Gold/Silver/REIT)
        if active_loans >= 2:
            weights = self._shift(weights, from_assets=["Equity_MidCap"] + _RISKY_NONEQUITY_ASSETS,
                                  to_assets=["Fixed_Deposit"], amount=0.05)
            applied.append("multiple_loans_liquidity_buffer")

        # Rule 3: Short-term goal ≤ 12 months → heavily debt-biased (all equity reduced)
        if min_goal_months is not None and min_goal_months <= 12:
            weights = self._shift(weights, from_assets=_EQUITY_ASSETS,
                                  to_assets=["Debt_ShortTerm", "Fixed_Deposit"], amount=0.15)
            applied.append(f"short_term_goal_{int(min_goal_months)}mo_shifted_debt")

        elif min_goal_months is not None and min_goal_months <= 36:
            weights = self._shift(weights, from_assets=["Equity_MidCap", "Equity_SmallCap"],
                                  to_assets=["Debt_ShortTerm"], amount=0.08)
            applied.append(f"medium_term_goal_{int(min_goal_months)}mo_shifted_debt")

        # Rule 4: Very low savings → don't invest in volatile assets
        # (mid/small-cap equity plus the higher-volatility non-equity assets)
        if savings_ratio is not None and savings_ratio < 0.05:
            weights = self._shift(weights, from_assets=["Equity_MidCap", "Equity_SmallCap"] + _RISKY_NONEQUITY_ASSETS,
                                  to_assets=["Fixed_Deposit"], amount=0.10)
            applied.append("low_savings_rate_conservative_shift")

        # Normalise weights to sum = 1
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        # Rebuild allocation list
        for alloc in p["allocations"]:
            alloc["weight"] = round(weights[alloc["asset"]], 4)
            alloc["weight_pct"] = round(weights[alloc["asset"]] * 100, 1)
            alloc["amount_inr"] = round(investable_amount * weights[alloc["asset"]], 2)

        # Update category rollup
        category_weights: Dict[str, float] = {}
        from portfolio_optimizer.markowitz_engine import CATEGORY_MAP
        for alloc in p["allocations"]:
            cat = CATEGORY_MAP[alloc["asset"]]
            category_weights[cat] = round(
                category_weights.get(cat, 0) + alloc["weight_pct"], 1
            )
        p["category_weights"] = category_weights

        # Recompute expected return from adjusted weights
        w_arr = np.array([weights[a] for a in ASSET_NAMES])
        p["applied_adjustments"] = applied
        p["investable_amount"] = investable_amount

        return p

    @staticmethod
    def _shift(
        weights: Dict[str, float],
        from_assets: List[str],
        to_assets: List[str],
        amount: float,
    ) -> Dict[str, float]:
        """
        Shift `amount` total weight from from_assets to to_assets,
        distributing equally from each source and to each destination.
        Clips to [0, 1].
        """
        w = dict(weights)
        per_source = amount / max(len(from_assets), 1)
        per_dest = amount / max(len(to_assets), 1)

        for asset in from_assets:
            if asset in w:
                w[asset] = max(0.0, w[asset] - per_source)

        for asset in to_assets:
            if asset in w:
                w[asset] = min(1.0, w[asset] + per_dest)

        return w
