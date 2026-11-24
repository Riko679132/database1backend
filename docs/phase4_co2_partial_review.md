# Phase 4 — 8 Missing `co2_partial_kPa` Review

The 8 missing fields were not all errors. Classification below follows the paper text.

| # | Sample | Paper | Original evidence | Decision | Final value |
|---:|---:|---|---|---|---|
| 1 | 27 | apenergy 2016 | 30 wt% amine, 1 bar, 15 vol% CO2 / 85% N2, 313.15 K | Derivable: 15% × 100 kPa | 15.0 kPa |
| 2 | 28 | apenergy 2016 | same | Derivable | 15.0 kPa |
| 3 | 29 | apenergy 2016 | same | Derivable | 15.0 kPa |
| 4 | 30 | apenergy 2016 | same | Derivable | 15.0 kPa |
| 5 | 24 | jece 2024 | 15 vol% CO2, 2 L/min; total pressure not stated | Insufficient evidence; do not assume 1 atm | null |
| 6 | 25 | jece 2024 | same | Insufficient evidence | null |
| 7 | 26 | jece 2024 | same | Insufficient evidence | null |
| 8 | 59 | ie400825 2013 | 20% CO2/80% N2, atmospheric pressure, 40 °C | Derivable: 20% × 101.325 kPa | 20.265 kPa |

## Implementation

1. `extract.normalize()` now derives `co2_partial_kPa` only when both `co2_vol_pct` and `total_pressure_kPa` are present:
   ```
   co2_partial = co2_vol_pct / 100 × total_pressure
   ```
   It adds the note `co2_partial_derived_from_vol_and_total_pressure`.
2. `server/condition_profile.py` provides a paper-specific profile for `10.1021/ie400825u`:
   - only applies when the text says `atmospheric pressure` and `20% CO2`;
   - sets total pressure 101.325 kPa, temperature 313.15 K, initial loading 0 (fresh 50 mL solution);
   - adds Explicit/Contextual evidence.
3. jece 2024 has 15 vol% but no total pressure. The value remains null. The historical L2 label's 15 kPa was based on atmospheric convention, not an explicit total pressure; we do not copy that assumption.

## Result

- Final Phase-4 batch: `co2_partial_kPa` completeness 34/37 (91.9%); the only missing 3 are jece.
- No value was guessed; no total pressure was assumed.
- A separate ijggc record (sample 58) has `co2_partial_kPa=9.5` but missing total pressure; that field remains null and is listed in the regression failures, not in this 8-row partial-pressure table.
