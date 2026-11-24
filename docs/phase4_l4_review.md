# Phase 4 — L4 Rejection Review

## Record

- DOI: `10.1016/j.ijggc.2016.12.018`
- Amine: MEA
- Validation result: L4
- Reason: `concentration_out_of_range;mass_balance;test_co2_vol_pct;test_initial_loading`
- Status: not imported.

## Paper evidence

The same paper already has a valid L2 MEA record with 30 wt% MEA, 70 wt% water, 313.15 K and its VLE/performance data. The paper's MEA baseline is 30 wt% aqueous.

## Finding

The rejected candidate has no wt%/water values, so:

- the recipe cannot close to 100 ± 0.1 wt%;
- total amine concentration cannot be established;
- `mass_balance` and `concentration_out_of_range` are correct hard rejections.

This is a **duplicate/incomplete candidate** from a DOI that already has a valid L2 record. It is not a paper-data omission that requires filling. Filling 30/70 from the other record would be a prohibited cross-record patch.

## Decision

- Keep L4; do not import.
- Classify in the negative set as `Duplicate`/`Insufficient Evidence`.
- No code change is required; `validate.py` is behaving correctly.
