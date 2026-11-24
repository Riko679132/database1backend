# Phase 3 — Rate Unit Scale Root Cause and Fix

## Error case

Paper: `10.1016/j.jece.2024.112664` (30 amines, Table 3).

The paper header reports initial absorption/desorption rates as:

```
(10-5 mol CO2/mol·s)
```

The table values are 34.0, 13.0, 27.0, 34.8, 13.7, 32.5. The correct standardized values are:

```
34.0 × 10^-5 = 0.00034 mol CO2/(mol amine·s)
13.0 × 10^-5 = 0.00013
27.0 × 10^-5 = 0.00027
34.8 × 10^-5 = 0.000348
13.7 × 10^-5 = 0.000137
32.5 × 10^-5 = 0.000325
```

## What the LLM produced

The LLM correctly copied the table value and the printed unit:

```
value = 34.0
unit  = 10-5 mol CO2/mol/s
value_original = 34.0
unit_original  = 10-5 mol CO2/mol/s
```

The failure was in **unit standardization**, not OCR, not numeric hallucination and not the metric definition: the `10^-5` prefix was part of the unit string but was never applied to the value. The record therefore stored 34.0 in the database-facing `value` field.

## Root cause classification

| Candidate cause | Verdict |
|---|---|
| OCR error | No — text layer, value 34.0 correct |
| LLM numeric hallucination | No — paper value is 34.0 |
| Metric definition error | No — rate definition correct |
| Unit parsing/prefix error | **Yes** — `10-5` not parsed as 1e-5 |
| Time-unit error | No — denominator was seconds |
| Mass/volume basis error | No — denominator was mol amine |
| Standardization bug | **Yes** — value was not multiplied by the prefix |
| Field mapping error | No — metric name correct |

## Fix: `server/units.py`

- `parse_scale`: recognizes `10-5`, `10^-5`, `10−5`, `1e-5`, `x10-5`, `mmol`, `umol`.
- `_basis`: distinguishes `mol_amine`, `mol_solution`, `kg_amine`, `g_amine`, `kg_solution`, `L_solution`, `m3`, unknown.
- `_time_unit`: recognizes s/sec, min, h/hr.
- `normalize_rate`: converts to canonical families:
  - `mol_CO2/(mol_amine*s)`
  - `mol_CO2/(kg_amine*s)`
  - `mol_CO2/(kg_solution*s)`
  - `mol_CO2/(L_solution*s)`
  - `mol_CO2/(m3*s)`
- Blocks conversion when the basis is `mol_solution` or unknown, or time is missing; it never guesses a density, concentration or molecular weight.
- `apply_to_performance` preserves `value_original`/`unit_original`, writes the normalized `value`/`unit`, and stores a `unit_normalization` record with scale, time, basis, factor and formula.
- `server/extract.py` calls the module in `normalize()` and appends `rate_unit_normalized` or `rate_unit_conversion_blocked` to QC notes.

## Test results

Unit tests: `evaluation/test_rate_units.py` → **14/14 passed**.

Cases include:

- 10-5/10^-5/10−5/1e-5 → 1e-5
- mmol → 1e-3
- umol → 1e-6
- min → 60 s
- h → 3600 s
- g amine → kg amine ×1000
- solution-volume/solution-mass rates preserved in their own family
- mol solution rate → blocked
- missing unit → missing_unit
- non-rate metric → not_rate

Paper test:

| Amine | Metric | Before value/unit | After value/unit |
|---|---|---|---|
| MEA | initial_absorption_rate | 34.0, `10-5 mol CO2/mol/s` | 0.00034, `mol_CO2/(mol_amine*s)` |
| MEA | initial_desorption_rate | 13.0 | 0.00013 |
| AMP | initial_absorption_rate | 27.0 | 0.00027 |
| AMP | initial_desorption_rate | 34.8 | 0.000348 |
| MDEA | initial_absorption_rate | 13.7 | 0.000137 |
| MDEA | initial_desorption_rate | 32.5 | 0.000325 |

In the final 7-paper regression, all three jece rate fields were within tolerance (36/39 fields; the missing 3 are `co2_partial_kPa`).

## What is preserved

- `value_original` = paper value (e.g. 34.0)
- `unit_original` = paper unit (e.g. `10-5 mol CO2/mol/s`)
- `metric_definition` includes the conversion note
- `unit_normalization` stores scale/time/basis/factor/formula
- No database schema change; the extra JSONL field is ignored by the importer but retained in the snapshot/JSONL.

## Remaining limitations

- Rates normalized by solution mass/volume are converted within their own family, not to mol amine, because that would require concentration/density.
- `mol solution` denominator is blocked (it needs a concentration definition).
- The module does not infer a missing time unit or a missing basis; those remain blocked for human review.
- The prompt still asks the LLM to preserve original values/units; the deterministic module is the authority for standardization.
