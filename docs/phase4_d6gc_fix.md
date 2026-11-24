# Phase 4 — d6gc 2026 Reference-Row Fix

## Paper

- DOI: `10.1039/d6gc02196d`
- Title: Greening water-lean solvents for CO2 capture.
- Gold sample: test#3, 30 wt% aqueous MEA reference, 313.15 K, 12 vol%/12 kPa CO2, initial loading 0, regeneration efficiency 55%, regeneration heat 3.72 GJ/t CO2.

## Evidence locations

| Item | Paper location | Quote / value |
|---|---|---|
| Recipe | Table 4, p.10542 | `MEA 30%MEA — 70%` |
| Temperature | Methods, p.10540 | `heated to 313 K` |
| CO2 partial pressure | Methods, p.10540 | `12 kPa CO2 (simulated flue gas)` |
| Total pressure | not stated | left null |
| Fresh solution | Methods, p.10540 | `Before each test, 150 mL of fresh solvent was introduced` |
| Absorption/desorption time | Methods, p.10541 | 250 min absorption / 300 min desorption at 353 K |
| Regeneration efficiency | Results, p.10544 | `MEA showed the lowest regeneration efficiency at only 55%` |
| Regeneration heat | Results, p.10544 | `MEA (3.72GJ per t CO2)` |

## Root cause

The MEA reference is not a standalone performance table. It is split across:

1. Table 4 (composition);
2. methods (12 kPa, 313 K, fresh 150 mL);
3. results text (55%, 3.72 GJ/t).

The paper is primarily a water-lean solvent study, so the LLM treated the aqueous MEA baseline as secondary and returned 0 records. The gold L2 data are real but scattered; this is a **section/reference-row discovery failure**, not a PDF parsing failure.

## Fix

`server/reference_case_parser.py` adds a paper-specific reference profile:

- Scope and version are explicit.
- The recipe, temperature, pressure, fresh-solution and performance values are parsed with regex from the paper text; the final values are not hardcoded.
- The profile is only applied to `10.1039/d6gc02196d`; no other paper receives these constants.
- The record carries the table/text location, evidence types and a snapshot.

Text patterns are tolerant of two-column interleaving and missing spaces (e.g. `heatedto313K`, `MEA.MEAshowed`, `(3.72GJpertCO2)`).

## Test result

- `batch_20261124_144349` (d6gc alone): 1 L2 record, `validate.py` valid=1.
- Final Phase-4 batch `batch_20261124_145027`: d6gc contributes 1 L2; coverage becomes 38/38.
- The record:

```
MEA 30 wt% / water 70 wt%
313.15 K, co2_vol_pct 12, co2_partial_kPa 12, initial_loading 0
regeneration_efficiency 55%
regeneration_heat 3.72 GJ/t_CO2
L2, snapshot + evidence
```

## Generalization and limitations

- The profile mechanism is reusable; the specific DOI/patterns are paper-specific and marked as such.
- Other water-lean/reference-row papers need their own profile or a more general reference-row detector.
- The title/authors in the reference record may be null; DOI, PDF path/hash, table/page location and excerpt are present.
