"""
Generate SAMPLE credit reports for credit-report-import tests.

A fictional borrower with five accounts, laid out two ways: the label/value
line style CIBIL consumer reports use (status row above a month row), and
the one-label-per-line style with a year-by-month payment grid that
Experian-type reports use. They are NOT real reports and the layouts are
approximations: validate against a real (redacted) report before trusting
the parser for a bureau.

    cd backend && python unit_test/fixtures/credit_reports/make_fixtures.py

Requires reportlab (dev-only; not in requirements.txt).
"""

from pathlib import Path

HERE = Path(__file__).parent
PDF_PASSWORD = "SAMP0101"
REPORT_DATE = (2026, 9, 30)
SCORE = 731
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _months_back(n, end=(2026, 9)):
    """n months ending at `end`, newest first, as (year, month)."""
    y, m = end
    out = []
    for _ in range(n):
        out.append((y, m))
        y, m = (y - 1, 12) if m == 1 else (y, m - 1)
    return out


def _history(n, end=(2026, 9), marks=None):
    """{(year, month): status} for n months, all on time except `marks`."""
    marks = marks or {}
    return {ym: marks.get(ym, "000") for ym in _months_back(n, end)}


# Fictional accounts. Amounts in rupees; history values are days past due or an asset class.
ACCOUNTS = [
    dict(lender="HDFC BANK", type="PERSONAL LOAN", number="XXXXXX4521", opened="15-03-2025", closed=None,
         sanctioned=300000, balance=210000, overdue=0, emi=9960, tenure=36, rate=12.00,
         history=_history(18, marks={(2026, 1): "030"})),
    dict(lender="STATE BANK OF INDIA", type="HOUSING LOAN", number="XXXXXXXX7788", opened="10-06-2022", closed=None,
         sanctioned=2500000, balance=2240000, overdue=0, emi=21500, tenure=240, rate=8.60,
         history=_history(24, marks={(2025, 3): "XXX"})),
    dict(lender="ICICI BANK", type="CREDIT CARD", number="XXXXXXXXXXXX9012", opened="05-01-2023", closed=None,
         sanctioned=150000, balance=42000, overdue=0, emi=None, tenure=None, rate=None,
         history=_history(24, marks={(2025, 11): "030", (2025, 12): "060"})),
    dict(lender="BAJAJ FINANCE LTD", type="CONSUMER LOAN", number="XXXX3344", opened="20-08-2024", closed="20-08-2025",
         sanctioned=40000, balance=0, overdue=0, emi=3600, tenure=12, rate=14.00,
         history=_history(12, end=(2025, 8), marks={(2025, 2): "030", (2025, 3): "060", (2025, 4): "090"})),
    # No EMI or interest rate reported: the importer must ask for them before creating a loan.
    dict(lender="AXIS BANK", type="TWO-WHEELER LOAN", number="XXXXX5566", opened="01-02-2026", closed=None,
         sanctioned=90000, balance=78000, overdue=0, emi=None, tenure=24, rate=None,
         history=_history(7, marks={})),
]


def _inr(v):
    if v is None:
        return "-"
    s = str(int(v))
    head, tail = (s[:-3], s[-3:]) if len(s) > 3 else ("", s)
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    if head:
        groups.insert(0, head)
    return ",".join(groups + [tail])


def cibil_lines():
    lines = ["CIBIL TRANSUNION CREDIT INFORMATION REPORT (SAMPLE - NOT A REAL REPORT)",
             "CONSUMER: SAMPLE USER    DATE: 30-09-2026    CONTROL NUMBER: 000000001",
             f"CIBIL TRANSUNION SCORE: {SCORE}", "", "ACCOUNT INFORMATION"]
    for a in ACCOUNTS:
        lines += [
            "",
            f"MEMBER NAME: {a['lender']}    TYPE: {a['type']}",
            f"ACCOUNT NUMBER: {a['number']}    OWNERSHIP: INDIVIDUAL",
            f"OPENED: {a['opened']}    LAST PAYMENT: 05-09-2026    CLOSED: {a['closed'] or '-'}",
            f"SANCTIONED: {_inr(a['sanctioned'])}    CURRENT BALANCE: {_inr(a['balance'])}    OVERDUE: {_inr(a['overdue'])}",
            f"EMI: {_inr(a['emi'])}    REPAYMENT TENURE: {a['tenure'] or '-'}    RATE OF INTEREST: "
            f"{'-' if a['rate'] is None else format(a['rate'], '.2f')}",
            "DAYS PAST DUE/ASSET CLASSIFICATION (UP TO 36 MONTHS; LEFT TO RIGHT)",
        ]
        items = list(a["history"].items())
        for i in range(0, len(items), 12):
            chunk = items[i:i + 12]
            lines.append("   ".join(status for _, status in chunk))
            lines.append("   ".join(f"{m:02d}-{str(y)[2:]}" for (y, m), _ in chunk))
    lines += ["", "ENQUIRIES", "MEMBER: SOME BANK    DATE: 01-02-2026    PURPOSE: TWO-WHEELER LOAN    AMOUNT: 90,000",
              "END OF REPORT"]
    return lines


def experian_lines():
    lines = ["Experian Credit Report (SAMPLE - NOT A REAL REPORT)", "Report Date 30/09/2026", f"Experian Credit Score {SCORE}",
             "", "Credit Account Details"]
    for a in ACCOUNTS:
        lines += [
            "",
            f"Lender                              {a['lender'].title()}",
            f"Account Type                        {a['type'].title()}",
            f"Account Number                      {a['number']}",
            f"Date Opened                         {a['opened'].replace('-', '/')}",
            f"Date Closed                         {(a['closed'] or '').replace('-', '/')}",
            f"Sanctioned Amt / Highest Credit     {_inr(a['sanctioned'])}",
            f"Current Balance                     {_inr(a['balance'])}",
            f"Amount Overdue                      {_inr(a['overdue'])}",
            f"EMI Amount                          {_inr(a['emi']) if a['emi'] else ''}",
            f"Repayment Tenure                    {a['tenure'] or ''}",
            f"Rate of Interest                    {'' if a['rate'] is None else format(a['rate'], '.2f')}",
            "Payment History (Days Past Due)",
            "Year   " + "   ".join(MONTHS),
        ]
        for year in sorted({y for y, _ in a["history"]}, reverse=True):
            cells = []
            for m in range(1, 13):
                status = a["history"].get((year, m))
                cells.append("-" if status is None else ("XXX" if status == "XXX" else str(int(status))))
            lines.append(f"{year}   " + "   ".join(f"{c:>3}" for c in cells))
    lines += ["", "Credit Enquiries", "Some Bank  01/02/2026  Two-Wheeler Loan  90,000", "End of Report"]
    return lines


def write_pdf(path, lines, password=None):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    kwargs = {}
    if password:
        from reportlab.lib.pdfencrypt import StandardEncryption
        kwargs["encrypt"] = StandardEncryption(password, canPrint=1)
    c = canvas.Canvas(str(path), pagesize=A4, **kwargs)
    width, height = A4
    y = height - 40
    c.setFont("Courier", 8)
    for line in lines:
        if y < 40:
            c.showPage()
            c.setFont("Courier", 8)
            y = height - 40
        c.drawString(30, y, line)
        y -= 11
    c.save()


if __name__ == "__main__":
    write_pdf(HERE / "cibil_style.pdf", cibil_lines())
    write_pdf(HERE / "cibil_style_protected.pdf", cibil_lines(), password=PDF_PASSWORD)
    write_pdf(HERE / "experian_style.pdf", experian_lines())
    (HERE / "cibil_style.txt").write_text("\n".join(cibil_lines()) + "\n", encoding="utf-8")
    print("wrote", sorted(p.name for p in HERE.glob("*.pdf")))
