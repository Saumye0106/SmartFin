"""
Generate SAMPLE bank statements for statement-import tests.

These are fictional transactions laid out the way HDFC / SBI / Axis / ICICI
statements are, so the parser is exercised against realistic structure
(preambles, wrapped narrations, Dr/Cr columns, multi-page PDFs, passwords).
They are NOT real statements. Validate against a real (redacted) statement
before trusting the parser on a new bank.

    cd backend && python unit_test/fixtures/statements/make_fixtures.py

Requires reportlab for the PDFs (dev-only; not in requirements.txt).
"""

import csv
from datetime import date
from pathlib import Path

import openpyxl

HERE = Path(__file__).parent
OPENING_BALANCE = 18250.00
PDF_PASSWORD = "SAUM0101"

# (date, narration, debit, credit)
TXNS = [
    (date(2026, 9, 1), "NEFT CR-HDFC0000001-ACME TECHNOLOGIES PVT LTD-SALARY SEP 2026", 0, 45000.00),
    (date(2026, 9, 1), "UPI/427100001111/RAMESH KUMAR/ramesh@oksbi/rent sep", 12000.00, 0),
    (date(2026, 9, 2), "UPI-SWIGGY-swiggy.order@icici-ICIC0DC0099-427112345678-Order", 412.50, 0),
    (date(2026, 9, 3), "ACH D- BAJAJ FINANCE LTD-EMI 450123", 4707.35, 0),
    (date(2026, 9, 4), "UPI-UBER INDIA-uber@axisbank-UTIB0000100-427123456789", 236.00, 0),
    (date(2026, 9, 5), "UPI-AIRTEL PREPAID-airtel@ybl-recharge", 299.00, 0),
    (date(2026, 9, 6), "UPI/427198765432/Zomato Ltd/zomato@hdfcbank/Payment", 568.00, 0),
    (date(2026, 9, 6), "UPI/427198765433/Zomato Ltd/zomato@hdfcbank/Payment", 568.00, 0),
    (date(2026, 9, 8), "POS 4512XXXXXX1234 AMAZON PAY INDIA", 1899.00, 0),
    (date(2026, 9, 10), "ATM WDL/MUMBAI ANDHERI/4512", 2000.00, 0),
    (date(2026, 9, 12), "LIC PREMIUM PAYMENT POLICY 1234", 3200.00, 0),
    (date(2026, 9, 14), "IMPS-427155556666-PRIYA SHARMA-SBIN0001234", 750.00, 0),
    (date(2026, 9, 15), "UPI-NETFLIX-netflix@icici-ICIC0DC0099-427133333333", 199.00, 0),
    (date(2026, 9, 18), "UPI/427144444444/APOLLO PHARMACY/apollo@ybl/medicines", 645.00, 0),
    (date(2026, 9, 20), "UPI-IRCTC-irctc@sbi-SBIN0000001-427177777777-ticket", 1340.00, 0),
    (date(2026, 9, 22), "REFUND-AMAZON PAY INDIA-ORDER 402-1234567", 0, 1899.00),
    (date(2026, 9, 25), "UPI-BLINKIT-blinkit@ybl-427188888888-groceries", 987.25, 0),
    (date(2026, 9, 28), "UPI-UDEMY-udemy@icici-ICIC0DC0099-427199999999-course", 499.00, 0),
    (date(2026, 9, 30), "INTEREST CREDIT FOR CURRENT QTR", 0, 213.40),
]

EXPECTED = {
    "count": len(TXNS),
    "debit_total": round(sum(t[2] for t in TXNS), 2),
    "credit_total": round(sum(t[3] for t in TXNS), 2),
}


def _with_balance():
    bal, out = OPENING_BALANCE, []
    for d, n, dr, cr in TXNS:
        bal = round(bal - dr + cr, 2)
        out.append((d, n, dr, cr, bal))
    return out


def _fmt(x):
    return f"{x:,.2f}" if x else ""


def hdfc_csv():
    with open(HERE / "hdfc_style.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["HDFC BANK Ltd. (SAMPLE - NOT A REAL STATEMENT)"])
        w.writerow(["Account No :", "XXXXXXXX4321"])
        w.writerow(["Statement From :", "01/09/2026", "To :", "30/09/2026"])
        w.writerow([])
        w.writerow(["Date", "Narration", "Chq./Ref.No.", "Value Dt", "Withdrawal Amt.", "Deposit Amt.", "Closing Balance"])
        for i, (d, n, dr, cr, bal) in enumerate(_with_balance()):
            ds = d.strftime("%d/%m/%y")
            w.writerow([ds, n, f"{400000000000 + i:016d}", ds, _fmt(dr), _fmt(cr), _fmt(bal)])
        w.writerow([])
        w.writerow(["STATEMENT SUMMARY :-"])
        w.writerow(["Opening Balance", "Dr Count", "Cr Count", "Debits", "Credits", "Closing Bal"])
        w.writerow([_fmt(OPENING_BALANCE), "16", "3", _fmt(EXPECTED["debit_total"]), _fmt(EXPECTED["credit_total"]), ""])


def sbi_xlsx():
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(["State Bank of India (SAMPLE - NOT A REAL STATEMENT)"])
    ws.append(["Account Number", "XXXXXXX9876"])
    ws.append([])
    ws.append(["Txn Date", "Value Date", "Description", "Ref No./Cheque No.", "Debit", "Credit", "Balance"])
    for d, n, dr, cr, bal in _with_balance():
        ds = d.strftime("%d %b %Y")
        if len(n) > 40:  # SBI wraps long narrations onto a second row
            ws.append([ds, ds, n[:40], "", dr or "", cr or "", bal])
            ws.append(["", "", n[40:], "", "", "", ""])
        else:
            ws.append([ds, ds, n, "", dr or "", cr or "", bal])
    ws.append([])
    ws.append(["**This is a computer generated statement**"])
    wb.save(HERE / "sbi_style.xlsx")


def axis_csv():
    with open(HERE / "axis_style.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["Axis Bank (SAMPLE - NOT A REAL STATEMENT)"])
        w.writerow([])
        w.writerow(["Tran Date", "PARTICULARS", "Amount (INR)", "Dr/Cr", "BAL"])
        for d, n, dr, cr, bal in _with_balance():
            w.writerow([d.strftime("%d-%m-%Y"), n, _fmt(dr or cr), "DR" if dr else "CR", _fmt(bal)])


def icici_pdf(path, password=None):
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.pdfencrypt import StandardEncryption
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet

    header = ["S No.", "Value Date", "Transaction Date", "Cheque Number", "Transaction Remarks",
              "Withdrawal Amount (INR )", "Deposit Amount (INR )", "Balance (INR )"]
    rows = [[str(i + 1), d.strftime("%d/%m/%Y"), d.strftime("%d/%m/%Y"), "-", n, _fmt(dr) or "0.00",
             _fmt(cr) or "0.00", _fmt(bal)] for i, (d, n, dr, cr, bal) in enumerate(_with_balance())]
    style = TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black), ("FONTSIZE", (0, 0), (-1, -1), 6)])
    enc = StandardEncryption(password, canPrint=1) if password else None
    doc = SimpleDocTemplate(str(path), pagesize=landscape(A4), encrypt=enc)
    title = Paragraph("ICICI Bank (SAMPLE - NOT A REAL STATEMENT) - Account XXXXXXXX5555", getSampleStyleSheet()["Normal"])
    half = len(rows) // 2
    doc.build([
        title, Table([header] + rows[:half], style=style),
        PageBreak(), Table([header] + rows[half:], style=style),  # header repeats on page 2
    ])


if __name__ == "__main__":
    hdfc_csv()
    sbi_xlsx()
    axis_csv()
    icici_pdf(HERE / "icici_style.pdf")
    icici_pdf(HERE / "icici_style_protected.pdf", password=PDF_PASSWORD)
    print("Wrote fixtures:", sorted(p.name for p in HERE.iterdir() if p.suffix != ".py"))
    print("Expected:", EXPECTED)
