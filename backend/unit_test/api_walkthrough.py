"""
Walk through the API as one user and print one line per call: name, HTTP status, and a digest of the response.

Run it against SQLite and against PostgreSQL and compare the output: the two must match line for line.

    python -X utf8 unit_test/api_walkthrough.py            # uses whatever DATABASE_URL / SMARTFIN_DATA_DIR say

Timestamps, ids and tokens are masked so the two runs are comparable. Not collected by pytest
(no test_ prefix); test_postgres.py runs it for both databases.
"""

import io
import json
import logging
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))
os.environ.setdefault("SMARTFIN_LOG_FILE", "")
os.environ.setdefault("SMARTFIN_AI_GUIDANCE_ENABLED", "false")

from app import app  # noqa: E402

logging.disable(logging.CRITICAL)
FIX = BACKEND / "unit_test" / "fixtures"
client = app.test_client()
UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
STAMP = re.compile(r"\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(\.\d+)?(\+00:00|Z)?")
VOLATILE_KEYS = {"access_token", "refresh_token", "token", "timestamp", "created_at", "updated_at", "calculated_at",
                 "imported_at", "generated_at", "fetched_at", "expires_at", "trained_at"}


def mask(value, key=None):
    if key in VOLATILE_KEYS:
        return "<volatile>"
    if isinstance(value, dict):
        return {k: mask(v, k) for k, v in sorted(value.items())}
    if isinstance(value, list):
        return [mask(v) for v in value]
    if isinstance(value, float):
        return round(value, 4)
    if isinstance(value, str):
        return STAMP.sub("<time>", UUID.sub("<uuid>", value))
    return value


state = {"headers": {}}


def call(name, method, path, body=None, files=None, show=None):
    kwargs = {"headers": state["headers"]}
    if files is not None:
        kwargs.update(data=files, content_type="multipart/form-data")
    elif body is not None:
        kwargs["json"] = body
    r = getattr(client, method)(path, **kwargs)
    data = r.get_json(silent=True)
    digest = json.dumps(mask(show(data) if (show and isinstance(data, (dict, list))) else data), sort_keys=True, default=str)
    print(f"{name:34} {r.status_code} {digest[:900]}")
    return data if data is not None else {}


def month_offset(n):
    d = date.today().replace(day=1)
    for _ in range(n):
        d = (d - timedelta(days=1)).replace(day=1)
    return d.strftime("%Y-%m")


EMAIL, PASSWORD = "walkthrough@example.com", "Str0ng!Passw0rd"
call("register", "post", "/register", {"email": EMAIL, "password": PASSWORD})
call("register again (duplicate)", "post", "/register", {"email": EMAIL, "password": PASSWORD})
call("login wrong password", "post", "/login", {"email": EMAIL, "password": "nope-nope"})
login = call("login", "post", "/login", {"email": EMAIL, "password": PASSWORD})
token = login.get("token") or login.get("access_token")
state["headers"] = {"Authorization": f"Bearer {token}"}
uid = login.get("user_id") or login.get("id") or (login.get("user") or {}).get("id")
call("protected", "get", "/protected")

# profile + goals
call("profile before create", "get", "/api/profile")
call("profile create", "post", "/api/profile/create", {"name": "Walk Through", "age": 27, "location": "Pune", "risk_tolerance": 6})
call("profile get", "get", "/api/profile")
call("profile update", "put", "/api/profile/update", {"age": 28, "location": "Mumbai"})
goal = call("goal create", "post", "/api/profile/goals", {
    "goal_type": "short-term", "target_amount": 150000, "target_date": (date.today() + timedelta(days=200)).isoformat(),
    "priority": "high", "description": "Emergency fund"})
goal_id = (goal.get("goal") or goal).get("id")
call("goal create invalid", "post", "/api/profile/goals", {"goal_type": "sometime", "target_amount": -5, "target_date": "2020-01-01"})
call("goal list", "get", "/api/profile/goals")
call("goal update", "put", f"/api/profile/goals/{goal_id}", {"priority": "medium", "target_amount": 175000})

# budget
this_month = date.today().strftime("%Y-%m")
call("budget save", "post", "/api/budget/monthly", {"month": this_month, "monthly_income": 60000, "planned_savings": 10000,
                                                    "categories": {"food": 9000, "rent": 15000, "travel": 3000}})
call("budget get", "get", f"/api/budget/monthly?month={this_month}")
exp = call("expense add", "post", "/api/budget/expenses", {"expense_date": date.today().isoformat(), "category": "food", "amount": 450.5, "note": "lunch"})
exp_id = (exp.get("expense") or exp).get("id")
call("expense add invalid", "post", "/api/budget/expenses", {"expense_date": "not-a-date", "category": "food", "amount": -1})
call("expense add second", "post", "/api/budget/expenses", {"expense_date": date.today().isoformat(), "category": "rent", "amount": 15000})
call("expense update", "put", f"/api/budget/expenses/{exp_id}", {"amount": 500, "note": "lunch + coffee"})
call("expense list", "get", f"/api/budget/expenses?month={this_month}")
call("budget summary", "get", f"/api/budget/summary?month={this_month}")
call("budget analysis input", "get", f"/api/budget/analysis-input?month={this_month}")
call("expense delete", "delete", f"/api/budget/expenses/{exp_id}")
call("budget data overview", "get", "/api/budget/data")

# statement import
stmt = (FIX / "statements" / "hdfc_style_6months.csv").read_bytes()
prev = call("statement preview", "post", "/api/import/statement/preview", files={"file": (io.BytesIO(stmt), "hdfc_style_6months.csv")},
            show=lambda d: {"summary": d.get("summary"), "rows": len(d.get("rows", [])), "error": d.get("error")})
conf = call("statement confirm", "post", "/api/import/statement/confirm", {"rows": prev.get("rows", [])})
call("statement re-preview (dupes)", "post", "/api/import/statement/preview", files={"file": (io.BytesIO(stmt), "hdfc_style_6months.csv")},
     show=lambda d: d.get("summary"))
call("transactions", "get", "/api/import/transactions?month=2026-09", show=lambda d: {"count": d.get("count"), "first": (d.get("transactions") or [None])[0]})
call("recurring", "get", "/api/import/recurring", show=lambda d: {"totals": d.get("totals"), "months": d.get("months_of_history"),
                                                                    "streams": sorted((r["merchant"], r["kind"], r["monthly_equivalent"]) for r in d.get("recurring", []))})
call("import batches", "get", "/api/import/batches")
call("budget summary (imported month)", "get", "/api/budget/summary?month=2026-08")
call("delete month", "delete", "/api/budget/month/2026-08")
call("delete all without confirm", "delete", "/api/budget/all")
call("undo statement import", "delete", f"/api/import/batch/{conf.get('batch_id')}")
call("budget data after undo", "get", "/api/budget/data")

# loans
loan = call("loan create", "post", "/api/loans", {"user_id": uid, "loan_type": "personal", "loan_amount": 200000, "loan_tenure": 24,
                                                   "monthly_emi": 9500, "interest_rate": 12.5,
                                                   "loan_start_date": (date.today() - timedelta(days=200)).isoformat(),
                                                   "loan_maturity_date": (date.today() + timedelta(days=530)).isoformat()})
loan_id = (loan.get("loan") or loan).get("loan_id")
call("loan create invalid", "post", "/api/loans", {"user_id": uid, "loan_type": "boat", "loan_amount": -1})
call("loan list", "get", f"/api/loans/user/{uid}")
call("loan get", "get", f"/api/loans/{loan_id}")
call("loan update", "put", f"/api/loans/{loan_id}", {"monthly_emi": 9600})
for i, status in enumerate(("on-time", "late", "missed")):
    call(f"payment record {status}", "post", f"/api/loans/{loan_id}/payments",
         {"payment_date": (date.today() - timedelta(days=30 * (i + 1))).isoformat(), "payment_amount": 9600, "payment_status": status})
pays = call("payment list", "get", f"/api/loans/{loan_id}/payments")
call("loan metrics", "get", f"/api/loans/metrics/{uid}")
call("loan metrics (cached)", "get", f"/api/loans/metrics/{uid}")
call("other user's loans", "get", f"/api/loans/user/{(uid or 0) + 999}")

# credit report
report = (FIX / "credit_reports" / "cibil_style.pdf").read_bytes()
cprev = call("credit report preview", "post", "/api/import/credit-report/preview", files={"file": (io.BytesIO(report), "cibil_style.pdf")},
             show=lambda d: {"summary": d.get("summary"), "bureau": d.get("bureau"), "score": d.get("score"),
                             "as": [(r["lender"], r["import_as"], r["needs"]) for r in d.get("rows", [])]})
cconf = call("credit report confirm", "post", "/api/import/credit-report/confirm",
             {"rows": cprev.get("rows", []), "bureau": cprev.get("bureau"), "score": cprev.get("score")})
call("credit report again (update)", "post", "/api/import/credit-report/confirm", {"rows": cprev.get("rows", [])})
call("credit report list", "get", "/api/import/credit-report")
call("risk profile", "get", "/api/risk-profile")
call("loan list after report", "get", f"/api/loans/user/{uid}", show=lambda d: sorted((l["loan_type"], l["loan_amount"], l["monthly_emi"]) for l in (d.get("loans") or [])))

# score
form = {"income": 60000, "rent": 15000, "food": 9000, "travel": 3000, "shopping": 4000, "emi": 9600, "savings": 10000}
call("predict", "post", "/api/predict", form, show=lambda d: {"score": d.get("score"), "class": (d.get("classification") or {}).get("category"), "risk": d.get("risk")})
call("whatif", "post", "/api/whatif", {"current": form, "modified": {**form, "emi": 2000}})
call("risk profile save", "put", "/api/risk-profile", {"card_limit": 120000, "card_balance": 30000})
call("risk profile bad", "put", "/api/risk-profile", {"card_limit": -4})
call("model info", "get", "/api/model-info", show=lambda d: {"features": d.get("features"), "auc": (d.get("summary") or {}).get("auc")})

# other modules
call("portfolio optimize", "post", "/api/portfolio/optimize", {"amount": 100000, "risk_score": 5},
     show=lambda d: {"ok": d.get("success", "error" not in d), "personalization": d.get("personalization") or d.get("adjustments"), "error": d.get("error")})
call("unknown address", "get", "/api/no-such-thing")
call("nudges scan", "get", "/api/nudges/", show=lambda d: {k: (v if not isinstance(v, list) else len(v)) for k, v in d.items()})
call("nudges patterns", "get", "/api/nudges/patterns", show=lambda d: {k: (v if not isinstance(v, list) else len(v)) for k, v in d.items()})
call("nudges history", "get", "/api/nudges/history", show=lambda d: {k: (v if not isinstance(v, list) else len(v)) for k, v in d.items()})
retire = {"user_id": uid, "current_age": 28, "retirement_age": 60, "life_expectancy": 85, "current_savings": 200000,
          "current_salary": 720000, "current_monthly_expenses": 40000, "inflation_rate": 0.06, "investment_return_rate": 0.10}
calc = call("retirement calculate", "post", "/api/retirement/calculate", retire, show=lambda d: {"keys": sorted(d)[:12], "error": d.get("error")})
plan = call("retirement plan save", "post", "/api/retirement/plans", {**retire, "plan_name": "Walkthrough plan"},
            show=lambda d: {"keys": sorted(d)[:8], "error": d.get("error")})
call("retirement plans list", "get", f"/api/retirement/plans/{uid}", show=lambda d: {"count": len(d.get("plans", d if isinstance(d, list) else [])), "error": d.get("error") if isinstance(d, dict) else None})
call("chat sessions", "get", "/api/chat/sessions")
call("sip calculator", "post", "/api/sip-calculator", {"monthly_investment": 5000, "annual_return": 12, "years": 10})

# cleanup paths
call("undo credit report", "delete", f"/api/import/credit-report/{cconf.get('batch_id')}")
call("payment delete", "delete", f"/api/loans/{loan_id}/payments/{((pays.get('payments') or [{}])[0]).get('payment_id')}")
call("loan delete", "delete", f"/api/loans/{loan_id}")
call("goal delete", "delete", f"/api/profile/goals/{goal_id}")
call("delete all", "delete", "/api/budget/all", {"confirm": "DELETE"})
call("budget data at the end", "get", "/api/budget/data")
call("healthz", "get", "/healthz")
