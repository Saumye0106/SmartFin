"""risk_profile: the few risk-model inputs SmartFin has nowhere else to keep (credit-card limit and balance)."""

import sqlite3
import dbapi


def create_tables(db_path: str) -> None:
    conn = dbapi.connect(db_path)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS risk_profile (
                user_id INTEGER PRIMARY KEY,
                card_limit REAL CHECK (card_limit IS NULL OR card_limit > 0),
                card_balance REAL CHECK (card_balance IS NULL OR card_balance >= 0),
                updated_at TEXT
            )""")
        conn.commit()
    finally:
        conn.close()
