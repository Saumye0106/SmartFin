"""
Model handle for the health-score routes.

The score used to come from enhanced_model.pkl, a GradientBoosting model
trained to copy an 8-factor formula. It now comes from risk_scorer: an
XGBoost model trained on real borrower outcomes (see risk_scorer/train_model.py).
The names below are kept because app.py and the routes import them.
"""

from risk_scorer.model import get_model
from risk_scorer.service import model_summary

risk_model = get_model()
model_metadata = risk_model.metadata
model_data = {'model_type': model_metadata['model_type']}
feature_names = model_metadata['features']

_summary = model_summary()
print(f"Risk model loaded: {_summary['model_type']}, trained on {_summary['trained_on']}")
print(f"Cross-validated AUC {_summary['auc']:.3f} (logistic baseline {_summary['baseline_auc']:.3f})")
