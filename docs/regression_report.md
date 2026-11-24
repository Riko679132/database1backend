# 38-Record L2 Regression Report

> **Phase 3 update:** this report documents the Phase-2 baseline (22/38). After the VLE table parser and rate-unit normalization, the corrected regression is **37/38, 95.9% completeness, 95.9% agreement**. See `docs/phase3_regression_comparison.md`.

## Evaluation set

- Source: `gold_standard_L2.json` (historical L2 export).
- Samples: 38 tests across 7 DOIs.
- Records: `evaluation/eval_set_v1.json`; human-review CSV: `evaluation/eval_set_v1.csv`.
- Label policy: **historical L2 labels, human_verified=false**. The report compares against historical labels, not independent human-confirmed truth.
- Integrity: all 7 PDFs and 38 snapshots exist; snapshot hashes match after the CRLF fix.

## Harness sanity check

`evaluation/build_historical_candidate.py` converts the gold records into a candidate JSONL. Evaluation result:

- coverage 38/38
- completeness 100%
- agreement 100%
- L2 38

This proves the evaluator can match and score the full set; it is **not** a model result.

## Final LLM regression

- Candidate batch: `extractions/batch_20261124_140349`
- Model: `deepseek-chat`
- Knowledge routing: enabled; prompt hashes recorded per paper
- Table-grid context: enabled
- SI: none found for these 7 papers
- Report: `evaluation/reports/final_regression_v1_20261124_140525.md` / `.json`

### Summary

| Metric | Value |
|---|---|
| Coverage | 22/38 |
| Field completeness | 76.7% |
| Numeric agreement (within tolerance) | 66.1% |
| Recipe closure | 22 complete |
| QC outcomes | 10 L2, 12 L3, 16 no-match |
| L2 downgraded/rejected | 28 |
| Extra candidate records | 8 |

### Per DOI

| DOI | Expected | Matched | Within-tolerance fields / fields |
|---|---:|---:|---:|
| 10.1016/j.apenergy.2016.03.043 | 4 | 4 | 32/36 |
| 10.1016/j.ijggc.2016.12.018 | 1 | 1 | 8/12 |
| 10.1016/j.jece.2024.112664 | 3 | 3 | 30/39 |
| 10.1021/acs.iecr.9b00552 | 1 | 1 | 8/8 |
| 10.1021/ie400825u | 1 | 1 | 6/12 |
| 10.1021/je00005a025 | 27 | 12 | 66/120 |
| 10.1039/d6gc02196d | 1 | 0 | 0/0 |

### Main failure categories

1. **27-point VLE table (Shen & Li 1992): 12/27.** The table has four side-by-side temperature groups and spans pages. Table-grid context improved coverage from 4 to 12, but column/row grouping is still incomplete.
2. **Unit-scale errors in jece 2024 rates.** Initial absorption/desorption rates were extracted as `34.0`/`13.0` while the reference expects `0.00034`/`0.00013`; the evaluator matches the records but marks the values outside tolerance. The model must preserve the paper's rate unit and record any conversion factor.
3. **Missing VLE conditions.** Many VLE points lack `co2_vol_pct`/`initial_loading` because total pressure or fresh-solution wording is absent; they are L3, not L2.
4. **Water-lean reference paper missed.** `10.1039/d6gc02196d` returned 0 records despite containing a 30 wt% MEA reference; section/table targeting needs improvement.
5. **Extra records.** 8 candidate records were not matched to a reference; they may be legitimate additional points or over-extraction and need human review.

### Trade-off

- Earlier 7-paper run: 14/38 coverage, ~84.6% completeness, ~79.2% agreement.
- Final run with table grid and stronger VLE rules: 22/38 coverage, 76.7% completeness, 66.1% agreement.

Coverage increased, but agreement/completeness decreased. This is the expected recall/precision trade-off; do not judge the extractor by coverage alone. The regression report deliberately keeps both metrics.

## Field-level observations

- Temperature: 100% present and within tolerance.
- Recipe wt% and total amine: 100% present/within tolerance for matched records.
- `co2_vol_pct`: 45.5% complete; many VLE points only report P_CO2.
- `co2_partial_kPa`: 61.9% complete; 6 outside tolerance (unit/condition issues).
- `rich_loading`: 100% present; 6 outside tolerance (VLE point matching/value issue).
- `initial_absorption_rate`/`initial_desorption_rate`: 100% present but 0% within tolerance (unit scale).

## Reproduce

```powershell
.\.venv\Scripts\python.exe evaluation\build_eval_set.py
.\.venv\Scripts\python.exe evaluation\evaluate.py `
  --candidate extractions\batch_20261124_140349 `
  --label final_regression_v1
```

## Next improvements

1. Deterministic table parser for multi-column VLE tables, or table-specific LLM chunks by page group.
2. Strong rate-unit rule and a unit-normalization validator (mol/L/s vs mol/L/min vs mol/m²/s).
3. Stronger reference-row targeting for water-lean/out-of-scope papers.
4. Add a negative evaluation set to measure false accepts (the 38 L2 set is positive-only).
5. Human-audit a stratified subset and replace `human_verified=false` labels with confirmed labels.
