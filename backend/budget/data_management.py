"""
Deleting a user's own budget history: one month, or everything.

Every statement is scoped with user_id, so one user can never remove another's
rows. Imported bank transactions are removed together with the expenses they
created; otherwise a later re-import would be skipped as "already imported".
"""

from __future__ import annotations

from statement_import.service import _touched_months, sync_income

CONFIRM_ALL_PHRASE = "DELETE"


def _delete_budgets(conn, user_id: int, where: str, params: tuple) -> int:
    ids = [r[0] for r in conn.execute(f"SELECT id FROM monthly_budgets WHERE user_id = ? {where}", (user_id, *params))]
    for budget_id in ids:
        conn.execute("DELETE FROM budget_categories WHERE budget_id = ?", (budget_id,))
        conn.execute("DELETE FROM monthly_budgets WHERE id = ? AND user_id = ?", (budget_id, user_id))
    return len(ids)


def delete_month(conn, user_id: int, month: str) -> dict:
    """Remove one month ('YYYY-MM'): its expenses, imported transactions and budget."""
    expenses = conn.execute(
        "DELETE FROM expense_entries WHERE user_id = ? AND substr(expense_date, 1, 7) = ?", (user_id, month)).rowcount
    transactions = conn.execute(
        "DELETE FROM bank_transactions WHERE user_id = ? AND substr(txn_date, 1, 7) = ?", (user_id, month)).rowcount
    budgets = _delete_budgets(conn, user_id, "AND month = ?", (month,))
    # Salary paid at the end of this month may have been counted as next month's income.
    sync_income(conn, user_id, _touched_months([f"{month}-01"]) - {month})
    conn.commit()
    return {"month": month, "expenses_removed": expenses, "transactions_removed": transactions,
            "budgets_removed": budgets}


def delete_all(conn, user_id: int) -> dict:
    """Remove every budget, expense, imported transaction and learned category for this user."""
    expenses = conn.execute("DELETE FROM expense_entries WHERE user_id = ?", (user_id,)).rowcount
    transactions = conn.execute("DELETE FROM bank_transactions WHERE user_id = ?", (user_id,)).rowcount
    rules = conn.execute("DELETE FROM merchant_category_overrides WHERE user_id = ?", (user_id,)).rowcount
    budgets = _delete_budgets(conn, user_id, "", ())
    conn.commit()
    return {"expenses_removed": expenses, "transactions_removed": transactions, "budgets_removed": budgets,
            "category_rules_removed": rules}


def data_overview(conn, user_id: int) -> dict:
    """What is stored for this user, so the UI can say exactly what a delete will remove."""
    def count(sql):
        return conn.execute(sql, (user_id,)).fetchone()[0]

    first, last = conn.execute(
        "SELECT MIN(expense_date), MAX(expense_date) FROM expense_entries WHERE user_id = ?", (user_id,)).fetchone()
    return {
        "expenses": count("SELECT COUNT(*) FROM expense_entries WHERE user_id = ?"),
        "budgets": count("SELECT COUNT(*) FROM monthly_budgets WHERE user_id = ?"),
        "transactions": count("SELECT COUNT(*) FROM bank_transactions WHERE user_id = ?"),
        "category_rules": count("SELECT COUNT(*) FROM merchant_category_overrides WHERE user_id = ?"),
        "first_expense_date": first,
        "last_expense_date": last,
    }
