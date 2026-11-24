# Table Extraction

## Goal

Extract the full table structure and every relevant row without losing headers, units, footnotes, merged cells or the table's relation to a specific test condition.

## Extraction order

1. **Locate the table** — caption, page, table number. `grep "Table"` on the parsed text is a starting point, but the caption may be split across lines.
2. **Read the caption** — it often contains the temperature, gas composition, amine concentration and loading basis.
3. **Read the header** — column names and units; check for multi-row headers.
4. **Read footnotes** — superscripts, "dry basis", "per total amine", "estimated", "n=3".
5. **Extract rows** — one row per test point; keep the row order and identifiers.
6. **Cross-check** — compare a few values with the text, abstract or figures.
7. **Record** — page, table number, caption, header, units, row text, included/excluded rows.

## pdfplumber strategy

Try in this order:

1. `page.extract_tables()` — works for bordered tables; returns a list of rows/cells. Check for empty cells caused by merged cells or missing borders.
2. `page.extract_text(layout=True)` — works for single-column layouts; multi-column pages may interleave columns.
3. `page.extract_words()` with row clustering — the reliable fallback for multi-column/no-border tables. The project's `tools/_wordgrid.py` clusters words by `round(top/4)` and sorts by `x0`.

```powershell
.\.venv\Scripts\python.exe tools\_wordgrid.py <pdf> <page> [y0 y1 x0 x1]
```

Use the crop window to isolate one table when the page contains multiple blocks.

## Header and unit checks

- Is the concentration wt%, mol%, mol/L, mol/kg, or a ratio? The column label may be in the caption, not the header.
- Is the loading per total amine, per specific amine, or per nitrogen site?
- Is the pressure total or CO2 partial? Is it absolute or gauge?
- Is the gas composition dry or wet basis?
- Is the temperature in K or °C?
- Are values "equilibrium", "rich", "lean", "initial", "maximum", or "after 30 min"?
- Are there superscripts/footnotes that change the definition?

If the header is ambiguous, do not guess; record the ambiguity and search the methods/caption.

## One row = one test

- A VLE table row `(T, P_CO2, α)` is one test.
- A table of multiple temperatures may have one row per `(T, P_CO2)` point.
- A table of blend ratios may have one row per blend and condition.
- Do not collapse rows into a single "average" record.
- Do not duplicate a row under multiple temperatures unless the table explicitly repeats it.

## Merged cells and multi-row headers

- If a cell spans several rows, carry the value down only when the table structure makes it unambiguous (e.g. a temperature group header).
- If a row is a sub-header, do not treat it as data.
- If a column is a unit column, attach it to the corresponding value column.
- If a table is transposed (conditions in columns, points in rows), transpose carefully and keep the original row/column labels in the snapshot.

## Table-only data

If a value exists only in a table and has no cross-check in the text:

- Extract it if the table is complete and the caption defines the conditions.
- Add `table_only_no_discrete_performance` or `table_only_no_text_crosscheck` to `qc_reason` if the value is a performance metric.
- Do not assume the value is representative of other temperatures/concentrations.

## Cross-checking

- Compare at least one value with the abstract, results text or a figure.
- Check whether the table's MEA reference row matches the text's stated baseline.
- Check whether units in the text and table agree (e.g. kJ/mol vs GJ/t).
- If the text and table conflict, keep both in the report and mark the conflict; do not silently choose one.

## Snapshot content for a table

- DOI, title, authors, journal, year, PDF path/hash.
- Table number, caption, page.
- Header and units.
- Full raw text of the extracted rows (or the relevant subset).
- Included rows and excluded rows with reasons.
- Conditions and derivations.
- Any footnotes that affect interpretation.

## Common mistakes

1. Reading only the numeric cells and ignoring the header/caption.
2. Treating a merged cell as a separate data row.
3. Mixing units from different columns.
4. Assuming a blank cell means zero.
5. Using a table's "average" row as a data point.
6. Extracting a model prediction column as experimental data.
7. Ignoring a second table with the same data on a different basis.
