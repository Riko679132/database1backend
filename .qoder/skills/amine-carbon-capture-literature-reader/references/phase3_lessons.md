# Phase-3 Lessons

## Multi-column VLE tables

- A single table can contain several repeated `t/p/loading` column groups (e.g. 40/80/100 °C side by side). Plain text extraction interleaves them.
- Use word x-coordinates: find `p/kPa` header positions, the nearest left `t` column and the nearest right `loading` column; assign each numeric token to its nearest column.
- Carry the temperature down a group; a data row often omits the temperature after the first row.
- A footnote can be printed in the middle of the table in a two-column layout. Do not stop at the footnote; skip rows without p/loading.
- Parse the table caption for amine names and wt% values; a caption can be interleaved with data from the previous table.
- Table II–V of Shen & Li 1992 are the 40 °C low-pressure groups (6+7+7+7=27); the high-pressure >180 kPa points are outside the reference selection.
- The profile (target temperature, max P, total pressure, liquid volume) is paper-specific. Do not apply 180 kPa/0.5 L to another paper.
- Merge parser records with LLM records by `(DOI, amine_a, amine_b, wt_a, wt_b, T, P_CO2, performance)` and prefer the deterministic table record; keep non-duplicate high-pressure LLM points as L3.

## Rate units

- A value and unit can be copied correctly while the prefix is not applied. `34.0` in `10-5 mol CO2/(mol·s)` is `0.00034`, not `34.0`.
- Parse `10-5`, `10^-5`, `10−5`, `1e-5`, `mmol`, `umol` deterministically.
- Parse the denominator basis separately from the time unit:
  - mol amine → `mol_CO2/(mol_amine*s)`
  - g/kg amine → `mol_CO2/(kg_amine*s)` (g→kg factor)
  - kg/L solution → their own family
  - mol solution → blocked; needs concentration
- Never infer a density or concentration to convert solution-basis rates to amine-basis.
- Preserve `value_original`/`unit_original`; write normalized `value`/`unit` and a `unit_normalization` record with factor/formula.
- A unit error is not an OCR error or an LLM numeric hallucination if the original value is correct; classify it as a standardization/prefix bug.

## Evaluator

- Different amine identities are different systems. Do not allow a high-pressure MDEA point to match a Table V MEA reference; require amine identity.
- A coverage jump can be caused by false matches; always inspect per-DOI and failure lists.
- The 38-record set is L2-positive only; false-accept needs a separate negative set.
