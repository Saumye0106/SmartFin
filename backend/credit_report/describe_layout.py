"""
Print a REDACTED skeleton of a credit report, to debug a layout the parser doesn't recognise
without sharing the report itself.

    cd backend
    python -X utf8 credit_report/describe_layout.py "C:\\path\\to\\report.pdf"            # asks for the password if needed
    python -X utf8 credit_report/describe_layout.py "C:\\path\\to\\report.pdf" > layout.txt

What is redacted, on your machine, before anything is printed:
  - every digit becomes 9 (amounts, dates, account numbers, phone numbers, scores)
  - every word that is not in a fixed list of credit-report terms becomes x's of the same length
    (names, lenders, addresses, employers, e-mail addresses)
What survives is the layout: label wording, column order, punctuation and line breaks.
Read the output before sharing it; if anything personal is still visible, remove it.
"""

from __future__ import annotations

import getpass
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from credit_report.parser import CreditReportNoTextError, _LABEL_RE, _read_text, parse_credit_report  # noqa: E402
from statement_import.parser import StatementParseError, StatementPasswordRequired  # noqa: E402

# Words that describe a report's structure and say nothing about the person.
VOCAB = set("""
a account accounts actual address all amount amt an and annual any as asset at auto balance bank bureau by card cash category
certified cibil classification closed closure collateral commercial company consumer control credit crif current cut dbt date dates
day days dd details disbursed dispute doubtful dpd due education emi end enquiries enquiry equifax experian facility finance for frequency
from gold grantor guarantor high highest history home housing id in individual information installment instalment institution interest is
joint last left lender limit limited loan loans loss lss ltd mark member mm month monthly months mortgage na name no not number of off on
open opened opening or outstanding overdraft overdue ownership page paid past payment payments period personal principal property purpose
rate remarks repayment report reported restructured right sanctioned score section secured settled settlement sma special standard status
std sub subscriber substandard suit summary tenure the to total transunion two type unsecured up used value vehicle wheeler wilful with
written xxx year years yy yyyy
jan feb mar apr may jun jul aug sep oct nov dec january february march april june july august september october november december
""".split())

_WORD = re.compile(r"[A-Za-z]+")
MAX_LINES = 260


def redact_line(line: str) -> str:
    """Digits -> 9; words outside VOCAB -> x/X of the same length. Punctuation and spacing are kept."""
    def mask(m):
        word = m.group(0)
        if word.lower() in VOCAB:
            return word
        return "".join("X" if ch.isupper() else "x" for ch in word)
    return _WORD.sub(mask, re.sub(r"\d", "9", line))


def pdf_structure(data: bytes, password: str | None) -> str:
    """Counts only (pages, pictures, text objects, fonts): tells an image-only PDF from one whose text can't be decoded."""
    import io

    import pdfplumber

    with pdfplumber.open(io.BytesIO(data), password=password or "") as pdf:
        pages = pdf.pages
        images = [len(p.images) for p in pages]
        chars = [len(p.chars) for p in pages]
        fonts = {c.get("fontname", "?").split("+")[-1] for p in pages[:3] for c in p.chars}
        big = sum(1 for p in pages for im in p.images
                  if (im["x1"] - im["x0"]) > 0.6 * p.width and (im["bottom"] - im["top"]) > 0.4 * p.height)
    verdict = ("pages are full-page pictures: a scan or image export, needs OCR" if sum(chars) < 50 and big
               else "no text objects and no large pictures: text may be drawn as shapes" if sum(chars) < 50
               else "text objects exist but could not be decoded (font without a character map)")
    return (f"pages: {len(pages)}   pictures per page: {images[:8]}{'...' if len(images) > 8 else ''}   "
            f"full-page pictures: {big}   text objects: {sum(chars)}   fonts: {sorted(fonts)[:6]}\n"
            f"diagnosis: {verdict}")


def describe(path: str, password: str | None = None) -> str:
    data = Path(path).read_bytes()
    try:
        text = _read_text(Path(path).name, data, password)
    except CreditReportNoTextError:
        return ("=== SmartFin credit report layout ===\n"
                f"NO READABLE TEXT   file size: {len(data)} bytes\n" + pdf_structure(data, password))
    lines = [re.sub(r"[ \t]+", " ", raw).rstrip() for raw in text.splitlines()]
    non_empty = [ln for ln in lines if ln.strip()]
    out = ["=== SmartFin credit report layout (REDACTED: digits are 9, unknown words are x) ===",
           f"characters of text: {len(text)}   lines: {len(non_empty)}   file size: {len(data)} bytes"]
    if len(text.strip()) < 200:
        out.append("ALMOST NO TEXT: this PDF is probably a scan (images), which the parser cannot read.")

    hits = Counter(m.lastgroup for ln in non_empty for m in _LABEL_RE.finditer(ln))
    out.append("labels the parser recognised: " + (", ".join(f"{k} x{v}" for k, v in sorted(hits.items())) or "NONE"))
    try:
        report = parse_credit_report(Path(path).name, data, password)
        out.append(f"parser result: {len(report.accounts)} accounts, history months per account: "
                   f"{[len(a.history) for a in report.accounts]}")
    except StatementParseError as e:
        out.append(f"parser result: FAILED ({type(e).__name__})")

    # Lines whose redacted form repeats many times (history grids, tables) are shown once with a count.
    redacted = [redact_line(ln) for ln in non_empty]
    out.append(f"--- first {min(MAX_LINES, len(redacted))} distinct line shapes, in order ---")
    counts = Counter(redacted)
    seen = set()
    shown = 0
    for ln in redacted:
        if ln in seen:
            continue
        seen.add(ln)
        out.append(f"{ln}" + (f"      [x{counts[ln]}]" if counts[ln] > 1 else ""))
        shown += 1
        if shown >= MAX_LINES:
            out.append(f"... {len(set(redacted)) - shown} more distinct lines not shown")
            break
    return "\n".join(out)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    try:
        print(describe(sys.argv[1]))
    except StatementPasswordRequired:
        # Typed at the prompt so the password never appears in the command history or the output.
        print(describe(sys.argv[1], getpass.getpass("PDF password (not shown, not stored): ")))
    except StatementParseError as e:
        print(f"Could not read the file: {e}")
        sys.exit(1)
