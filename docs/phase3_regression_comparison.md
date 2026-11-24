# Phase 3 — Before/After Regression Comparison

## Evaluation setup

- Test set: 38 historical L2 records across 7 DOIs (`evaluation/eval_set_v1.json`).
- Labels: historical L2 export, `human_verified=false`; this is a regression baseline, not independent human truth.
- Before: `extractions/batch_20261124_140349` (Phase-2 final LLM batch).
- After: `extractions/batch_20261124_143107` (Phase-3 batch with deterministic VLE parser + rate-unit normalization).
- Evaluator: `evaluation/evaluate.py`, amine identity now required (different amine = different system; no weak penalty).
- Reports:
  - Before: `evaluation/reports/phase3_before_corrected_20261124_143322.md`
  - After: `evaluation/reports/phase3_after_corrected_20261124_143322.md`

## Headline metrics

| Metric | Before | After |
|---|---:|---:|
| Coverage | 16/38 | **37/38** |
| Field completeness | 79.0% | **95.9%** |
| Numeric agreement (within tolerance) | 75.5% | **95.9%** |
| Recipe complete | 16 | **37** |
| QC L2 | 10 | **37** |
| QC L3 | 6 | 0 |
| No-match | 22 | **1** |
| Extra candidate records | 14 | 13 |
| L2 downgraded/rejected | 28 | **1** |
| VLE target (Shen & Li) | 6/27 | **27/27** |
| Absorption rate within tolerance | 0/3 | **3/3** |
| Desorption rate within tolerance | 0/3 | **3/3** |
| CO2 vol% completeness | 62.5% | **100%** |
| Equilibrium loading agreement | 100% (7 expected) | **100% (28 expected)** |

## Per-DOI coverage

| DOI | Expected | Before matched | After matched |
|---|---:|---:|---:|
| 10.1016/j.apenergy.2016.03.043 | 4 | 4 | 4 |
| 10.1016/j.ijggc.2016.12.018 | 1 | 1 | 1 |
| 10.1016/j.jece.2024.112664 | 3 | 3 | 3 |
| 10.1021/acs.iecr.9b00552 | 1 | 1 | 1 |
| 10.1021/ie400825u | 1 | 1 | 1 |
| 10.1021/je00005a025 | 27 | **6** | **27** |
| 10.1039/d6gc02196d | 1 | 0 | **0** |

## Why the before VLE number is 6, not 12

The original Phase-2 report said 12/27. That was an evaluator false-match artifact:

- the LLM extracted 12 MDEA 30 wt% points: 6 at ≤180 kPa and 6 at >180 kPa;
- the evaluator allowed amine identity to be only a +20 penalty, so the 6 high-pressure MDEA points matched Table V MEA points;
- after requiring amine identity, true coverage is **6/27**.

The detailed per-point before/after checklist is `evaluation/reports/vle_27_point_checklist.md`.

## Rate-unit before/after (jece 2024)

| Metric | Before | After |
|---|---|---|
| MEA absorption | 34.0 `10-5 mol CO2/mol/s` (outside) | 0.00034 `mol_CO2/(mol_amine*s)` |
| MEA desorption | 13.0 | 0.00013 |
| AMP absorption | 27.0 | 0.00027 |
| AMP desorption | 34.8 | 0.000348 |
| MDEA absorption | 13.7 | 0.000137 |
| MDEA desorption | 32.5 | 0.000325 |

Original values/units are preserved in `value_original`/`unit_original`; conversion metadata is stored in `unit_normalization`. Unit tests: `evaluation/test_rate_units.py` → **14/14**.

## Remaining issues and human-review list

1. **d6gc 2026 water-lean paper (1 L2) is still not extracted.** It contains a 30 wt% MEA reference but the LLM returns 0 records. This is outside the two Phase-3 fixes; needs section/table targeting or a second reference-row rule.
2. **8 expected `co2_partial_kPa` fields remain missing** (apenergy/jece/ijggc/ie400825). If the paper does not state total pressure, leaving null is correct; do not derive by assuming 1 atm. Human review should confirm whether the total pressure is stated.
3. **13 extra candidate records** remain (extra high-pressure VLE points and other non-reference points). They are not counted as matched; review whether they are valid L3 additions or over-extraction.
4. **1 rejected record** in the final batch: `10.1016/j.ijggc.2016.12.018` MEA with missing wt and mass-balance failure (`concentration_out_of_range;mass_balance;...`). `validate.py` rejected it as L4; it was not imported.
5. **No negative eval set.** The 38-record set is L2-positive only, so false-accept cannot be measured. A negative set is needed.
6. **Labels are historical, not human-verified.** `human_verified=false` for every sample; a stratified human audit is still needed before claiming gold-standard agreement.
7. **VLE parser profile is paper-specific.** The column-group algorithm is generic, but the 40 °C/180 kPa/0.5 L constants apply only to `10.1021/je00005a025`. Other papers need their own method profile.
8. **Other fields still missing in matched records** (some volumetric metrics, pKa, lean loading, total pressure). These are paper-specific and should not be filled by guessing.
9. **Rate module does not convert solution-basis rates to amine-basis** without concentration/density; such conversions are marked blocked.

## Human review checklist

- [ ] Inspect the 27 VLE raw rows in `evaluation/reports/vle_27_point_checklist.json`.
- [ ] Spot-check 5 of the 27 values against the PDF pages 3–4.
- [ ] Verify the 6 rate conversions preserve original value/unit and use 1e-5.
- [ ] Review the d6gc water-lean paper for the 30 wt% MEA reference.
- [ ] Review the 13 extra candidate records and classify as valid L3 or over-extraction.
- [ ] Confirm whether the 8 missing `co2_partial_kPa` are genuinely unstated.

## Reproduce

```powershell
.\.venv\Scripts\python.exe evaluation\build_eval_set.py
.\.venv\Scripts\python.exe evaluation\build_vle_checklist.py
.\.venv\Scripts\python.exe evaluation\test_rate_units.py
.\.venv\Scripts\python.exe evaluation\evaluate.py --candidate extractions\batch_20261124_143107 --label phase3_after
```
