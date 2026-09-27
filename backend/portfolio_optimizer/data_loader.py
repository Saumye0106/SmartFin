"""
data_loader.py — Generate realistic Indian asset class return series
Uses historically-grounded statistics for Indian market asset classes:
  - Equity (Nifty 50 proxy): ~12% mean annual return, ~18% std
  - Mid-Cap Equity: ~14% mean, ~22% std
  - Debt (Short-term MF): ~6.5% mean, ~2% std
  - Gold: ~8% mean, ~14% std
  - Fixed Deposit: ~6.5% mean, ~0.5% std

Returns are monthly (annualised figures divided by 12 with monthly vol).
We simulate 7 years (84 months) of correlated returns with a realistic
correlation matrix estimated from historical Indian market data.
"""

import numpy as np
import pandas as pd
from pathlib import Path

# ── Asset class parameters (annual, India-calibrated) ──────────────────────
ASSETS = {
    "Equity_LargeCap": {"mu_annual": 0.12, "sigma_annual": 0.18},
    "Equity_MidCap":   {"mu_annual": 0.14, "sigma_annual": 0.22},
    "Debt_ShortTerm":  {"mu_annual": 0.065, "sigma_annual": 0.02},
    "Gold":            {"mu_annual": 0.08,  "sigma_annual": 0.14},
    "Fixed_Deposit":   {"mu_annual": 0.065, "sigma_annual": 0.005},
}

# Correlation matrix (5×5) — empirically estimated for Indian markets
CORRELATION = np.array([
    # LC    MC    Debt  Gold  FD
    [1.00, 0.85, -0.10, 0.05, 0.00],  # LargeCap
    [0.85, 1.00, -0.08, 0.06, 0.00],  # MidCap
    [-0.10, -0.08, 1.00, 0.15, 0.70],  # Debt
    [0.05,  0.06, 0.15, 1.00, 0.10],  # Gold
    [0.00,  0.00, 0.70, 0.10, 1.00],  # FD
])

ASSET_NAMES = list(ASSETS.keys())
N_ASSETS = len(ASSET_NAMES)
N_MONTHS = 84  # 7 years
RANDOM_SEED = 42


def _build_monthly_params():
    """Convert annual mu/sigma to monthly."""
    mu_m = np.array([ASSETS[a]["mu_annual"] / 12 for a in ASSET_NAMES])
    sigma_m = np.array([ASSETS[a]["sigma_annual"] / np.sqrt(12) for a in ASSET_NAMES])
    return mu_m, sigma_m


def _build_cov_matrix(sigma_m: np.ndarray) -> np.ndarray:
    """Build covariance matrix from sigmas and correlation."""
    D = np.diag(sigma_m)
    return D @ CORRELATION @ D


def generate_return_series(n_months: int = N_MONTHS, seed: int = RANDOM_SEED) -> pd.DataFrame:
    """
    Generate a DataFrame of monthly returns for all asset classes.

    Returns:
        pd.DataFrame shape (n_months, 5) with columns = ASSET_NAMES
        Index = DatetimeIndex (monthly, ending today)
    """
    rng = np.random.default_rng(seed)
    mu_m, sigma_m = _build_monthly_params()
    cov_m = _build_cov_matrix(sigma_m)

    # Multivariate normal samples
    returns = rng.multivariate_normal(mean=mu_m, cov=cov_m, size=n_months)

    # Build DatetimeIndex going back n_months from now
    end = pd.Timestamp.now().normalize()
    dates = pd.date_range(end=end, periods=n_months, freq="ME")

    df = pd.DataFrame(returns, index=dates, columns=ASSET_NAMES)
    return df


def load_or_generate_data(cache_path: str | None = None) -> pd.DataFrame:
    """
    Load cached return series CSV, or generate and cache it.

    Args:
        cache_path: Optional path to CSV file. Defaults to
                    portfolio_optimizer/data/asset_returns.csv

    Returns:
        pd.DataFrame of monthly returns
    """
    if cache_path is None:
        here = Path(__file__).parent
        cache_path = here / "data" / "asset_returns.csv"

    cache_path = Path(cache_path)

    if cache_path.exists():
        df = pd.read_csv(cache_path, index_col=0, parse_dates=True)
        return df

    # Generate and cache
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df = generate_return_series()
    df.to_csv(cache_path)
    return df


def get_asset_summary(df: pd.DataFrame) -> dict:
    """
    Compute annualised mean return and volatility for each asset class.

    Returns:
        dict with keys 'mean_annual' and 'vol_annual' → each a Series
    """
    mean_monthly = df.mean()
    std_monthly = df.std()

    return {
        "mean_annual": (mean_monthly * 12).to_dict(),
        "vol_annual": (std_monthly * np.sqrt(12)).to_dict(),
        "correlation": df.corr().to_dict(),
    }


if __name__ == "__main__":
    df = load_or_generate_data()
    print(f"Return series shape: {df.shape}")
    print("\nAnnualised stats:")
    summary = get_asset_summary(df)
    for asset in ASSET_NAMES:
        print(
            f"  {asset:22s}: mean={summary['mean_annual'][asset]:.1%}  "
            f"vol={summary['vol_annual'][asset]:.1%}"
        )
