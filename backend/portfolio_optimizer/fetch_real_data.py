"""
fetch_real_data.py — Pull real historical returns for the 9-asset universe via yfinance.

Replaces the synthetic Gaussian data in data_loader.py with real market data.
Run manually (offline, like train_model.py) — not called at request time.

Each asset keeps its own full available real history (no truncation to a
shared window): older instruments like Nifty 50 / Gold / Liquid ETFs go back
to 2007-2009, while newer ones (Silver ETF, REIT, Mid/Small-cap ETFs) only
go back as far as they've actually been listed. Gaps before an asset's
inception are left as NaN rather than padded or backfilled. pandas' mean/
cov/corr already skip NaN (skipna / pairwise-complete by default), so
downstream code needs no changes to handle this.

Fixed Deposit has no market price series (FDs aren't traded) and stays a
flat assumption for the whole date range — explicitly labeled as such in
the output manifest, never silently blended in as if it were real data.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import yfinance as yf

DATA_DIR = Path(__file__).parent / "data"
CSV_PATH = DATA_DIR / "asset_returns.csv"
MANIFEST_PATH = DATA_DIR / "data_source.json"

# asset_key -> yfinance ticker (None = no market series, assumption-based)
TICKERS = {
    "Equity_LargeCap":     "^NSEI",
    "Equity_MidCap":       "MIDCAPETF.NS",
    "Equity_SmallCap":     "SMALLCAP.NS",
    "International_Equity": "MON100.NS",
    "Debt_ShortTerm":      "LIQUIDBEES.NS",
    "Gold":                "GOLDBEES.NS",
    "Silver":              "SILVERBEES.NS",
    "REIT":                "EMBASSY.NS",
    "Fixed_Deposit":       None,
}

FIXED_DEPOSIT_ANNUAL_RATE = 0.065


def _fetch_monthly_returns(ticker: str) -> pd.Series:
    """Fetch full available history for a ticker and return month-end pct-change returns."""
    hist = yf.Ticker(ticker).history(period="max")
    if hist.empty:
        raise ValueError(f"No data returned for ticker {ticker!r}")
    close = hist["Close"].tz_localize(None)
    monthly = close.resample("ME").last()
    returns = monthly.pct_change().dropna()
    return returns


def fetch_and_save() -> dict:
    """Fetch real data for all tradeable assets, assemble the DataFrame, and cache to disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    series_by_asset: dict[str, pd.Series] = {}
    achieved_ranges: dict[str, dict] = {}
    failures: list[str] = []

    for asset, ticker in TICKERS.items():
        if ticker is None:
            continue
        try:
            s = _fetch_monthly_returns(ticker)
            series_by_asset[asset] = s
            achieved_ranges[asset] = {
                "ticker": ticker,
                "start": s.index[0].strftime("%Y-%m-%d"),
                "end": s.index[-1].strftime("%Y-%m-%d"),
                "months": len(s),
            }
            print(f"  {asset:22s} ({ticker:16s}) -> {len(s):4d} months, "
                  f"{s.index[0].date()} .. {s.index[-1].date()}")
        except Exception as e:
            failures.append(f"{asset} ({ticker}): {e}")
            print(f"  {asset:22s} ({ticker:16s}) -> FAILED: {e}")

    if failures:
        raise RuntimeError(
            "Failed to fetch real data for: " + "; ".join(failures) +
            ". Fix the ticker mapping in fetch_real_data.py before proceeding."
        )

    # Outer-join all real series on their union of month-end dates.
    df = pd.concat(series_by_asset, axis=1)
    df = df.sort_index()

    # Fixed Deposit: flat assumption across the full combined date range (no gaps).
    fd_monthly_rate = (1 + FIXED_DEPOSIT_ANNUAL_RATE) ** (1 / 12) - 1
    df["Fixed_Deposit"] = fd_monthly_rate

    # Reorder columns to match TICKERS dict order.
    df = df[list(TICKERS.keys())]

    df.to_csv(CSV_PATH)

    common_start = max(r["start"] for r in achieved_ranges.values())
    common_end = min(r["end"] for r in achieved_ranges.values())

    manifest = {
        "type": "real_historical",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "tickers": {a: t for a, t in TICKERS.items() if t is not None},
        "per_asset_range": achieved_ranges,
        "common_overlap_window": {
            "start": common_start,
            "end": common_end,
            "note": (
                "All 9 assets have real data only within this overlap window. "
                "Assets with longer individual history (e.g. Nifty 50, Gold, "
                "Liquid ETF) still use their full real range for risk/return "
                "statistics (pandas mean/cov/corr skip NaN by default); only "
                "the XGBoost next-month predictor is limited to this shared "
                "window, since it trains one aligned feature matrix across "
                "all assets."
            ),
        },
        "fixed_deposit_note": (
            f"Fixed_Deposit has no market price series (FDs aren't traded) — "
            f"assumed flat {FIXED_DEPOSIT_ANNUAL_RATE:.1%} annual for the full "
            f"date range. This is the only assumption-based column; all others "
            f"are real market data."
        ),
    }

    with open(MANIFEST_PATH, "w") as fh:
        json.dump(manifest, fh, indent=2)

    return manifest


if __name__ == "__main__":
    print("Fetching real historical returns for the 9-asset universe...\n")
    manifest = fetch_and_save()
    print(f"\nSaved {CSV_PATH}")
    print(f"Saved {MANIFEST_PATH}")
    print(f"\nCommon overlap window (all 9 assets have real data here): "
          f"{manifest['common_overlap_window']['start']} .. {manifest['common_overlap_window']['end']}")
