# CIBLens

Credit exposure intelligence for Bangladesh Bank CIB reports. Upload a CIB PDF and get an automated overview, related-party (connected) exposure, existing-client behaviour scoring from a loan statement, and a one-click Excel report.

## Features
| Module | What it does |
|---|---|
| PDF upload | Reads one or many CIB PDFs in the browser (nothing is sent to a server). Related parties’ CIBs can be added one by one. |
| Overview | CIB signal gauge, funded / non-funded / guarantor exposure, trend, risk flags, contract table, indicative decision. |
| Concerns & parties | One card per concern (the client and each proprietorship): borrower, funded / non-funded, guarantor exposure, overdue, utilisation and share of group exposure. A concern map and a checklist of related-party CIBs still to collect. |
| Behaviour | Upload a loan or account statement (CSV/Excel) to score utilisation, limit breaches, repayment coverage, regularity, penal events and trend (grade A–E). |
| Export | Excel workbook: Summary, Contracts, Concerns, Related parties, Risk flags, Behaviour. |

## Run it
Open `index.html` in a modern browser (internet needed for the PDF, Excel and font libraries on CDN). For a local server: `python -m http.server 8000` then open http://localhost:8000.

## Command-line parser (optional)
Needs poppler-utils (`pdftotext`).
```
python cib_parser.py report.pdf report.json
```
The JSON can be dropped into the upload box in place of the PDF.

## Project layout
```
index.html        The app (single file, starts blank)
cib_parser.py     PDF -> JSON command-line parser (optional)
```

## Privacy and security
CIB reports are confidential under Bangladesh Bank rules. Never commit real CIB PDFs or JSON exports (`.gitignore` blocks them). The demo data is masked. Host the app only inside your institution’s approved environment.

## Notes and limits
- Built for the current Bangladesh Bank CIB PDF layout; a layout change may need parser updates.
- The signal, behaviour grade and decision text are rule-based aids, not credit decisions. Tune thresholds to your credit policy.
- Other banks’ names are masked in the CIB itself, so exposure is grouped by CIB subject, not lender.
