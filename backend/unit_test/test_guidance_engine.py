import os
import sys


BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from guidance_engine import PersonalizedGuidanceEngine


def _sample_data(**overrides):
    data = {
        "income": 100000,
        "rent": 30000,
        "food": 12000,
        "travel": 6000,
        "shopping": 9000,
        "emi": 18000,
        "savings": 25000,
    }
    data.update(overrides)
    return data


def _sample_patterns(**overrides):
    patterns = {
        "expense_ratio": 0.75,
        "savings_ratio": 0.25,
        "emi_ratio": 0.18,
        "breakdown": {
            "rent": 30.0,
            "food": 12.0,
            "travel": 6.0,
            "shopping": 9.0,
            "emi": 18.0,
            "savings": 25.0,
        },
    }
    patterns.update(overrides)
    return patterns


def test_guidance_schema_is_backward_compatible():
    guidance = PersonalizedGuidanceEngine.generate_guidance(
        _sample_data(), 68, _sample_patterns()
    )

    assert set(guidance.keys()) == {"recommendations", "strengths", "warnings"}
    assert isinstance(guidance["recommendations"], list)
    assert isinstance(guidance["strengths"], list)
    assert isinstance(guidance["warnings"], list)


def test_guidance_reacts_to_higher_risk_profile():
    base = PersonalizedGuidanceEngine.generate_guidance(
        _sample_data(), 68, _sample_patterns()
    )
    risky = PersonalizedGuidanceEngine.generate_guidance(
        _sample_data(savings=1000, emi=48000),
        42,
        _sample_patterns(savings_ratio=0.01, emi_ratio=0.48, expense_ratio=0.92),
    )

    assert len(risky["warnings"]) >= len(base["warnings"])
    assert len(risky["recommendations"]) >= 1


def test_investment_schema_is_backward_compatible():
    inv = PersonalizedGuidanceEngine.suggest_investments(
        68, _sample_data(), _sample_patterns()
    )

    assert set(inv.keys()) == {"eligible", "suggestions", "message", "advice"}
    assert isinstance(inv["eligible"], bool)
    assert isinstance(inv["suggestions"], list)
    assert isinstance(inv["message"], str)
    assert isinstance(inv["advice"], str)


def test_investment_not_eligible_when_financials_weak():
    inv = PersonalizedGuidanceEngine.suggest_investments(
        30,
        _sample_data(savings=0, emi=55000),
        _sample_patterns(savings_ratio=0.0, emi_ratio=0.55, expense_ratio=0.95),
    )

    assert inv["eligible"] is False
    assert len(inv["suggestions"]) >= 1
    assert any(s.get("suitable") is False for s in inv["suggestions"])


def test_investment_eligible_when_financials_good():
    inv = PersonalizedGuidanceEngine.suggest_investments(
        78,
        _sample_data(savings=35000, emi=12000),
        _sample_patterns(savings_ratio=0.35, emi_ratio=0.12, expense_ratio=0.53),
    )

    assert inv["eligible"] is True
    assert len(inv["suggestions"]) >= 2
    assert all("allocation" in s for s in inv["suggestions"])
