# Experimental Methods

## Purpose

Distinguish what each common apparatus actually measures. Many extraction errors come from calling a rate a capacity, a rich loading an equilibrium loading, or a pilot result a VLE point.

## Method map

| Method | What is measured | Typical output | Not the same as |
|---|---|---|---|
| Static equilibrium cell (synthetic/analytical) | equilibrium P_CO2 vs loading at fixed T | VLE isotherm | dynamic capacity; rate |
| Headspace GC equilibrium | equilibrium gas composition and P_CO2 | VLE point | total pressure; feed composition |
| Titration/chemical analysis | liquid CO2 content after equilibration | loading | gas-phase measurement |
| Bubble column | absorption rate / approach to equilibrium | rate, mass transfer | equilibrium loading |
| Wetted-wall column | absorption flux and kinetics | rate, k_L, reaction rate | equilibrium capacity |
| Stirred cell | absorption rate with controlled interface | rate, mass transfer | cyclic capacity |
| Packed column / pilot | capture efficiency, rich/lean loading, pressure drop | process performance | equilibrium VLE |
| Continuous absorption–desorption cycle | cyclic capacity, regeneration energy, stability | cyclic metrics | single-point equilibrium |
| Calorimetry | heat of absorption/desorption | ΔH (kJ/mol CO2) | regeneration heat (includes sensible/latent) |
| NMR/FTIR/titration speciation | species concentrations | speciation | total loading alone |

## Static equilibrium methods

- A known liquid volume is contacted with CO2 (pure or mixed) at controlled temperature.
- The system is allowed to reach equilibrium (hours; check the paper's criterion).
- Loading is obtained from pressure change, gas chromatography, or liquid titration.
- The result is a point on an isotherm: `(T, P_CO2, α)`.
- Check whether the reported pressure is total or partial; check whether the gas is pure CO2 or a mixture.
- Replicates and equilibrium time are quality indicators.

## Dynamic/kinetic methods

- Bubble column, wetted wall, stirred cell, stopped-flow, laminar jet.
- The measured quantity is a rate or mass-transfer coefficient, not an equilibrium loading.
- Rate depends on interfacial area, hydrodynamics, concentration, temperature and loading.
- Do not compare rates from different apparatus without normalizing for area and driving force.
- If the paper reports "initial absorption rate", record it as `initial_absorption_rate` with the original unit; do not convert it to a capacity.

## Continuous/pilot methods

- Packed absorber/desorber, pilot plant, rotating packed bed.
- Reported metrics: capture efficiency (%), rich/lean loading, cyclic capacity, regeneration energy, pressure drop, stability over cycles.
- The rich loading may be kinetically limited and not equilibrium; do not label it `equilibrium_loading`.
- Capture efficiency depends on gas flow, liquid flow, packing, height and temperature; it is not a solvent-only property.
- Pilot data are valuable but often not directly comparable across scales.

## Calorimetry and heat

- Heat of absorption (ΔH_abs) is measured calorimetrically or derived from VLE via Gibbs–Helmholtz/van't Hoff.
- Regeneration heat (GJ/t CO2) includes reaction enthalpy, sensible heat and vaporization; it is not the same as ΔH_abs.
- If the paper reports only one of these, do not convert it to the other without a full energy balance.

## Method-to-field mapping

| Reported quantity | Likely field | Caution |
|---|---|---|
| equilibrium loading vs P_CO2 | `equilibrium_loading`; test T/P_CO2/initial_loading | one test per point |
| initial absorption rate | `initial_absorption_rate` | unit may be mol/L/s, mol/m²/s, etc. |
| cyclic capacity | `cyclic_capacity` | define rich − lean and basis |
| regeneration energy | `regeneration_energy` | unit GJ/t CO2 or kJ/mol CO2 |
| regeneration heat | `regeneration_heat` | distinguish from ΔH_abs |
| capture efficiency | `co2_removal_efficiency` | process-specific, not solvent-only |
| heat of absorption | `regeneration_heat` only if the paper explicitly defines it as regeneration heat; otherwise keep in report and propose a metric | do not mislabel ΔH_abs |

## Quality indicators

- Temperature control (±0.1 K is common for VLE; ±1 K may be acceptable for pilot).
- Pressure measurement accuracy and calibration.
- Gas composition analysis (GC/TCD, NDIR) and calibration standards.
- Liquid loading analysis method (titration, BaCl2, GC, NMR).
- Equilibrium time and replicate count.
- Mass balance closure (gas in/out, liquid CO2 content).
- Whether the solution was prepared by mass or volume; whether density was measured.

If these are not reported, mark the evidence quality lower; do not invent uncertainty.

## Common traps

1. Calling a rich loading "equilibrium loading" when the absorber did not reach equilibrium.
2. Comparing a pilot capture efficiency with a lab VLE loading.
3. Treating a rate measured in a stirred cell as an intrinsic kinetic constant.
4. Using feed gas composition as equilibrium gas composition.
5. Confusing heat of absorption with regeneration heat.
6. Ignoring the method when comparing solvents; apparatus effects can exceed solvent differences.

## References

- Kohl & Nielsen, *Gas Purification*, 5th ed., 1997.
- Rochelle, G. T. "Amine scrubbing for CO2 capture." *Science* 325 (2009): 1652–1654.
- Jou, F.-Y., Mather, A. E., & Otto, F. D. "The solubility of CO2 in a 30 mass percent monoethanolamine solution." *Can. J. Chem. Eng.* 73 (1995): 140–147.
- Bishnoi, S., & Rochelle, G. T. "Absorption of carbon dioxide into aqueous piperazine." *Chem. Eng. Sci.* 55 (2000): 5531–5543.
- Wilcox, J. *Carbon Capture*, Springer, 2012.
