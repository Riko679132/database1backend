# Mass Balance

## Recipe closure

For a monoamine:

```
wt_amine + wt_water = 100
```

For a binary blend:

```
wt_A + wt_B + wt_water = 100
```

The project accepts a tolerance of ±0.1 wt%. If the paper reports component masses rather than percentages, convert to wt% using the total solution mass:

```
wt_i = m_i / m_total × 100
```

If the paper reports "balance water", compute water as `100 − wt_A − wt_B` and flag it as derived.

## Total amine

```
total_amine_wt = wt_A + wt_B
```

Do not use the concentration of one amine as the total amine concentration in a blend.

## Dilution and mixing

When a stock solution is diluted:

```
m_stock × wt_stock = m_final × wt_final
```

This is exact for mass-based dilution. For volume-based dilution, density is required.

When two solutions are mixed:

```
m_total = m_1 + m_2
wt_i = (m_1 × wt_i,1 + m_2 × wt_i,2) / m_total
```

Do not add volumes unless the densities are known and the volumes are additive (they often are not).

## Absorber CO2 balance

For a steady absorber:

```
n_CO2,in − n_CO2,out = n_CO2,absorbed
```

With gas flow `Q`, CO2 mole fraction `y`, and molar volume `V_m`:

```
n_dot,CO2 = y × Q / V_m
```

For the liquid:

```
n_CO2,absorbed = n_amine × (α_out − α_in)
```

where `n_amine` is the molar flow of amine (total amine for a blend, with the basis stated).

Combining:

```
α_out − α_in = (n_CO2,in − n_CO2,out) / n_amine
```

This is the basis for cyclic capacity; it requires consistent gas and liquid flow measurements.

## Desorber balance

```
n_CO2,desorbed = n_amine × (α_rich − α_lean)
```

Regeneration energy per tonne CO2:

```
E_specific = Q_reboiler / m_CO2,desorbed
```

Report the unit (GJ/t CO2, kJ/mol CO2) and whether it includes sensible/latent heat.

## Uncertainty and closure checks

- Sum of component wt% should be 100 ± 0.1; larger deviations need an explanation (e.g. unreported additive, water of crystallization, balance gas).
- Gas-side and liquid-side CO2 balances should agree within the reported uncertainty; a large discrepancy suggests a measurement or basis error.
- Check whether gas flow is dry or wet, and whether the CO2 concentration is on the same basis.
- Check whether the amine flow is total amine or one component.

## Common traps

1. Using total solution mass as amine mass.
2. Adding volumes without density.
3. Treating "balance" as water when the paper used another solvent.
4. Mixing dry-basis gas flow with wet-basis concentration.
5. Using one amine's molar flow for a blend's total amine balance.
6. Forgetting that some CO2 is physically dissolved (especially at high pressure).
7. Reporting a cyclic capacity without stating rich/lean conditions.

## Executable calculator

```powershell
python .qoder\skills\amine-carbon-capture-literature-reader\scripts\calc.py recipe-check --wt-a 30 --wt-b 5 --water 65
```
