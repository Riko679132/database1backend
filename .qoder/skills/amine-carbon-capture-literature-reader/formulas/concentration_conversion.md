# Concentration Conversions

## Symbols

| Symbol | Meaning | Unit |
|---|---|---|
| `w_i` | mass fraction of component i | – (0–1) |
| `wt_i` | mass percentage of component i | % |
| `x_i` | mole fraction of component i | – (0–1) |
| `m_i` | molality | mol/kg solvent |
| `c_i` | molarity | mol/L solution |
| `M_i` | molar mass | g/mol |
| `ρ` | solution density | g/mL (= kg/L) |

## Mass fraction ↔ mole fraction

For a mixture of components i:

```
x_i = (w_i / M_i) / Σ_j (w_j / M_j)
w_i = (x_i × M_i) / Σ_j (x_j × M_j)
```

For an aqueous single amine:

```
x_amine = (wt_amine / 100 / M_amine) /
          (wt_amine / 100 / M_amine + wt_water / 100 / M_water)
```

Example: 30 wt% MEA, 70 wt% water, M_MEA = 61.08, M_water = 18.015.

```
n_MEA = 0.30 / 61.08 = 0.004912 mol per g solution
n_water = 0.70 / 18.015 = 0.03886 mol per g solution
x_MEA = 0.004912 / (0.004912 + 0.03886) = 0.1123
```

## Molality → wt% (exact, no density needed)

```
wt_amine (%) = m × M_amine / (m × M_amine + 1000) × 100
```

where `m` is mol amine per kg solvent (water). For a single amine this is exact. For a blend, replace `m × M_amine` with the sum over amines:

```
wt_total_amine (%) = Σ_i (m_i × M_i) / (Σ_i (m_i × M_i) + 1000) × 100
```

Example: m = 7.017 mol/kg, M_MEA = 61.08.

```
wt% = 7.017 × 61.08 / (7.017 × 61.08 + 1000) × 100 = 30.0%
```

## Molarity → wt% (requires density)

```
mass of amine per L = c × M          (g/L)
mass of 1 L solution = ρ × 1000      (g/L)
wt_amine (%) = c × M / (ρ × 1000) × 100
```

For a blend, compute each amine separately and sum for total amine.

**Do not use ρ = 1.0 g/mL for a concentrated amine solution unless the paper reports that density.** A density for a different composition or temperature is also invalid.

Example: c = 4.90 mol/L MEA, M = 61.08, ρ = 1.00 g/mL (explicitly assumed for this example only).

```
wt% = 4.90 × 61.08 / (1.00 × 1000) × 100 = 29.9%
```

If the paper does not report density, stop: report molarity and mark the record as not convertible to recipe wt%.

## wt% → molarity (requires density)

```
c = (wt_amine / 100) × ρ × 1000 / M
```

Example: 30 wt% MEA, ρ = 1.00 g/mL.

```
c = 0.30 × 1.00 × 1000 / 61.08 = 4.91 mol/L
```

## Mass ratio / molar ratio → wt%

Mass ratio `A:B = r_A:r_B` (by mass):

```
wt_A = r_A / (r_A + r_B + r_water) × 100
```

Molar ratio `n_A:n_B`:

```
mass_A = n_A × M_A
mass_B = n_B × M_B
wt_A = mass_A / (mass_A + mass_B + mass_water) × 100
```

You need the water amount or total amine concentration to close the recipe.

## Gas composition

For an ideal gas:

```
y_i = vol% / 100
P_i = y_i × P_total
```

- If the gas analysis is on a dry basis, convert to wet basis using the water vapour partial pressure before combining with total pressure.
- If the paper gives only vol% and no total pressure, `co2_vol_pct` can be recorded, but `co2_partial_kPa` cannot.

## Common traps

1. Treating wt% as mol% or vice versa.
2. Using the density of water for a 30 wt% amine solution.
3. Using a density at 25 °C for data at 40 °C.
4. Forgetting that "balance" may be water or another solvent.
5. Converting mol/L to wt% when no density is reported.
6. Using the total amine wt% as if it were the concentration of one component in a blend.
7. Confusing molality (mol/kg solvent) with molarity (mol/L solution).

## Executable calculator

Use `scripts/calc.py` for these conversions; do not rely on mental arithmetic for records.

```powershell
python .qoder\skills\amine-carbon-capture-literature-reader\scripts\calc.py wt-to-mol-fraction --wt 30 --mw 61.08 --water-wt 70
python .qoder\skills\amine-carbon-capture-literature-reader\scripts\calc.py molality-to-wt --molality 7.017 --mw 61.08
python .qoder\skills\amine-carbon-capture-literature-reader\scripts\calc.py molarity-to-wt --molarity 4.90 --mw 61.08 --density 1.00
```
