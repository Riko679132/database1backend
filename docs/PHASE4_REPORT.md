# Phase 4 Final Acceptance Report

## 1. Frozen baseline

Phase 3 was frozen at:

- batch: `extractions/batch_20261124_143107`
- report: `evaluation/reports/phase3_after_corrected_20261124_143322.json`
- metrics: 22/38 coverage, 76.7% completeness, 66.1% agreement
- code/test/Skill hashes: `evaluation/phase3_freeze.json`

Phase 4 final batch: `extractions/batch_20261124_145027`.

## 2. Final metrics

### Positive set (38 historical L2 labels)

| Metric | Value |
|---|---:|
| Coverage | **38/38** |
| Field completeness | **97.25%** |
| Numeric agreement (within field tolerance) | **97.25%** |
| Recipe complete | **38/38** |
| QC L2 | **38** |
| False reject L2 | **0** |
| Extra candidate records | 15 |
| Rejected records | 1 (L4 duplicate) |

Field-level remaining gaps:

- 3 `co2_partial_kPa` missing (jece 2024; total pressure not stated → correctly null);
- 1 total pressure, 1 lean loading, 1 cyclic capacity, 1 regeneration efficiency missing (ijggc);
- 3 volumetric metrics missing (ie400825; metric-name/definition mapping pending).

Precision/Recall/F1 on the combined positive+negative strict L2 view:

- TP = 38, FN = 0, FP = 0 → **Precision 100%, Recall 100%, F1 100%** for L2 classification against this test set.
- This is based on historical labels and a small negative set; it is **not** a human gold-standard metric.

### Negative set

- 18 negative samples; 7 have candidate records in the batches.
- Outcomes: 6 correct L3 downgrades, 1 correct L4 rejection, 11 correct not-extracted.
- **False accept L2: 0; false accept any L2/L3: 0.**
- FAR (L2 / all negatives): **0%**; FAR (L2 / negatives with candidate): **0%**.
- Report: `evaluation/reports/negative_eval.md`.

### VLE

- Target Shen & Li: **27/27** points, 4 tables (II 6, III 7, IV 7, V 7), 284/284 expected fields within tolerance.
- Table/group/temperature/pressure/loading association: **27/27**.
- Cross-paper profile test: target profile selects 27; three other VLE papers have no profile, detect no repeated t/p/loading groups and select 0; no target constants are applied.
- Report: `docs/phase4_vle_profile.md`, `evaluation/reports/vle_27_point_checklist.md`.

### Rate units

- Unit tests: **15/15**.
- jece 2024: 6/6 rates correct (e.g. 34.0 × 1e-5 = 0.00034).
- Actual blocked case `g-CO2/L-soln/min`: correctly `unparsed`; no density/concentration guess.
- Metric-name mismatch (`initial_absorption_rate` vs `absorption_rate_volumetric`) remains for human review.
- Report: `docs/phase4_blocked_rates.md`.

### d6gc

- 30 wt% MEA reference recovered from Table 4 + methods + results text.
- 1 L2 record: 55% regeneration efficiency, 3.72 GJ/t CO2.
- Final coverage 38/38.
- Report: `docs/phase4_d6gc_fix.md`.

### CO2 partial pressure

- apenergy 4 records: derived 15 kPa from 15 vol% × 100 kPa.
- ie400825 1 record: derived 20.265 kPa from 20 vol% × 101.325 kPa (atmospheric).
- jece 3 records: 15 vol% but no total pressure → null, not guessed.
- Report: `docs/phase4_co2_partial_review.md`.

### Snapshots and database

- 7/7 paper snapshots; 53/53 batch records with existing, hash-matching snapshots.
- `postcheck.py`: seven hard checks PASS; L2 snapshots 38/38.
- Database unchanged: 63 test / 73 performance / 17 source / 38 L2; no Phase-4 batch imported; max test id 63.
- No schema change.

## 3. Deliverables

1. d6gc root cause/fix — `docs/phase4_d6gc_fix.md`
2. 8 partial-pressure review — `docs/phase4_co2_partial_review.md`
3. 15 extra-candidate review — `evaluation/reports/extra_candidates_review.md`
4. L4 review — `docs/phase4_l4_review.md`
5. Negative set — `evaluation/negative_set_v1.json`, `docs/phase4_extras_negative.md`
6. Human review packet — `evaluation/human_review_packet_v1.json/.csv`, `docs/human_review_progress.md`
7. VLE profile specification/cross-paper test — `docs/phase4_vle_profile.md`, `evaluation/test_vle_profiles.py`
8. Blocked-rate review — `docs/phase4_blocked_rates.md`
9. Regression reports — `evaluation/reports/phase4_definitive_20261124_145214.md`, `evaluation/reports/negative_eval.md`
10. Code changes — listed below
11. Remaining risks — section 5

### Phase 4 code changes

- `server/vle_table_parser.py` — profile separation, no-default selection, deterministic points/records.
- `server/reference_case_parser.py` — d6gc reference-row profile.
- `server/condition_profile.py` — ie400825 atmospheric/20% CO2 condition profile.
- `server/provenance.py` — metric semantics (heat of absorption vs regeneration heat).
- `server/extract.py` — CO2 partial derivation, rate prompt.
- `server/tasks.py` — VLE/reference/condition profiles, merging/dedup, snapshot metadata.
- `server/units.py` — rate unit parsing/normalization (Phase 3, extended tests).
- `evaluation/build_vle_checklist.py`, `build_negative_set.py`, `evaluate_negative.py`, `build_human_review_packet.py`, `test_vle_profiles.py`, `test_metric_semantics.py`, `test_rate_units.py`.
- `docs/` Phase-4 reports.

## 4. Completion status

### Completed

- Known d6gc omission has root cause, evidence, fix and L2 result.
- 8 partial-pressure cases reviewed; 5 derivable/filled, 3 correctly null.
- 15 extras classified; 6 mislabeled heat records downgraded to L3; 9 valid L3.
- L4 duplicate reviewed and correctly rejected.
- Positive and negative evaluation exists; FAR 0 with stated denominators.
- VLE algorithm/profile separated; target 27/27; no profile leakage.
- Rate conversion/blocking verified; original values/units preserved.
- Snapshot/hash completeness verified; DB untouched.
- 38/38 positive coverage, 97.25% historical-label field agreement.

### Partially completed

- **Human gold standard**: 0/38 human-verified; packet ready, all pending.
- **VLE cross-paper**: only the target paper has a working profile; three other VLE papers need profiles. The test proves no false application, not universal parsing.
- **Negative set**: 18 samples, only 7 with candidates; out-of-scope coverage should be expanded.

### Not completed

- Human-verified field/sample agreement.
- Full VLE parsing for other layouts.
- Full metric-name mapping for mass/volume rates (`absorption_rate_volumetric`).
- Full completeness for jece partial pressure (paper does not state total pressure).
- Source excerpt persistence in the database schema (still a schema-extension proposal).

## 5. Remaining risks

| Risk | Level | Impact | Mitigation |
|---|---|---|---|
| Historical labels not human-verified | High | 97.25% is not human accuracy | Complete human review packet |
| VLE profiles only for one paper | High | New multi-column papers need manual config | Add profiles per paper / deterministic parser |
| Negative set small | Medium | FAR confidence limited | Add out-of-scope and near-miss candidates |
| Metric-name mapping | Medium | `initial_absorption_rate` vs volumetric rate can be mislabeled | Add metric-name semantics rule |
| jece partial pressure | Low | 3 null fields | Keep null; document unstated total pressure |
| Source excerpt not in DB | Medium | Traceability relies on snapshot files | Schema extension proposal |
| Human review not done | High | Cannot claim production-grade accuracy | Human audit before production |

## 6. Recommendation

- **Do not enter unattended production yet.**
- **Can enter a human-in-the-loop trial run**: the extractor now produces traceable L2 candidates, correctly rejects/degrades known bad cases, and has 38/38 positive coverage with 97.25% historical-label agreement.
- Before formal production, complete:
  1. human review of at least the 28 priority-1 samples;
  2. VLE profiles for at least 3 additional multi-column papers;
  3. expand the negative set to at least 30–50 samples with candidates;
  4. metric-name mapping for volumetric/mass rates;
  5. human-confirmed gold-standard metrics;
  6. decide whether to add the proposed schema fields (excerpt, gas basis, error type, etc.).
