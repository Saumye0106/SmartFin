"""
markowitz_engine.py — Markowitz Mean-Variance Portfolio Optimizer

Computes:
1. The Efficient Frontier (set of optimal portfolios)
2. The optimal portfolio for a given risk score (1–10)
3. The Global Minimum Variance (GMV) portfolio

Uses scipy.optimize.minimize with SLSQP to solve the quadratic program:
    min  w' Σ w  s.t.  w'μ = target_return, Σw = 1, w ≥ 0
"""

from __future__ import annotations

from typing import Dict, List, Tuple

import numpy as np
import pandas as pd

try:
    from scipy.optimize import minimize, OptimizeResult
    SCIPY_AVAILABLE = True
except ImportError:
    SCIPY_AVAILABLE = False


ASSET_NAMES = [
    "Equity_LargeCap",
    "Equity_MidCap",
    "Debt_ShortTerm",
    "Gold",
    "Fixed_Deposit",
]

# Friendly display names
DISPLAY_NAMES = {
    "Equity_LargeCap": "Large-Cap Equity",
    "Equity_MidCap":   "Mid-Cap Equity",
    "Debt_ShortTerm":  "Short-Term Debt",
    "Gold":            "Gold",
    "Fixed_Deposit":   "Fixed Deposit",
}

# Category grouping for the frontend donut chart
CATEGORY_MAP = {
    "Equity_LargeCap": "Equity",
    "Equity_MidCap":   "Equity",
    "Debt_ShortTerm":  "Debt",
    "Gold":            "Gold",
    "Fixed_Deposit":   "FD / Cash",
}


class MarkowitzEngine:
    """
    Markowitz Mean-Variance Optimizer for Indian retail asset classes.

    Usage:
        engine = MarkowitzEngine(mu_annual, cov_annual)
        frontier = engine.efficient_frontier(n_points=50)
        portfolio = engine.optimal_for_risk_score(risk_score=6)
    """

    def __init__(self, mu_annual: np.ndarray, cov_annual: np.ndarray):
        """
        Args:
            mu_annual: Expected annual returns vector, shape (n_assets,)
            cov_annual: Annual covariance matrix, shape (n_assets, n_assets)
        """
        self.mu = mu_annual
        self.cov = cov_annual
        self.n = len(mu_annual)
        self._validate()

    def _validate(self):
        assert self.mu.shape == (self.n,), "mu shape mismatch"
        assert self.cov.shape == (self.n, self.n), "cov shape mismatch"
        # Ensure PSD by adding small diagonal jitter
        self.cov = self.cov + np.eye(self.n) * 1e-8

    @classmethod
    def from_return_series(cls, df: pd.DataFrame) -> "MarkowitzEngine":
        """
        Build engine from a monthly return DataFrame.

        Args:
            df: pd.DataFrame, columns = asset names, monthly returns
        """
        mu_monthly = df.mean().values
        cov_monthly = df.cov().values
        # Annualise
        mu_annual = mu_monthly * 12
        cov_annual = cov_monthly * 12
        return cls(mu_annual, cov_annual)

    # ── Core solver ──────────────────────────────────────────────────────────

    def _portfolio_variance(self, w: np.ndarray) -> float:
        return float(w @ self.cov @ w)

    def _portfolio_return(self, w: np.ndarray) -> float:
        return float(w @ self.mu)

    def _portfolio_std(self, w: np.ndarray) -> float:
        return float(np.sqrt(self._portfolio_variance(w)))

    def _minimize_variance(self, target_return: float) -> OptimizeResult | None:
        """Solve min-variance portfolio for a given target return."""
        if not SCIPY_AVAILABLE:
            return None

        constraints = [
            {"type": "eq", "fun": lambda w: w.sum() - 1},
            {"type": "eq", "fun": lambda w: w @ self.mu - target_return},
        ]
        bounds = [(0, 1)] * self.n
        w0 = np.ones(self.n) / self.n

        result = minimize(
            self._portfolio_variance,
            w0,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"ftol": 1e-12, "maxiter": 500},
        )
        return result if result.success else None

    # ── Efficient Frontier ───────────────────────────────────────────────────

    def efficient_frontier(self, n_points: int = 60) -> List[Dict]:
        """
        Compute efficient frontier by solving the min-var problem
        for a range of target returns.

        Returns:
            List of dicts: {return, risk, weights, sharpe}
        """
        mu_min = self.mu.min()
        mu_max = self.mu.max()
        target_returns = np.linspace(mu_min * 1.02, mu_max * 0.98, n_points)

        frontier = []
        for target in target_returns:
            result = self._minimize_variance(target)
            if result is None:
                continue
            w = np.clip(result.x, 0, 1)
            w /= w.sum()
            ret = self._portfolio_return(w)
            std = self._portfolio_std(w)
            sharpe = (ret - 0.065) / (std + 1e-8)  # risk-free ≈ repo rate 6.5%
            frontier.append({
                "return": round(float(ret), 4),
                "risk":   round(float(std), 4),
                "sharpe": round(float(sharpe), 4),
                "weights": {ASSET_NAMES[i]: round(float(w[i]), 4) for i in range(self.n)},
            })

        # Sort by risk
        frontier.sort(key=lambda x: x["risk"])
        return frontier

    # ── Global Minimum Variance ──────────────────────────────────────────────

    def gmv_portfolio(self) -> Dict:
        """Compute the Global Minimum Variance portfolio."""
        if not SCIPY_AVAILABLE:
            # Equal-weight fallback
            w = np.ones(self.n) / self.n
        else:
            result = minimize(
                self._portfolio_variance,
                np.ones(self.n) / self.n,
                method="SLSQP",
                bounds=[(0, 1)] * self.n,
                constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}],
                options={"ftol": 1e-12, "maxiter": 500},
            )
            w = np.clip(result.x, 0, 1) if result.success else np.ones(self.n) / self.n
            w /= w.sum()

        return self._portfolio_dict(w, label="Global Minimum Variance")

    # ── Max Sharpe ───────────────────────────────────────────────────────────

    def max_sharpe_portfolio(self, risk_free_rate: float = 0.065) -> Dict:
        """Compute the Maximum Sharpe Ratio portfolio (Tangency Portfolio)."""
        if not SCIPY_AVAILABLE:
            w = np.ones(self.n) / self.n
        else:
            def neg_sharpe(w):
                ret = w @ self.mu
                std = np.sqrt(w @ self.cov @ w + 1e-8)
                return -(ret - risk_free_rate) / std

            result = minimize(
                neg_sharpe,
                np.ones(self.n) / self.n,
                method="SLSQP",
                bounds=[(0, 1)] * self.n,
                constraints=[{"type": "eq", "fun": lambda w: w.sum() - 1}],
                options={"ftol": 1e-12, "maxiter": 500},
            )
            w = np.clip(result.x, 0, 1) if result.success else np.ones(self.n) / self.n
            w /= w.sum()

        return self._portfolio_dict(w, label="Maximum Sharpe Ratio")

    # ── Risk-score based selection ───────────────────────────────────────────

    def optimal_for_risk_score(self, risk_score: int) -> Dict:
        """
        Select the optimal portfolio from the efficient frontier
        for a given risk score (1–10).

        Mapping:
          1–3 (Conservative) → low-risk end of frontier
          4–6 (Moderate)     → middle (near max-Sharpe)
          7–10 (Aggressive)  → high-return end

        Returns:
            dict with weights, projected return, risk, Sharpe
        """
        risk_score = max(1, min(10, int(risk_score)))

        # For very conservative: use GMV
        if risk_score <= 2:
            return self.gmv_portfolio()

        # For very aggressive: use Max Sharpe (or slightly beyond)
        if risk_score >= 9:
            return self.max_sharpe_portfolio()

        frontier = self.efficient_frontier(n_points=80)
        if not frontier:
            return self.gmv_portfolio()

        # Normalise risk score to 0–1
        t = (risk_score - 1) / 9.0  # 0.0 = most conservative, 1.0 = aggressive

        # Map t to frontier index
        idx = int(t * (len(frontier) - 1))
        idx = max(0, min(idx, len(frontier) - 1))
        chosen = frontier[idx]

        w = np.array([chosen["weights"].get(a, 0) for a in ASSET_NAMES])
        return self._portfolio_dict(w, label=f"Risk Score {risk_score}")

    # ── Helper ───────────────────────────────────────────────────────────────

    def _portfolio_dict(self, w: np.ndarray, label: str = "") -> Dict:
        ret = self._portfolio_return(w)
        std = self._portfolio_std(w)
        sharpe = (ret - 0.065) / (std + 1e-8)

        # Per-asset weights with display info
        asset_allocations = []
        for i, name in enumerate(ASSET_NAMES):
            asset_allocations.append({
                "asset": name,
                "display_name": DISPLAY_NAMES[name],
                "category": CATEGORY_MAP[name],
                "weight": round(float(w[i]), 4),
                "weight_pct": round(float(w[i]) * 100, 1),
                "expected_return_annual": round(float(self.mu[i]), 4),
            })

        # Category-level rollup for the donut chart
        category_weights: Dict[str, float] = {}
        for alloc in asset_allocations:
            cat = alloc["category"]
            category_weights[cat] = round(
                category_weights.get(cat, 0) + alloc["weight_pct"], 1
            )

        # Projected returns (compound)
        projected = {
            "1yr":  round((1 + ret) ** 1 - 1, 4),
            "3yr":  round((1 + ret) ** 3 - 1, 4),
            "5yr":  round((1 + ret) ** 5 - 1, 4),
            "10yr": round((1 + ret) ** 10 - 1, 4),
        }

        return {
            "label": label,
            "allocations": asset_allocations,
            "category_weights": category_weights,
            "expected_return_annual": round(float(ret), 4),
            "expected_return_pct": round(float(ret) * 100, 2),
            "risk_annual": round(float(std), 4),
            "risk_pct": round(float(std) * 100, 2),
            "sharpe_ratio": round(float(sharpe), 3),
            "projected_returns": projected,
        }
