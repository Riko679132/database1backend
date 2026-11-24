# Mixed Amine Systems

## Purpose

Help the reader interpret single-amine and blended-amine formulations, identify the ratio basis, and avoid comparing concentrations or ratios that are defined differently.

## System definitions

| System | Definition | Current project boundary |
|---|---|---|
| Single amine (mono) | One amine + water; no other amine | in scope, aqueous, total amine 20–50 wt% |
| Binary blend | Two amines + water | in scope, aqueous, total amine 20–50 wt% |
| Ternary/multicomponent blend | Three or more amines | out of the current boundary; report, do not emit |
| Amine + inorganic salt | e.g. amine + K2CO3, amine + salt additive | out of scope (salt_flag=1) |
| Amine + organic solvent | e.g. amine + methanol, sulfolane, glycol ether | out of scope (non-aqueous/water-lean) |
| Phase-change / biphasic | A CO2-rich phase separates | out of scope (phase_flag=1) |
| Slurry / solid sorbent / membrane / IL / DES | Different capture media | out of scope |

The current database only accepts `recipe_type='mono'` or `'binary'`. A paper with a ternary blend can be read for knowledge, but its records must not be emitted as in-scope data.

## Ratio and concentration notations

Papers use at least six different notations. They are not interchangeable:

1. **Mass fraction / wt%** — grams of component per 100 g of solution. The database recipe requires this.
2. **Mole fraction / mol%** — moles of component per 100 mol of all species (including water unless stated).
3. **Mass ratio** — e.g. "MEA:PZ = 7:3 by mass"; convert to wt% only if the total mass or the third component is known.
4. **Molar ratio** — e.g. "MEA:PZ = 7:3 by mole"; requires molecular weights to convert to mass.
5. **Mass concentration** — g/L or kg/m³ of solution; requires density to convert to wt%.
6. **Molar concentration** — mol/L or mol/dm³ of solution; requires density to convert to wt%; molality (mol/kg solvent) is different and can be converted exactly without density.

**Never compare a wt% blend with a mol% blend directly.** Normalize both to the same basis first, and state the basis in the record.

## Worked conversion rules

### Binary blend from wt%

```
total_amine_wt = wt_A + wt_B
water_wt = 100 − total_amine_wt
```

The recipe must close to 100 ± 0.1 wt%. If the paper reports "30 wt% MEA + 5 wt% PZ", the total amine is 35 wt% and water is 65 wt%, not 70 wt%.

### Binary blend from molarity

You need the solution density for the same composition and temperature:

```
mass of A per L = c_A × M_A
mass of B per L = c_B × M_B
wt_A = c_A × M_A / (ρ × 1000) × 100
wt_B = c_B × M_B / (ρ × 1000) × 100
```

If the paper does not give the density of the actual blend, **do not compute wt%**; report the molarity and mark the record out of scope for the current recipe table.

### Binary blend from molar ratio

```
mass_A = n_A × M_A
mass_B = n_B × M_B
wt_A = mass_A / (mass_A + mass_B + mass_water) × 100
```

You need the water amount (or total amine concentration) to close the recipe.

### Amine site basis

PZ has two nitrogen sites; polyamines have multiple sites. A loading of "0.5 mol CO2/mol amine" for PZ is not the same as "0.5 mol CO2/mol nitrogen site". Record the basis explicitly in `metric_definition`.

## Roles of components in blends

| Component | Typical role | What to check in the paper |
|---|---|---|
| Primary amine (MEA, AMP) | fast carbamate; AMP also promotes bicarbonate | concentration, steric hindrance, carbamate vs bicarbonate evidence |
| Secondary amine (PZ, DEA) | fast carbamate; PZ often a rate promoter | PZ solubility limit, PZ/amine ratio, carbamate speciation |
| Tertiary amine (MDEA, TEA) | low heat, bicarbonate, slow kinetics | blend partner, MDEA concentration, rate vs capacity trade-off |
| Water | reactant, solvent, heat sink | water wt% from mass balance; do not treat "balance" as unknown if all components are given |
| Organic solvent | changes solubility, lowers regeneration energy | non-aqueous/water-lean → out of scope |
| Additive/salt/catalyst | alters kinetics, degradation or corrosion | additive_flag/salt_flag → out of scope |

## Effects to expect (qualitative)

- Increasing total amine concentration usually increases capacity per volume but can increase viscosity and reduce mass transfer.
- Adding a small amount of PZ often increases absorption rate, but the effect depends on concentration, ratio and apparatus.
- Tertiary amines reduce heat of absorption but may slow kinetics; they are often blended with a fast primary/secondary amine.
- Sterically hindered amines such as AMP can reduce regeneration energy but may have lower equilibrium capacity at low P_CO2.
- Organic solvents can change the equilibrium and speciation; do not apply aqueous correlations to non-aqueous systems.

These are expectations, not data. The paper's measured values always take precedence.

## Reading checklist for a blend paper

1. What is the exact composition of each component? Are all components named?
2. What is the basis: wt%, mol%, mass ratio, molar ratio, g/L, mol/L, or mol/kg?
3. Is the "balance" water, or another solvent? Is the total amine 20–50 wt%?
4. Are there additives, salts, phase-change behaviour or solid materials?
5. Are the reported concentrations nominal (prepared) or measured (titration/density)?
6. Does the paper report density for the actual blend? If not, do not convert mol/L to wt%.
7. Does the paper report loading per total amine, per specific amine, or per nitrogen site?
8. Are blend ratios varied independently, or confounded with total concentration?

## Common traps

- "30 wt% MEA/PZ" may mean 30 wt% total amine with a certain MEA:PZ ratio, or 30 wt% MEA plus an unspecified amount of PZ. Check the methods.
- "1 M MEA + 1 M PZ" is not 50/50 wt%; PZ and MEA have different molecular weights.
- "MEA:PZ = 7:3" without "by mass" or "by mole" is ambiguous; do not guess.
- A ternary blend with a small third component is still ternary; do not collapse it to a binary recipe.
- A phase-change solvent may report a single-phase loading; the phase behaviour still puts it outside the current boundary.

## References

- Kohl & Nielsen, *Gas Purification*, 5th ed., 1997.
- Rochelle, G. T. "Amine scrubbing for CO2 capture." *Science* 325 (2009): 1652–1654.
- Dang, H., & Rochelle, G. T. "CO2 absorption rate and solubility in monoethanolamine/piperazine/water." *Sep. Sci. Technol.* 38 (2003): 337–357.
- Bishnoi, S., & Rochelle, G. T. "Absorption of carbon dioxide into aqueous piperazine." *Chem. Eng. Sci.* 55 (2000): 5531–5543.
