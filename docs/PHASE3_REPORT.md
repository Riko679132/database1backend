# Phase 3 Report

> **Phase 4 update:** after d6gc reference extraction, condition profiles and metric semantics, the final positive regression is **38/38 coverage, 97.25% completeness/agreement**. See `docs/PHASE4_REPORT.md`.

## Scope

Only two problems were addressed:

1. The 27-point multi-column VLE table (Shen & Li 1992) was incomplete.
2. Rate metrics had a unit-scale error.

No database schema change, no value filling, no threshold reduction.

## Results

| Item | Before | After |
|---|---|---|
| VLE target points | 6/27 (true; 12/27 was an evaluator artifact) | **27/27** |
| Rate metrics (jece) | 0/6 within tolerance | **6/6** |
| 38-record coverage | 16/38 | **37/38** |
| Field completeness | 79.0% | **95.9%** |
| Numeric agreement | 75.5% | **95.9%** |
| QC L2 | 10 | **37** |
| No-match | 22 | **1** |

The only remaining L2 no-match is the d6gc 2026 water-lean paper with a 30 wt% MEA reference.

## Deliverables

1. Root cause: `docs/phase3_vle_root_cause.md`
2. 27-point checklist: `evaluation/reports/vle_27_point_checklist.md` / `.json`
3. Parser code: `server/vle_table_parser.py`
4. Before/after VLE results: `docs/phase3_vle_root_cause.md` + checklist
5. Rate root cause: `docs/phase3_rate_unit_root_cause.md`
6. Rate semantics module: `server/units.py`
7. Unit tests: `evaluation/test_rate_units.py` (14/14)
8. 38-record comparison: `docs/phase3_regression_comparison.md`
9. Remaining issues and human review: `docs/phase3_regression_comparison.md`
10. Integration: `server/tasks.py` now merges deterministic VLE records and normalizes rate units.

## Key finding about the original 12/27

The prior evaluator allowed a different amine identity to match with only a +20 penalty. Six >180 kPa MDEA points were falsely matched to Table V MEA points, inflating 6/27 to 12/27. The evaluator now treats different amine identities as non-matching. The true before coverage was 6/27.

## What was fixed

### Multi-column VLE

- `server/vle_table_parser.py` reconstructs repeated `t/p/loading` column groups from word x-coordinates.
- It carries temperature down a group, skips interleaved footnotes, parses table captions/recipes, and selects the paper-specific 40 °C / ≤180 kPa target.
- `server/tasks.py` merges parser records with LLM records, removes duplicates, and keeps non-duplicate high-pressure LLM points as L3.
- Each parser record has a table/page/row excerpt, method-derived total pressure/initial loading, evidence types, and an L2 snapshot.

### Rate units

- `server/units.py` parses `10-5`, `10^-5`, `1e-5`, `mmol`, `umol`, time units and denominator basis.
- It converts to canonical unit families only when the basis is convertible; solution-basis rates that need concentration/density are blocked.
- `server/extract.py` calls the module in `normalize()` and preserves `value_original`/`unit_original`.

## Remaining work

- d6gc water-lean reference row.
- Missing `co2_partial_kPa` in 8 records (likely genuinely unstated; do not guess).
- 13 extra candidate records for human review.
- 1 rejected record in the final batch: `10.1016/j.ijggc.2016.12.018` MEA (missing wt/mass balance), not imported.
- Negative eval set for false-accept measurement.
- Human audit of historical L2 labels.
- Generalizing the VLE method profile beyond this paper.
