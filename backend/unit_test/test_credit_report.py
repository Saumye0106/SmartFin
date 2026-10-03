"""Credit report import: parser on SAMPLE reports, preview/confirm/undo, and what it feeds the risk model."""

import sqlite3
import sys
from datetime import date
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from credit_report import service
from credit_report.migrations import create_tables
from credit_report.describe_layout import describe, redact_line
from credit_report.parser import CreditReportNoTextError, CreditReportParseError, parse_credit_report, status_to_dpd
from risk_scorer.migrations import create_tables as create_risk_tables
from risk_scorer.service import assess_request, get_risk_profile, save_risk_profile, user_history
from statement_import.parser import StatementParseError, StatementPasswordRequired

FIXTURES = Path(__file__).parent / "fixtures" / "credit_reports"
PASSWORD = "SAMP0101"


def _read(name):
    return (FIXTURES / name).read_bytes()


# ── Parser ───────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("name,password,bureau", [
    ("cibil_style.pdf", None, "CIBIL"),
    ("experian_style.pdf", None, "Experian"),
    ("cibil_style_protected.pdf", PASSWORD, "CIBIL"),
    ("cibil_style.txt", None, "CIBIL"),
])
def test_both_layouts_give_the_same_accounts(name, password, bureau):
    report = parse_credit_report(name, _read(name), password)
    assert report.bureau == bureau and report.score == 731 and len(report.accounts) == 5
    hdfc, sbi, card, bajaj, axis = report.accounts
    assert (hdfc.lender.upper(), hdfc.account_type.upper(), hdfc.account_number) == ("HDFC BANK", "PERSONAL LOAN", "XXXXXX4521")
    assert (hdfc.opened, hdfc.closed) == (date(2025, 3, 15), None)
    assert (hdfc.sanctioned, hdfc.balance, hdfc.overdue, hdfc.emi, hdfc.tenure_months, hdfc.interest_rate) == \
        (300000.0, 210000.0, 0.0, 9960.0, 36, 12.0)
    assert len(hdfc.history) == 18 and hdfc.history["2026-01"] == 30 and hdfc.history["2026-09"] == 0
    assert (sbi.sanctioned, sbi.tenure_months, sbi.interest_rate) == (2500000.0, 240, 8.6)
    assert "2025-03" not in sbi.history and len(sbi.history) == 23          # XXX = not reported, so left out
    assert (card.sanctioned, card.balance, card.emi) == (150000.0, 42000.0, None)
    assert (card.history["2025-11"], card.history["2025-12"]) == (30, 60)
    assert bajaj.closed == date(2025, 8, 20) and bajaj.history["2025-04"] == 90 and len(bajaj.history) == 12
    assert (axis.emi, axis.interest_rate, axis.tenure_months) == (None, None, 24) and len(axis.history) == 7


def test_protected_pdf_asks_for_a_password():
    with pytest.raises(StatementPasswordRequired):
        parse_credit_report("cibil_style_protected.pdf", _read("cibil_style_protected.pdf"))
    with pytest.raises(StatementPasswordRequired):
        parse_credit_report("cibil_style_protected.pdf", _read("cibil_style_protected.pdf"), "wrong")


@pytest.mark.parametrize("name,data", [
    ("report.docx", b"x"), ("empty.pdf", b""), ("broken.pdf", b"not a pdf"),
    ("notes.txt", b"just some notes about my finances\nnothing else"),
])
def test_rejects_files_that_are_not_credit_reports(name, data):
    with pytest.raises(StatementParseError):
        parse_credit_report(name, data)
    assert issubclass(CreditReportParseError, StatementParseError)


@pytest.mark.parametrize("token,dpd", [("000", 0), ("030", 30), ("90", 90), ("STD", 0), ("SMA", 30), ("SUB", 180),
                                       ("DBT", 180), ("LSS", 180), ("XXX", None), ("-", None)])
def test_status_tokens(token, dpd):
    assert status_to_dpd(token) == dpd


@pytest.mark.parametrize("account_type,expected", [
    ("PERSONAL LOAN", ("loan", "personal")), ("Housing Loan", ("loan", "home")), ("TWO-WHEELER LOAN", ("loan", "auto")),
    ("Auto Loan (Personal)", ("loan", "auto")), ("Education Loan", ("loan", "education")),
    ("CONSUMER LOAN", ("loan", "personal")), ("Gold Loan", ("loan", "personal")), ("CREDIT CARD", ("card", None)),
])
def test_account_classification(account_type, expected):
    assert service.classify_account(account_type) == expected


def test_days_past_due_map_to_the_models_definitions():
    assert [service.payment_status(d) for d in (0, 15, 29, 30, 60, 89, 90, 180)] == \
        ["on-time", "on-time", "on-time", "late", "late", "late", "missed", "missed"]
    assert service.emi_for(300000, 12.0, 36) == pytest.approx(9964.29, abs=0.01)
    assert service.emi_for(12000, 0, 12) == 1000.0


# ── Preview / confirm / undo on a temp DB ────────────────────────────────────

@pytest.fixture
def conn(tmp_path, monkeypatch):
    db = tmp_path / "t.db"
    c = sqlite3.connect(db)
    c.executescript("""
        CREATE TABLE users_profile (user_id INTEGER PRIMARY KEY, age INTEGER);
        INSERT INTO users_profile VALUES (1, 29), (2, 35);
        CREATE TABLE loans (loan_id TEXT PRIMARY KEY, user_id INTEGER NOT NULL,
            loan_type TEXT NOT NULL CHECK (loan_type IN ('personal', 'home', 'auto', 'education')),
            loan_amount REAL NOT NULL CHECK (loan_amount > 0), loan_tenure INTEGER NOT NULL CHECK (loan_tenure > 0),
            monthly_emi REAL NOT NULL CHECK (monthly_emi > 0),
            interest_rate REAL NOT NULL CHECK (interest_rate >= 0 AND interest_rate <= 50),
            loan_start_date TEXT NOT NULL, loan_maturity_date TEXT NOT NULL, default_status INTEGER DEFAULT 0,
            created_at TEXT, updated_at TEXT, deleted_at TEXT);
        CREATE TABLE loan_payments (payment_id TEXT PRIMARY KEY, loan_id TEXT NOT NULL, payment_date TEXT NOT NULL,
            payment_amount REAL NOT NULL CHECK (payment_amount > 0),
            payment_status TEXT NOT NULL CHECK (payment_status IN ('on-time', 'late', 'missed')), created_at TEXT, updated_at TEXT);
        CREATE TABLE loan_metrics (user_id INTEGER PRIMARY KEY, calculated_at TEXT);
        INSERT INTO loan_metrics VALUES (1, 'stale'), (2, 'other user');
    """)
    c.commit()
    c.close()
    create_tables(str(db))
    create_risk_tables(str(db))
    # The sample report is dated Sep 2026; pin the 24-month window so the counts don't drift as time passes.
    monkeypatch.setattr(service, "_window_start", lambda today=None: "2024-10")
    c = sqlite3.connect(db)
    c.row_factory = sqlite3.Row
    yield c
    c.close()


def _preview(conn, user_id=1, name="cibil_style.pdf"):
    return service.preview(conn, user_id, name, _read(name))


def test_preview_decides_how_each_account_is_imported(conn):
    p = _preview(conn)
    assert (p["bureau"], p["score"]) == ("CIBIL", 731)
    by = {r["lender"]: r for r in p["rows"]}
    assert [(r["lender"], r["import_as"], r["needs"]) for r in p["rows"]] == [
        ("HDFC BANK", "loan", []), ("STATE BANK OF INDIA", "loan", []), ("ICICI BANK", "card", []),
        ("BAJAJ FINANCE LTD", "history_only", []),                      # closed
        ("AXIS BANK", "history_only", ["emi", "interest_rate"]),       # open, but the report has no EMI or rate
    ]
    assert (by["HDFC BANK"]["late_24m"], by["ICICI BANK"]["late_24m"]) == (1, 2)
    assert (by["BAJAJ FINANCE LTD"]["late_24m"], by["BAJAJ FINANCE LTD"]["missed_24m"]) == (2, 1)
    assert p["summary"] == {"accounts": 5, "open_loans": 3, "closed_loans": 1, "cards": 1, "late_24m": 5, "missed_24m": 1,
                            "card_limit": 150000.0, "card_balance": 42000.0, "history_window_months": 24}
    assert not any(r["already_imported"] for r in p["rows"])
    assert conn.execute("SELECT COUNT(*) FROM credit_accounts").fetchone()[0] == 0     # preview saves nothing


def test_confirm_creates_loans_payments_history_and_card_details(conn):
    p = _preview(conn)
    res = service.confirm(conn, 1, p["rows"], p["bureau"], p["score"])
    assert (res["accounts_added"], res["loans_created"], res["cards"], res["history_only"]) == (5, 2, 1, 2)
    assert res["payments_recorded"] == 18 + 23 and res["history_months"] == 18 + 23 + 24 + 12 + 7
    loans = {r["loan_type"]: dict(r) for r in conn.execute("SELECT * FROM loans WHERE user_id = 1")}
    assert set(loans) == {"personal", "home"}
    assert (loans["personal"]["loan_amount"], loans["personal"]["monthly_emi"], loans["personal"]["loan_tenure"],
            loans["personal"]["interest_rate"], loans["personal"]["loan_start_date"], loans["personal"]["loan_maturity_date"]) == \
        (300000.0, 9960.0, 36, 12.0, "2025-03-15", "2028-03-15")
    statuses = dict(conn.execute("SELECT payment_status, COUNT(*) FROM loan_payments WHERE loan_id = ? GROUP BY 1",
                                 (loans["personal"]["loan_id"],)).fetchall())
    assert statuses == {"on-time": 17, "late": 1}
    assert get_risk_profile(conn, 1) == {"card_limit": 150000.0, "card_balance": 42000.0}
    assert (res["card_limit"], res["card_balance"]) == (150000.0, 42000.0)
    assert [r[0] for r in conn.execute("SELECT user_id FROM loan_metrics")] == [2]        # user 1's cached scores cleared
    assert conn.execute("SELECT bureau, score, accounts FROM credit_report_imports").fetchone()[:] == ("CIBIL", 731, 5)


def test_filling_in_missing_details_turns_an_account_into_a_loan(conn):
    rows = _preview(conn)["rows"]
    axis = next(r for r in rows if r["lender"] == "AXIS BANK")
    axis["interest_rate"] = 11.5                                  # user types the rate; EMI is then calculated
    res = service.confirm(conn, 1, rows)
    assert res["loans_created"] == 3 and res["history_only"] == 1
    emi, loan_type = conn.execute("SELECT monthly_emi, loan_type FROM loans WHERE loan_amount = 90000").fetchone()
    assert loan_type == "auto" and emi == service.emi_for(90000, 11.5, 24)


def test_reimport_updates_instead_of_duplicating(conn):
    first = service.confirm(conn, 1, _preview(conn)["rows"])
    again = _preview(conn, name="experian_style.pdf")              # same accounts, other bureau's layout
    # lender/type casing differs between the two layouts; identity must not
    assert all(r["already_imported"] for r in again["rows"])
    res = service.confirm(conn, 1, again["rows"])
    assert (res["accounts_added"], res["accounts_updated"], res["loans_created"], res["payments_recorded"], res["history_months"]) == \
        (0, 5, 0, 0, 0)
    assert conn.execute("SELECT COUNT(*) FROM credit_accounts").fetchone()[0] == 5
    assert conn.execute("SELECT COUNT(*) FROM loans").fetchone()[0] == 2
    assert conn.execute("SELECT COUNT(*) FROM loan_payments").fetchone()[0] == first["payments_recorded"]


def test_newer_report_adds_only_the_new_months(conn):
    rows = _preview(conn)["rows"]
    service.confirm(conn, 1, rows)
    hdfc = next(r for r in rows if r["lender"] == "HDFC BANK")
    hdfc["history"] = hdfc["history"] + [{"month": "2026-10", "dpd": 45}]
    hdfc["balance"] = 201000
    res = service.confirm(conn, 1, [hdfc])
    assert (res["accounts_updated"], res["payments_recorded"], res["history_months"]) == (1, 1, 1)
    assert conn.execute("SELECT payment_status FROM loan_payments WHERE payment_date = '2026-10-01'").fetchone()[0] == "late"
    assert conn.execute("SELECT balance FROM credit_accounts WHERE lender = 'HDFC BANK'").fetchone()[0] == 201000


def test_users_are_isolated(conn):
    service.confirm(conn, 1, _preview(conn)["rows"])
    assert not any(r["already_imported"] for r in _preview(conn, user_id=2)["rows"])
    assert service.list_imports(conn, 2) == {"imports": [], "accounts": []}
    assert service.undo_batch(conn, 2, service.list_imports(conn, 1)["imports"][0]["batch_id"])["found"] is False
    assert conn.execute("SELECT COUNT(*) FROM credit_accounts WHERE user_id = 1").fetchone()[0] == 5


def test_undo_removes_everything_the_import_created_and_restores_card_details(conn):
    save_risk_profile(conn, 1, 50000, 1000)                        # typed earlier by the user
    res = service.confirm(conn, 1, _preview(conn)["rows"])
    assert get_risk_profile(conn, 1)["card_limit"] == 150000.0
    listing = service.list_imports(conn, 1)
    assert len(listing["imports"]) == 1 and len(listing["accounts"]) == 5
    card = next(a for a in listing["accounts"] if a["kind"] == "card")
    assert (card["late_24m"], card["missed_24m"], card["months_24m"]) == (2, 0, 24) and "id" not in card
    out = service.undo_batch(conn, 1, res["batch_id"])
    assert out == {"found": True, "accounts_removed": 5, "loans_removed": 2}
    for table in ("credit_accounts", "credit_account_history", "credit_report_imports", "loans", "loan_payments"):
        assert conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0, table
    assert get_risk_profile(conn, 1) == {"card_limit": 50000.0, "card_balance": 1000.0}
    assert service.undo_batch(conn, 1, res["batch_id"])["found"] is False


@pytest.mark.parametrize("mutate,message", [
    (lambda r: r.update(lender=""), "lender"),
    (lambda r: r.update(emi="abc"), "EMI"),
    (lambda r: r.update(interest_rate=80), "interest rate"),
    (lambda r: r.update(loan_type="mortgage"), "Loan type"),
    (lambda r: r.update(opened="15/03/2025"), "opened"),
    (lambda r: r.update(history=[{"month": "2026-13", "dpd": 0}]), "YYYY-MM"),
    (lambda r: r.update(history=[{"month": "2026-01", "dpd": -5}]), "days past due"),
])
def test_confirm_revalidates_what_the_client_sends(conn, mutate, message):
    rows = _preview(conn)["rows"][:1]
    mutate(rows[0])
    with pytest.raises(ValueError, match=message):
        service.confirm(conn, 1, rows)
    assert conn.execute("SELECT COUNT(*) FROM credit_accounts").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM loans").fetchone()[0] == 0


def test_confirm_rejects_empty_and_duplicate_selections(conn):
    rows = _preview(conn)["rows"]
    for bad in ([], None, [dict(r, include=False) for r in rows], [rows[0], rows[0]]):
        with pytest.raises(ValueError):
            service.confirm(conn, 1, bad)


# ── What the import gives the risk model ─────────────────────────────────────

def _month(offset):
    """'YYYY-MM' for `offset` months before the current month."""
    return service._add_months(date.today().replace(day=1), -offset).strftime("%Y-%m")


def test_imported_history_reaches_the_risk_model(conn):
    assert user_history(conn, 1) == {"age": 29, "times_late": 0, "times_seriously_late": 0, "payments_on_record": 0}
    before = assess_request({"income": 0}, user_history(conn, 1))
    assert before["score"] is None and before["confidence"] == "insufficient"

    loan = dict(lender="Some Bank", account_type="Personal Loan", account_number="X1", opened="2024-01-10", sanctioned=200000,
                balance=120000, emi=7000, tenure_months=36, interest_rate=13,
                history=[{"month": _month(i), "dpd": d} for i, d in ((1, 0), (2, 0), (3, 35), (4, 0), (30, 120))])
    card = dict(lender="Card Co", account_type="Credit Card", account_number="X2", opened="2023-05-01", sanctioned=100000,
                balance=80000, history=[{"month": _month(i), "dpd": d} for i, d in ((1, 0), (2, 95), (3, 60), (4, 10))])
    closed = dict(lender="Old Lender", account_type="Consumer Loan", account_number="X3", opened="2023-01-01",
                  closed="2025-12-01", sanctioned=30000, balance=0,
                  history=[{"month": _month(5), "dpd": 30}, {"month": _month(40), "dpd": 180}])
    service.confirm(conn, 1, [loan, card, closed])

    h = user_history(conn, 1)
    # in the last 2 years: loan 1 late (the 120-day month is 30 months old), card 1 late + 1 missed, closed loan 1 late
    assert (h["times_late"], h["times_seriously_late"]) == (3, 1)
    assert h["payments_on_record"] == 4 + 4 + 1 and (h["card_limit"], h["card_balance"]) == (100000.0, 80000.0)

    after = assess_request({"income": 0}, h)
    assert after["confidence"] == "good" and after["score"] is not None
    assert after["features"]["utilization"] == 0.8 and after["features"]["times_late"] == 3.0
    assert {d["feature"] for d in after["drivers"][:3]} >= {"times_late", "times_seriously_late"}
    clean = assess_request({"income": 0}, {"age": 29, "times_late": 0, "times_seriously_late": 0, "payments_on_record": 9,
                                           "card_limit": 100000, "card_balance": 80000})
    assert after["risk_probability"] > 2 * clean["risk_probability"]


# ── Image-only PDFs and the redacted layout tool ─────────────────────────────

@pytest.fixture
def image_only_pdf(tmp_path):
    """A PDF whose pages are pictures of text, like a scanned report."""
    from PIL import Image, ImageDraw
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    img = tmp_path / "page.png"
    picture = Image.new("RGB", (800, 1100), "white")
    ImageDraw.Draw(picture).text((40, 40), "MEMBER NAME: SOME BANK   TYPE: PERSONAL LOAN", fill="black")
    picture.save(img)
    path = tmp_path / "scan.pdf"
    c = canvas.Canvas(str(path), pagesize=A4)
    for _ in range(2):
        c.drawImage(str(img), 0, 0, width=A4[0], height=A4[1])
        c.showPage()
    c.save()
    return path


def test_image_only_pdf_gets_a_specific_error(image_only_pdf):
    with pytest.raises(CreditReportNoTextError, match="no readable text.*2 page.*images"):
        parse_credit_report("scan.pdf", image_only_pdf.read_bytes())
    out = describe(str(image_only_pdf))
    assert "NO READABLE TEXT" in out and "pages: 2" in out and "full-page pictures: 2" in out and "needs OCR" in out


def test_layout_tool_redacts_everything_personal():
    line = redact_line("MEMBER NAME: HDFC BANK  Saumye Singh  ACCOUNT NUMBER: 5021 4488  s.singh2004@gmail.com  12-03-2021  Rs 4,50,000 Pune")
    assert line == "MEMBER NAME: XXXX BANK  Xxxxxx Xxxxx  ACCOUNT NUMBER: 9999 9999  x.xxxxx9999@xxxxx.xxx  99-99-9999  Xx 9,99,999 Xxxx"
    out = describe(str(FIXTURES / "cibil_style.pdf"))
    assert "parser result: 5 accounts" in out and "lender x5" in out
    body = [ln.split("      [x")[0] for ln in out.split("in order ---\n", 1)[1].splitlines()]   # drop the tool's own repeat counts
    assert len(body) > 20 and not any(ch in "012345678" for ln in body for ch in ln)
    assert "HDFC" not in out and "SAMPLE USER" not in out and "MEMBER NAME: XXXX BANK TYPE: PERSONAL LOAN" in out

