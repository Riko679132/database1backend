# Supplementary Information (SI)

## Why SI matters

Many L1 datasets and model parameters are in the SI, not the main PDF:

- raw VLE tables;
- full composition tables;
- NMR/FTIR spectra and species fractions;
- model parameters and regression coefficients;
- additional temperatures/pressures;
- uncertainty and replicate data.

A paper that looks like a figure-only study in the main text may have a complete SI table. Always check.

## Locating SI

1. Search the parsed text for "Supporting Information", "Supplementary", "ESI", "Appendix", "Data Availability".
2. Check the publisher page for a "Supporting Information" link (ACS, Wiley, Elsevier, RSC, Springer).
3. In the CDP browser, open the article page and list links containing `supp`, `support`, `si`, or `pdf`.
4. Download the SI with the same browser/CDP path used for the paper when it is paywalled.
5. Record the SI file name, path and SHA-256.

Do not assume the SI is public just because the article is open access; some SI files require the same institutional access.

## Reading SI

- Treat SI tables like main-text tables: caption, header, units, footnotes, one row per point.
- Check whether the SI table is the raw data behind a main-text figure; if so, it is the preferred source (L1).
- Check whether the SI gives the density, total pressure or gas composition missing from the main text; this can rescue a record from L3 to L2.
- Record which main-text table/figure the SI supports.
- If the SI is a scanned image or a spreadsheet, state the format and whether it was parsed.

## SI in the snapshot

Add to the snapshot:

- SI file name/path/SHA-256;
- SI table number/caption;
- the row(s) used;
- whether the SI is the primary source or a cross-check.

## If SI is unavailable

- State "SI not available / not accessible" in the report.
- Do not infer SI values from the main text or from a figure.
- If the main text gives a summary value and the SI is missing, record the summary as a main-text value with its own location; do not claim it is the raw dataset.
- Mark the record L3 if a required L2 field depends on the missing SI.

## SI quality checks

- Does the SI table have the same conditions as the main text?
- Are the units consistent?
- Are there multiple versions of the same table (e.g. corrected vs original)?
- Is the SI a "sample calculation" rather than a complete dataset?
- Are the values rounded differently from the main text?

## Common mistakes

1. Skipping the SI because the main text already has a summary table.
2. Using a main-text average when the SI has the full distribution.
3. Assuming an SI table is L1 without checking whether it is raw data or a model output.
4. Failing to record the SI file hash, so the source cannot be re-checked.
5. Treating an SI figure as a table.
