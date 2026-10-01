# Standalone App Ideas

> Saved 2026-10-02. These came out of SmartFin brainstorming but don't depend on SmartFin's modules. Each could ship as its own app, or later as a "Protect" section inside SmartFin.
> Common thread: problems that hit Indian students and early earners, where the answer can be **verified by maths or real data** rather than taken on an AI's word.
> Status: none started.

---

## 1. True-Cost Decoder: "No-Cost EMI" and BNPL ⭐ top pick

**Problem.** "No-cost EMI" usually isn't free. The processing fee, 18% GST on the interest, and the upfront discount you give up when you choose EMI push the effective rate to roughly 12–20% a year. Buy-now-pay-later late fees and "convenience fees" are worse. Students and first-jobbers use both heavily and rarely compute the real cost.

**How it works.**
- Input: product price, EMI amount, tenure, processing fee, any upfront discount lost by choosing EMI. Alternatively, paste the offer text and have it parsed.
- Build the actual cash-flow schedule (what you'd pay today vs. what you pay over time, including GST on interest and fees).
- Solve for the **effective annual rate (IRR)** of that schedule.
- Output: "This '0% EMI' costs you ₹2,340 extra, an effective **16.4% a year**." Compare with paying upfront by credit card within the interest-free period, or using a personal loan.

**Why it stands out.** Every number is exact and reproducible; there is no "the model guessed". It's very relatable, uncommon as a project, and easy to demo live.

**Data / tech.** Pure maths (`numpy_financial.irr`, or a small Newton solver). Optional: an LLM or regex to parse pasted offer text into the input fields.

**MVP.** Single page: form → IRR → plain-language verdict + cost breakdown chart. Then add BNPL late-fee scenarios and a side-by-side comparison of 2–3 offers.

**Effort.** Low–moderate. **Risks.** Offer terms vary (cashback vs. upfront discount, GST treatment). Clearly state the assumptions shown.

---

## 2. Finfluencer and Investment-Scam Checker

**Problem.** In 2024 SEBI restricted unregistered finfluencers. Telegram/WhatsApp "guaranteed 30% monthly returns" schemes, fake trading apps and fake-KYC messages are widespread, and young investors are the main targets.

**How it works.** The user pastes a message, tip, link or person/channel name:
1. **Registry check.** Is this person or firm on SEBI's public lists of Registered Investment Advisers / Research Analysts (and broker lists)?
2. **Red-flag detection.** An NLP classifier and rules flag scam language: "guaranteed", "double your money", "limited slots", "pay to this UPI ID", urgency, requests for OTP or screen sharing.
3. **Claim verification.** If the tip names a stock and a claimed return ("gave 300% in 6 months"), check it against actual price history.
4. Output: a risk verdict with the specific reasons and evidence.

**Why it stands out.** Socially useful and very topical. It uses real government data, and few student projects check a SEBI registry. It has a clear "consumer protection" story.

**Data / tech.** SEBI intermediary lists (public, downloadable, need periodic refresh); yfinance for price checks; a small text classifier (labelled examples from public scam advisories plus rules) or an LLM with a fixed rubric.

**MVP.** Registry lookup + red-flag rules + verdict page. Then add the claim-backtest and a browser/WhatsApp share-to-check flow.

**Effort.** Moderate; mostly data plumbing for the SEBI lists. **Risks.** Name matching (aliases, spelling); never present a "safe" verdict as a guarantee.

---

## 3. Loan and Insurance Fine-Print Analyzer

**Problem.** Loan agreements and insurance policies hide the expensive parts: foreclosure penalties, processing and "documentation" fees, rate-reset clauses, waiting periods, sub-limits, exclusions. Most people sign without reading.

**How it works.**
- Upload a PDF; an LLM extracts structured fields (fees, penalties, rate type, waiting periods, exclusions, sub-limits).
- **Verification layer:** recompute the true annual rate from the extracted fees and EMI schedule (same IRR engine as idea #1) and check it against the headline rate. Flag mismatches.
- Output: a one-page "what you're actually agreeing to" summary with red/amber/green clauses.

**Why it stands out.** The LLM finds the clauses and the maths checks the numbers, so the AI's output is verified rather than trusted. That makes a strong design argument in a viva.

**Data / tech.** PDF text extraction (with OCR fallback for scanned docs), LLM structured extraction, shared IRR engine.

**MVP.** Personal-loan agreements only (most standardised). Then add health-insurance policies.

**Effort.** Higher; document formats vary widely. **Risks.** Extraction errors on unusual layouts. Show the source clause next to every extracted fact so users can check.

---

## 4. Group Expense Settlement (fewest payments)

**Problem.** Roommates, trips and group dinners create tangled IOUs.

**How it works.** Track shared expenses, then run a minimum-transactions settlement algorithm (net balances, then greedily match largest creditor with largest debtor) to turn, say, 12 debts into 3 payments, with one-tap UPI payment links (`upi://pay?...`).

**Why it's here.** Useful and a clean algorithms showcase, but **not novel** (Splitwise exists). Worth building only as a feature inside something else or as an algorithms demo.

**Effort.** Low.

---

## Suggested pairing

#1 and #2 share a theme ("Is this offer / tip legit?") and #1's IRR engine is reused by #3. A single app or section called **"Protect"** with #1 + #2 (and #3 later) would be a strong, coherent product: a defensive finance tool, which most finance apps aren't.

See also: SmartFin-integrated novelty ideas (personal inflation rate, goal-success Monte Carlo, present-bias score, tax-aware portfolio) in `AGENTS.md` §12 → "Feature ideas backlog".
