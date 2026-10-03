"""Tables for imported credit reports. Created at startup; safe to run repeatedly."""

import sqlite3


def create_tables(db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS credit_report_imports (
                batch_id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                bureau TEXT,
                score INTEGER,
                accounts INTEGER NOT NULL DEFAULT 0,
                -- card details saved before this import overwrote them, so an undo can put them back
                prev_card_limit REAL,
                prev_card_balance REAL,
                card_details_set INTEGER NOT NULL DEFAULT 0,
                imported_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS credit_accounts (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                account_hash TEXT NOT NULL,
                lender TEXT NOT NULL,
                account_type TEXT NOT NULL,
                kind TEXT NOT NULL CHECK (kind IN ('loan', 'card')),
                account_number TEXT,
                opened TEXT,
                closed TEXT,
                sanctioned REAL,
                balance REAL,
                overdue REAL,
                emi REAL,
                tenure_months INTEGER,
                interest_rate REAL,
                loan_id TEXT,            -- the SmartFin loan created from this account, if any
                import_batch_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE (user_id, account_hash)
            );
            CREATE TABLE IF NOT EXISTS credit_account_history (
                account_id TEXT NOT NULL,
                month TEXT NOT NULL,     -- 'YYYY-MM'
                dpd INTEGER NOT NULL,    -- days past due that month
                PRIMARY KEY (account_id, month)
            );
            CREATE INDEX IF NOT EXISTS idx_credit_accounts_user ON credit_accounts(user_id);
        """)
        conn.commit()
    finally:
        conn.close()
