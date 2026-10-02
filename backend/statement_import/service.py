"""
Statement import workflow: preview -> (user reviews/edits) -> confirm -> optional undo.

Functions take an open sqlite3 connection with row_factory = sqlite3.Row
(db_core.get_db() in requests, a plain connection in tests).
"""

from __future__ import annotations

import hashlib
import re
import uuid
from collections import Counter
from datetime import date, datetime

from statement_import.categorizer import (
    ALL_CATEGORIES, EXPENSE_CATEGORIES, categorize, extract_merchant,
)
from statement_import.parser import ParsedTransaction, parse_statement
from statement_import.recurring import detect_monthly_income, detect_recurring

_HASH_PARAM_CHUNK = 500


def _identity(txn_date: str, direction: str, amount: float, description: str, balance) -> str:
    desc = re.sub(r"\s+", " ", description or "").strip().lower()
    bal = "" if balance is None else f"{float(balance):.2f}"
    return f"{txn_date}|{direction}|{float(amount):.2f}|{desc}|{bal}"


def assign_hashes(rows: list[dict]) -> None:
    """
    Stable per-transaction hash used to skip re-imported rows. Genuinely
    identical rows in one file (two ₹20 chai on the same day, no balance
    column) get an occurrence counter so they aren't collapsed into one.
    """
    seen: Counter = Counter()
    for r in rows:
        ident = _identity(r["date"], r["direction"], r["amount"], r["description"], r.get("balance"))
        seen[ident] += 1
        r["txn_hash"] = hashlib.sha256(f"{ident}|{seen[ident]}".encode()).hexdigest()


def _load_overrides(conn, user_id: int) -> dict[str, str]:
    return {r["merchant"]: r["category"] for r in conn.execute(
        "SELECT merchant, category FROM merchant_category_overrides WHERE user_id = ?", (user_id,))}


def _existing_hashes(conn, user_id: int, hashes: list[str]) -> set[str]:
    found: set[str] = set()
    for i in range(0, len(hashes), _HASH_PARAM_CHUNK):
        chunk = hashes[i:i + _HASH_PARAM_CHUNK]
        q = f"SELECT txn_hash FROM bank_transactions WHERE user_id = ? AND txn_hash IN ({','.join('?' * len(chunk))})"
        found.update(r["txn_hash"] for r in conn.execute(q, (user_id, *chunk)))
    return found


def _to_row(t: ParsedTransaction, overrides: dict[str, str]) -> dict:
    merchant = extract_merchant(t.description)
    category, source = categorize(t.description, t.direction, merchant, overrides)
    return {
        "date": t.txn_date.isoformat(),
        "description": t.description,
        "merchant": merchant,
        "amount": t.amount,
        "direction": t.direction,
        "balance": t.balance,
        "category": category,
        "suggested_category": category,
        "category_source": source,
    }


def preview(conn, user_id: int, filename: str, data: bytes, password: str | None = None) -> dict:
    txns = parse_statement(filename, data, password)
    overrides = _load_overrides(conn, user_id)
    rows = [_to_row(t, overrides) for t in txns]
    rows.sort(key=lambda r: r["date"])
    assign_hashes(rows)

    dupes = _existing_hashes(conn, user_id, [r["txn_hash"] for r in rows])
    for r in rows:
        r["duplicate"] = r["txn_hash"] in dupes

    new = [r for r in rows if not r["duplicate"]]
    by_category: dict[str, float] = {}
    for r in new:
        if r["direction"] == "debit":
            by_category[r["category"]] = round(by_category.get(r["category"], 0) + r["amount"], 2)

    return {
        "rows": rows,
        "summary": {
            "count": len(rows),
            "new_count": len(new),
            "duplicate_count": len(rows) - len(new),
            "period": {"start": rows[0]["date"], "end": rows[-1]["date"]},
            "total_debit": round(sum(r["amount"] for r in new if r["direction"] == "debit"), 2),
            "total_credit": round(sum(r["amount"] for r in new if r["direction"] == "credit"), 2),
            "debit_by_category": dict(sorted(by_category.items(), key=lambda kv: -kv[1])),
        },
        "categories": list(ALL_CATEGORIES),
    }


def _validate(row: dict) -> dict:
    """Server-side re-validation: never trust the client's copy of the preview."""
    try:
        d = date.fromisoformat(str(row["date"]))
        amount = round(float(row["amount"]), 2)
    except (KeyError, TypeError, ValueError) as e:
        raise ValueError(f"Invalid row date/amount: {e}") from e
    if amount <= 0:
        raise ValueError("Amount must be positive")
    direction = row.get("direction")
    if direction not in ("debit", "credit"):
        raise ValueError(f"Invalid direction {direction!r}")
    category = row.get("category")
    if category not in ALL_CATEGORIES:
        raise ValueError(f"Invalid category {category!r}")
    description = str(row.get("description") or "").strip()[:500]
    if not description:
        raise ValueError("Description is required")
    balance = row.get("balance")
    return {
        "date": d.isoformat(),
        "description": description,
        "merchant": str(row.get("merchant") or extract_merchant(description))[:80],
        "amount": amount,
        "direction": direction,
        "balance": None if balance in (None, "") else float(balance),
        "category": category,
        "suggested_category": row.get("suggested_category"),
        "include": row.get("include", True) is not False,
    }


def confirm(conn, user_id: int, raw_rows: list[dict]) -> dict:
    if not raw_rows:
        raise ValueError("No rows to import")
    rows = [_validate(r) for r in raw_rows]
    rows.sort(key=lambda r: r["date"])
    assign_hashes(rows)  # over ALL rows, so hashes match the preview and future re-uploads

    batch_id = str(uuid.uuid4())
    now = datetime.now().isoformat()
    budgets = {r["month"]: r["id"] for r in conn.execute(
        "SELECT id, month FROM monthly_budgets WHERE user_id = ?", (user_id,))}

    imported = duplicates = expenses = excluded = 0
    learned: dict[str, str] = {}
    for r in rows:
        if not r["include"]:
            excluded += 1
            continue
        txn_id = str(uuid.uuid4())
        cur = conn.execute(
            "INSERT OR IGNORE INTO bank_transactions (id, user_id, txn_date, description, merchant, amount, "
            "direction, balance, category, import_batch_id, txn_hash) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (txn_id, user_id, r["date"], r["description"], r["merchant"], r["amount"], r["direction"],
             r["balance"], r["category"], batch_id, r["txn_hash"]),
        )
        if cur.rowcount == 0:
            duplicates += 1
            continue
        imported += 1

        if r["direction"] == "debit" and r["category"] in EXPENSE_CATEGORIES:
            expense_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO expense_entries (id, user_id, budget_id, expense_date, category, amount, note, "
                "created_at, updated_at, source) VALUES (?,?,?,?,?,?,?,?,?,'import')",
                (expense_id, user_id, budgets.get(r["date"][:7]), r["date"], r["category"], r["amount"],
                 r["merchant"], now, now),
            )
            conn.execute("UPDATE bank_transactions SET expense_id = ? WHERE id = ?", (expense_id, txn_id))
            expenses += 1

        if r["suggested_category"] and r["category"] != r["suggested_category"] and r["merchant"]:
            learned[r["merchant"].lower()] = r["category"]

    for merchant, category in learned.items():
        conn.execute(
            "INSERT INTO merchant_category_overrides (user_id, merchant, category, updated_at) VALUES (?,?,?,?) "
            "ON CONFLICT(user_id, merchant) DO UPDATE SET category = excluded.category, updated_at = excluded.updated_at",
            (user_id, merchant, category, now),
        )
    income = sync_income(conn, user_id, _touched_months(r["date"] for r in rows if r["include"]))
    conn.commit()
    return {
        "batch_id": batch_id,
        "imported": imported,
        "skipped_duplicates": duplicates,
        "excluded": excluded,
        "expenses_created": expenses,
        "rules_learned": len(learned),
        **income,
    }


def undo_batch(conn, user_id: int, batch_id: str) -> dict:
    """Remove one import batch and the budget expenses it created; recompute import-set income."""
    batch = conn.execute(
        "SELECT txn_date, expense_id FROM bank_transactions WHERE user_id = ? AND import_batch_id = ?",
        (user_id, batch_id)).fetchall()
    expense_ids = [r["expense_id"] for r in batch if r["expense_id"]]
    for eid in expense_ids:
        conn.execute("DELETE FROM expense_entries WHERE id = ? AND user_id = ?", (eid, user_id))
    cur = conn.execute("DELETE FROM bank_transactions WHERE user_id = ? AND import_batch_id = ?", (user_id, batch_id))
    if batch:
        sync_income(conn, user_id, _touched_months(r["txn_date"] for r in batch))
    conn.commit()
    return {"transactions_removed": cur.rowcount, "expenses_removed": len(expense_ids)}


def _touched_months(dates) -> set[str]:
    """Months of the given dates plus each following month (salary paid early lands a month ahead)."""
    out = set()
    for d in dates:
        y, m = int(d[:4]), int(d[5:7])
        out.add(f"{y:04d}-{m:02d}")
        out.add(f"{y + (m == 12):04d}-{m % 12 + 1:02d}")
    return out


def _user_txns(conn, user_id: int) -> list[dict]:
    return [dict(r) for r in conn.execute(
        "SELECT id, txn_date, description, merchant, amount, direction, category "
        "FROM bank_transactions WHERE user_id = ?", (user_id,))]


def sync_income(conn, user_id: int, months: set[str]) -> dict:
    """
    Set monthly_budgets.monthly_income from detected salary for the given months.
    Income the user typed (income_source 'manual' with a non-zero value) is never
    touched; import-set income is kept in sync. Creates the budget row if missing
    and links unlinked expenses of that month to it. Does not commit.
    """
    detected = detect_monthly_income(_user_txns(conn, user_id))
    now = datetime.now().isoformat()
    income_set: dict[str, float] = {}
    kept_manual: list[str] = []
    for month in sorted(months):
        amount = detected.get(month, 0.0)
        row = conn.execute(
            "SELECT id, monthly_income, income_source FROM monthly_budgets WHERE user_id = ? AND month = ?",
            (user_id, month)).fetchone()
        if row is None:
            if amount <= 0:
                continue
            budget_id = str(uuid.uuid4())
            conn.execute(
                "INSERT INTO monthly_budgets (id, user_id, month, monthly_income, planned_savings, created_at, "
                "updated_at, income_source) VALUES (?,?,?,?,0,?,?,'import')",
                (budget_id, user_id, month, amount, now, now))
        else:
            budget_id = row["id"]
            manual = row["income_source"] != "import" and (row["monthly_income"] or 0) > 0
            if manual:
                if amount > 0:
                    kept_manual.append(month)
                continue
            if (row["monthly_income"] or 0) == amount:
                continue
            conn.execute(
                "UPDATE monthly_budgets SET monthly_income = ?, income_source = 'import', updated_at = ? WHERE id = ?",
                (amount, now, budget_id))
        income_set[month] = amount
        conn.execute(
            "UPDATE expense_entries SET budget_id = ? WHERE user_id = ? AND budget_id IS NULL "
            "AND substr(expense_date, 1, 7) = ?", (budget_id, user_id, month))
    return {"income_set": income_set, "income_kept_manual": kept_manual}


def recurring_summary(conn, user_id: int) -> dict:
    txns = _user_txns(conn, user_id)
    recurring = detect_recurring(txns)
    for r in recurring:
        r.pop("txn_ids", None)
    active = [r for r in recurring if r["active"]]
    months = sorted({t["txn_date"][:7] for t in txns})
    return {
        "recurring": recurring,
        "totals": {
            "fixed_outflow_monthly": round(sum(r["monthly_equivalent"] for r in active
                                               if r["direction"] == "debit" and r["kind"] != "investment"), 2),
            "investments_monthly": round(sum(r["monthly_equivalent"] for r in active if r["kind"] == "investment"), 2),
            "income_monthly": round(sum(r["monthly_equivalent"] for r in active if r["direction"] == "credit"), 2),
        },
        "months_of_history": len(months),
        "as_of": max((t["txn_date"] for t in txns), default=None),
    }


def list_transactions(conn, user_id: int, month: str | None = None, limit: int = 500) -> list[dict]:
    q = "SELECT * FROM bank_transactions WHERE user_id = ?"
    params: list = [user_id]
    if month:
        q += " AND substr(txn_date, 1, 7) = ?"
        params.append(month)
    q += " ORDER BY txn_date DESC, created_at DESC LIMIT ?"
    params.append(max(1, min(int(limit), 2000)))
    return [dict(r) for r in conn.execute(q, params)]
