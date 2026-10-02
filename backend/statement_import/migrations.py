"""Tables for bank-statement import. Idempotent; run at app startup."""

import sqlite3


def create_tables(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS bank_transactions (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                txn_date TEXT NOT NULL,
                description TEXT NOT NULL,
                merchant TEXT,
                amount REAL NOT NULL CHECK (amount > 0),
                direction TEXT NOT NULL CHECK (direction IN ('debit', 'credit')),
                balance REAL,
                category TEXT NOT NULL,
                expense_id TEXT,
                import_batch_id TEXT NOT NULL,
                txn_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (user_id, txn_hash),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_bank_txn_user_date ON bank_transactions(user_id, txn_date);

            CREATE TABLE IF NOT EXISTS merchant_category_overrides (
                user_id INTEGER NOT NULL,
                merchant TEXT NOT NULL,
                category TEXT NOT NULL,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, merchant),
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            );
        """)
        cols = {r[1] for r in conn.execute("PRAGMA table_info(expense_entries)")}
        if cols and "source" not in cols:
            conn.execute("ALTER TABLE expense_entries ADD COLUMN source TEXT DEFAULT 'manual'")
        # 'manual' income is never overwritten by imports; 'import' income is kept in sync with imported salary.
        cols = {r[1] for r in conn.execute("PRAGMA table_info(monthly_budgets)")}
        if cols and "income_source" not in cols:
            conn.execute("ALTER TABLE monthly_budgets ADD COLUMN income_source TEXT DEFAULT 'manual'")
        conn.commit()
    finally:
        conn.close()
