# Phase 4 — Blocked Rate Case Review

## Unit tests

`evaluation/test_rate_units.py` → **15/15 passed**.

Covered:

- 10-5 / 10^-5 / 10−5 / 1e-5 prefixes;
- mmol, umol;
- min, h, s;
- mol amine, g/kg amine, kg/L solution, m3;
- `mol solution` blocked;
- missing unit blocked;
- actual paper case `g-CO2/L-soln/min` → unparsed;
- non-rate metric ignored.

## Actual blocked paper case

Paper: `10.1021/ie400825u`.

```
metric_name: initial_absorption_rate
value: 1.56
unit: g-CO2/L-soln/min
status: unparsed
reason: numerator is not a molar amount
```

### Is blocked correct?

**Yes.** The unit is a mass-based volumetric rate:

```
g CO2 / L solution / min
```

It cannot be converted to `mol_CO2/(mol_amine*s)` without:

- solution density (to convert L solution to mass/volume basis);
- amine concentration/composition (to convert to mol amine).

The paper does not provide those in this record. Guessing a density or concentration is prohibited.

### Separate issue: metric-name mismatch

The metric is named `initial_absorption_rate`, but the physical definition is a volumetric absorption rate. The expected/clean metric should be `absorption_rate_volumetric`, not a molar rate. This is a metric-name/definition issue, not a unit-conversion error.

Current behavior:

- the value and original unit are preserved;
- `unit_normalization` records `unparsed`;
- no conversion is attempted;
- the record remains available for review, but the metric mapping needs a future fix.

## Other blocked cases

- `mol CO2/(mol solution*s)` → blocked: denominator is solution moles, not amine; requires concentration.
- Missing unit → blocked: no basis to convert.
- Missing time unit → blocked.

## Conclusion

The blocked mechanism is working as intended: it refuses conversions that require missing physical data. It does not silently guess density, concentration or time units. The remaining work is metric-name mapping for mass/volume rates, not force-converting them.
