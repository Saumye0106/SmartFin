"""
fetch_real_data.py — Pull real historical prices for the 9-asset universe.

Run manually (offline, like train_model.py) — not called at request time.

Each asset uses the longest clean real series available for it:
  - Index levels instead of recently-launched ETFs where the ETF is young
    (Mid-Cap, Small-Cap): a 2-year ETF history made the mean return
    meaningless (95% range -19%..+29%/yr), while the index it tracks goes
    back to 2005-2007.
  - Silver = COMEX silver futures (USD/oz) x USD/INR, back to 2003, instead
    of the 2022-listed SILVERBEES.
  - Debt = Nippon India Liquid Fund growth-plan NAV (mfapi.in). The
    LIQUIDBEES ETF pays its yield out as daily dividends, so its price
    barely moves and price-based returns showed ~3%/yr instead of ~6.8%.
    A growth-plan NAV accumulates that yield.

Gaps before an asset's history begins are left as NaN (never padded);
pandas mean/cov/corr skip NaN by default. Fixed Deposit has no market
series and stays a flat, explicitly-labeled assumption.

Outputs:
  data/asset_returns.csv         monthly returns (training, expected returns)
  data/asset_returns_weekly.csv  weekly returns (covariance estimation)
  data/data_source.json          manifest describing every source
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

DATA_DIR = Path(__file__).parent / "data"
CSV_PATH = DATA_DIR / "asset_returns.csv"
WEEKLY_CSV_PATH = DATA_DIR / "asset_returns_weekly.csv"
MANIFEST_PATH = DATA_DIR / "data_source.json"

# asset_key -> source spec. Order matches ASSET_NAMES everywhere else.
SOURCES = {
    "Equity_LargeCap":      {"kind": "yfinance", "ticker": "^NSEI", "label": "NIFTY 50 index"},
    "Equity_MidCap":        {"kind": "yfinance", "ticker": "^NSEMDCP50", "label": "NIFTY MIDCAP 50 index"},
    "Equity_SmallCap":      {"kind": "yfinance", "ticker": "NIFTYSMLCAP250.NS", "label": "NIFTY SMALLCAP 250 index"},
    "International_Equity": {"kind": "yfinance", "ticker": "MON100.NS", "label": "Motilal Oswal Nasdaq-100 ETF (INR)"},
    "Debt_ShortTerm":       {"kind": "mfapi", "scheme_code": 100851, "label": "Nippon India Liquid Fund - Growth NAV"},
    "Gold":                 {"kind": "yfinance", "ticker": "GOLDBEES.NS", "label": "Nippon India Gold BeES ETF"},
    "Silver":               {"kind": "fx_product", "tickers": ["SI=F", "USDINR=X"], "label": "COMEX silver futures x USD/INR"},
    "REIT":                 {"kind": "yfinance", "ticker": "EMBASSY.NS", "label": "Embassy Office Parks REIT"},
    "Fixed_Deposit":        {"kind": "assumption", "label": "Flat assumed FD rate"},
}

FIXED_DEPOSIT_ANNUAL_RATE = 0.065

# A daily move this large in a liquid-fund NAV can only be a face-value
# rescale (e.g. Rs 10 -> Rs 1000 units in 2012), never a real return.
NAV_RESCALE_THRESHOLD = 0.5


def _drop_bad_ticks(close: pd.Series) -> pd.Series:
    """
    Remove daily prices more than 3x away from their 5-day median. Yahoo
    leaves unit splits unadjusted for a day or two (GOLDBEES 1:100 in Dec 2019
    showed -99% then +9900%; MON100 1:10 in Jun 2021). Monthly sampling happened
    to hide these; weekly returns exposed them as 2000%+ volatility.
    """
    ratio = close / close.rolling(5, center=True, min_periods=1).median()
    return close[(ratio > 1 / 3) & (ratio < 3)]


def _yf_close(ticker: str) -> pd.Series:
    hist = yf.Ticker(ticker).history(period="max")
    if hist.empty:
        raise ValueError(f"No data returned for ticker {ticker!r}")
    close = hist["Close"].tz_localize(None).dropna()
    close.index = close.index.normalize()
    return _drop_bad_ticks(close[close > 0])


def _mfapi_nav(scheme_code: int) -> pd.Series:
    resp = requests.get(f"https://api.mfapi.in/mf/{scheme_code}", timeout=30)
    resp.raise_for_status()
    data = resp.json()["data"]
    nav = pd.Series({pd.to_datetime(d["date"], dayfirst=True): float(d["nav"]) for d in data}).sort_index()
    nav = nav[nav > 0]
    daily = nav.pct_change().dropna()
    daily = daily[daily.abs() < NAV_RESCALE_THRESHOLD]
    return (1 + daily).cumprod()


def _price_series(spec: dict) -> pd.Series:
    """Daily price (or NAV / price index) for one asset."""
    if spec["kind"] == "yfinance":
        return _yf_close(spec["ticker"])
    if spec["kind"] == "mfapi":
        return _mfapi_nav(spec["scheme_code"])
    if spec["kind"] == "fx_product":
        a, b = (_yf_close(t) for t in spec["tickers"])
        joined = pd.concat([a, b], axis=1, join="inner").dropna()
        return joined.iloc[:, 0] * joined.iloc[:, 1]
    raise ValueError(f"Unsupported source kind {spec['kind']!r}")


def _last_complete_month_end() -> pd.Timestamp:
    return pd.Timestamp.today().normalize().to_period("M").start_time - pd.Timedelta(days=1)


def _returns(prices: pd.Series, freq: str) -> pd.Series:
    # Drop the in-progress month so a 1-day partial period isn't treated as a full return.
    cutoff = _last_complete_month_end()
    prices = prices[prices.index <= cutoff]
    out = prices.resample(freq).last().pct_change().dropna()
    return out[out.index <= cutoff]


def fetch_and_save() -> dict:
    """Fetch every asset's real series, write monthly + weekly returns and a manifest."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    monthly: dict[str, pd.Series] = {}
    weekly: dict[str, pd.Series] = {}
    ranges: dict[str, dict] = {}
    failures: list[str] = []

    for asset, spec in SOURCES.items():
        if spec["kind"] == "assumption":
            continue
        try:
            prices = _price_series(spec)
            m = _returns(prices, "ME")
            monthly[asset] = m
            weekly[asset] = _returns(prices, "W-FRI")
            ranges[asset] = {
                "source": spec["label"],
                "kind": spec["kind"],
                "id": spec.get("ticker") or spec.get("scheme_code") or "+".join(spec.get("tickers", [])),
                "start": m.index[0].strftime("%Y-%m-%d"),
                "end": m.index[-1].strftime("%Y-%m-%d"),
                "months": len(m),
            }
            print(f"  {asset:22s} {spec['label']:42s} {len(m):4d} months  "
                  f"{m.index[0].date()} .. {m.index[-1].date()}")
        except Exception as e:
            failures.append(f"{asset} ({spec['label']}): {e}")
            print(f"  {asset:22s} {spec['label']:42s} FAILED: {e}")

    if failures:
        raise RuntimeError("Failed to fetch real data for: " + "; ".join(failures))

    fd_monthly = (1 + FIXED_DEPOSIT_ANNUAL_RATE) ** (1 / 12) - 1
    fd_weekly = (1 + FIXED_DEPOSIT_ANNUAL_RATE) ** (1 / 52) - 1

    df = pd.concat(monthly, axis=1, sort=True)
    df["Fixed_Deposit"] = fd_monthly
    df = df[list(SOURCES)]
    df.to_csv(CSV_PATH)

    dfw = pd.concat(weekly, axis=1, sort=True)
    dfw["Fixed_Deposit"] = fd_weekly
    dfw = dfw[list(SOURCES)]
    dfw.to_csv(WEEKLY_CSV_PATH)

    common_start = max(r["start"] for r in ranges.values())
    common_end = min(r["end"] for r in ranges.values())

    manifest = {
        "type": "real_historical",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "tickers": {a: r["id"] for a, r in ranges.items()},
        "per_asset_range": ranges,
        "common_overlap_window": {
            "start": common_start,
            "end": common_end,
            "note": (
                "Window where every asset has real data. Each asset still uses its "
                "full own history for its mean return; covariances use pairwise "
                "overlapping weekly returns."
            ),
        },
        "frequencies": {
            "monthly": "asset_returns.csv — expected returns and the XGBoost predictor",
            "weekly": "asset_returns_weekly.csv — covariance matrix (~4.3x more observations than monthly)",
        },
        "fixed_deposit_note": (
            f"Fixed_Deposit has no market price series (FDs aren't traded) — "
            f"assumed flat {FIXED_DEPOSIT_ANNUAL_RATE:.1%} annual. The only "
            f"assumption-based column; all others are real market data."
        ),
    }
    with open(MANIFEST_PATH, "w") as fh:
        json.dump(manifest, fh, indent=2)
    return manifest


if __name__ == "__main__":
    print("Fetching real historical prices for the 9-asset universe...\n")
    manifest = fetch_and_save()
    print(f"\nSaved {CSV_PATH.name}, {WEEKLY_CSV_PATH.name}, {MANIFEST_PATH.name}")
    print(f"Common overlap window: {manifest['common_overlap_window']['start']} .. "
          f"{manifest['common_overlap_window']['end']}")
