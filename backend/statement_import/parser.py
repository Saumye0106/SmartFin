"""
Parse bank statements (CSV / XLS / XLSX / PDF) into normalized transactions.

Indian banks don't share a format, so instead of one hardcoded parser per
bank this finds the header row by keyword and maps columns by meaning:
  - date        ("Txn Date", "Transaction Date", "Date", "Value Dt", ...)
  - description ("Narration", "Description", "Particulars", "Remarks", ...), or, when
    there is no narration column, a payment-mode column plus a counterparty column
    ("mode" + "name") joined into one description
  - debit/credit as two columns ("Withdrawal Amt.", "Deposit Amt.", "Debit", "Credit")
    or one amount column plus a Dr/Cr indicator
  - balance (optional)
Rows above the header (account details) and below the table (totals,
disclaimers) are ignored because their "date" cell doesn't parse.

Everything works on in-memory bytes; nothing is written to disk.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass
from datetime import date, datetime

import pandas as pd

SUPPORTED_EXTENSIONS = (".csv", ".xls", ".xlsx", ".pdf")


class StatementParseError(ValueError):
    """The file couldn't be read as a bank statement."""


class StatementPasswordRequired(StatementParseError):
    """The PDF is encrypted and no (or a wrong) password was supplied."""


@dataclass
class ParsedTransaction:
    txn_date: date
    description: str
    amount: float
    direction: str  # "debit" | "credit"
    balance: float | None


# ── Column detection ─────────────────────────────────────────────────────────

_DESC_KEYS = ("narration", "description", "particulars", "remarks", "details", "transaction details")
_DEBIT_KEYS = ("withdrawal", "debit", "paid out", "dr amount", "dr amt")
_CREDIT_KEYS = ("deposit", "credit", "paid in", "cr amount", "cr amt")
# Compared with everything but letters removed, so "Dr/Cr", "DrCr" and "Dr | Cr" all match.
_DRCR_KEYS = ("drcr", "crdr", "debitcredit", "creditdebit", "txntype", "transactiontype", "type")
# Exports with no narration column: description = "<mode> <counterparty>".
_MODE_KEYS = ("mode", "channel", "payment mode", "txn mode", "transaction mode", "method")
_PARTY_KEYS = ("name", "payee", "merchant", "beneficiary", "counterparty", "party", "paid to", "to/from")


def _norm(cell) -> str:
    return re.sub(r"\s+", " ", str(cell or "")).strip().lower()


def _find_columns(header: list[str]) -> dict | None:
    """Map logical fields to column indexes for a candidate header row, or None."""
    cols: dict[str, int] = {}
    date_candidates = []
    for i, raw in enumerate(header):
        h = _norm(raw)
        if not h:
            continue
        if "date" in h or h in ("dt", "value dt", "txn dt"):
            date_candidates.append((i, h))
        elif any(k in h for k in _DESC_KEYS) and "desc" not in cols:
            cols["desc"] = i
        elif re.sub(r"[^a-z]", "", h) in _DRCR_KEYS and "drcr" not in cols:
            cols["drcr"] = i
        elif h in _MODE_KEYS and "mode" not in cols:
            cols["mode"] = i
        elif h in _PARTY_KEYS and "party" not in cols:
            cols["party"] = i
        elif (h in ("dr", "withdrawals", "debits") or any(k in h for k in _DEBIT_KEYS)) and "debit" not in cols:
            cols["debit"] = i
        elif (h in ("cr", "deposits", "credits") or any(k in h for k in _CREDIT_KEYS)) and "credit" not in cols:
            cols["credit"] = i
        elif ("balance" in h or h in ("bal", "bal.")) and "balance" not in cols:
            cols["balance"] = i
        elif "amount" in h and "amount" not in cols:
            cols["amount"] = i

    if not date_candidates or not ("desc" in cols or "mode" in cols or "party" in cols):
        return None
    # Prefer the transaction date over the value date when both exist.
    preferred = [c for c in date_candidates if "value" not in c[1]]
    cols["date"] = (preferred or date_candidates)[0][0]

    has_split = "debit" in cols and "credit" in cols
    has_signed = "amount" in cols
    if not (has_split or has_signed):
        return None
    return cols


# ── Cell parsing ─────────────────────────────────────────────────────────────

_DATE_FORMATS = (
    "%d/%m/%Y", "%d/%m/%y", "%d-%m-%Y", "%d-%m-%y", "%d.%m.%Y", "%d.%m.%y",
    "%d %b %Y", "%d-%b-%Y", "%d-%b-%y", "%d %b %y", "%d %B %Y", "%d-%B-%Y",
    "%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M",
)


def parse_date(value) -> date | None:
    """Day-first parsing only: Indian statements never use month-first dates."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    s = re.sub(r"\s+", " ", str(value or "")).strip()
    if not s or s.lower() in ("nan", "none"):
        return None
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def parse_amount(value) -> float | None:
    """'1,23,456.78', '₹ 500', 'INR 50.00', '(120.00)', '500.00 Dr' -> float; blank/'-' -> None."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return None if pd.isna(value) else float(value)
    s = str(value).strip()
    if not s or s.lower() in ("nan", "-", "--", "none"):
        return None
    negative = s.startswith("(") and s.endswith(")")
    s = re.sub(r"(?i)\b(inr|rs\.?|dr|cr)\b|₹|,|\(|\)|\s", "", s)
    if not s:
        return None
    try:
        num = float(s)
    except ValueError:
        return None
    return -num if negative else num


def _drcr_direction(value) -> str | None:
    v = _norm(value)
    if v.startswith("d"):
        return "debit"
    if v.startswith("c"):
        return "credit"
    return None


# ── Readers: every format becomes a list of string rows ──────────────────────

def _rows_from_csv(data: bytes) -> list[list[str]]:
    text = data.decode("utf-8-sig", errors="replace")
    return [row for row in csv.reader(io.StringIO(text))]


def _rows_from_excel(data: bytes, ext: str) -> list[list[str]]:
    engine = "xlrd" if ext == ".xls" else "openpyxl"
    try:
        df = pd.read_excel(io.BytesIO(data), header=None, dtype=object, engine=engine)
    except Exception as e:
        raise StatementParseError(f"Could not read the spreadsheet: {e}") from e
    rows = []
    for _, r in df.iterrows():
        rows.append(["" if pd.isna(v) else (v if isinstance(v, (datetime, date)) else str(v)) for v in r.tolist()])
    return rows


def _rows_from_pdf(data: bytes, password: str | None) -> list[list[str]]:
    import pdfplumber
    from pdfminer.pdfdocument import PDFPasswordIncorrect

    try:
        pdf = pdfplumber.open(io.BytesIO(data), password=password or "")
    except Exception as e:
        # pdfplumber wraps pdfminer's PDFPasswordIncorrect in its own exception.
        if isinstance(e, PDFPasswordIncorrect) or isinstance(getattr(e, "__cause__", None), PDFPasswordIncorrect) \
                or any(isinstance(a, PDFPasswordIncorrect) for a in getattr(e, "args", ())):
            raise StatementPasswordRequired(
                "This PDF is password-protected. Banks usually use a mix of your name and date of birth."
                if not password else "That password didn't open the PDF."
            ) from e
        raise StatementParseError(f"Could not open the PDF: {e}") from e

    rows: list[list[str]] = []
    with pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            if not tables:
                tables = page.extract_tables({"vertical_strategy": "text", "horizontal_strategy": "text"})
            for table in tables:
                for row in table:
                    rows.append([("" if c is None else str(c)) for c in row])
    return rows


def _read_rows(filename: str, data: bytes, password: str | None) -> list[list]:
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in SUPPORTED_EXTENSIONS:
        raise StatementParseError(f"Unsupported file type '{ext or filename}'. Upload CSV, XLS, XLSX or PDF.")
    if ext == ".csv":
        return _rows_from_csv(data)
    if ext in (".xls", ".xlsx"):
        return _rows_from_excel(data, ext)
    return _rows_from_pdf(data, password)


# ── Main entry point ─────────────────────────────────────────────────────────

def parse_statement(filename: str, data: bytes, password: str | None = None) -> list[ParsedTransaction]:
    rows = _read_rows(filename, data, password)
    if not rows:
        raise StatementParseError("The file is empty.")

    header_idx, cols = None, None
    for i, row in enumerate(rows[:80]):
        found = _find_columns(row)
        if found:
            header_idx, cols = i, found
            break
    if cols is None:
        raise StatementParseError(
            "Couldn't find the transaction table. Expected columns like Date, "
            "Narration/Description, and Withdrawal/Deposit (or Amount with Dr/Cr)."
        )
    header_norm = [_norm(c) for c in rows[header_idx]]

    def cell(row, key):
        i = cols.get(key)
        return row[i] if i is not None and i < len(row) else None

    txns: list[ParsedTransaction] = []
    for row in rows[header_idx + 1:]:
        if [_norm(c) for c in row] == header_norm:
            continue  # header repeated on each PDF page
        d = parse_date(cell(row, "date"))
        desc_cells = [cell(row, "desc")] if "desc" in cols else [cell(row, "mode"), cell(row, "party")]
        desc = re.sub(r"\s+", " ", " ".join(str(c or "") for c in desc_cells)).strip()
        if d is None:
            # Multi-line narrations: continuation rows have a description but no date.
            if "desc" in cols and desc and txns                     and all(not str(c).strip() for j, c in enumerate(row) if j != cols["desc"]):
                txns[-1].description = f"{txns[-1].description} {desc}".strip()
            continue

        if "debit" in cols and "credit" in cols:
            dr, cr = parse_amount(cell(row, "debit")), parse_amount(cell(row, "credit"))
            if dr and abs(dr) > 0:
                amount, direction = abs(dr), "debit"
            elif cr and abs(cr) > 0:
                amount, direction = abs(cr), "credit"
            else:
                continue
        else:
            amt = parse_amount(cell(row, "amount"))
            if not amt:
                continue
            raw_amount = str(cell(row, "amount") or "")
            direction = (
                _drcr_direction(cell(row, "drcr"))
                or _drcr_direction(re.findall(r"(?i)\b(dr|cr)\b", raw_amount)[-1] if re.findall(r"(?i)\b(dr|cr)\b", raw_amount) else "")
                or ("debit" if amt < 0 else "credit")
            )
            amount = abs(amt)

        txns.append(ParsedTransaction(
            txn_date=d,
            description=desc,
            amount=round(amount, 2),
            direction=direction,
            balance=parse_amount(cell(row, "balance")),
        ))

    if not txns:
        raise StatementParseError("Found the statement header but no transactions under it.")
    return txns
