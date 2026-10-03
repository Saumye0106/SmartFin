"""
Parse a credit bureau report (PDF or plain text) into credit accounts.

Bureaus don't share a layout, so this reads the report as text and finds
fields by their labels ("Member Name" / "Lender", "Date Opened" / "Opened",
"Sanctioned" / "High Credit", ...). A new account starts at each lender
label. Two payment-history layouts are understood:

  - a row of statuses with a row of months under (or over) it:
        000 000 030 STD XXX
        09-26 08-26 07-26 06-26 05-26
  - a year-by-month grid:
        Year  Jan Feb Mar ...
        2026    0   0  30 ...

Statuses are days past due, or an asset class: STD (standard, on time),
SMA (special mention, overdue), SUB / DBT / LSS (sub-standard, doubtful,
loss: 90+ days). XXX or "-" means the lender reported nothing that month.

Everything works on in-memory bytes; nothing is written to disk.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from datetime import date

from statement_import.parser import StatementParseError, StatementPasswordRequired, parse_amount, parse_date

SUPPORTED_EXTENSIONS = (".pdf", ".txt")


class CreditReportParseError(StatementParseError):
    """The file couldn't be read as a credit report."""


class CreditReportNoTextError(CreditReportParseError):
    """The PDF's pages are images (a scan or an image export): there is no text to parse."""


# A real report has thousands of characters; an image-only PDF yields little more than page breaks.
MIN_TEXT_CHARS = 200


@dataclass
class ParsedAccount:
    lender: str
    account_type: str
    account_number: str | None = None
    opened: date | None = None
    closed: date | None = None
    sanctioned: float | None = None
    balance: float | None = None
    overdue: float | None = None
    emi: float | None = None
    tenure_months: int | None = None
    interest_rate: float | None = None
    # 'YYYY-MM' -> days past due; months the lender didn't report are left out
    history: dict[str, int] = field(default_factory=dict)


@dataclass
class ParsedReport:
    bureau: str | None
    score: int | None
    accounts: list[ParsedAccount]


# ── Labels ───────────────────────────────────────────────────────────────────
# Longer alternatives first, so "account type" wins over "type" and "date closed" over "closed".
_LABELS: list[tuple[str, str]] = [
    ("lender", r"member name|subscriber name|credit grantor|lender name|lender|institution"),
    ("account_type", r"account type|type of account|type"),
    ("account_number", r"account number|account no\.?|a/c no\.?"),
    ("ownership", r"ownership"),
    ("opened", r"date opened|date of opening|open date|opened"),
    ("closed", r"date closed|date of closure|closed"),
    ("last_payment", r"date of last payment|last payment date|last payment"),
    ("reported", r"date reported and certified|reported and certified|date reported"),
    ("sanctioned", r"sanctioned amt ?/ ?high(?:est)? credit|sanctioned amount|sanctioned amt|sanctioned"
                   r"|high(?:est)? credit|credit limit|disbursed amount"),
    ("balance", r"current balance|outstanding balance"),
    ("overdue", r"amount overdue|overdue amount|overdue"),
    ("emi", r"emi amount|instal?lment amount|emi"),
    ("tenure", r"repayment tenure|tenure"),
    ("rate", r"rate of interest|interest rate"),
]
_LABEL_RE = re.compile(
    "|".join(f"(?P<{name}>(?<![a-z]){pattern}(?![a-z]))" for name, pattern in _LABELS) + r"\s*[:\-]?\s*", re.I)
_HISTORY_MARKER = re.compile(r"days past due|payment history|asset classification", re.I)
_SECTION_END = re.compile(r"^\s*(enquir|credit enquir|end of report|summary)", re.I)

_MONTHS = {m: i for i, m in enumerate(
    ("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1)}
_STATUS_TOKEN = re.compile(r"^(\d{1,3}|std|sma|sub|dbt|lss|xxx|-|na)$", re.I)
_MONTH_TOKEN = re.compile(r"^(?:(\d{1,2})|([a-z]{3}))[-/](\d{2}|\d{4})$", re.I)
_ASSET_CLASS_DPD = {"std": 0, "sma": 30, "sub": 180, "dbt": 180, "lss": 180}


def status_to_dpd(token: str) -> int | None:
    """Days past due for a history cell; None when nothing was reported."""
    t = token.strip().lower()
    if t in ("xxx", "-", "na", ""):
        return None
    if t in _ASSET_CLASS_DPD:
        return _ASSET_CLASS_DPD[t]
    return int(t) if t.isdigit() else None


def _month_key(token: str) -> str | None:
    m = _MONTH_TOKEN.match(token.strip())
    if not m:
        return None
    month = int(m.group(1)) if m.group(1) else _MONTHS.get(m.group(2).lower())
    if not month or not 1 <= month <= 12:
        return None
    year = int(m.group(3))
    year += 2000 if year < 100 else 0
    return f"{year:04d}-{month:02d}"


# ── Reading the file ─────────────────────────────────────────────────────────

def _text_from_pdf(data: bytes, password: str | None) -> str:
    import pdfplumber
    from pdfminer.pdfdocument import PDFPasswordIncorrect

    try:
        pdf = pdfplumber.open(io.BytesIO(data), password=password or "")
    except Exception as e:
        # pdfplumber wraps pdfminer's PDFPasswordIncorrect in its own exception.
        if isinstance(e, PDFPasswordIncorrect) or isinstance(getattr(e, "__cause__", None), PDFPasswordIncorrect) \
                or any(isinstance(a, PDFPasswordIncorrect) for a in getattr(e, "args", ())):
            raise StatementPasswordRequired(
                "This PDF is password-protected. Bureaus usually use part of your name and date of birth."
                if not password else "That password didn't open the PDF.") from e
        raise CreditReportParseError(f"Could not open the PDF: {e}") from e
    with pdf:
        text = "\n".join((page.extract_text() or "") for page in pdf.pages)
        if len(text.strip()) < MIN_TEXT_CHARS:
            images = sum(len(page.images) for page in pdf.pages)
            raise CreditReportNoTextError(
                f"This PDF has no readable text: its {len(pdf.pages)} page(s) are images"
                f"{f' ({images} pictures)' if images else ''}, like a scan or a screenshot. "
                "SmartFin can only read reports that contain real text. Try downloading the report again as a PDF from "
                "the bureau's website, or open it there and use the browser's Print > Save as PDF. "
                "If you can select and copy words in the PDF with your mouse, tell us: that is a different problem.")
        return text


def _read_text(filename: str, data: bytes, password: str | None) -> str:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in SUPPORTED_EXTENSIONS:
        raise CreditReportParseError(f"Unsupported file type '{ext or filename}'. Upload the report as a PDF.")
    if not data:
        raise CreditReportParseError("The file is empty.")
    if ext == ".txt":
        return data.decode("utf-8-sig", errors="replace")
    return _text_from_pdf(data, password)


# ── Parsing ──────────────────────────────────────────────────────────────────

def _fields_in(line: str) -> list[tuple[str, str]]:
    """(field, value) for every label on a line; a value runs up to the next label."""
    matches = list(_LABEL_RE.finditer(line))
    out = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(line)
        out.append((m.lastgroup, line[m.end():end].strip(" :-\t")))
    return out


def _clean_number(value: str) -> float | None:
    return None if value.strip() in ("", "-", "--") else parse_amount(value)


def _apply(account: ParsedAccount, name: str, value: str) -> None:
    if name == "account_type":
        account.account_type = account.account_type or value
    elif name == "account_number":
        account.account_number = account.account_number or (value or None)
    elif name in ("opened", "closed"):
        setattr(account, name, getattr(account, name) or parse_date(value))
    elif name in ("sanctioned", "balance", "overdue", "emi"):
        if getattr(account, name) is None:
            setattr(account, name, _clean_number(value))
    elif name == "tenure":
        n = _clean_number(re.sub(r"(?i)\s*months?", "", value))
        account.tenure_months = account.tenure_months or (int(n) if n and n > 0 else None)
    elif name == "rate":
        n = _clean_number(value.replace("%", ""))
        account.interest_rate = account.interest_rate if account.interest_rate is not None else n


def _read_history(lines: list[str]) -> dict[str, int]:
    history: dict[str, int] = {}
    grid_months: list[int] | None = None
    pending_status: list[str] | None = None
    pending_months: list[str] | None = None

    def pair_up():
        nonlocal pending_status, pending_months
        if pending_status and pending_months and len(pending_status) == len(pending_months):
            for status, month in zip(pending_status, pending_months):
                dpd = status_to_dpd(status)
                if dpd is not None:
                    history[month] = dpd
            pending_status = pending_months = None

    for line in lines:
        tokens = line.split()
        if not tokens:
            continue
        lowered = [t.lower() for t in tokens]
        # grid header: "Year Jan Feb ..."
        month_cols = [_MONTHS[t[:3]] for t in lowered if t[:3] in _MONTHS and len(t) <= 9]
        if len(month_cols) >= 6 and len(month_cols) >= len(tokens) - 1:
            grid_months = month_cols
            continue
        # grid row: "2026 0 0 30 ..."
        if grid_months and re.fullmatch(r"20\d\d", tokens[0]) and all(_STATUS_TOKEN.match(t) for t in tokens[1:]):
            for month, status in zip(grid_months, tokens[1:]):
                dpd = status_to_dpd(status)
                if dpd is not None:
                    history[f"{tokens[0]}-{month:02d}"] = dpd
            continue
        months = [_month_key(t) for t in tokens]
        if all(months):
            pending_months = months
            pair_up()
        elif all(_STATUS_TOKEN.match(t) for t in tokens):
            pending_status = tokens
            pair_up()
    return history


def parse_credit_report(filename: str, data: bytes, password: str | None = None) -> ParsedReport:
    text = _read_text(filename, data, password)
    lines = [re.sub(r"[ \t]+", " ", raw).strip() for raw in text.splitlines()]
    low = text.lower()

    bureau = next((name for key, name in (("cibil", "CIBIL"), ("transunion", "CIBIL"), ("experian", "Experian"),
                                          ("equifax", "Equifax"), ("crif", "CRIF High Mark")) if key in low), None)
    score = None
    m = re.search(r"(?i)score\D{0,20}(\d{3})\b", text)
    if m and 300 <= int(m.group(1)) <= 900:
        score = int(m.group(1))

    accounts: list[ParsedAccount] = []
    current: ParsedAccount | None = None
    history_lines: list[str] | None = None

    def close_history():
        nonlocal history_lines
        if current is not None and history_lines:
            current.history.update(_read_history(history_lines))
        history_lines = None

    for line in lines:
        fields = _fields_in(line)
        starts_account = any(name == "lender" and value for name, value in fields)
        if starts_account or _SECTION_END.match(line):
            close_history()
            if not starts_account:
                current = None
                continue
        if starts_account:
            lender = next(value for name, value in fields if name == "lender")
            current = ParsedAccount(lender=lender, account_type="")
            accounts.append(current)
        if current is None:
            continue
        if history_lines is not None:
            history_lines.append(line)
            continue
        if _HISTORY_MARKER.search(line):
            history_lines = []
            continue
        for name, value in fields:
            _apply(current, name, value)
    close_history()

    accounts = [a for a in accounts if a.account_type or a.opened or a.sanctioned is not None]
    if not accounts:
        raise CreditReportParseError(
            "Couldn't find any credit accounts in this file. Expected a bureau report with account sections "
            "(lender / member name, account type, date opened, payment history).")
    return ParsedReport(bureau=bureau, score=score, accounts=accounts)
