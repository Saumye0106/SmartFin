"""
SmartFin Behavioral Nudge Engine
Isolation Forest anomaly detection on user spending patterns.
"""
from .anomaly_detector import AnomalyDetector
from .feature_builder import FeatureBuilder
from .nudge_generator import NudgeGenerator

__all__ = ["AnomalyDetector", "FeatureBuilder", "NudgeGenerator"]
