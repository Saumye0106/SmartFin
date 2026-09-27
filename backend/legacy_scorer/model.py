"""
Loads the legacy 8-factor GradientBoosting financial health model at import
time, so all scorer routes/helpers share one in-memory model instance.
"""

import os

import joblib

print("Loading ML model...")
# Get the absolute path to the data directory for enhanced model
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data')

# Load enhanced model
model_data = joblib.load(os.path.join(DATA_DIR, 'enhanced_model.pkl'))
model = model_data['model']
feature_names = model_data['feature_cols']
model_metadata = model_data['metrics']
print(f"Model loaded: {model_data['model_type']}")
print(f"Model R2 Score: {model_metadata['r2_test']:.4f} (95.85% - Enhanced 8-Factor Model)")
