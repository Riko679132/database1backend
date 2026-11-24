# SI Discovery, Download and Parsing Test Report

## Tool

`tools/fetch_si.py`:

- Opens the article DOI/URL in the authorized CDP Chrome session (port 9222).
- Collects links whose text/href match Supporting Information / Supplementary / Additional Data / Appendix / ESI.
- Filters ACS help pages, Google Scholar, Wiley support and landing-only anchors.
- Downloads file-like links through the browser context (cookies/institutional access preserved).
- Parses PDF/CSV/XLSX/DOCX/ZIP and writes `si_manifest.json`.
- Does not bypass login/paywall; failures are recorded with URL and reason.

## Test paper

- DOI: `10.1021/acs.iecr.4c03980`
- Title: Iron Solubility Measurements in Aqueous MEA for CO2 Capture.
- Page: ACS article page.

## Result

- SI found: yes.
- Candidate links after filtering: 1.
- Downloaded: `data/raw_si/10.1021_acs.iecr.4c03980/si_01.pdf`
- Type: PDF
- Pages: 9
- Parsed text: `data/raw_si/10.1021_acs.iecr.4c03980/parsed/si_01.txt`
- Parsed chars: 4,891
- Manifest: `data/raw_si/10.1021_acs.iecr.4c03980/si_manifest.json`
- SI PDF SHA-256: `89ccbf69193fb5d97bf5e1bb681724330605d695b394e9b7111e8f51fe648601`
- The parsed text contains `Supplementary Information`, uncertainty analysis and the paper title.

The first run also discovered ACS support/Google Scholar links; the filter was tightened and the second run returned only the real SI file.

## Integration into B

`server/tasks.py` looks for `data/raw_si/<sanitized doi>/si_manifest.json`; if a parsed SI text exists, it is appended to the extraction prompt under `【补充材料（SI）】`. The snapshot records:

```json
"si": {
  "status": "loaded",
  "manifest": "data/raw_si/10.1021_acs.iecr.4c03980/si_manifest.json",
  "files": [{"type": "pdf", "sha256": "89cc...", "parsed": {"pages": 9, "chars": 4891}}],
  "chars": 4891
}
```

A preview run on the iron-solubility paper confirmed `补充材料：4891 字符` and `si.status=loaded`. The paper itself produced 0 in-scope records (iron solubility, not amine performance), which is the correct boundary decision.

## Limitations

- Publisher-specific link patterns: ACS SI worked; Wiley/Elsevier/RSC may use landing pages or different link structures.
- Some links return HTML (landing/redirect) or require login; these are recorded as `not_a_file`/`failed`, not bypassed.
- SI PDF parsing uses the same text-layer logic; scanned SI may need OCR.
- XLSX/DOCX parsing reports sheet/table counts and previews; it does not yet map SI tables into the database.
- The manifest is the A-stage handoff; it is not automatically fetched for every paper. Run `fetch_si.py` before the B preview when SI is needed.

## Commands

```powershell
# start CDP once
powershell -NoProfile -ExecutionPolicy Bypass -File tools\start_cdp_browser.ps1

# fetch and parse SI
.\.venv\Scripts\python.exe tools\fetch_si.py --doi 10.1021/acs.iecr.4c03980

# discovery/download only, no parsing
.\.venv\Scripts\python.exe tools\fetch_si.py --doi 10.1021/acs.iecr.4c03980 --no-parse
```
