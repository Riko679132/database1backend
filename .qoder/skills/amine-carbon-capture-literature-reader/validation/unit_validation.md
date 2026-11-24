# Unit Validation

## Principle

Every number in a record needs a unit and a basis. A value without a unit is not a measurement; it is a number waiting to be misinterpreted.

## Dimensional checks

| Quantity | Allowed units | Do not confuse with |
|---|---|---|
| Temperature | K, °C (convert to K) | temperature difference vs absolute temperature |
| Pressure | kPa, Pa, bar, atm, MPa | gauge vs absolute; total vs partial |
| CO2 concentration | vol%, mol%, ppm, mg/m³ | dry vs wet basis |
| Amine concentration | wt%, mol%, mol/L, mol/kg, g/L | solute vs solution basis |
| Loading | mol CO2/mol amine, mol CO2/mol N | per total amine vs per component/site |
| Capacity | mol/mol, mol/L, g/L | equilibrium vs rich vs cyclic |
| Rate | mol/(L·s), mol/(m²·s), 1/s | volumetric vs interfacial vs kinetic constant |
| Energy | kJ/mol, GJ/t CO2, kJ/kg | heat of absorption vs regeneration heat |
| Density | g/mL, kg/m³ | solution vs pure amine/water |
| Viscosity | mPa·s, Pa·s | kinematic vs dynamic |
| Molecular weight | g/mol, kg/kmol | number-average vs formula weight |

## Conversion gates

Before converting, confirm:

1. The source unit and the target unit are dimensionally compatible.
2. The basis is the same (dry/wet, total/partial, solute/solution, per amine/per site).
3. Density is available for any mol/L ↔ wt% conversion, for the same composition and temperature.
4. Molecular weight is the correct compound (and the correct mixture average for a blend).
5. The conversion is recorded with formula, inputs and assumptions.

If any gate fails, leave the field null and report why.

## Common unit traps

1. **wt% vs mol%.** A 30 wt% MEA solution is about 11.2 mol% MEA; a 30 mol% solution is much more concentrated.
2. **mol/L vs mol/kg.** Molarity depends on density; molality does not.
3. **Total vs partial pressure.** A table labelled "pressure" is often total pressure; a VLE table may report P_CO2.
4. **Gauge vs absolute.** Add atmospheric pressure only if the paper says gauge.
5. **Dry vs wet gas.** Water vapour can be several kPa at 40–60 °C; dry-basis vol% is not the same as wet-basis.
6. **K vs °C.** Add 273.15; do not add 273 (small but avoidable error).
7. **kJ/mol vs GJ/t CO2.** Convert with the CO2 molar mass (44.01 g/mol); 1 GJ/t = 1 kJ/g = 44.01 kJ/mol CO2.
8. **per amine vs per nitrogen site.** PZ and polyamines have multiple sites.
9. **g/L CO2 vs mol/mol.** Requires density and amine concentration.
10. **Rate units.** mol/(L·s) is volumetric; mol/(m²·s) is interfacial; do not compare without area.

## Precision and rounding

- Keep the paper's significant figures in `value_original`.
- Do not round a derived value more than the inputs justify.
- Do not turn "approximately 30%" into 30.00.
- If the paper reports a range, record the range in the report; do not pick the midpoint unless the paper defines it as the value.

## Unit field conventions

- `temperature_K`: K.
- `co2_vol_pct`: vol% (0–100).
- `co2_partial_kPa`, `total_pressure_kPa`: kPa.
- `initial_loading`, `rich_loading`, `lean_loading`: mol CO2/mol amine (state basis in `metric_definition`).
- `performance.unit`: the standardized unit; `unit_original`: the paper's unit.
- For volumetric metrics, keep the original unit and use a `_volumetric` metric name.

## If a unit is ambiguous

- Search the methods, table caption and footnotes.
- Search for the same quantity elsewhere in the paper with a unit.
- If still ambiguous, mark it `Unknown` and do not convert; report the ambiguity.
- Never resolve an ambiguity by choosing the most common unit in the field.
