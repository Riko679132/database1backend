# Phase-2 Extraction Lessons

## What worked

1. **Conditional L2 is possible with a machine-verified snapshot.** Barzagli 2019 (30 wt% MEA, pure CO2, 8 h, 313.15 K) produced one L2 record from the new LLM path after the prompt required: fresh-solution initial loading, pure-CO2 vol%, and verbatim/table-row evidence. The snapshot records prompt hash, knowledge module hashes, model, evidence and verification.
2. **Dynamic knowledge routing changes the prompt.** A VLE paper selected `co2_equilibrium`, a blend paper selected `mixed_amine_systems`, and the selected module hashes are recorded.
3. **Table-grid context improves multi-column tables.** The 27-point Shen & Li table went from 4 extracted rows to 12 when a coordinate grid was supplied. It is still incomplete, but the direction is correct.
4. **The evaluator catches both recall and precision problems.** It reported the 27-point paper's partial coverage, unit-scale errors in jece rates, and extra/missing records separately.

## What still fails

1. **Multi-column VLE tables remain the largest gap.** Shen & Li 1992 has four side-by-side temperature groups and multiple pages; even with table-grid context, only 12 of 27 reference points were captured. A deterministic table parser or table-specific LLM chunks are needed.
2. **Rate units are not normalized reliably.** Jece 2024 initial absorption/desorption rates were reported by the model with a different scale (e.g. 34.0 vs 0.00034). Matching now identifies the record, but the value is outside tolerance. The prompt must require preserving the paper's rate unit and recording any conversion factor.
3. **VLE points often lack `co2_vol_pct`/`initial_loading`.** When only P_CO2 is reported and total pressure is absent, `co2_vol_pct` must stay null; the record is L3 unless the paper states a fresh solution for initial loading. Do not force L2 by guessing.
4. **Water-lean/reference-row papers can return empty.** The d6gc 2026 water-lean paper contains a 30 wt% MEA reference but the model returned no records. Reference-row extraction needs stronger table/section targeting.
5. **SI is publisher-specific.** ACS SI download worked; other publishers may return HTML landing pages, login gates or different link patterns. Record failures; do not bypass access control.
6. **Figure digitization is not automatic for arbitrary curves.** Colored markers can be auto-detected; overlapping/black curves require manual points or an external digitizer.

## Regression expectations

- Historical fixture: 38/38, 100% completeness and agreement (harness sanity only).
- First 7-paper LLM run: 11–14/38 coverage, ~80% completeness, ~79% agreement.
- Final 7-paper LLM run with table grid/prompt improvements: 22/38 coverage, 76.7% completeness, 66.1% agreement, 10 L2 / 12 L3 / 16 no-match.

The final run trades precision for recall: more VLE rows are captured, but some are incomplete or have unit/condition errors. This trade-off is exactly what the regression report is intended to expose; do not treat coverage alone as success.

## Phase-3 update

- The 27-point Shen & Li VLE table is now extracted by `server/vle_table_parser.py` at **27/27**. The original 12/27 was an evaluator artifact; true LLM coverage was 6/27.
- Rate units are normalized by `server/units.py`; jece 2024 rates now match 6/6 (e.g. 34.0 × 1e-5 = 0.00034).
- Final 38-record regression: **37/38 coverage, 95.9% completeness, 95.9% agreement**.
- Remaining: d6gc water-lean reference, missing `co2_partial_kPa` where total pressure is not stated, 13 extra candidate records, no negative eval set, historical labels not human-verified.

## Snapshot integrity lesson

A historical snapshot was written with `Path.write_text` on Windows, which converted `\n` to `\r\n`; the stored SHA-256 was computed over LF text and did not match the file. The writer now writes bytes (`write_bytes`) and hashes those bytes. The affected Barzagli snapshot was normalized to LF and now matches its stored hash.
