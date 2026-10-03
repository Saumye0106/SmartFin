"""
demo_seeder.py — Seeds realistic expense history for a demo user account.

Run from backend/ directory:
    python nudge_engine/demo_seeder.py --user-id 1 --weeks 16

Seeds 16 weeks of categorized expenses with:
  - Realistic Indian spending patterns
  - A week-1 "salary spike" on Shopping
  - Two anomalous high-spend weeks (for nudge demonstration)
"""

from __future__ import annotations

import argparse
import random
import sqlite3
import dbapi
from datetime import datetime, timedelta
from pathlib import Path


SEED = 42
random.seed(SEED)

# Category name → (weekly_mean_inr, weekly_std_inr)
CATEGORY_PROFILES = {
    "Food & Groceries":         (3200, 600),
    "Travel & Transport":       (1800, 400),
    "Shopping & Entertainment": (2500, 1200),
    "Rent & Housing":           (0, 0),       # Usually paid monthly; skip
    "EMI & Loans":              (0, 0),       # Handled via loans table; skip
    "Healthcare":               (400, 300),
    "Utilities":                (600, 100),
    "Other":                    (500, 200),
}

ANOMALY_WEEKS = [3, 10]       # 0-indexed weeks with anomalous shopping spend
ANOMALY_MULTIPLIER = 2.8


def _get_or_create_categories(cur: sqlite3.Cursor, user_id: int) -> dict[str, int]:
    """Return dict {category_name: category_id}, creating any that don't exist."""
    cat_ids = {}
    for cat_name in CATEGORY_PROFILES:
        if cat_name in ("Rent & Housing", "EMI & Loans"):
            continue
        cur.execute(
            "SELECT id FROM budget_categories WHERE user_id = ? AND name = ?",
            (user_id, cat_name),
        )
        row = cur.fetchone()
        if row:
            cat_ids[cat_name] = row[0]
        else:
            cur.execute(
                "INSERT INTO budget_categories (user_id, name, budget_limit, color) VALUES (?, ?, ?, ?)",
                (user_id, cat_name, CATEGORY_PROFILES[cat_name][0] * 4, "#6366f1"),
            )
            cat_ids[cat_name] = cur.lastrowid
    return cat_ids


def _week_start(weeks_ago: int) -> datetime:
    """Return the Monday of the week `weeks_ago` weeks in the past."""
    today = datetime.utcnow().date()
    monday = today - timedelta(days=today.weekday())
    return datetime.combine(monday - timedelta(weeks=weeks_ago), datetime.min.time())


def seed(db_path: str, user_id: int, n_weeks: int = 16, clear_existing: bool = False):
    """Seed expense data for a user."""
    conn = dbapi.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Verify user exists
    cur.execute("SELECT id, username FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    if not user:
        print(f"❌ User {user_id} not found in {db_path}")
        conn.close()
        return

    print(f"👤 Seeding for user: {user['username']} (id={user_id})")

    if clear_existing:
        cur.execute("DELETE FROM expenses WHERE user_id = ?", (user_id,))
        print("   Cleared existing expenses.")

    cat_ids = _get_or_create_categories(cur, user_id)
    total_inserted = 0

    for week_idx in range(n_weeks - 1, -1, -1):
        week_start = _week_start(week_idx)
        is_week1 = week_start.day <= 7  # First week of month
        is_anomaly = week_idx in ANOMALY_WEEKS

        for cat_name, (mean, std) in CATEGORY_PROFILES.items():
            if mean == 0:
                continue
            cat_id = cat_ids.get(cat_name)
            if cat_id is None:
                continue

            # Base amount
            amount = max(0, random.gauss(mean, std))

            # Week-1 salary spike: shopping goes up
            if is_week1 and cat_name == "Shopping & Entertainment":
                amount *= random.uniform(1.4, 1.8)

            # Anomaly weeks: shopping is unusually high
            if is_anomaly and cat_name == "Shopping & Entertainment":
                amount *= ANOMALY_MULTIPLIER

            if amount < 10:
                continue

            # Spread across 2-5 transactions in the week
            n_txn = random.randint(2, 5)
            for _ in range(n_txn):
                day_offset = random.randint(0, 6)
                txn_date = (week_start + timedelta(days=day_offset)).date()
                txn_amount = round(amount / n_txn * random.uniform(0.7, 1.3), 2)
                if txn_amount < 5:
                    continue

                cur.execute(
                    """INSERT INTO expenses (user_id, category_id, amount, description, date, created_at)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        user_id,
                        cat_id,
                        txn_amount,
                        f"Demo {cat_name} expense",
                        txn_date.isoformat(),
                        datetime.utcnow().isoformat(),
                    ),
                )
                total_inserted += 1

    conn.commit()
    conn.close()
    print(f"✅ Seeded {total_inserted} expense records across {n_weeks} weeks.")
    print(f"   Anomalous weeks (Shopping spike): weeks {ANOMALY_WEEKS} ago")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed demo expense data for SmartFin nudge engine")
    parser.add_argument("--user-id", type=int, default=1)
    parser.add_argument("--weeks", type=int, default=16)
    parser.add_argument("--clear", action="store_true", help="Clear existing expenses first")
    parser.add_argument(
        "--db",
        default=str(Path(__file__).parent.parent / "auth.db"),
    )
    args = parser.parse_args()
    seed(args.db, args.user_id, args.weeks, args.clear)
