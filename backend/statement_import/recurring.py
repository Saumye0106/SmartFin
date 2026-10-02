"""
Recurring-payment and income detection over a user's imported transactions.

A merchant stream counts as recurring when:
  - it has at least MIN_OCCURRENCES transactions in the same direction,
  - the median gap between them falls in a known cadence band (weekly,
    monthly, quarterly, yearly) and at least 75% of gaps fall in that band,
  - the amount is reasonably stable (coefficient of variation <= 0.35, so a
    variable electricity bill qualifies but irregular food orders don't).

Gap-based rather than calendar-based, so a 28-day prepaid recharge or a
salary that lands on the 30th one month still qualifies.
"""

from __future__ import annotations

import re
import statistics
from collections import Counter, defaultdict
from datetime import date, timedelta

MIN_OCCURRENCES = 3
MAX_AMOUNT_CV = 0.35
FIXED_AMOUNT_CV = 0.05
MIN_SHARE_IN_BAND = 0.75
DAYS_PER_MONTH = 30.44

# name, (min_gap, max_gap) in days
CADENCES = (
    ("weekly", (5, 9)),
    ("monthly", (25, 36)),
    ("quarterly", (80, 100)),
    ("yearly", (345, 385)),
)

_PER_MONTH = {"weekly": 52 / 12, "quarterly": 1 / 3, "yearly": 1 / 12}
# Salary that lands this close to month-end usually belongs to the next month.
EARLY_PAY_WINDOW_DAYS = 5


def _add_month(d: date) -> date:
    y, m = (d.year + 1, 1) if d.month == 12 else (d.year, d.month + 1)
    last_day = (date(y + (m == 12), m % 12 + 1, 1) - timedelta(days=1)).day
    return date(y, m, min(d.day, last_day))


def _calendar_monthly(cadence: str, median_gap: float) -> bool:
    """Calendar-month billing (gaps of 29-31 days) vs fixed-length cycles like 28-day prepaid plans."""
    return cadence == "monthly" and median_gap >= 29


_SALARY = re.compile(r"(?<![a-z])(salary|sal|payroll|stipend)(?![a-z])")


def _kind(direction: str, category: str) -> str:
    if direction == "credit":
        return "income"
    return {"rent": "rent", "emi": "emi", "investment": "investment", "insurance": "insurance"}.get(category, "bill")


def detect_recurring(txns: list[dict], as_of: date | None = None) -> list[dict]:
    """
    txns: dicts with txn_date (date or 'YYYY-MM-DD'), merchant, direction, amount, category, id (optional).
    Returns one entry per recurring stream, largest monthly impact first.
    """
    groups: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for t in txns:
        d = t["txn_date"] if isinstance(t["txn_date"], date) else date.fromisoformat(t["txn_date"])
        groups[((t.get("merchant") or "").strip().lower(), t["direction"])].append({**t, "_d": d})

    if as_of is None:
        all_dates = [t["_d"] for g in groups.values() for t in g]
        as_of = max(all_dates) if all_dates else date.today()

    out = []
    for (merchant_key, direction), items in groups.items():
        if not merchant_key or len(items) < MIN_OCCURRENCES:
            continue
        items.sort(key=lambda t: t["_d"])
        gaps = [(b["_d"] - a["_d"]).days for a, b in zip(items, items[1:])]
        gaps = [g for g in gaps if g > 0] or [0]
        median_gap = statistics.median(gaps)
        cadence = next(((name, band) for name, band in CADENCES if band[0] <= median_gap <= band[1]), None)
        if cadence is None:
            continue
        name, (lo, hi) = cadence
        if sum(lo <= g <= hi for g in gaps) / len(gaps) < MIN_SHARE_IN_BAND:
            continue

        amounts = [float(t["amount"]) for t in items]
        mean_amt = statistics.mean(amounts)
        cv = statistics.pstdev(amounts) / mean_amt if mean_amt else 1.0
        if cv > MAX_AMOUNT_CV:
            continue

        typical = round(statistics.median(amounts), 2)
        last = items[-1]["_d"]
        category = Counter(t["category"] for t in items).most_common(1)[0][0]
        out.append({
            "merchant": items[-1].get("merchant") or merchant_key.title(),
            "direction": direction,
            "kind": _kind(direction, category),
            "category": category,
            "cadence": name,
            "interval_days": round(median_gap),
            "amount_type": "fixed" if cv <= FIXED_AMOUNT_CV else "variable",
            "typical_amount": typical,
            "monthly_equivalent": round(typical * (
                1 if _calendar_monthly(name, median_gap)
                else _PER_MONTH.get(name, DAYS_PER_MONTH / median_gap)), 2),
            "occurrences": len(items),
            "first_date": items[0]["_d"].isoformat(),
            "last_date": last.isoformat(),
            "next_expected": (_add_month(last) if _calendar_monthly(name, median_gap)
                              else last + timedelta(days=round(median_gap))).isoformat(),
            # Stopped streams (e.g. a cancelled subscription) are reported but flagged inactive.
            "active": (as_of - last).days <= hi * 1.5,
            "txn_ids": [t["id"] for t in items if t.get("id")],
        })

    out.sort(key=lambda r: -r["monthly_equivalent"])
    return out


def detect_monthly_income(txns: list[dict], recurring: list[dict] | None = None) -> dict[str, float]:
    """
    Salary-like income per month ('YYYY-MM' -> amount): credits that belong to a
    monthly recurring income stream, plus any credit whose narration says
    salary/stipend/payroll (so a single-month statement still works). Refunds,
    cashback and interest are deliberately excluded: they aren't budgetable income.
    """
    if recurring is None:
        recurring = detect_recurring(txns)
    stream_merchants = {r["merchant"].lower() for r in recurring
                        if r["direction"] == "credit" and r["cadence"] == "monthly"}

    income = []
    for t in txns:
        if t["direction"] != "credit" or t.get("category") not in ("income", None):
            continue
        desc = (t.get("description") or "").lower()
        merchant = (t.get("merchant") or "").lower()
        if merchant in stream_merchants or _SALARY.search(desc):
            d = t["txn_date"] if isinstance(t["txn_date"], date) else date.fromisoformat(t["txn_date"])
            income.append((merchant, d, float(t["amount"])))

    # Attribute early-paid salary (e.g. June's salary on 30 May) to the month it's for:
    # if it lands in the last few days of a month and that payer has no credit next month.
    months_by_payer: dict[str, set[str]] = defaultdict(set)
    for merchant, d, _ in income:
        months_by_payer[merchant].add(d.strftime("%Y-%m"))
    by_month: dict[str, float] = defaultdict(float)
    for merchant, d, amount in income:
        month = d.strftime("%Y-%m")
        next_month = _add_month(d.replace(day=1)).strftime("%Y-%m")
        days_left = (_add_month(d.replace(day=1)) - d).days
        if days_left <= EARLY_PAY_WINDOW_DAYS and next_month not in months_by_payer[merchant]:
            month = next_month
        by_month[month] += amount
    return {m: round(v, 2) for m, v in sorted(by_month.items())}
