# PDF Reading Protocol

## Goal

Build a reliable mental model of the paper before extracting numbers. Do not start from the abstract and conclusion only; most operating conditions and definitions live in the methods, table captions, footnotes and supporting information.

## Reading order

1. **First page** — title, authors, journal, year, DOI, abstract.
2. **Section map** — list Introduction, Experimental/Methods, Results, Discussion, Conclusion, References, Supporting Information.
3. **Methods** — apparatus, materials, solution preparation, gas composition, temperature/pressure control, analysis methods, equilibrium criterion.
4. **Tables and captions** — table number, caption, headers, units, footnotes, number of rows/columns.
5. **Results text** — authors' interpretation, comparisons, stated uncertainties, conflicts.
6. **Figures** — captions and axis labels, used to locate/confirm, not to read numbers.
7. **Supporting Information** — extra tables, raw data, model parameters, spectra.
8. **References** — only if a method/parameter is cited rather than described.

## Paper map template

Write this before extracting:

```
DOI:
Title:
System(s):            (amines, solvent, claimed concentration)
Research type:        experiment / model / simulation / review / property / degradation
Apparatus:
Main variables:       T, P, gas composition, amine concentration, blend ratio, loading
Reported metrics:
Boundary decision:    in scope / out of scope / needs SI
Key tables:           Table 1 ... page ...
Key figures:          Figure 1 ... page ...
SI:                   yes/no, file name, tables
```

## Cross-section linking

A single test point may require information from several places:

| Information | Typical location | Example |
|---|---|---|
| Amine identity/concentration | Methods, table caption | "30 wt% aqueous MEA" |
| Temperature | Methods, table header | "313 K" |
| Gas composition | Methods, table caption | "15 vol% CO2 in N2" |
| Total pressure | Methods, table caption | "101 kPa" |
| Loading definition | Methods, equations | "mol CO2/mol amine" |
| Performance value | Results table | "0.609" |
| Uncertainty/replicates | Footnotes, methods | "±0.005, n=3" |
| Initial loading | Methods | "fresh solution" |

If a value appears without its condition, search the methods and table caption before assuming a standard condition.

## Boundary decision

Before extracting, apply the current boundary:

- aqueous monoamine or two-component amine blend;
- total amine 20–50 wt%;
- no additive, salt, two-phase or slurry;
- amines in the project whitelist.

If the paper is out of scope, record the reason and stop — unless it contains an in-scope table (e.g. a 30 wt% MEA reference row inside a non-aqueous study). In that case, extract only the in-scope row and document the exclusion of the rest.

## Text quality checks

- Count characters per page; average < 50 suggests a scan/OCR need.
- Look for garbled headings or broken characters (e.g. `CO 2`, `T�298 K`); these are parsing artefacts, not paper values.
- For multi-column layouts, plain text extraction may interleave columns; use `tools/_wordgrid.py` to reconstruct rows.
- If a table is split across pages, join it only when headers repeat or the continuation is unambiguous.

## Evidence ledger

For every candidate point, record:

```
field | raw value | unit | page/table/figure | evidence type | note
```

Use the evidence types in `validation/evidence_classification.md`. Do not promote an assumption to a fact.

## Output of the reading stage

- `paper_map` (the template above).
- `evidence_ledger` (all candidate values, including rejected ones).
- `excluded_rows` (with reasons).
- `open_questions` (missing density, missing total pressure, ambiguous ratio basis, figure-only data).
- A first-pass boundary decision.

Only after this should you create JSONL records.

## Tools available in this project

| Task | Tool |
|---|---|
| PDF → text | `scripts/pdf_to_text.py` (pdfplumber) |
| Table extraction | `page.extract_tables()` in pdfplumber |
| Layout text | `page.extract_text(layout=True)` |
| Multi-column/word grid | `tools/_wordgrid.py` (`extract_words`, cluster by `round(top/4)`) |
| PDF verification | `tools/verify_pdfs.py` (pypdf) |
| OCR | not installed — scans are deferred |
| Chart digitization | not installed — figure-only values are not extracted |

## Common mistakes

1. Reading the abstract and assuming the conditions apply to all tables.
2. Taking a feed gas composition as the equilibrium gas composition.
3. Missing a table footnote that defines the loading basis or units.
4. Ignoring a second table with the same data normalized differently.
5. Mixing data from different temperatures or concentrations into one record.
6. Treating a model fit as measured data.
7. Starting extraction before checking the boundary.
