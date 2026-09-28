"""
personalizer.py — User-context adjustments on top of Markowitz allocations

Applies rule-based nudges based on the user's actual financial situation
(loans, goals, EMI burden) drawn from the SmartFin database.

These adjustments shift allocations toward liquidity / safety when the user
has high debt burden or short-term goals, and allow more equity exposure
when the user is in a strong financial position.
"""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import numpy as np


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

    def _get_emi_ratio(self, user_id: int) -> Optional[float]:
        """Return EMI / income ratio from the user's profile."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT income, emi FROM users WHERE id = ?", (user_id,)
            )
            row = cur.fetchone()
            conn.close()
            if row and row["income"] and row["income"] > 0:
                emi = row["emi"] or 0
                return emi / row["income"]
        except Exception:
            pass
        return None

    def _get_active_loans_count(self, user_id: int) -> int:
        """Return number of active loans."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT COUNT(*) as cnt FROM loans WHERE user_id = ? AND status = 'active'",
                (user_id,),
            )
            row = cur.fetchone()
            conn.close()
            return row["cnt"] if row else 0
        except Exception:
            return 0

    def _get_shortest_goal_months(self, user_id: int) -> Optional[int]:
        """Return months to the nearest active financial goal deadline."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT target_date FROM goals WHERE user_id = ? AND status = 'active'",
                (user_id,),
            )
            rows = cur.fetchall()
            conn.close()
            now = datetime.utcnow()
            months_list = []
            for row in rows:
                if row["target_date"]:
                    try:
                        td = datetime.fromisoformat(row["target_date"].replace("Z", ""))
                        delta = (td - now).days / 30
                        if delta > 0:
                            months_list.append(delta)
                    except Exception:
                        pass
            return min(months_list) if months_list else None
        except Exception:
            return None

    def _get_savings_ratio(self, user_id: int) -> Optional[float]:
        """Return monthly savings / income ratio."""
        try:
            conn = self._get_conn()
            cur = conn.cursor()
            cur.execute(
                "SELECT income, savings FROM users WHERE id = ?", (user_id,)
            )
            row = cur.fetchone()
            conn.close()
            if row and row["income"] and row["income"] > 0:
                savings = row["savings"] or 0
                return savings / row["income"]
        except Exception:
            pass
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
