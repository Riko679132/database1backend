# CO2 Loading and Capacity

## Definitions

| Quantity | Definition | Unit |
|---|---|---|
| Loading (α) | mol CO2 absorbed per mol amine (basis must be stated) | mol CO2/mol amine |
| Equilibrium loading | loading at equilibrium with a gas of known P_CO2 | mol/mol |
| Rich loading | loading of the CO2-rich liquid leaving the absorber | mol/mol |
| Lean loading | loading of the regenerated liquid entering the absorber | mol/mol |
| Cyclic capacity | rich loading − lean loading | mol/mol |
| Volumetric capacity | CO2 absorbed per volume of solution | mol/L or g/L |

For blends, state whether "per mol amine" means total amine, a specific amine, or a nitrogen site.

## From moles

```
α = n_CO2 / n_amine
```

If the paper reports masses:

```
n_CO2 = m_CO2 / M_CO2
n_amine = m_amine / M_amine
α = (m_CO2 / M_CO2) / (m_amine / M_amine)
```

Example: 26.8 g CO2 absorbed by 100 g MEA (M = 61.08; M_CO2 = 44.01):

```
n_CO2 = 26.8 / 44.01 = 0.609 mol
n_MEA = 100 / 61.08 = 1.637 mol
α = 0.609 / 1.637 = 0.372 mol CO2/mol MEA
```

## From a solution composition and CO2 content

If the liquid contains `m_solution` grams of solution, amine wt% `w`, and `m_CO2` grams of CO2:

```
n_amine = (m_solution × w / 100) / M_amine
n_CO2 = m_CO2 / M_CO2
α = n_CO2 / n_amine
```

Do not use the total solution mass as the amine mass.

## From gas uptake

For a gas stream of flow `Q` (L/s at a known T and P), CO2 mole fraction `y`, and absorption time `t`:

```
n_CO2 = y × Q × t / V_m
```

where `V_m` is the molar volume at the measurement conditions (22.414 L/mol at 0 °C, 101.325 kPa; 24.45 L/mol at 25 °C). Correct for water vapour and for the actual gas temperature/pressure.

If the gas flow is given in NL/h or SL/h, clarify the reference conditions before using it.

## Cyclic capacity

```
Δα = α_rich − α_lean
```

Volumetric cyclic capacity:

```
cyclic_capacity_volumetric = Δα × c_amine × M_CO2   (g CO2/L solution)
```

or directly from measured CO2 amounts per volume. If the paper reports `g-CO2/L-soln` without a density, keep the original unit and use `cyclic_capacity_volumetric`; do not convert to mol/mol.

## From titration or GC

- **Titration:** the CO2 content is determined by acid/base titration; use the calibration and stoichiometry stated in the paper.
- **GC:** the gas phase CO2 is measured; combine with gas flow and time for uptake, or with the liquid analysis for loading.
- **NMR/FTIR:** species concentrations; convert to loading only with a stated basis and calibration.

Do not assume a titration factor (e.g. 1 mol CO2 = 1 mol NaOH) unless the method states it.

## Common traps

1. Using the total solution mass instead of the amine mass.
2. Using the total amine concentration for a blend without stating the basis.
3. Treating a rich loading as equilibrium loading.
4. Treating a dynamic capacity as cyclic capacity.
5. Converting g/L to mol/mol without the solution density and amine concentration.
6. Forgetting the CO2/amine stoichiometry when interpreting a carbamate loading above 0.5.
7. Using the gas feed composition instead of the equilibrium gas composition for a VLE point.

## Executable calculator

```powershell
python .qoder\skills\amine-carbon-capture-literature-reader\scripts\calc.py loading --co2-mol 0.609 --amine-mol 1.0
python .qoder\skills\amine-carbon-capture-literature-reader\scripts\calc.py loading-from-mass --co2-g 26.8 --amine-g 100 --amine-mw 61.08
python .qoder\skills\amine-carbon-capture-literature-reader\scripts\calc.py cyclic --rich 0.609 --lean 0.200
```
