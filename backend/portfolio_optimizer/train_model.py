"""
train_model.py — One-time training script for the Portfolio Return Predictor.

Run this from the backend/ directory:
    python portfolio_optimizer/train_model.py               # train on whatever's cached
    python portfolio_optimizer/train_model.py --refresh-data # re-fetch real data first

Outputs:
    portfolio_optimizer/models/return_predictor.pkl
    portfolio_optimizer/models/scaler.pkl (per-asset scalers, see return_predictor.py)
    portfolio_optimizer/models/model_metadata.json
    portfolio_optimizer/data/asset_returns.csv
    portfolio_optimizer/data/data_source.json
"""

import sys
import os
import argparse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from portfolio_optimizer.data_loader import load_or_generate_data, get_asset_summary, get_data_source_info
from portfolio_optimizer.return_predictor import train

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh-data", action="store_true",
                         help="Re-fetch real market data via yfinance before training")
    args = parser.parse_args()

    data_source = get_data_source_info()
    needs_fetch = args.refresh_data or data_source["type"] != "real_historical"

    if needs_fetch:
        print(">> Fetching real market data via yfinance...")
        from portfolio_optimizer.fetch_real_data import fetch_and_save
        data_source = fetch_and_save()
        print()

    print(">> Loading asset return data...")
    df = load_or_generate_data()
    print(f"   Data shape: {df.shape}  ({df.index[0].date()} -> {df.index[-1].date()})")
    print(f"   Data source: {data_source['type']}")
    if data_source["type"] != "real_historical":
        print("   *** WARNING: training on synthetic fallback data, not real market history. ***")
        print("   *** Run with --refresh-data to fetch real historical returns. ***")

    summary = get_asset_summary(df)
    print("\n-- Annualised stats (full available history per asset; NaN-safe):")
    for asset, mu in summary["mean_annual"].items():
        vol = summary["vol_annual"][asset]
        print(f"   {asset:22s}: mu={mu:.1%}  sigma={vol:.1%}")

    print("\n>> Training XGBoost models (one per asset, each on its own available history)...")
    metadata = train(df)

    print(f"\n>> Training complete!")
    print(f"   Algorithm       : {metadata['algorithm']}")
    print(f"   Trained assets  : {len(metadata['trained_assets'])}/{metadata['n_assets']}")
    if metadata["skipped_assets"]:
        print(f"   Skipped (thin real history, using historical mean instead): "
              f"{', '.join(metadata['skipped_assets'])}")
    if metadata["overall_r2"] is not None:
        print(f"   Overall R2      : {metadata['overall_r2']:.4f}")
        print(f"   Avg RMSE (ann)  : {metadata['overall_rmse_annual_pct']:.3f}%")

    print(f"\n   Per-asset metrics:")
    for asset, m in metadata["per_asset_metrics"].items():
        if m["status"] == "trained":
            window = m["training_window"]
            print(f"   {asset:22s}: R2={m['r2']:.4f}  RMSE={m['rmse_annual_pct']:.3f}%  "
                  f"trained on {window['usable_rows']} months ({window['start']} .. {window['end']})")
        elif m["status"] == "constant_target":
            print(f"   {asset:22s}: constant target ({m['months_available']} months) -- "
                  f"nothing for a model to learn, predict() uses the historical mean directly")
        else:
            print(f"   {asset:22s}: insufficient real history "
                  f"({m['months_available']} months available -> {m['usable_rows']} usable "
                  f"rows after feature/target construction, need >= {m['min_required']}) -- "
                  f"predict() falls back to this asset's historical mean")

    if metadata["top_features"]:
        print(f"\n   Top features (averaged across trained assets):")
        for item in metadata["top_features"][:5]:
            print(f"   {item['feature']:12s}: {item['importance']:.4f}")

    print("\n>> Artifacts saved to portfolio_optimizer/models/ and portfolio_optimizer/data/")
