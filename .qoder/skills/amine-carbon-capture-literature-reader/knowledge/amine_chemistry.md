# Amine–CO2 Chemistry

## Purpose

Explain the reaction pathways that control loading, speciation, kinetics and regeneration. Use this file to judge whether a paper's reported values are chemically plausible and to avoid assigning a mechanism that the paper did not measure.

## Core reactions

### Carbamate route (primary and secondary amines)

```
2 RNH2 + CO2 ⇌ RNHCOO⁻ + RNH3⁺
```

or, written through the zwitterion:

```
RNH2 + CO2 ⇌ RNH2⁺COO⁻
RNH2⁺COO⁻ + RNH2 ⇌ RNHCOO⁻ + RNH3⁺
```

- Maximum carbamate stoichiometry is **0.5 mol CO2 per mol amine** if every amine forms carbamate.
- The carbamate is stable for many primary/secondary amines, but its stability decreases with steric hindrance.
- The reaction is fast relative to bicarbonate formation for MEA, PZ and DEA.

### Bicarbonate route (tertiary and sterically hindered amines)

```
CO2 + H2O ⇌ H2CO3 ⇌ H⁺ + HCO3⁻
R3N + H2O + CO2 ⇌ R3NH⁺ + HCO3⁻   (tertiary amine as base)
```

- Tertiary amines (MDEA, TEA) cannot form carbamate; they act as proton acceptors and promote bicarbonate/carbonate formation.
- Sterically hindered primary amines such as AMP form carbamate poorly; bicarbonate becomes more important.
- The theoretical maximum approaches **1.0 mol CO2 per mol amine** when bicarbonate/carbonate dominates, but actual loading depends on pH, temperature, pressure and amine concentration.

### Carbonate and water equilibria

```
CO2 + H2O ⇌ H2CO3
H2CO3 ⇌ H⁺ + HCO3⁻
HCO3⁻ ⇌ H⁺ + CO3²⁻
2 H2O ⇌ H3O⁺ + OH⁻
```

These equilibria matter at high pH, high loading and high temperature. Do not calculate species concentrations from a single reaction equation without a speciation model or measured data.

## Speciation and loading

- **MEA:** carbamate and protonated MEA dominate at low-to-moderate loading; bicarbonate grows at higher loading and higher temperature.
- **PZ:** carbamate forms at each secondary nitrogen; PZ carbamate and protonated PZ are important; PZ can also participate in proton transfer with other amines.
- **AMP:** steric hindrance reduces carbamate stability; bicarbonate and protonated AMP are relatively more important.
- **MDEA:** essentially no carbamate; protonated MDEA and bicarbonate/carbonate dominate.
- **Blends:** a fast carbamate-forming amine can donate a proton to a tertiary/hindered amine, shifting the equilibrium and changing the apparent capacity. This is a chemical explanation, not proof that a specific blend will show a specific loading.

### Rule

**Never infer species fractions from the amine class alone.** If the paper does not report speciation (NMR, FTIR, titration, speciation model), report the loading and conditions only; do not add a species distribution.

## Temperature, pressure, solvent and loading effects

| Variable | Typical effect | Extraction caution |
|---|---|---|
| Temperature ↑ | equilibrium CO2 solubility ↓; kinetics ↑; carbamate stability ↓ | do not mix isotherms measured at different temperatures |
| CO2 partial pressure ↑ | equilibrium loading ↑ | distinguish partial pressure from total pressure |
| Amine concentration ↑ | more amine sites, but viscosity and non-ideality change | wt% and molarity are not interchangeable |
| Water content ↓ / organic solvent | changes solubility and reaction path | non-aqueous or water-lean systems are outside the current boundary |
| Loading ↑ | free amine ↓; pH and speciation change | do not assume a linear loading–capacity relation |
| Steric hindrance ↑ | carbamate stability ↓; bicarbonate route more important | AMP is not "MEA with a methyl group" in behaviour |

## Kinetics versus equilibrium

- **Equilibrium loading** is the solubility at a given T and P_CO2 after sufficient time. It is a thermodynamic quantity.
- **Absorption rate** is a flux or rate (mol m⁻² s⁻¹, mol L⁻¹ s⁻¹, etc.); it depends on kinetics, mass transfer, interfacial area and apparatus.
- **Cyclic capacity** is the difference between rich and lean loading in a absorption–desorption cycle; it is not the same as equilibrium capacity.
- **Heat of absorption** is an enthalpy change; it is not the same as regeneration heat (which includes sensible and latent heat).

Do not compare a rate from a wetted-wall column with a rate from a stirred cell without accounting for mass-transfer area and hydrodynamics.

## Degradation and side reactions

- **Oxidative degradation:** MEA and other amines can degrade in the presence of O2, especially at high temperature and with metal ions; products include organic acids, ammonia, aldehydes and heat-stable salts.
- **Thermal degradation:** carbamates can dehydrate or rearrange at high temperature; PZ and MEA have different degradation pathways.
- **Additives and inhibitors:** corrosion inhibitors, antioxidants, catalysts and salts change the system; the current boundary excludes additives and salts, so such papers are out of scope unless they also report a clean aqueous baseline.

Degradation data are only extracted if the paper reports a discrete, quantified metric (e.g. amine loss %, degradation product concentration). Do not convert a qualitative statement into a number.

## Common chemistry traps in papers

1. **Loading basis.** `mol CO2/mol amine` may mean per total amine, per active amine, or per amine site. For blends, check the definition; PZ has two nitrogen sites, so "per amine" and "per nitrogen" differ.
2. **Carbamate stoichiometry.** A loading above 0.5 does not prove bicarbonate; it may reflect a blend, a different amine basis, or a measurement artefact.
3. **Tertiary amine carbamate.** If a paper claims MDEA carbamate, check the evidence; MDEA is generally unable to form a stable carbamate.
4. **Steric hindrance.** "Hindered amine" is a structural description, not a guarantee that carbamate is absent.
5. **Blend promotion.** A rate increase may come from higher pH, higher amine concentration, a shuttle mechanism or better mass transfer; do not attribute it to a single mechanism without evidence.

## References

- Rochelle, G. T. "Amine scrubbing for CO2 capture." *Science* 325 (2009): 1652–1654.
- Kohl & Nielsen, *Gas Purification*, 5th ed., 1997.
- Austgen, D. M., Rochelle, G. T., Peng, X., & Chen, C. C. "Model of vapor-liquid equilibria for aqueous acid gas-alkanolamine systems using the electrolyte-NRTL equation." *Ind. Eng. Chem. Res.* 28 (1989): 1060–1073.
- Bishnoi, S., & Rochelle, G. T. "Absorption of carbon dioxide into aqueous piperazine: reaction kinetics, mass transfer and solubility." *Chem. Eng. Sci.* 55 (2000): 5531–5543.
- Dang, H., & Rochelle, G. T. "CO2 absorption rate and solubility in monoethanolamine/piperazine/water." *Sep. Sci. Technol.* 38 (2003): 337–357.
