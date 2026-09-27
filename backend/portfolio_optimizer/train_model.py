"""
train_model.py — One-time training script for the Portfolio Return Predictor.

Run this from the backend/ directory:
    python portfolio_optimizer/train_model.py

Outputs:
    portfolio_optimizer/models/return_predictor.pkl
    portfolio_optimizer/models/scaler.pkl
    portfolio_optimizer/models/model_metadata.json
    portfolio_optimizer/data/asset_returns.csv
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from portfolio_optimizer.data_loader import load_or_generate_data, get_asset_summary
from portfolio_optimizer.return_predictor import train

if __name__ == "__main__":
    print(">> Loading / generating asset return data...")
    df = load_or_generate_data()
    print(f"   Data shape: {df.shape}  ({df.index[0].date()} -> {df.index[-1].date()})")

    summary = get_asset_summary(df)
    print("\n-- Annualised stats:")
    for asset, mu in summary["mean_annual"].items():
        vol = summary["vol_annual"][asset]
        print(f"   {asset:22s}: mu={mu:.1%}  sigma={vol:.1%}")

    print("\n>> Training XGBoost models (one per asset class)...")
    metadata = train(df)

    print(f"\n>> Training complete!")
    print(f"   Algorithm     : {metadata['algorithm']}")
    print(f"   Overall R2    : {metadata['overall_r2']:.4f}")
    print(f"   Avg RMSE (ann): {metadata['overall_rmse_annual_pct']:.3f}%")
    print(f"\n   Per-asset metrics:")
    for asset, m in metadata["per_asset_metrics"].items():
        print(f"   {asset:22s}: R2={m['r2']:.4f}  RMSE={m['rmse_annual_pct']:.3f}%")

    print(f"\n   Top features:")
    for item in metadata["top_features"][:5]:
        print(f"   {item['feature']:35s}: {item['importance']:.4f}")

    print("\n>> Artifacts saved to portfolio_optimizer/models/")
