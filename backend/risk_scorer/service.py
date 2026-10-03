"""
Turn SmartFin's own data into a risk assessment.

Form/budget fields used: income, emi, rent, and optionally age, times_late,
times_seriously_late, card_balance, card_limit. For a logged-in user, age, the
payment counts and saved card details come from their records unless the
request states them.

Every assessment carries a confidence level, because the model is only as good
as the evidence it is given:
  good          payment history or credit-card data is known (AUC 0.83-0.86)
  limited       only the debt ratio is known (AUC about 0.66)
  insufficient  none of the above: no score is returned
"""

from __future__ import annotations

import logging
import math
import sqlite3
from datetime import date, datetime, timedelta

from risk_scorer.features import build_features
from risk_scorer.model import get_model

logger = logging.getLogger(__name__)

HISTORY_WINDOW_DAYS = 730  # the model's payment counts cover the last two years

MISSING_HINTS = {
    "payment_history": "Record loan payments in SmartFin, or enter your late and missed payments for the last 2 years (0 if none).",
    "card": "Add your credit-card limit and current balance, if you have a card.",
    "debt_ratio": "Enter your monthly income, rent and EMIs.",
}
CONFIDENCE_NOTES = {
    "good": None,
    "limited": "Low confidence: this is based on your age and debt ratio only. Payment history or credit-card "
               "data is what the model relies on most.",
    "insufficient": "Not enough data to score. The model would be guessing from your age alone.",
}


def user_history(conn, user_id) -> dict:
    """Age, 2-year late/missed payment counts and saved card details for a user, from SmartFin's own records."""
    history = {}
    try:
        row = conn.execute("SELECT age FROM users_profile WHERE user_id = ?", (user_id,)).fetchone()
        if row and row[0]:
            history["age"] = row[0]
        since = (date.today() - timedelta(days=HISTORY_WINDOW_DAYS)).isoformat()
        counts = dict(conn.execute(
            """SELECT p.payment_status, COUNT(*) FROM loan_payments p
               JOIN loans l ON l.loan_id = p.loan_id
               WHERE l.user_id = ? AND l.deleted_at IS NULL AND p.payment_date >= ?
               GROUP BY p.payment_status""", (user_id, since)).fetchall())
        # SmartFin records 'late' and 'missed'; the model's two inputs are 30-89 days late and 90+ days late.
        history["times_late"] = counts.get("late", 0)
        history["times_seriously_late"] = counts.get("missed", 0)
        history["payments_on_record"] = sum(counts.values())
    except Exception as e:  # a missing table must not take the score endpoint down
        logger.warning("risk_scorer: user history lookup failed: %s", e)
    try:
        # Credit-report accounts that did not become SmartFin loans (cards, closed loans, loans missing details).
        # Accounts that did are already counted through their loan_payments above.
        since_month = (date.today() - timedelta(days=HISTORY_WINDOW_DAYS)).strftime("%Y-%m")
        late, missed, months = conn.execute(
            """SELECT COALESCE(SUM(CASE WHEN h.dpd >= 30 AND h.dpd < 90 THEN 1 ELSE 0 END), 0),
                      COALESCE(SUM(CASE WHEN h.dpd >= 90 THEN 1 ELSE 0 END), 0), COUNT(*)
               FROM credit_account_history h JOIN credit_accounts a ON a.id = h.account_id
               WHERE a.user_id = ? AND a.loan_id IS NULL AND h.month >= ?""", (user_id, since_month)).fetchone()
        if months:
            history["times_late"] = history.get("times_late", 0) + late
            history["times_seriously_late"] = history.get("times_seriously_late", 0) + missed
            history["payments_on_record"] = history.get("payments_on_record", 0) + months
    except sqlite3.OperationalError:
        pass  # credit report tables not created yet
    history.update({k: v for k, v in get_risk_profile(conn, user_id).items() if v is not None})
    return history


def get_risk_profile(conn, user_id) -> dict:
    try:
        row = conn.execute("SELECT card_limit, card_balance FROM risk_profile WHERE user_id = ?", (user_id,)).fetchone()
    except Exception as e:
        logger.warning("risk_scorer: risk_profile lookup failed: %s", e)
        row = None
    return {"card_limit": row[0] if row else None, "card_balance": row[1] if row else None}


def save_risk_profile(conn, user_id, card_limit, card_balance) -> dict:
    """Store (or clear, with None) the user's card limit and balance. Raises ValueError on bad input."""
    def clean(v, name, allow_zero):
        if v is None or v == "":
            return None
        try:
            v = float(v)
        except (TypeError, ValueError):
            raise ValueError(f"{name} must be a number")
        if not math.isfinite(v) or v < 0 or (v == 0 and not allow_zero):
            raise ValueError(f"{name} must be {'zero or more' if allow_zero else 'greater than zero'}")
        return v

    limit = clean(card_limit, "card_limit", allow_zero=False)
    balance = clean(card_balance, "card_balance", allow_zero=True)
    if limit is None:
        balance = None  # a balance means nothing without a limit
    conn.execute(
        """INSERT INTO risk_profile (user_id, card_limit, card_balance, updated_at) VALUES (?, ?, ?, ?)
           ON CONFLICT(user_id) DO UPDATE SET card_limit = excluded.card_limit,
               card_balance = excluded.card_balance, updated_at = excluded.updated_at""",
        (user_id, limit, balance, datetime.now().isoformat()))
    conn.commit()
    return {"card_limit": limit, "card_balance": balance}


def features_from_request(data: dict, history: dict | None = None) -> dict:
    history = history or {}

    def pick(key, default=None):
        return data[key] if data.get(key) is not None else history.get(key, default)

    return build_features(
        age=pick("age"),
        monthly_income=data.get("income"),
        monthly_debt_payments=data.get("emi", 0),
        # Housing only, not all spending: see the debt_ratio note in assess_request.
        monthly_living_costs=data.get("rent", 0),
        times_late=pick("times_late", 0),
        times_seriously_late=pick("times_seriously_late", 0),
        card_balance=pick("card_balance"),
        card_limit=pick("card_limit"),
    )


def _confidence(data: dict, history: dict | None, features: dict) -> tuple[str, list[str]]:
    history = history or {}
    stated = data.get("times_late") is not None or data.get("times_seriously_late") is not None
    known = {
        "payment_history": stated or history.get("payments_on_record", 0) > 0,
        "card": not math.isnan(features["utilization"]),
        "debt_ratio": not math.isnan(features["debt_ratio"]),
    }
    level = "good" if known["payment_history"] or known["card"] else "limited" if known["debt_ratio"] else "insufficient"
    return level, [k for k, v in known.items() if not v]


def assess_request(data: dict, history: dict | None = None) -> dict:
    """
    debt_ratio = (EMI + rent) / income. The training data defines it as "monthly debt
    payments, alimony, living costs" over gross income, but its median is 0.37, far
    too low to include all household spending, so in practice it is debt plus housing.
    """
    features = features_from_request(data, history)
    out = get_model().assess(features)
    out["features"] = {k: (None if v != v else round(float(v), 4)) for k, v in features.items()}  # NaN -> None
    out["history_source"] = "smartfin_records" if history and "times_late" in history else "request_only"
    out["payments_on_record"] = (history or {}).get("payments_on_record", 0)

    level, missing = _confidence(data, history, features)
    out["confidence"] = level
    out["confidence_note"] = CONFIDENCE_NOTES[level]
    out["missing"] = [{"input": k, "hint": MISSING_HINTS[k]} for k in missing]
    if level == "insufficient":
        # Without any evidence the number would be age alone dressed up as a score.
        out["score"] = None
        out["risk_probability"] = None
        out["drivers"] = []
    return out


def assess_user(conn, user_id) -> dict:
    """
    Assess a user purely from what SmartFin already holds, no form:
    income from the latest budget with income, EMI from active loans, rent from
    the detected recurring rent (else the latest month's rent expenses).
    """
    today = date.today().isoformat()
    sources = {}

    row = conn.execute(
        "SELECT month, monthly_income FROM monthly_budgets WHERE user_id = ? AND monthly_income > 0 "
        "ORDER BY month DESC LIMIT 1", (user_id,)).fetchone()
    income = float(row[1]) if row else None
    sources["income"] = f"budget {row[0]}" if row else None

    emi = conn.execute(
        "SELECT COALESCE(SUM(monthly_emi), 0) FROM loans WHERE user_id = ? AND deleted_at IS NULL "
        "AND loan_maturity_date >= ?", (user_id, today)).fetchone()[0]
    sources["emi"] = "active loans" if emi else None

    rent = 0.0
    try:
        from statement_import.service import recurring_summary
        rent = sum(r["monthly_equivalent"] for r in recurring_summary(conn, user_id)["recurring"]
                   if r["kind"] == "rent" and r["active"])
        if rent:
            sources["rent"] = "recurring payments"
    except Exception as e:
        logger.warning("risk_scorer: recurring rent lookup failed: %s", e)
    if not rent:
        row = conn.execute(
            "SELECT substr(expense_date, 1, 7) AS m, SUM(amount) FROM expense_entries "
            "WHERE user_id = ? AND category = 'rent' GROUP BY m ORDER BY m DESC LIMIT 1", (user_id,)).fetchone()
        rent = float(row[1]) if row else 0.0
        sources["rent"] = f"expenses {row[0]}" if row else None

    out = assess_request({"income": income, "emi": float(emi or 0), "rent": rent}, user_history(conn, user_id))
    out["sources"] = sources
    return out


def model_summary() -> dict:
    meta = get_model().metadata
    m = meta["metrics"]
    return {
        "model_type": meta["model_type"],
        "trained_on": f"{meta['n_rows']:,} real borrowers ({meta['data_source']['name']})",
        "label": meta["data_source"]["label"],
        "auc": m["xgb"]["auc"],
        "baseline_auc": m["baseline"]["auc"],
        "auc_without_card_data": m["xgb_no_util"]["auc"],
        "validation": meta["validation"],
        "caveats": meta["caveats"],
    }
