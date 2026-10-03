"""
Credit report import: preview -> confirm -> undo.

What an import does with each account in the report:
  - open loan with EMI, tenure and interest rate known  -> a SmartFin loan plus one payment per reported month
  - open loan missing any of those                       -> kept as payment history only, until the user fills them in
  - closed loan                                          -> payment history only
  - credit card                                          -> payment history, and its limit/balance become the saved card details

Payment history is what the risk model relies on most. Days past due map to
SmartFin's payment statuses the way the model's inputs are defined:
  under 30 days -> on-time, 30-89 days -> late, 90+ days -> missed.

Nothing from the uploaded file is stored except the parsed accounts.
Re-importing a newer report updates accounts already imported (matched by
lender, type, account number and opening date) instead of duplicating them.
"""

from __future__ import annotations

import hashlib
import uuid
from datetime import date, datetime

from credit_report.parser import ParsedAccount, parse_credit_report
from risk_scorer.service import get_risk_profile, save_risk_profile

LOAN_TYPES = ("personal", "home", "auto", "education")
HISTORY_WINDOW_MONTHS = 24
LATE_DPD, MISSED_DPD = 30, 90

# checked in order against the lowercased account type
_LOAN_TYPE_HINTS = (
    ("home", ("housing", "home", "property", "mortgage")),
    ("auto", ("auto", "vehicle", "two-wheeler", "two wheeler", "car loan", "commercial vehicle")),
    ("education", ("education", "student")),
)


def classify_account(account_type: str) -> tuple[str, str | None]:
    """('card', None) or ('loan', smartfin_loan_type)."""
    t = (account_type or "").lower()
    if "card" in t:
        return "card", None
    for loan_type, hints in _LOAN_TYPE_HINTS:
        if any(h in t for h in hints):
            return "loan", loan_type
    return "loan", "personal"


def payment_status(dpd: int) -> str:
    return "missed" if dpd >= MISSED_DPD else "late" if dpd >= LATE_DPD else "on-time"


def account_hash(lender: str, account_type: str, account_number: str | None, opened: str | None) -> str:
    """Stable identity for an account across reports (balances and history change; these don't)."""
    def norm(s):
        return "".join(ch for ch in (s or "").lower() if ch.isalnum())
    return hashlib.sha256("|".join((norm(lender), norm(account_type), norm(account_number), opened or "")).encode()).hexdigest()


def emi_for(amount: float, annual_rate: float, months: int) -> float:
    """Standard reducing-balance EMI."""
    r = annual_rate / 12 / 100
    if r == 0:
        return round(amount / months, 2)
    return round(amount * r * (1 + r) ** months / ((1 + r) ** months - 1), 2)


def _add_months(d: date, months: int) -> date:
    y, m = divmod(d.month - 1 + months, 12)
    y, m = d.year + y, m + 1
    last = (date(y + (m == 12), m % 12 + 1, 1) - date.resolution).day
    return date(y, m, min(d.day, last))


def _window_start(today: date | None = None) -> str:
    today = today or date.today()
    return _add_months(today.replace(day=1), -HISTORY_WINDOW_MONTHS).strftime("%Y-%m")


def _row_from_account(a: ParsedAccount) -> dict:
    kind, loan_type = classify_account(a.account_type)
    opened = a.opened.isoformat() if a.opened else None
    since = _window_start()
    recent = {m: d for m, d in a.history.items() if m >= since}
    row = {
        "account_hash": account_hash(a.lender, a.account_type, a.account_number, opened),
        "lender": a.lender,
        "account_type": a.account_type,
        "kind": kind,
        "loan_type": loan_type,
        "account_number": a.account_number,
        "opened": opened,
        "closed": a.closed.isoformat() if a.closed else None,
        "is_open": a.closed is None,
        "sanctioned": a.sanctioned,
        "balance": a.balance,
        "overdue": a.overdue,
        "emi": a.emi,
        "tenure_months": a.tenure_months,
        "interest_rate": a.interest_rate,
        "emi_calculated": False,
        "history": [{"month": m, "dpd": d, "status": payment_status(d)} for m, d in sorted(a.history.items())],
        "months_reported": len(a.history),
        "late_24m": sum(1 for d in recent.values() if LATE_DPD <= d < MISSED_DPD),
        "missed_24m": sum(1 for d in recent.values() if d >= MISSED_DPD),
        "include": True,
    }
    return _resolve(row)


def _resolve(row: dict) -> dict:
    """Decide how a row will be imported and what is still missing for it to become a loan."""
    row["needs"] = []
    if row["kind"] == "card":
        row["import_as"] = "card"
        return row
    if not row["is_open"]:
        row["import_as"] = "history_only"
        return row
    if not row.get("emi") and row.get("sanctioned") and row.get("tenure_months") and row.get("interest_rate") is not None:
        row["emi"] = emi_for(row["sanctioned"], row["interest_rate"], row["tenure_months"])
        row["emi_calculated"] = True
    # A SmartFin loan needs all of these (the loans table enforces amount, EMI and tenure > 0); 0% interest is allowed.
    row["needs"] = [f for f in ("sanctioned", "emi", "tenure_months") if not row.get(f)]
    row["needs"] += [f for f in ("opened", "interest_rate") if row.get(f) is None]
    row["import_as"] = "history_only" if row["needs"] else "loan"
    return row


def preview(conn, user_id: int, filename: str, data: bytes, password: str | None = None) -> dict:
    report = parse_credit_report(filename, data, password)
    rows = [_row_from_account(a) for a in report.accounts]
    existing = {r[0] for r in conn.execute("SELECT account_hash FROM credit_accounts WHERE user_id = ?", (user_id,))}
    for r in rows:
        r["already_imported"] = r["account_hash"] in existing
    cards = [r for r in rows if r["kind"] == "card" and r["is_open"] and (r["sanctioned"] or 0) > 0]
    return {
        "bureau": report.bureau,
        "score": report.score,
        "loan_types": list(LOAN_TYPES),
        "rows": rows,
        "summary": {
            "accounts": len(rows),
            "open_loans": sum(1 for r in rows if r["kind"] == "loan" and r["is_open"]),
            "closed_loans": sum(1 for r in rows if r["kind"] == "loan" and not r["is_open"]),
            "cards": sum(1 for r in rows if r["kind"] == "card"),
            "late_24m": sum(r["late_24m"] for r in rows),
            "missed_24m": sum(r["missed_24m"] for r in rows),
            "card_limit": sum(r["sanctioned"] for r in cards) or None,
            "card_balance": sum(r["balance"] or 0 for r in cards) if cards else None,
            "history_window_months": HISTORY_WINDOW_MONTHS,
        },
    }


# ── Confirm ──────────────────────────────────────────────────────────────────

def _num(value, name, *, minimum=None, maximum=None, integer=False):
    if value in (None, ""):
        return None
    try:
        v = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a number")
    if v != v or v in (float("inf"), float("-inf")):
        raise ValueError(f"{name} must be a number")
    if minimum is not None and v < minimum or maximum is not None and v > maximum:
        raise ValueError(f"{name} is out of range")
    return int(v) if integer else v


def _iso_date(value, name):
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(str(value)).isoformat()
    except ValueError:
        raise ValueError(f"{name} must be a date (YYYY-MM-DD)")


def _clean_row(raw: dict) -> dict:
    """Never trust the client: rebuild the row from validated fields and recompute everything derived."""
    lender = str(raw.get("lender") or "").strip()[:120]
    account_type = str(raw.get("account_type") or "").strip()[:80]
    if not lender or not account_type:
        raise ValueError("Each account needs a lender and an account type")
    kind, default_loan_type = classify_account(account_type)
    loan_type = raw.get("loan_type") or default_loan_type
    if kind == "loan" and loan_type not in LOAN_TYPES:
        raise ValueError(f"Loan type must be one of {', '.join(LOAN_TYPES)}")
    opened = _iso_date(raw.get("opened"), "opened")
    closed = _iso_date(raw.get("closed"), "closed")
    history = {}
    for h in raw.get("history") or []:
        month = str(h.get("month") or "")
        try:
            datetime.strptime(month, "%Y-%m")
        except ValueError:
            raise ValueError("History months must be YYYY-MM")
        history[month] = _num(h.get("dpd"), "days past due", minimum=0, maximum=999, integer=True) or 0
    number = raw.get("account_number")
    row = {
        "lender": lender, "account_type": account_type, "kind": kind,
        "loan_type": loan_type if kind == "loan" else None,
        "account_number": str(number).strip()[:40] if number else None,
        "opened": opened, "closed": closed, "is_open": closed is None,
        "sanctioned": _num(raw.get("sanctioned"), "sanctioned amount", minimum=0),
        "balance": _num(raw.get("balance"), "balance", minimum=0),
        "overdue": _num(raw.get("overdue"), "overdue", minimum=0),
        "emi": _num(raw.get("emi"), "EMI", minimum=0),
        "tenure_months": _num(raw.get("tenure_months"), "tenure", minimum=0, maximum=600, integer=True),
        "interest_rate": _num(raw.get("interest_rate"), "interest rate", minimum=0, maximum=50),
        "history": history,
        "emi_calculated": False,
    }
    row["account_hash"] = account_hash(lender, account_type, row["account_number"], opened)
    return _resolve(row)


def _insert_loan(conn, user_id: int, row: dict, now: str) -> str:
    loan_id = str(uuid.uuid4())
    start = date.fromisoformat(row["opened"])
    conn.execute(
        "INSERT INTO loans (loan_id, user_id, loan_type, loan_amount, loan_tenure, monthly_emi, interest_rate, "
        "loan_start_date, loan_maturity_date, default_status, created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
        (loan_id, user_id, row["loan_type"], row["sanctioned"], row["tenure_months"], row["emi"], row["interest_rate"],
         row["opened"], _add_months(start, row["tenure_months"]).isoformat(),
         1 if any(d >= MISSED_DPD for d in row["history"].values()) else 0, now, now))
    return loan_id


def _insert_payments(conn, loan_id: str, emi: float, months: dict[str, int], now: str) -> int:
    for month, dpd in months.items():
        conn.execute(
            "INSERT INTO loan_payments (payment_id, loan_id, payment_date, payment_amount, payment_status, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?)", (str(uuid.uuid4()), loan_id, f"{month}-01", emi, payment_status(dpd), now, now))
    return len(months)


def confirm(conn, user_id: int, rows: list[dict], bureau: str | None = None, score=None) -> dict:
    if not isinstance(rows, list) or not rows:
        raise ValueError("No accounts to import")
    cleaned = [_clean_row(r) for r in rows if r.get("include", True)]
    if not cleaned:
        raise ValueError("No accounts selected")
    if len({r["account_hash"] for r in cleaned}) != len(cleaned):
        raise ValueError("The same account appears twice")

    now = datetime.now().isoformat()
    batch_id = str(uuid.uuid4())
    result = {"batch_id": batch_id, "accounts_added": 0, "accounts_updated": 0, "loans_created": 0,
              "payments_recorded": 0, "history_months": 0, "history_only": 0, "cards": 0}

    for row in cleaned:
        existing = conn.execute(
            "SELECT id, loan_id, emi FROM credit_accounts WHERE user_id = ? AND account_hash = ?",
            (user_id, row["account_hash"])).fetchone()
        if existing:
            account_id, loan_id = existing[0], existing[1]
            known = {r[0] for r in conn.execute("SELECT month FROM credit_account_history WHERE account_id = ?", (account_id,))}
            new_months = {m: d for m, d in row["history"].items() if m not in known}
            conn.execute(
                "UPDATE credit_accounts SET closed = ?, sanctioned = ?, balance = ?, overdue = ?, updated_at = ? WHERE id = ?",
                (row["closed"], row["sanctioned"], row["balance"], row["overdue"], now, account_id))
            if loan_id is None and row["import_as"] == "loan":   # details filled in on a later import
                loan_id = _insert_loan(conn, user_id, row, now)
                result["loans_created"] += 1
                result["payments_recorded"] += _insert_payments(conn, loan_id, row["emi"], row["history"], now)
                conn.execute("UPDATE credit_accounts SET loan_id = ?, emi = ?, tenure_months = ?, interest_rate = ? WHERE id = ?",
                             (loan_id, row["emi"], row["tenure_months"], row["interest_rate"], account_id))
            elif loan_id is not None:
                result["payments_recorded"] += _insert_payments(conn, loan_id, existing[2] or row["emi"], new_months, now)
            result["accounts_updated"] += 1
        else:
            account_id, loan_id, new_months = str(uuid.uuid4()), None, row["history"]
            if row["import_as"] == "loan":
                loan_id = _insert_loan(conn, user_id, row, now)
                result["loans_created"] += 1
                result["payments_recorded"] += _insert_payments(conn, loan_id, row["emi"], row["history"], now)
            conn.execute(
                "INSERT INTO credit_accounts (id, user_id, account_hash, lender, account_type, kind, account_number, opened, "
                "closed, sanctioned, balance, overdue, emi, tenure_months, interest_rate, loan_id, import_batch_id, "
                "created_at, updated_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (account_id, user_id, row["account_hash"], row["lender"], row["account_type"], row["kind"],
                 row["account_number"], row["opened"], row["closed"], row["sanctioned"], row["balance"], row["overdue"],
                 row["emi"], row["tenure_months"], row["interest_rate"], loan_id, batch_id, now, now))
            result["accounts_added"] += 1
        for month, dpd in new_months.items():
            conn.execute("INSERT INTO credit_account_history (account_id, month, dpd) VALUES (?,?,?) "
                         "ON CONFLICT (account_id, month) DO NOTHING",
                         (account_id, month, dpd))
        result["history_months"] += len(new_months)
        result["cards"] += row["kind"] == "card"
        result["history_only"] += row["import_as"] == "history_only"

    # Open cards -> the card details the risk model uses (total limit and total balance).
    cards = conn.execute(
        "SELECT COALESCE(SUM(sanctioned), 0), COALESCE(SUM(balance), 0), COUNT(*) FROM credit_accounts "
        "WHERE user_id = ? AND kind = 'card' AND closed IS NULL AND sanctioned > 0", (user_id,)).fetchone()
    previous = get_risk_profile(conn, user_id)
    card_set = bool(cards[2])
    if card_set:
        save_risk_profile(conn, user_id, cards[0], cards[1])
        result["card_limit"], result["card_balance"] = cards[0], cards[1]

    clean_score = _num(score, "score", minimum=300, maximum=900, integer=True) if score not in (None, "") else None
    conn.execute(
        "INSERT INTO credit_report_imports (batch_id, user_id, bureau, score, accounts, prev_card_limit, prev_card_balance, "
        "card_details_set, imported_at) VALUES (?,?,?,?,?,?,?,?,?)",
        (batch_id, user_id, str(bureau)[:40] if bureau else None, clean_score, len(cleaned),
         previous["card_limit"], previous["card_balance"], int(card_set), now))
    conn.execute("DELETE FROM loan_metrics WHERE user_id = ?", (user_id,))  # cached loan scores are now stale
    conn.commit()
    return result


# ── Undo / list ──────────────────────────────────────────────────────────────

def undo_batch(conn, user_id: int, batch_id: str) -> dict:
    """Remove the accounts an import added, with the loans and payments it created. Accounts it only updated stay."""
    batch = conn.execute(
        "SELECT prev_card_limit, prev_card_balance, card_details_set FROM credit_report_imports "
        "WHERE batch_id = ? AND user_id = ?", (batch_id, user_id)).fetchone()
    if batch is None:
        return {"found": False, "accounts_removed": 0, "loans_removed": 0}
    accounts = conn.execute(
        "SELECT id, loan_id FROM credit_accounts WHERE user_id = ? AND import_batch_id = ?", (user_id, batch_id)).fetchall()
    loans = 0
    for account_id, loan_id in accounts:
        conn.execute("DELETE FROM credit_account_history WHERE account_id = ?", (account_id,))
        if loan_id:
            conn.execute("DELETE FROM loan_payments WHERE loan_id = ?", (loan_id,))
            loans += conn.execute("DELETE FROM loans WHERE loan_id = ? AND user_id = ?", (loan_id, user_id)).rowcount
    conn.execute("DELETE FROM credit_accounts WHERE user_id = ? AND import_batch_id = ?", (user_id, batch_id))
    conn.execute("DELETE FROM credit_report_imports WHERE batch_id = ? AND user_id = ?", (batch_id, user_id))
    if batch[2]:
        save_risk_profile(conn, user_id, batch[0], batch[1])
    conn.execute("DELETE FROM loan_metrics WHERE user_id = ?", (user_id,))
    conn.commit()
    return {"found": True, "accounts_removed": len(accounts), "loans_removed": loans}


def list_imports(conn, user_id: int) -> dict:
    imports = [dict(zip(("batch_id", "bureau", "score", "accounts", "imported_at"), r)) for r in conn.execute(
        "SELECT batch_id, bureau, score, accounts, imported_at FROM credit_report_imports WHERE user_id = ? "
        "ORDER BY imported_at DESC", (user_id,))]
    since = _window_start()
    accounts = []
    for r in conn.execute(
            "SELECT id, lender, account_type, kind, account_number, opened, closed, sanctioned, balance, overdue, emi, loan_id "
            "FROM credit_accounts WHERE user_id = ? ORDER BY closed IS NOT NULL, opened DESC", (user_id,)).fetchall():
        a = dict(zip(("id", "lender", "account_type", "kind", "account_number", "opened", "closed", "sanctioned",
                      "balance", "overdue", "emi", "loan_id"), r))
        late, missed, months = conn.execute(
            "SELECT COALESCE(SUM(CASE WHEN dpd >= ? AND dpd < ? THEN 1 ELSE 0 END), 0), "
            "COALESCE(SUM(CASE WHEN dpd >= ? THEN 1 ELSE 0 END), 0), COUNT(*) "
            "FROM credit_account_history WHERE account_id = ? AND month >= ?",
            (LATE_DPD, MISSED_DPD, MISSED_DPD, a.pop("id"), since)).fetchone()
        accounts.append({**a, "late_24m": late, "missed_24m": missed, "months_24m": months})
    return {"imports": imports, "accounts": accounts}
