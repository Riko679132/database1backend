# Partial Pressure and Gas Composition

## Core relations

For an ideal gas mixture:

```
P_i = y_i × P_total
y_i = P_i / P_total
```

With volume percent:

```
P_CO2 (kPa) = (vol% / 100) × P_total (kPa)
vol% = (P_CO2 / P_total) × 100
```

Example: 15 vol% CO2 at 101.325 kPa total pressure:

```
P_CO2 = 0.15 × 101.325 = 15.199 kPa
```

## What the paper may report

| Reported form | What you can compute | Caution |
|---|---|---|
| P_CO2 and P_total | y_CO2 = P_CO2/P_total; vol% | check dry/wet basis |
| y_CO2 and P_total | P_CO2 | ideal-gas assumption |
| vol% only | no P_CO2 unless total pressure is stated | do not assume 1 atm |
| P_CO2 only | no vol% unless total pressure is stated | do not assume 1 atm |
| total pressure and gas flow | partial pressure if composition known | flow reference conditions matter |

## Water vapour and dry/wet basis

At equilibrium, the gas can contain water vapour. A simple consistency check:

```
P_CO2 + P_H2O(T) ≤ P_total
```

If the sum exceeds the stated total pressure, the stated total pressure is inconsistent with the temperature and gas composition. Possible causes: the pressure is a partial pressure mislabelled as total, the gas temperature is different, or the water vapour pressure is not accounted for. Do not silently adjust; flag the inconsistency and discard the affected temperature column if it cannot be resolved.

Dry-basis vol% and wet-basis vol% differ. If a gas analyser reports dry-basis CO2, convert to wet basis using the water vapour mole fraction before comparing with a total pressure that includes water vapour.

## Feed gas vs equilibrium gas

- The feed gas composition (e.g. 15% CO2 in N2) is an inlet condition.
- The equilibrium gas composition is the gas in contact with the liquid after absorption; CO2 may be lower and water vapour may be present.
- For a VLE point, use the equilibrium P_CO2 if the paper reports it. If only the feed composition is given, do not label it as the equilibrium gas composition.

## Total pressure vs partial pressure

A table column labelled "pressure" may be:

- total pressure (absolute);
- CO2 partial pressure;
- gauge pressure;
- pressure drop.

Check the caption, units and nearby text. If the paper reports "CO2 partial pressure" and a separate "total pressure", use them as stated. If only one is given, do not infer the other without the gas composition.

## Gas flow conversions

For a flow `Q` at temperature `T` and pressure `P`:

```
n_dot = P × Q / (R × T)
```

with consistent units (e.g. Pa, m³/s, J/(mol·K), K). For ideal gas at standard conditions:

```
1 mol gas = 22.414 L at 0 °C, 101.325 kPa
1 mol gas = 24.45 L at 25 °C, 101.325 kPa
```

If the paper uses NL/h or SL/h, identify the reference conditions (often 0 °C or 20 °C, 1 atm). Do not mix NL and SL without conversion.

## Extraction rules

1. Record `co2_vol_pct`, `co2_partial_kPa` and `total_pressure_kPa` exactly as supported by the paper.
2. If total pressure is not stated, leave `co2_partial_kPa` and/or `co2_vol_pct` null as appropriate; never assume 1 atm.
3. If a value is derived, put the formula and inputs in the snapshot and set `is_derived=1` on the relevant performance row if applicable.
4. For VLE points, `co2_vol_pct` derived from a stated total pressure must be tagged `co2_vol_pct_derived_from_stated_total_pressure_*` in `qc_reason`.
5. Run the water-vapour check before accepting a total pressure.

## Executable calculator

```powershell
python .qoder\skills\amine-carbon-capture-literature-reader\scripts\calc.py partial-pressure --vol-pct 15 --total-kpa 101.325
python .qoder\skills\amine-carbon-capture-literature-reader\scripts\calc.py partial-pressure --y-co2 0.15 --total-kpa 101.325
```
