"""Risk scorer: feature building, the trained model's guarantees, and SmartFin history lookup."""

import math
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from risk_scorer.features import DEFAULT_AGE, FEATURES, RAW_COLUMNS, age_band, build_features, prepare_training_frame
from risk_scorer.model import get_model
from risk_scorer.migrations import create_tables
from risk_scorer.service import assess_request, assess_user, get_risk_profile, save_risk_profile, user_history

BASE = dict(age=26, monthly_income=60000, monthly_debt_payments=12000, monthly_living_costs=12000)


# ── Features ─────────────────────────────────────────────────────────────────

def test_training_frame_cleans_the_known_quirks():
    raw = pd.DataFrame([
        ["No", 0.2, 40, 0, 0.30, 5000.0, 8, 0, 1, 0, 0.0],
        ["Yes", 0.9, 30, 2, 0.50, 3000.0, 4, 1, 0, 1, 2.0],
        ["No", 0.1, 50, 98, 0.10, 4000.0, 5, 98, 0, 98, 0.0],   # 98 = "unknown", not 98 late payments
        ["No", 0.1, 45, 0, 1500.0, np.nan, 5, 0, 0, 0, 0.0],    # no income: DebtRatio holds an absolute amount
        ["No", 0.1, 0, 0, 0.2, 4000.0, 5, 0, 0, 0, 0.0],        # age 0 is a data error
    ], columns=RAW_COLUMNS)
    X, y = prepare_training_frame(raw)
    assert list(X.columns) == FEATURES and len(X) == 4 and y.tolist() == [0, 1, 0, 0]
    assert X.loc[1, "times_late"] == 3 and X.loc[1, "times_seriously_late"] == 1 and X.loc[1, "utilization"] == 0.9
    assert math.isnan(X.loc[2, "times_late"]) and math.isnan(X.loc[2, "times_seriously_late"])
    assert math.isnan(X.loc[3, "debt_ratio"])


def test_build_features():
    f = build_features(**BASE, times_late=1, card_balance=20000, card_limit=100000)
    assert f == {"age": 26.0, "debt_ratio": 0.4, "times_late": 1.0, "times_seriously_late": 0.0, "utilization": 0.2}
    # no card, no income, no age: unknowns stay unknown, except age which the model can't take as missing
    f = build_features()
    assert f["age"] == DEFAULT_AGE and math.isnan(f["debt_ratio"]) and math.isnan(f["utilization"])
    assert math.isnan(build_features(card_balance=500, card_limit=0)["utilization"])
    assert build_features(age="abc", monthly_income="x")["age"] == DEFAULT_AGE


@pytest.mark.parametrize("age,band", [(18, "18-29"), (29, "18-29"), (30, "30-39"), (59, "50-59"), (60, "60+"), (85, "60+")])
def test_age_band(age, band):
    assert age_band(age) == band


# ── The trained model ────────────────────────────────────────────────────────

def test_model_beats_the_baseline_on_held_out_data():
    m = get_model().metadata["metrics"]
    assert m["xgb"]["auc"] > m["baseline"]["auc"] + 0.01
    assert m["xgb_no_util"]["auc"] > m["baseline_no_util"]["auc"]
    assert m["xgb"]["brier"] < m["baseline"]["brier"] < m["always_base_rate"]["brier"]


def test_model_is_calibrated():
    for arm in ("with_utilization", "without_utilization"):
        for row in get_model().metadata["calibration"][arm]:
            assert abs(row["predicted"] - row["observed"]) <= max(0.015, 0.15 * row["observed"]), (arm, row)


@pytest.mark.parametrize("field,values", [
    ("times_late", [0, 1, 2, 4]),
    ("times_seriously_late", [0, 1, 3]),
    ("monthly_debt_payments", [0, 12000, 30000, 60000]),
    ("card_balance", [0, 20000, 60000, 100000]),
])
def test_risk_never_falls_when_things_get_worse(field, values):
    model = get_model()
    extra = {"card_limit": 100000} if field == "card_balance" else {}
    risks = [model.probability(build_features(**{**BASE, **extra, field: v})) for v in values]
    assert risks == sorted(risks) and risks[-1] > risks[0]


def test_score_and_drivers():
    model = get_model()
    clean = model.assess(build_features(**BASE))
    late = model.assess(build_features(**BASE, times_late=2, times_seriously_late=1))
    assert 0 <= late["score"] < clean["score"] <= 100
    assert late["risk_probability"] > 3 * clean["risk_probability"]
    assert clean["age_band"] == "18-29" and clean["inputs_missing"] == ["utilization"]
    top = late["drivers"][0]
    assert top["feature"] in ("times_late", "times_seriously_late") and top["direction"] == "raises risk"
    assert {d["feature"] for d in late["drivers"]} == set(FEATURES)
    assert [d["actionable"] for d in late["drivers"] if d["feature"] == "age"] == [False]


def test_score_is_relative_to_the_users_age_band():
    """Same record, different age: the younger user has the higher risk but isn't penalised in the score for age alone."""
    model = get_model()
    young = model.assess(build_features(**{**BASE, "age": 24}))
    older = model.assess(build_features(**{**BASE, "age": 55}))
    assert young["risk_probability"] > older["risk_probability"]
    assert abs(young["score"] - older["score"]) < 35


# ── History from SmartFin's own tables ───────────────────────────────────────

@pytest.fixture
def conn(tmp_path):
    c = sqlite3.connect(tmp_path / "t.db")
    c.executescript("""
        CREATE TABLE users_profile (user_id INTEGER PRIMARY KEY, age INTEGER);
        CREATE TABLE loans (loan_id TEXT PRIMARY KEY, user_id INTEGER, deleted_at TEXT);
        CREATE TABLE loan_payments (payment_id TEXT PRIMARY KEY, loan_id TEXT, payment_date TEXT, payment_status TEXT);
        INSERT INTO users_profile VALUES (1, 27);
        INSERT INTO loans VALUES ('a', 1, NULL), ('gone', 1, '2026-01-01'), ('other', 2, NULL);
    """)
    today = date.today()
    rows = [("p1", "a", today - timedelta(days=30), "on-time"), ("p2", "a", today - timedelta(days=60), "late"),
            ("p3", "a", today - timedelta(days=90), "late"), ("p4", "a", today - timedelta(days=120), "missed"),
            ("p5", "a", today - timedelta(days=900), "missed"),      # older than two years
            ("p6", "gone", today - timedelta(days=10), "missed"),    # deleted loan
            ("p7", "other", today - timedelta(days=10), "late")]     # someone else
    c.executemany("INSERT INTO loan_payments VALUES (?, ?, ?, ?)", [(a, b, d.isoformat(), s) for a, b, d, s in rows])
    c.commit()
    yield c
    c.close()


def test_user_history_counts_two_years_of_own_payments(conn):
    assert user_history(conn, 1) == {"age": 27, "times_late": 2, "times_seriously_late": 1, "payments_on_record": 4}
    assert user_history(conn, 99) == {"times_late": 0, "times_seriously_late": 0, "payments_on_record": 0}


def test_user_history_survives_a_missing_table(tmp_path):
    c = sqlite3.connect(tmp_path / "empty.db")
    assert user_history(c, 1) == {}
    c.close()


def test_assess_request_uses_history_unless_the_request_says_otherwise(conn):
    form = {"income": 50000, "emi": 10000, "rent": 15000, "food": 8000}
    history = user_history(conn, 1)
    a = assess_request(form, history)
    assert a["features"] == {"age": 27.0, "debt_ratio": 0.5, "times_late": 2.0, "times_seriously_late": 1.0, "utilization": None}
    assert a["history_source"] == "smartfin_records" and a["payments_on_record"] == 4
    # food/shopping are not model inputs: only EMI and housing enter the debt ratio
    assert assess_request({**form, "food": 30000}, history)["score"] == a["score"]
    stated = assess_request({**form, "times_late": 0, "times_seriously_late": 0, "age": 40}, history)
    assert stated["features"]["times_late"] == 0.0 and stated["features"]["age"] == 40.0 and stated["score"] > a["score"]
    assert assess_request(form)["history_source"] == "request_only"


# ── Confidence: no score without evidence ────────────────────────────────────

def test_no_score_when_the_model_would_only_have_age():
    a = assess_request({"income": 0, "emi": 0, "rent": 0, "age": 21})
    assert a["confidence"] == "insufficient" and a["score"] is None and a["risk_probability"] is None and a["drivers"] == []
    assert [m["input"] for m in a["missing"]] == ["payment_history", "card", "debt_ratio"]
    assert all(m["hint"] for m in a["missing"])
    # an empty payment record in SmartFin is not evidence of a clean one
    assert assess_request({"income": 0}, {"times_late": 0, "times_seriously_late": 0, "payments_on_record": 0})["score"] is None


@pytest.mark.parametrize("data,history,level,missing", [
    ({"income": 50000, "emi": 10000, "rent": 15000}, None, "limited", ["payment_history", "card"]),
    ({"income": 50000, "emi": 10000, "times_late": 0, "times_seriously_late": 0}, None, "good", ["card"]),
    ({"income": 0, "card_limit": 100000, "card_balance": 20000}, None, "good", ["payment_history", "debt_ratio"]),
    ({"income": 50000, "emi": 10000}, {"times_late": 1, "times_seriously_late": 0, "payments_on_record": 6}, "good", ["card"]),
    ({"income": 50000, "emi": 10000}, {"card_limit": 100000, "card_balance": 5000}, "good", ["payment_history"]),
])
def test_confidence_levels(data, history, level, missing):
    a = assess_request(data, history)
    assert a["confidence"] == level and [m["input"] for m in a["missing"]] == missing
    assert a["score"] is not None and 0 <= a["score"] <= 100
    assert (a["confidence_note"] is None) == (level == "good")


# ── Saved card details and scoring from the user's own records ──────────────

@pytest.fixture
def records(tmp_path):
    db = tmp_path / "r.db"
    c = sqlite3.connect(db)
    c.executescript("""
        CREATE TABLE users_profile (user_id INTEGER PRIMARY KEY, age INTEGER);
        CREATE TABLE loans (loan_id TEXT PRIMARY KEY, user_id INTEGER, monthly_emi REAL, loan_maturity_date TEXT, deleted_at TEXT);
        CREATE TABLE loan_payments (payment_id TEXT PRIMARY KEY, loan_id TEXT, payment_date TEXT, payment_status TEXT);
        CREATE TABLE monthly_budgets (id TEXT PRIMARY KEY, user_id INTEGER, month TEXT, monthly_income REAL);
        CREATE TABLE expense_entries (id TEXT PRIMARY KEY, user_id INTEGER, expense_date TEXT, category TEXT, amount REAL);
        INSERT INTO users_profile VALUES (1, 28), (2, 21);
        INSERT INTO loans VALUES ('live', 1, 8000, '2099-01-01', NULL), ('ended', 1, 5000, '2020-01-01', NULL),
                                 ('deleted', 1, 7000, '2099-01-01', '2026-01-01');
        INSERT INTO monthly_budgets VALUES ('b1', 1, '2026-08', 60000), ('b2', 1, '2026-09', 0), ('b0', 1, '2026-05', 40000);
        INSERT INTO expense_entries VALUES ('e1', 1, '2026-08-03', 'rent', 12000), ('e2', 1, '2026-09-03', 'rent', 13000),
                                           ('e3', 1, '2026-09-09', 'food', 9000);
    """)
    c.execute("INSERT INTO loan_payments VALUES ('p1', 'live', ?, 'on-time')", ((date.today() - timedelta(days=20)).isoformat(),))
    c.commit()
    c.close()
    create_tables(str(db))
    c = sqlite3.connect(db)
    c.row_factory = sqlite3.Row
    yield c
    c.close()


def test_risk_profile_round_trip_and_validation(records):
    assert get_risk_profile(records, 1) == {"card_limit": None, "card_balance": None}
    assert save_risk_profile(records, 1, "100000", 25000) == {"card_limit": 100000.0, "card_balance": 25000.0}
    assert save_risk_profile(records, 1, 150000, 0) == {"card_limit": 150000.0, "card_balance": 0.0}   # update, not duplicate
    assert records.execute("SELECT COUNT(*) FROM risk_profile").fetchone()[0] == 1
    assert get_risk_profile(records, 2) == {"card_limit": None, "card_balance": None}                # per user
    assert save_risk_profile(records, 1, None, 5000) == {"card_limit": None, "card_balance": None}    # cleared
    for limit, balance in ((0, 10), (-5, 10), ("abc", 1), (1000, -1), (float("inf"), 1)):
        with pytest.raises(ValueError):
            save_risk_profile(records, 1, limit, balance)


def test_assess_user_reads_income_emi_rent_and_card_from_records(records):
    save_risk_profile(records, 1, 100000, 30000)
    a = assess_user(records, 1)
    # income: latest budget with income (Aug, not the empty Sep); EMI: only the live loan; rent: latest month's rent expenses
    assert a["sources"] == {"income": "budget 2026-08", "emi": "active loans", "rent": "expenses 2026-09"}
    assert a["features"] == {"age": 28.0, "debt_ratio": round((8000 + 13000) / 60000, 4), "times_late": 0.0,
                             "times_seriously_late": 0.0, "utilization": 0.3}
    assert a["confidence"] == "good" and a["missing"] == [] and a["payments_on_record"] == 1 and a["score"] is not None


def test_assess_user_with_nothing_on_record_gives_no_score(records):
    a = assess_user(records, 2)
    assert a["score"] is None and a["confidence"] == "insufficient"
    assert a["sources"] == {"income": None, "emi": None, "rent": None}


# ── What-if and classification with no score ─────────────────────────────────

def test_whatif_and_classification_handle_a_missing_score():
    from legacy_scorer.service import classify_score, compare_scores

    assert classify_score(None)["category"] == "Not enough data"
    form = {"income": 50000, "emi": 10000, "rent": 15000}
    better = compare_scores(form, {**form, "emi": 2000})
    assert better["impact"] == "positive" and better["score_change"] > 0 and better["confidence"] == "limited"
    worse = compare_scores(form, {**form, "emi": 30000})
    assert worse["impact"] == "negative" and worse["score_change"] < 0
    none = compare_scores({"income": 0}, {"income": 0, "emi": 500})
    assert none["current_score"] is None and none["score_change"] is None and none["impact"] == "neutral"
    assert "Not enough data" in none["message"] and none["current_classification"]["category"] == "Not enough data"

