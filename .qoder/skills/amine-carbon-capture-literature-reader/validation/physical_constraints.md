# Physical and Boundary Constraints

## Research boundary (literature)

A literature record is in scope only if:

- the solvent is aqueous;
- the system is a single amine or a two-component amine blend;
- total amine is 20–50 wt%;
- there is no additive, salt, phase-change behaviour or slurry;
- the amine(s) are in the project whitelist.

If any condition fails, do not emit an in-scope record. Report the reason and keep the paper in the reading report.

## Recipe constraints

- `wt_a + wt_b + water_wt = 100 ± 0.1`.
- `total_amine_wt = wt_a + wt_b` and must be 20–50 for literature.
- `recipe_type='mono'` requires `amine_b=null` and `wt_b=null`.
- `recipe_type='binary'` requires a second amine with a valid InChIKey and `wt_b`.
- `additive_flag`, `salt_flag`, `phase_flag` must be 0 for in-scope literature; any 1 is a hard rejection.
- A ternary or multicomponent blend is not a binary; do not collapse it.

## Test constraints

- `temperature_K` must be positive; typical aqueous amine data are 273–473 K. Flag values outside 250–500 K as suspicious.
- `co2_vol_pct` must be 0–100.
- `co2_partial_kPa` must be ≥ 0 and ≤ `total_pressure_kPa` when both are present.
- `total_pressure_kPa` must be positive; flag values below 10 kPa or above 10 MPa unless the paper justifies them.
- `initial_loading`, `rich_loading`, `lean_loading` must be ≥ 0; flag > 1.5 as implausible without explanation; flag > 1.0 for a single amine as needing a bicarbonate/site-basis explanation.
- `rich_loading ≥ lean_loading`; `initial_loading` is usually 0 for a fresh solution, but do not assume if the paper says otherwise.
- Gas flow, liquid volume and gas/liquid ratio must be positive and in a consistent basis.

## VLE-specific constraints

- `P_CO2 + P_H2O(T) ≤ P_total` (water-vapour check).
- A VLE point at a given temperature should not be duplicated with the same conditions.
- Do not derive `co2_vol_pct` from an unstated total pressure.
- A point reported only as a figure is not a table point; mark it figure-only.

## Simulation exception

For `test_origin='simulation'`:

- total amine may exceed 50 wt%;
- mass balance and binary identity still apply;
- `qc_level='L3'`, `qc_reason` starts with `simulation_data`, `performance.is_derived=1`;
- simulation never enters L1/L2 gold standard.

## Plausibility flags (do not auto-correct)

Flag, but do not silently change, values that:

- imply a negative or >100% component;
- give a loading far above the expected stoichiometric range;
- give a density/viscosity far outside the paper's other data;
- give a regeneration energy below the heat of absorption or physically unrealistic;
- give a capture efficiency >100%;
- give a pressure/temperature inconsistent with the stated phase.

Record the flag in the report and, if it affects a database field, in `qc_reason`.

## Identity constraints

- Resolve amine identity from CAS/name, not abbreviation alone.
- Binary records need both identities.
- SMILES/InChIKey must be resolved from a reliable source, not hand-typed.
- If identity is uncertain, do not emit the record; mark it Unknown.

## What not to do

- Do not "fix" a paper's value to satisfy a constraint.
- Do not reject a record solely because a value is surprising; investigate first.
- Do not lower a QC level to hide a boundary violation.
- Do not treat a simulation result as experimental data.
