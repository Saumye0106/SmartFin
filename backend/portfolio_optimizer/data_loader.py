"""
data_loader.py — Loads real market data for the 9-asset universe, with a
synthetic-Gaussian fallback used only if real data has never been fetched
(e.g. fresh clone, no internet). Real data lives in fetch_real_data.py;
see get_data_source_info() for how to tell which one is actually in use.

Fallback asset class parameters (annual, India-calibrated, ILLUSTRATIVE —
not derived from real prices):
  - Large-Cap Equity: ~12% mean annual return, ~18% std
  - Mid-Cap Equity: ~14% mean, ~22% std
  - Small-Cap Equity: ~16% mean, ~26% std
  - International Equity (Nasdaq 100 proxy): ~13% mean, ~20% std
  - Debt (Short-term/Liquid): ~6.5% mean, ~2% std
  - Gold: ~8% mean, ~14% std
  - Silver: ~9% mean, ~24% std
  - REIT: ~9% mean, ~16% std
  - Fixed Deposit: ~6.5% mean, ~0.5% std

Returns are monthly (annualised figures divided by 12 with monthly vol).
The fallback simulates 7 years (84 months) of correlated returns with an
assumed correlation matrix — used only when data/asset_returns.csv doesn't
exist yet; once fetch_real_data.py has run, that real CSV is always
preferred (see load_or_generate_data()).
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path

# ── Fallback asset class parameters (annual, India-calibrated, SYNTHETIC) ──
ASSETS = {
    "Equity_LargeCap":      {"mu_annual": 0.12,  "sigma_annual": 0.18},
    "Equity_MidCap":        {"mu_annual": 0.14,  "sigma_annual": 0.22},
    "Equity_SmallCap":      {"mu_annual": 0.16,  "sigma_annual": 0.26},
    "International_Equity": {"mu_annual": 0.13,  "sigma_annual": 0.20},
    "Debt_ShortTerm":       {"mu_annual": 0.065, "sigma_annual": 0.02},
    "Gold":                 {"mu_annual": 0.08,  "sigma_annual": 0.14},
    "Silver":               {"mu_annual": 0.09,  "sigma_annual": 0.24},
    "REIT":                 {"mu_annual": 0.09,  "sigma_annual": 0.16},
    "Fixed_Deposit":        {"mu_annual": 0.065, "sigma_annual": 0.005},
}

# Fallback correlation matrix (9×9) — assumed, used only by the synthetic generator
#           LC     MC     SC     Intl   Debt   Gold   Silv   REIT   FD
CORRELATION = np.array([
    [1.00,  0.85,  0.75,  0.35, -0.10,  0.05,  0.05,  0.45,  0.00],  # LargeCap
    [0.85,  1.00,  0.88,  0.30, -0.08,  0.06,  0.06,  0.42,  0.00],  # MidCap
    [0.75,  0.88,  1.00,  0.25, -0.05,  0.04,  0.05,  0.38,  0.00],  # SmallCap
    [0.35,  0.30,  0.25,  1.00, -0.05,  0.10,  0.08,  0.20,  0.00],  # International
    [-0.10, -0.08, -0.05, -0.05, 1.00,  0.15,  0.10,  0.20,  0.70],  # Debt
    [0.05,  0.06,  0.04,  0.10,  0.15,  1.00,  0.85,  0.10,  0.10],  # Gold
    [0.05,  0.06,  0.05,  0.08,  0.10,  0.85,  1.00,  0.08,  0.05],  # Silver
    [0.45,  0.42,  0.38,  0.20,  0.20,  0.10,  0.08,  1.00,  0.15],  # REIT
    [0.00,  0.00,  0.00,  0.00,  0.70,  0.10,  0.05,  0.15,  1.00],  # FD
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

    # Generate and cache (synthetic fallback — no real data fetched yet)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    df = generate_return_series()
    df.to_csv(cache_path)
    return df


def get_data_source_info(manifest_path: str | None = None) -> dict:
    """
    Report whether the currently-cached asset_returns.csv is real historical
    data (from fetch_real_data.py) or the synthetic Gaussian fallback.

    This is the single source of truth for "is this real or fake," read by
    the training script and surfaced in API responses / the frontend.
    """
    if manifest_path is None:
        here = Path(__file__).parent
        manifest_path = here / "data" / "data_source.json"

    manifest_path = Path(manifest_path)
    if manifest_path.exists():
        with open(manifest_path) as fh:
            return json.load(fh)

    return {
        "type": "synthetic_fallback",
        "note": (
            "No data_source.json found — asset_returns.csv (if present) was "
            "generated by the synthetic Gaussian fallback in data_loader.py, "
            "not real market data. Run fetch_real_data.py to replace it with "
            "real historical returns."
        ),
    }


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
