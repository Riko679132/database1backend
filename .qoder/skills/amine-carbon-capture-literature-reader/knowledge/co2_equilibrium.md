# CO2 Equilibrium (VLE)

## Purpose

Provide the minimum theory needed to read VLE tables and figures correctly, distinguish equilibrium from rate/capacity measurements, and decide whether a VLE point can be extracted into the database.

## Definitions

- **Loading (α):** moles of CO2 absorbed per mole of amine (or per mole of a specified amine/site). The basis must be stated.
- **Equilibrium CO2 partial pressure (P_CO2):** the partial pressure of CO2 in the gas phase at equilibrium with the liquid.
- **Total pressure (P_total):** the absolute pressure of the gas phase.
- **Gas mole fraction (y_CO2):** moles CO2 per mole of dry or wet gas; the basis must be stated.
- **Volumetric CO2 concentration (vol%):** approximately equal to y_CO2 for an ideal gas; correct for water vapour and dry/wet basis when needed.
- **Henry's law:** at low-to-moderate pressure, the physical solubility of a gas is proportional to its partial pressure: `p_i = H_i × x_i` (or `p_i = H_i × C_i`, depending on the convention). H depends on temperature, solvent and units.
- **Activity coefficient:** in concentrated electrolyte solutions, Henry's law with concentration is not sufficient; activity coefficients and speciation must be included.

## Core relations

### Partial pressure from gas composition

```
P_CO2 = y_CO2 × P_total
```

If the paper gives vol% and total pressure:

```
P_CO2 = (vol% / 100) × P_total
```

If the paper gives only vol% but not total pressure, you can record `co2_vol_pct` but **not** `co2_partial_kPa`. Do not assume 1 atm unless the paper states it.

### Gas composition from partial pressure

```
y_CO2 = P_CO2 / P_total
vol% = y_CO2 × 100
```

This is only valid if the gas is ideal and the basis (dry/wet) is consistent.

### Water vapour check

At equilibrium, the gas may contain water vapour:

```
P_CO2 + P_H2O(T) ≤ P_total
```

If the stated total pressure is lower than the sum, the stated total pressure is inconsistent (or the gas is not at the stated temperature). Discard that temperature column or flag it; do not silently "fix" it.

### Henry's law and temperature dependence

```
p_CO2 = H(T) × x_CO2
ln(H(T2)/H(T1)) ≈ −ΔH_sol/R × (1/T2 − 1/T1)
```

The sign and magnitude depend on the enthalpy of solution; check the paper's convention. For reactive solvents, Henry's law applies to the physical (unreacted) CO2 concentration, not total loading.

### Van't Hoff relation for absorption heat

```
ln(P2/P1) = −ΔH_abs/R × (1/T2 − 1/T1)
```

or

```
ln P = A + B/T
```

where `B = −ΔH_abs/R` for a consistent convention. Use this only when the paper provides equilibrium data at multiple temperatures and the same loading.

## What VLE data look like

| Form | Example | Extraction implication |
|---|---|---|
| Table of `(T, P_CO2, α)` | each row is a point | one test per row; best source |
| Table of `(T, P_total, y_CO2, α)` | compute P_CO2 | one test per row; record both P_total and P_CO2 if stated |
| Isotherm figure | α vs P_CO2 at fixed T | figure-only; do not digitize without a tool |
| Loading vs time | kinetic/dynamic | not equilibrium; do not label as equilibrium loading |
| Parity plot (measured vs model) | model validation | do not extract individual points unless the table/SI gives them |

## Measurement methods (VLE)

- **Static synthetic/analytical method:** known amounts of gas and liquid are equilibrated; gas phase is sampled or pressure change is measured.
- **Headspace gas chromatography:** equilibrium gas composition is measured; useful for low P_CO2.
- **Titration/chemical analysis:** liquid loading is measured after equilibration (e.g. BaCl2/NaOH titration for CO2).
- **Bubble column / wetted wall:** often used for kinetics or mass transfer, not equilibrium.
- **Pilot/packed column:** rich/lean loadings and capture efficiency; not a VLE isotherm.

Do not mix data from different methods without noting the method and its definition of loading.

## Data-expression traps

1. **Total pressure vs partial pressure.** A table labelled "pressure" may be total pressure; check the caption and gas composition.
2. **Dry vs wet gas.** Vol% on a dry basis differs from the equilibrium wet gas; water vapour can be several kPa at 40–60 °C.
3. **Feed gas vs equilibrium gas.** The feed composition (e.g. 15% CO2 in N2) is not necessarily the equilibrium gas composition. Use the equilibrium P_CO2 if reported.
4. **Loading basis.** Per total amine, per specific amine, per nitrogen site; for blends, this changes the number.
5. **Equilibrium vs rich loading.** A column's rich loading may be kinetically limited, not equilibrium.
6. **Temperature.** K vs °C; isotherms at 298, 313, 333, 353 K are different data sets.
7. **Model vs experiment.** A smooth curve may be a model fit; only extract measured points from tables/SI or clearly marked symbols.

## L2 criteria for a VLE point

A VLE point can be a complete L2 record only if:

- temperature_K is stated;
- co2_vol_pct is stated or derivable from a stated total pressure and gas composition;
- initial_loading is known (fresh/unloaded solution for an equilibrium point, usually 0);
- the recipe is closed in wt% (or the paper reports wt% directly);
- a raw snapshot records the table/figure, row text, conditions and derivation.

If the paper gives only P_CO2 and loading but no total pressure or gas composition, `co2_vol_pct` is missing; the point may be L3 (incomplete) or not extracted, depending on the project rule. Do not invent a total pressure.

## References

- Jou, F.-Y., Mather, A. E., & Otto, F. D. "The solubility of CO2 in a 30 mass percent monoethanolamine solution." *Can. J. Chem. Eng.* 73 (1995): 140–147.
- Austgen, D. M., Rochelle, G. T., Peng, X., & Chen, C. C. "Model of vapor-liquid equilibria for aqueous acid gas-alkanolamine systems using the electrolyte-NRTL equation." *Ind. Eng. Chem. Res.* 28 (1989): 1060–1073.
- Deshmukh, R. D., & Mather, A. E. "A mathematical model for equilibrium solubility of hydrogen sulfide and carbon dioxide in aqueous alkanolamine solutions." *Chem. Eng. Sci.* 36 (1981): 355–362.
- Kohl & Nielsen, *Gas Purification*, 5th ed., 1997.
- Wilcox, J. *Carbon Capture*, Springer, 2012.
