# ML — Training and Test Guide

This document explains how to generate a dataset, train the model, and run the project tests locally.

Prerequisites
- Python 3.11+ (virtualenv recommended)
- Activate the repo venv: `smartfin_exp.venv\Scripts\Activate.ps1` (Windows) or `source smartfin_exp.venv/Scripts/activate` (WSL)
- Install dependencies (if needed):

```powershell
.\smartfin_exp.venv\Scripts\pip.exe install -r requirements.txt
.\smartfin_exp.venv\Scripts\pip.exe install pandas numpy scikit-learn joblib matplotlib requests
```

Quickstart — synthetic dataset (for CI / local development)

```powershell
# Generate a synthetic dataset (creates data/smartfin_dataset.csv)
python ml/generate_synthetic_dataset.py

# Train model (writes artifacts to ml/)
python ml/train_model.py

# Run unit & integration tests (starts server in-process)
.\smartfin_exp.venv\Scripts\python.exe scripts/run_tests_with_server.py
```

Using a real dataset

- Place your CSV in `data/smartfin_dataset.csv` with the columns:
  `income, rent, food, travel, shopping, emi, savings, score`
- Or pass a custom path to the trainer:

```powershell
python ml/train_model.py --data path/to/your_dataset.csv --output-dir ml
```

Notes
- The training script supports `--data` and `--output-dir` flags.
- Tests and backend expect model artifacts in `ml/` (`financial_health_model.pkl`, `feature_names.pkl`, `model_metadata.pkl`).
- For production training, replace the synthetic dataset with your real, cleaned dataset before retraining.
