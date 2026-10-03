"""
Merchant extraction and categorization for bank-statement narrations.

Order of precedence:
  1. The user's own corrections (merchant -> category), learned on import.
  2. A keyword rulebook of common Indian merchants/billers.
  3. "other" for debits / "income" for credits.

There is no trained classifier yet on purpose: SmartFin has no real
labelled transactions to train one on. User corrections are stored so a
classifier can be trained on genuine labels later.
"""

from __future__ import annotations

import re

# Budget categories the rest of the app understands (budget/service.py),
# plus two import-only categories that never become expenses.
EXPENSE_CATEGORIES = ("rent", "food", "travel", "shopping", "emi", "utilities",
                      "healthcare", "education", "insurance", "other")
NON_EXPENSE_CATEGORIES = ("income", "transfer", "investment")
ALL_CATEGORIES = EXPENSE_CATEGORIES + NON_EXPENSE_CATEGORIES

# (category, keywords) — checked in order against the lowercased narration.
_DEBIT_RULES: list[tuple[str, tuple[str, ...]]] = [
    # Before "emi": SIPs are often collected via NACH mandates too, but they are savings, not spending.
    ("investment", ("sip", "mutual fund", "mf", "bse star", "nse mfss", "cams", "kfintech", "kfin", "zerodha",
                    "coin by zerodha", "groww", "kuvera", "upstox", "paytm money", "indmoney", "et money", "smallcase",
                    "nps", "ppf", "rd installment", "recurring deposit")),
    ("emi", ("emi", "loan", "bajaj fin", "bajajfin", "home credit", "nach", "ach d", "ecs/", "hdfc ltd", "lic housing", "tata capital", "fullerton")),
    ("insurance", ("insurance", "policybazaar", "lic of india", "lic premium", "hdfc ergo", "icici lombard", "star health", "acko", "digit insurance", "max life", "sbi life")),
    ("rent", ("rent", "nobroker", "nestaway", "housing.com", "landlord")),
    ("food", ("swiggy", "zomato", "dominos", "domino's", "mcdonald", "kfc", "starbucks", "pizza hut", "burger king",
              "eatsure", "faasos", "blinkit", "zepto", "bigbasket", "big basket", "dmart", "instamart", "jiomart",
              "restaurant", "cafe", "bakery", "chai", "dunzo", "licious", "freshtohome", "haldiram")),
    ("travel", ("uber", "ola ", "olacabs", "ola cabs", "rapido", "irctc", "makemytrip", "goibibo", "redbus", "cleartrip",
                "yatra", "ixigo", "indigo", "air india", "vistara", "akasa", "spicejet", "metro", "fastag", "petrol",
                "hpcl", "bpcl", "iocl", "indian oil", "shell", "fuel")),
    ("shopping", ("amazon", "amzn", "flipkart", "myntra", "ajio", "meesho", "nykaa", "croma", "reliance digital",
                  "decathlon", "tata cliq", "lenskart", "snapdeal", "firstcry", "ikea", "pantaloons", "westside",
                  "lifestyle", "shoppers stop", "h&m", "zara", "uniqlo")),
    ("utilities", ("airtel", "jio", "jioinapp", "vodafone", "vi prepaid", "bsnl", "electricity", "bescom", "msedcl", "mseb",
                   "tata power", "adani electricity", "torrent power", "tneb", "bses", "hescom", "indane", "hp gas", "bharat gas",
                   "broadband", "act fibernet", "hathway", "recharge", "water bill", "dth", "tata play", "dish tv",
                   "netflix", "spotify", "hotstar", "prime video", "youtube premium", "google play", "apple.com")),
    ("healthcare", ("apollo", "pharmeasy", "1mg", "netmeds", "medplus", "hospital", "clinic", "pharmacy",
                    "practo", "diagnostic", "lal path", "thyrocare", "medical")),
    ("education", ("udemy", "coursera", "byju", "unacademy", "upgrad", "college", "university", "school", "tuition",
                   "exam fee", "course fee", "vedantu", "physics wallah")),
]

_CREDIT_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("income", ("salary", "sal ", "sal/", "payroll", "stipend", "interest", "int.pd", "int pd", "sbint", "cashback",
                "refund", "reversal", "dividend")),
]

_SELF_TRANSFER_HINTS = ("self", "own account", "to own", "sweep", "fd booked", "fd closure")

# Tokens that are never the merchant name in a narration.
_STOP = {
    "upi", "imps", "neft", "rtgs", "nach", "ach", "ecs", "pos", "atm", "cr", "dr", "p2a", "p2m", "to", "by", "from",
    "transfer", "trf", "txn", "ref", "inb", "mb", "ib", "bil", "billpay", "payment", "paid", "via", "pay", "upiint",
    "collect", "intent", "nwd", "nfs", "vps", "ecom", "debit", "credit", "card", "ltd", "pvt", "limited", "india",
    "sbin", "hdfc", "icic", "utib", "kkbk", "ybl", "okaxis", "okicici", "oksbi", "okhdfcbank", "paytm", "axl", "ibl",
}


# Single-word keywords this long may also match as the start of a longer word, because
# statements run names together or cut them short ("AMAZONPAY", "DOMINOSP", "HESCOMBI").
_PREFIX_MATCH_MIN_LEN = 6


def _has_word(text: str, keyword: str) -> bool:
    """Whole-word match, so 'emi' doesn't hit 'premium' and 'rent' doesn't hit 'current'."""
    k = keyword.strip()
    tail = "" if len(k) >= _PREFIX_MATCH_MIN_LEN and k.isalnum() else "(?![a-z0-9])"
    return re.search(rf"(?<![a-z0-9]){re.escape(k)}{tail}", text) is not None


def extract_merchant(description: str) -> str:
    """Best-effort human-readable counterparty from a raw narration."""
    d = description or ""
    low = d.lower()
    if any(k in low for k in ("atm", "cash wdl", "cash withdrawal", "nwd")):
        return "Cash withdrawal"
    tokens = re.split(r"[/\-|:*@]+|\s{2,}", d)
    for tok in tokens:
        t = tok.strip()
        tl = t.lower()
        if len(t) < 3 or tl in _STOP or not re.search(r"[a-zA-Z]{3,}", t):
            continue
        if re.fullmatch(r"[A-Za-z]{4}0[A-Za-z0-9]{6}", t):  # IFSC code
            continue
        if re.search(r"\d{5,}", t):  # reference numbers
            continue
        words = [w for w in re.split(r"\s+", t)
                 if w.lower() not in _STOP
                 and not re.search(r"\d{3,}", w)          # reference / card numbers
                 and not re.search(r"(?i)x{3,}", w)]      # masked card numbers
        name = " ".join(words).strip()
        if len(name) >= 3:
            return name.title()[:60]
    return (d.strip()[:40] or "Unknown").title()


def categorize(description: str, direction: str, merchant: str,
               user_overrides: dict[str, str] | None = None) -> tuple[str, str]:
    """Return (category, source) where source is 'user_rule' | 'keyword' | 'default'."""
    if user_overrides and merchant.lower() in user_overrides:
        return user_overrides[merchant.lower()], "user_rule"

    low = description.lower()
    if any(_has_word(low, h) for h in _SELF_TRANSFER_HINTS):
        return "transfer", "keyword"

    rules = _DEBIT_RULES if direction == "debit" else _CREDIT_RULES
    for category, keywords in rules:
        if any(_has_word(low, k) for k in keywords):
            return category, "keyword"

    return ("other" if direction == "debit" else "income"), "default"
