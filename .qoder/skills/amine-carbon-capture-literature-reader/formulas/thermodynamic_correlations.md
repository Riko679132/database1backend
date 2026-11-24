# Thermodynamic Correlations

## Purpose

Provide the small set of relations commonly used to check or derive amine–CO2 data. Use them only when the inputs are explicit and the assumptions are recorded.

## Van't Hoff relation

For a reaction or absorption equilibrium with constant enthalpy over the temperature range:

```
ln(K2/K1) = −ΔH/R × (1/T2 − 1/T1)
```

For CO2 solubility at constant loading:

```
ln(P2/P1) = −ΔH_abs/R × (1/T2 − 1/T1)
```

or

```
ln P = A + B/T
```

with `B = −ΔH_abs/R` under a consistent sign convention.

- Use only when the paper reports the same loading at two or more temperatures.
- Check the sign: absorption is usually exothermic, so ΔH_abs is negative by the thermodynamic convention used in the paper.
- Do not fit a line through points at different loadings.

## Gibbs–Helmholtz relation

```
∂(ΔG/T)/∂T = −ΔH/T²
```

For equilibrium data, the temperature dependence of `ln P_CO2` at constant loading gives the heat of absorption. This is the basis of the common "heat of absorption from VLE" method.

## Henry's law temperature dependence

```
ln(H2/H1) = −ΔH_sol/R × (1/T2 − 1/T1)
```

H is the Henry constant for the physical solubility of CO2 in the solvent; it is not the reactive loading. The units of H must match the concentration basis (mol fraction, mol/L, mol/kg).

## Arrhenius relation

```
k = A × exp(−Ea/(R T))
ln k = ln A − Ea/(R T)
```

For a reaction rate constant or an apparent kinetic constant. Do not apply it to a mass-transfer coefficient without checking the mechanism.

## Equilibrium constants

For an equilibrium reaction:

```
K = exp(−ΔG°/(R T))
ΔG° = ΔH° − T ΔS°
```

If the paper reports `ln K = a/T + b ln T + c`, use the paper's fitted coefficients; do not replace them with generic values.

## CO2 partial pressure from loading

There is no universal `P_CO2 = f(loading)` relation for all amines. Use:

- the paper's measured isotherm;
- a validated thermodynamic model with parameters for the system;
- an empirical correlation fitted to the same amine/temperature/concentration range.

Do not use a correlation for MEA to predict AMP, PZ or MDEA without validation.

## Mixing rules

For a blend, do not average pure-amine isotherms linearly. Blend behaviour depends on speciation, pH, activity coefficients and interactions. Use measured blend data or a model with blend parameters.

## Error propagation (simple cases)

For `P_CO2 = y × P_total`:

```
(δP/P)² = (δy/y)² + (δP_total/P_total)²
```

For `α = n_CO2/n_amine`:

```
(δα/α)² = (δn_CO2/n_CO2)² + (δn_amine/n_amine)²
```

Report the uncertainty only if the paper reports the component uncertainties; otherwise mark it unknown.

## When not to use a correlation

- The temperature, concentration or loading is outside the fitted range.
- The amine system is different from the one used to fit the correlation.
- The solvent is not water (unless the correlation explicitly includes it).
- The paper reports a measured value; the measured value always wins.
- The result would be used to fill a database field that requires an L2 measurement; a correlation-derived value is not an L2 experimental point.

## Executable calculator

For simple partial pressure, loading and cyclic capacity, use `scripts/calc.py`. For model fitting or heat-of-absorption regression, use a dedicated numerical tool (Python/NumPy) and record the model, data points and residuals; do not estimate by hand.
