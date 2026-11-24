# Physical Properties and Performance Parameters

## Purpose

Define the properties and performance metrics that appear in amine-CO2 papers, with their units and extraction cautions. Distinguish a measured property from a derived or assumed one.

## Property table

| Property | Definition | Common units | Method | Extraction caution |
|---|---|---|---|---|
| Density | mass per volume of solution | g/cm³, kg/m³ | pycnometer, densimeter, vibrating tube | needed for mol/L ↔ wt%; must match composition and T |
| Viscosity | resistance to flow | mPa·s, Pa·s | viscometer | strongly depends on concentration, loading and T |
| Surface tension | force per length at interface | mN/m | tensiometer | changes with amine and loading; not a capacity metric |
| Heat capacity | energy to raise temperature | kJ/(kg·K), J/(mol·K) | calorimetry, DSC | needed for sensible heat; basis (mass/mole) matters |
| Thermal conductivity | heat conduction | W/(m·K) | transient hot wire | used in process design; rarely a primary capture metric |
| Vapour pressure | equilibrium vapour pressure of amine/water | kPa, Pa | ebulliometry, GC | important for amine loss; not CO2 capacity |
| CO2 solubility | equilibrium CO2 content at given T/P | mol CO2/mol amine, mol/kg, g/L | VLE apparatus | define loading basis and P_CO2 |
| Absorption capacity | amount absorbed under specified conditions | mol/mol, mol/L, g/L | equilibrium or dynamic | distinguish equilibrium vs rich vs cyclic |
| Absorption rate | CO2 uptake per time/area/volume | mol/(L·s), mol/(m²·s), 1/s | wetted wall, stirred cell, bubble column | apparatus-dependent; do not compare directly |
| Desorption rate | CO2 release per time | mol/(L·s), mol/(m²·s) | desorption apparatus | temperature and loading dependent |
| Regeneration energy | energy per tonne CO2 released | GJ/t CO2, kJ/mol CO2 | pilot/calorimetry/energy balance | includes sensible + latent + reaction; not ΔH_abs alone |
| Cyclic capacity | rich − lean loading | mol/mol, mol/L | cyclic absorption–desorption | define rich/lean basis and cycle conditions |
| Cyclic stability | performance retention over cycles | % retention, % loss/cycle | long-run cycling | report cycle count and conditions |
| Degradation | amine loss or product formation | %, ppm, mg/L | HPLC/IC/NMR/GC | qualitative statements are not numbers |

## Density and concentration conversions

Density is the bridge between volume-based and mass-based concentrations:

```
wt% = c (mol/L) × M (g/mol) / (ρ (g/mL) × 1000) × 100
c (mol/L) = wt% / 100 × ρ (g/mL) × 1000 / M (g/mol)
```

- ρ must be for the **same solution composition and temperature** as the concentration.
- A density reported for a different amine concentration or temperature is not a valid conversion factor.
- If the paper does not report density, do not convert mol/L to wt%; report the original molarity and mark the record out of scope for the recipe table.
- Molality (mol/kg solvent) does not need density; use the exact formula in `formulas/concentration_conversion.md`.

## Loading definitions

| Term | Definition | Typical use |
|---|---|---|
| Equilibrium loading | CO2 content at equilibrium with a gas of known P_CO2 | VLE, thermodynamic data |
| Rich loading | loading of the CO2-rich stream leaving the absorber | process performance |
| Lean loading | loading of the regenerated stream entering the absorber | process performance |
| Cyclic capacity | rich loading − lean loading | working capacity |
| Dynamic capacity | amount absorbed before breakthrough or at a specified time | dynamic/column tests |
| Saturation capacity | maximum loading at given conditions | equilibrium or long-time absorption |

These are not interchangeable. A paper may report several; record each with its own definition.

## Rate definitions

- Volumetric rate: mol CO2 per L solution per s.
- Interfacial rate: mol CO2 per m² per s (flux).
- Overall mass-transfer coefficient: mol/(m²·s·kPa) or similar.
- Pseudo-first-order rate constant: 1/s.
- Second-order rate constant: L/(mol·s).

Do not convert between these without the interfacial area, liquid volume and driving force. A pKa is recorded as `pka`; a rate constant has no matching enum value, so keep it in the report and propose a metric extension rather than forcing it into `pka`.

## Thermal metrics

- **Heat of absorption (ΔH_abs):** enthalpy change per mol CO2 absorbed; can be negative (exothermic). Unit kJ/mol CO2.
- **Regeneration heat:** total energy per tonne CO2 released; unit GJ/t CO2; includes sensible heat, latent heat and reaction enthalpy.
- **Regeneration energy:** sometimes synonymous with regeneration heat; check the definition.
- **Specific reboiler duty:** kJ/kg CO2 or GJ/t CO2; process-specific.

Do not convert ΔH_abs to regeneration heat without a full energy balance.

## Property data quality

- Check temperature, concentration and loading for every property value.
- Check whether the property is for the unloaded or CO2-loaded solution.
- Check whether the value is measured or estimated by a correlation.
- Check units and basis (per mass, per volume, per mole, per amine, per nitrogen site).
- Check replicate/uncertainty; if absent, mark lower confidence.

## Common traps

1. Using water density (≈1.0 g/mL) as the density of a concentrated amine solution.
2. Using a density at 25 °C to convert a concentration at 40 °C.
3. Treating g/L CO2 as mol/mol without density.
4. Comparing volumetric capacity (g/L) with molar loading (mol/mol) directly.
5. Calling a rich loading an equilibrium loading.
6. Calling heat of absorption a regeneration heat.
7. Treating viscosity or surface tension as a capture performance metric.

## References

- Kohl & Nielsen, *Gas Purification*, 5th ed., 1997.
- Rochelle, G. T. "Amine scrubbing for CO2 capture." *Science* 325 (2009): 1652–1654.
- Weiland, R. H., Chakravarti, S., & Mather, A. E. "Solubility of CO2 and H2S in aqueous alkanolamine solutions." GPA Research Report RR-155, 1993.
- Wilcox, J. *Carbon Capture*, Springer, 2012.
- PubChem/NIST for pure-component property lookups (never substitute a lookup value for a paper's measured value).
