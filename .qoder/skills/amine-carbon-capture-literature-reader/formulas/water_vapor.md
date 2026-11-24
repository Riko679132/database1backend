# Water Vapour and Gas-Phase Pressure Balance

## Core checks

For a gas phase containing CO2 and water vapour:

```
0 <= P_CO2 <= P_total
P_CO2 + P_H2O <= P_total
0 <= y_i <= 1; sum(y_i) <= 1
```

If other gases are reported, add their partial pressures to the sum.

## Wet basis

If the paper explicitly states a wet-basis CO2 mole fraction and total pressure:

```
P_CO2 = y_CO2,wet × P_total
```

## Dry basis

If the paper explicitly states a dry-basis CO2 mole fraction and P_H2O:

```
P_CO2 = y_CO2,dry × (P_total − P_H2O)
```

If the paper gives a dry-basis composition but no P_H2O, do **not** use P_total as the dry-gas pressure and do not generate P_CO2. Keep `gas_basis=dry`, `co2_partial_kPa=null` unless the paper separately reports P_CO2.

## Pure-water saturation pressure

Only for pure water, with the NIST Antoine constants:

```
log10(P/mmHg) = 8.07131 − 1730.63 / (233.426 + T/°C)
P/kPa = P/mmHg × 0.133322387415
```

- Source: NIST Chemistry WebBook, Antoine equation for water, https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Mask=4&Type=ANTOINE
- Valid range: 1–100 °C (conservative lower bound; NIST tabulates a wider range).
- Version: `nist-antoine-water-1-100c`.
- This is **not** the water vapour pressure above an amine solution.

## Amine solutions

For an aqueous amine solution, P_H2O may be used or calculated only when:

1. the paper explicitly reports P_H2O; or
2. the paper reports water activity `a_w`, in which case `P_H2O = a_w × P_sat(T)`; or
3. a verified thermodynamic model and its parameters are explicitly available.

Without one of these, keep P_H2O unknown and mark the water-vapour check `not_assessable`. Do not substitute pure-water saturation pressure for a solution.

## Status vocabulary

| Status | Meaning |
|---|---|
| `derived_wet_basis` | P_CO2 derived from wet-basis fraction |
| `derived_dry_basis_with_p_h2o` | P_CO2 derived from dry-basis fraction with known P_H2O |
| `blocked_dry_basis_missing_p_h2o` | dry basis but P_H2O unknown; no P_CO2 generated |
| `blocked_basis_unknown` | basis not stated; no P_CO2 generated from total pressure |
| `not_assessable` | insufficient gas-phase inputs; basic checks only |
| `anomaly` | a pressure/fraction consistency check failed; downgrade, do not silently adjust |

Missing water-vapour information is not a rejection reason.
