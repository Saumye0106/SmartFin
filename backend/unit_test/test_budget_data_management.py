"""Deleting budget history: one month, everything, and listing past imports. Always scoped to one user."""

import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from budget import data_management
from statement_import import service
from statement_import.migrations import create_tables

FIXTURES = Path(__file__).parent / "fixtures" / "statements"
SIX = "hdfc_style_6months.csv"


@pytest.fixture
def conn(tmp_path):
    db = tmp_path / "t.db"
    c = sqlite3.connect(db)
    c.executescript("""
        CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT);
        INSERT INTO users (id, username) VALUES (1, 'a@x.com'), (2, 'b@x.com');
        CREATE TABLE monthly_budgets (id TEXT PRIMARY KEY, user_id INTEGER, month TEXT, monthly_income REAL,
                                      planned_savings REAL, created_at TEXT, updated_at TEXT);
        CREATE TABLE budget_categories (id TEXT PRIMARY KEY, budget_id TEXT, category TEXT, planned_amount REAL,
                                        created_at TEXT, updated_at TEXT);
        CREATE TABLE expense_entries (id TEXT PRIMARY KEY, user_id INTEGER NOT NULL, budget_id TEXT,
                                      expense_date TEXT NOT NULL, category TEXT NOT NULL,
                                      amount REAL NOT NULL CHECK (amount > 0), note TEXT,
                                      created_at TEXT, updated_at TEXT);
    """)
    c.commit()
    c.close()
    create_tables(str(db))
    c = sqlite3.connect(db)
    c.row_factory = sqlite3.Row
    yield c
    c.close()


def _import(conn, user_id):
    data = (FIXTURES / SIX).read_bytes()
    return service.confirm(conn, user_id, service.preview(conn, user_id, SIX, data)["rows"])


def _counts(conn, user_id):
    o = data_management.data_overview(conn, user_id)
    return o["expenses"], o["budgets"], o["transactions"]


def _a_month(conn, user_id):
    return conn.execute("SELECT substr(txn_date, 1, 7) FROM bank_transactions WHERE user_id = ? "
                        "ORDER BY txn_date LIMIT 1 OFFSET 40", (user_id,)).fetchone()[0]


def test_overview_and_batches(conn):
    assert _counts(conn, 2) == (0, 0, 0) and service.list_batches(conn, 2) == []
    res = _import(conn, 2)
    o = data_management.data_overview(conn, 2)
    assert o["expenses"] == res["expenses_created"] and o["transactions"] == res["imported"] and o["budgets"] == 6
    assert o["first_expense_date"] < o["last_expense_date"]
    (batch,) = service.list_batches(conn, 2)
    assert batch["batch_id"] == res["batch_id"] and batch["transactions"] == res["imported"]
    assert batch["expenses"] == res["expenses_created"] and batch["total_credit"] > 0 and batch["period_start"] < batch["period_end"]
    assert service.list_batches(conn, 1) == []


def test_delete_month_removes_only_that_month_for_that_user(conn):
    _import(conn, 1)
    _import(conn, 2)
    month = _a_month(conn, 2)
    before_other_user = _counts(conn, 1)
    exp_before, _, txn_before = _counts(conn, 2)
    conn.execute("INSERT INTO budget_categories VALUES ('c1', (SELECT id FROM monthly_budgets WHERE user_id = 2 AND month = ?), "
                 "'food', 5000, '', '')", (month,))

    res = data_management.delete_month(conn, 2, month)

    assert res["expenses_removed"] > 0 and res["transactions_removed"] > 0 and res["budgets_removed"] == 1
    for table, col in (("expense_entries", "expense_date"), ("bank_transactions", "txn_date")):
        assert conn.execute(f"SELECT COUNT(*) FROM {table} WHERE user_id = 2 AND substr({col}, 1, 7) = ?",
                            (month,)).fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM monthly_budgets WHERE user_id = 2 AND month = ?", (month,)).fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM budget_categories").fetchone()[0] == 0
    exp_after, budgets_after, txn_after = _counts(conn, 2)
    assert (exp_after, txn_after) == (exp_before - res["expenses_removed"], txn_before - res["transactions_removed"])
    assert budgets_after == 5
    assert _counts(conn, 1) == before_other_user


def test_deleted_month_can_be_imported_again(conn):
    _import(conn, 2)
    month = _a_month(conn, 2)
    removed = data_management.delete_month(conn, 2, month)["transactions_removed"]
    preview = service.preview(conn, 2, SIX, (FIXTURES / SIX).read_bytes())
    new_rows = [r for r in preview["rows"] if not r["duplicate"]]
    assert len(new_rows) == removed and {r["date"][:7] for r in new_rows} == {month}


def test_delete_all_wipes_one_user_and_leaves_the_other(conn):
    _import(conn, 1)
    _import(conn, 2)
    conn.execute("INSERT INTO merchant_category_overrides VALUES (2, 'swiggy', 'food', ''), (1, 'swiggy', 'other', '')")
    conn.execute("INSERT INTO expense_entries (id, user_id, expense_date, category, amount, note) "
                 "VALUES ('manual1', 2, '2026-09-05', 'food', 120, 'typed by hand')")
    before_other_user = _counts(conn, 1)

    res = data_management.delete_all(conn, 2)

    assert res["expenses_removed"] > 1 and res["transactions_removed"] > 0 and res["budgets_removed"] == 6
    assert res["category_rules_removed"] == 1
    assert data_management.data_overview(conn, 2) == {
        "expenses": 0, "budgets": 0, "transactions": 0, "category_rules": 0,
        "first_expense_date": None, "last_expense_date": None}
    assert _counts(conn, 1) == before_other_user
    assert conn.execute("SELECT category FROM merchant_category_overrides WHERE user_id = 1").fetchone()[0] == "other"
    # nothing left behind that would block a fresh import
    assert all(not r["duplicate"] for r in service.preview(conn, 2, SIX, (FIXTURES / SIX).read_bytes())["rows"])


def test_deleting_nothing_is_harmless(conn):
    assert data_management.delete_month(conn, 2, "2020-01") == {
        "month": "2020-01", "expenses_removed": 0, "transactions_removed": 0, "budgets_removed": 0}
    assert data_management.delete_all(conn, 2)["expenses_removed"] == 0
