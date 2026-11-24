# Phase 4 — Extra Candidates and Negative Set

## Extra-candidate review

Final batch: `extractions/batch_20261124_145027`.

Full table: `evaluation/reports/extra_candidates_review.md` / `.json`.

| Category | Count | Decision |
|---|---:|---|
| VLE high-pressure or other-temperature points | 7 | Valid L3; outside the 27-point 40 °C low-P target, not negative |
| MEA VLE at 353 K | 1 | Valid L3; additional point, missing total/initial |
| Pilot CO2 removal efficiency | 1 | Valid L3; missing initial loading |
| `regeneration_heat` but actually heat of absorption/reaction (kJ/mol) | 6 | Insufficient Evidence; downgraded to L3 by metric semantics |
| **Total extras** | **15** | 9 Valid L3, 6 Insufficient Evidence, 0 Pending Review |

The six heat cases (4 apenergy, 1 ie400825, 1 acs) had negative or kJ/mol values and metric definitions saying heat of absorption/reaction. They were previously L2; `metric_semantics()` now downgrades them to L3.

High-pressure VLE points are **not** rejected merely for >180 kPa; they are real VLE data but outside the reference's 40 °C low-pressure selection and lack required conditions for L2.

## Negative set

File: `evaluation/negative_set_v1.json` (18 samples).

| Label | Count | Meaning |
|---|---:|---|
| Insufficient Evidence | 6 | Heat-of-absorption mislabeled as regeneration heat; L3 acceptable, L2 false accept |
| Duplicate | 1 | L4 rejected record from a DOI with a valid L2 MEA record |
| Out of Scope | 10 | 6 assessment-ledger papers + 4 actually processed boundary-out papers |
| Model-derived | 1 | Simulation paper; L3 only |
| Pending Review | 0 | — |

The four processed out-of-scope papers are:

- `10.1021/acs.iecr.1c04123` — mol/L blends, no density;
- `10.1155/2022/6278342` — VLE only in figures, embargo;
- `10.1021/acs.iecr.4c03980` — iron solubility, not amine performance;
- `10.1016/j.ces.2017.02.036` — 2–5 M blends, no wt%/density.

They were run through the final extractor in `batch_20261124_145418`; all produced **0 records**.

## Negative evaluation

Command:

```powershell
.\.venv\Scripts\python.exe evaluation\evaluate_negative.py `
  --candidate extractions\batch_20261124_145027 `
  --candidate extractions\batch_20261124_145418
```

Result:

| Metric | Value |
|---|---:|
| Negative samples | 18 |
| With a candidate in the batches | 7 |
| Correct L3 downgrade | 6 |
| Correct L4 reject | 1 |
| Correct not extracted | 11 |
| False accept L2 | 0 |
| False accept any L2/L3 | 0 |
| FAR (L2 / all negatives) | 0.0% |
| FAR (L2 / negatives with candidate) | 0.0% |

Report: `evaluation/reports/negative_eval.md`.

## Interpretation

- The heat-of-absorption cases are correctly downgraded to L3, not L2.
- The L4 duplicate is correctly rejected.
- The four processed boundary-out papers produce no accepted records.
- The negative set is still limited: only 7 samples have candidate records. It should be expanded before production.
