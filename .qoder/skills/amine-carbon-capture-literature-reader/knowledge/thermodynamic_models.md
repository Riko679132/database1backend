# Thermodynamic Models

## Purpose

Help the reader recognize common amine–CO2 equilibrium models, understand what they predict, and avoid treating model output as experimental data or extrapolating a model outside its validated range.

## Model map

| Model | Core idea | Typical inputs | Strengths | Limitations |
|---|---|---|---|---|
| Kent–Eisenberg | equilibrium reactions + empirical equilibrium constants; activity coefficients simplified | T, amine concentration, loading or P_CO2, equilibrium constants | simple, widely used for MEA/DEA/MDEA screening | empirical constants; poor for high ionic strength, sterically hindered amines and some blends; not predictive outside fitted range |
| Deshmukh–Mather | equilibrium reactions + Debye–Hückel activity coefficients + interaction parameters | T, composition, P_CO2, interaction parameters | better for concentrated amine solutions; MEA/DEA/MDEA | requires fitted interaction parameters; parameter availability and range matter |
| Electrolyte NRTL (eNRTL) | local composition model for electrolyte activity coefficients | T, composition, binary interaction parameters | strong for MDEA/MEA and mixed solvents; used in process simulators | many parameters; parameter regression and range dependence |
| Pitzer | virial expansion for electrolyte activity coefficients | T, ionic strength, Pitzer parameters | good for electrolyte solutions; relatively compact | parameter-heavy; less common for full amine speciation |
| Other | UNIQUAC/UNIFAC variants, empirical correlations, machine-learning fits | depends | fast screening | validity domain often narrow; not mechanistic |

## Kent–Eisenberg

- Represents the main equilibria (carbamate, bicarbonate, water ionization, amine protonation) with equilibrium constants.
- Usually assumes ideal or simplified activity behaviour; some versions add activity coefficients.
- Common for MEA, DEA and MDEA; often used to fit solubility data.
- Do not apply it to a new amine or a blend without checking that the equilibrium constants/parameters were fitted for that system.
- If a paper reports "modified Kent–Eisenberg", read what was modified; do not assume it is the original model.

## Deshmukh–Mather

- Combines equilibrium reactions with activity coefficients from a Debye–Hückel-type model and fitted interaction parameters.
- Better suited to concentrated aqueous amine solutions than the simplest Kent–Eisenberg form.
- Requires interaction parameters for the specific amine mixture; missing parameters mean the model cannot be applied.
- Do not use parameters fitted at one temperature/composition range to predict another range without validation.

## Electrolyte NRTL

- Chen & Evans local-composition model; Austgen et al. applied it to aqueous acid gas–alkanolamine systems.
- Represents long-range electrostatic interactions and short-range local interactions; requires binary interaction parameters.
- Often implemented in Aspen Plus and other process simulators; the exact parameter set and standard state matter.
- Do not compare eNRTL predictions from different parameter sets as if they were the same model.

## Pitzer

- Virial expansion for excess Gibbs energy of electrolyte solutions; activity coefficients from Pitzer parameters.
- Useful for concentrated electrolytes and mixed-salt systems; parameter-heavy.
- Less commonly the primary model in amine–CO2 papers, but appears in speciation/thermodynamic studies.

## Model outputs and evidence type

- A model-predicted P_CO2 or speciation is **not** an experimental measurement.
- If a paper reports model output, mark it `Derived` (if the inputs and equations are explicit) or `External` (if taken from a cited model), and never label it L1/L2 experimental data.
- If a model is used to fill a missing parameter, record the model name, version/parameters, inputs and assumptions; the result is a derivation, not a paper fact.
- Simulation results are `test_origin="simulation"`, `qc_level="L3"`; they never enter the L1/L2 gold standard.

## Applicability checklist

Before applying a model, confirm:

1. The amine system (single/blend, amine class) is within the model's validated range.
2. The temperature and pressure range are within the fitted range.
3. The concentration range (wt% or molarity) is within the fitted range.
4. The solvent is water (or the model explicitly supports the organic solvent).
5. The model parameters are reported or available from a cited source.
6. The output is compared with experimental data, not treated as ground truth.

If any item is missing, do not apply the model; report the gap.

## References

- Kent, R. L., & Eisenberg, B. "Better data for amine treating." *Hydrocarbon Processing* 55 (1976): 87–90.
- Deshmukh, R. D., & Mather, A. E. "A mathematical model for equilibrium solubility of hydrogen sulfide and carbon dioxide in aqueous alkanolamine solutions." *Chem. Eng. Sci.* 36 (1981): 355–362.
- Chen, C. C., & Evans, L. B. "A local composition model for the excess Gibbs energy of aqueous electrolyte systems." *AIChE J.* 32 (1986): 444–454.
- Austgen, D. M., Rochelle, G. T., Peng, X., & Chen, C. C. "Model of vapor-liquid equilibria for aqueous acid gas-alkanolamine systems using the electrolyte-NRTL equation." *Ind. Eng. Chem. Res.* 28 (1989): 1060–1073.
- Pitzer, K. S. "Thermodynamics of electrolytes. I. Theoretical basis and general equations." *J. Phys. Chem.* 77 (1973): 268–277.
- Weiland, R. H., Chakravarti, S., & Mather, A. E. "Solubility of CO2 and H2S in aqueous alkanolamine solutions." GPA Research Report RR-155, 1993.
