# Figure Extraction

## Current capability and limitation

This project has:

- `pdfplumber` for text/table extraction;
- `pypdf` for PDF verification;
- Pillow for image handling;
- **no OCR** (no pytesseract);
- **no chart digitizer** (no WebPlotDigitizer/automated curve tracing).

Therefore:

- Figures are used for **locating, understanding and qualitative confirmation**.
- Numeric values that exist only in a figure are **not extracted** by default.
- Do not estimate a value from pixel positions.
- If a future digitizer is added, record the tool, calibration points, axis ranges and reading error; until then, mark `figure_only_not_extracted`.

## What to record from a figure

- Figure number, caption, page.
- Axis labels and units (x and y).
- Whether the y-axis is linear or logarithmic.
- Temperature, gas composition, amine concentration and other conditions in the caption.
- Legend: which symbol/line corresponds to which condition.
- Whether the curves are experimental points, model fits, or both.
- Any annotations (arrows, shaded regions, error bars).

These help you interpret a table and detect inconsistencies, even when you do not read numbers.

## Figure types in amine papers

| Figure type | What it usually shows | Extraction use |
|---|---|---|
| VLE isotherm (α vs P_CO2) | equilibrium solubility at fixed T | confirm table trends; do not read points unless tabulated |
| Loading vs time | absorption/desorption kinetics | identify dynamic vs equilibrium; do not treat as equilibrium |
| Rate vs loading/concentration | kinetics/mass transfer | identify rate metric and apparatus |
| Cyclic stability | capacity retention over cycles | confirm cycle count and trend |
| Regeneration energy vs conditions | process performance | locate the corresponding table value |
| Speciation vs loading | NMR/FTIR species fractions | qualitative; use SI tables if available |
| Parity plot (measured vs model) | model validation | do not extract individual points unless tabulated |
| Column profile / pilot | temperature, loading, efficiency along column | process context; not a solvent VLE point |

## Figure-only data protocol

If a value is only in a figure:

1. Record the figure number, caption, axis labels/units, and the exact condition.
2. State that the value is figure-only and cannot be extracted with the current tooling.
3. If the paper also gives a table/SI with the same data, use the table.
4. If the task explicitly authorizes image digitization and a tool is available, record:
   - tool and version;
   - axis calibration points;
   - pixel-to-value mapping;
   - number of points read;
   - estimated reading error;
   - the digitized values in a separate file, not silently merged into L2 data.
5. Without such a tool, do not invent a number.

## Using figures to catch errors

- If a table says the loading increases with P_CO2 but the isotherm figure shows a plateau or decrease, check the table/units.
- If a figure's legend says "model" but the table presents the same values as "experimental", flag the conflict.
- If the figure caption gives a different temperature from the table header, check which one applies.
- If the figure shows error bars but the table has no uncertainty, note the omission.

## Figure and table cross-check

Use a figure to confirm:

- the order of magnitude;
- the trend with temperature/pressure/concentration;
- whether a reported "equilibrium" point is on the plateau;
- whether a reported "rich loading" is far from equilibrium.

Do not use a figure to override a table value; report conflicts.

## Limitations to state in the report

- "Figure X contains values that are not tabulated; they were not digitized because no chart-digitization tool is installed."
- "The curve is a model fit; only the symbols are experimental, and the symbols are not tabulated."
- "The figure axis is logarithmic; reading linear positions would be wrong even with a digitizer."
- "The figure has no error bars; uncertainty is unknown."

## References

- Project tooling: `scripts/pdf_to_text.py`, `tools/_wordgrid.py`, `tools/verify_pdfs.py`.
- If a digitizer is added later, document it in the skill and require calibration/error reporting.
