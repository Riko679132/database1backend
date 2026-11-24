# Amine Properties

## Purpose

Use this file to identify the amine in a paper, check its class and typical reaction behaviour, and avoid confusing similar abbreviations. This file is **not** a source of paper data. Never copy a property from here into a record unless the paper reports it or a derivation is explicitly allowed.

## Current project whitelist

The extraction whitelist is `data/compound_whitelist.csv`. The four in-scope compounds are:

| Abbrev. | Standard name | CAS | Formula | MW (g/mol) | Class | SMILES | InChIKey |
|---|---|---|---|---|---|---|---|
| MEA | monoethanolamine; 2-aminoethanol | 141-43-5 | C2H7NO | 61.08 | primary alkanolamine | NCCO | HZAXFHJVJLSVMW-UHFFFAOYSA-N |
| PZ | piperazine | 110-85-0 | C4H10N2 | 86.14 | cyclic secondary diamine | C1CNCCN1 | GLUUGHFVERTEDX-UHFFFAOYSA-N |
| AMP | 2-amino-2-methyl-1-propanol | 124-68-5 | C4H11NO | 89.14 | sterically hindered primary alkanolamine | CC(C)(CO)N | CBTVGIZVANXIJB-UHFFFAOYSA-N |
| MDEA | N-methyldiethanolamine | 105-59-9 | C5H13NO2 | 119.16 | tertiary alkanolamine | CN(CCO)CCO | CRVGTESFCCXCTH-UHFFFAOYSA-N |

The SMILES/InChIKey above match the project whitelist. If the paper uses a different name, resolve it by CAS or by the full chemical name; never infer identity from an abbreviation alone.

## Other amines commonly seen in the literature

These are useful for reading and comparison, but are **outside the current extraction whitelist**. Do not emit in-scope records for them unless the whitelist is explicitly expanded.

| Abbrev. | Standard name | CAS | Formula | MW (g/mol) | Class | Notes |
|---|---|---|---|---|---|---|
| DEA | diethanolamine; 2,2'-iminodiethanol | 111-42-2 | C4H11NO2 | 105.14 | secondary alkanolamine | carbamate former; often a baseline |
| TEA | triethanolamine | 102-71-6 | C6H15NO3 | 149.19 | tertiary alkanolamine | bicarbonate route; slow kinetics |
| DGA | diglycolamine; 2-(2-aminoethoxy)ethanol | 929-06-6 | C4H11NO2 | 105.14 | primary ether amine | carbamate former; lower vapour pressure |
| DETA | diethylenetriamine | 111-40-0 | C4H13N3 | 103.17 | polyamine | multiple amine sites; often blended |
| TETA | triethylenetetramine | 112-24-3 | C6H18N4 | 146.23 | polyamine | multiple amine sites; often blended |

Amino-alcohol isomers such as 2-AP, 1-AP and MAE appear in some papers with ambiguous abbreviations. Resolve their CAS and structure from the paper/PubChem before using them; do not assume that "2-AP" means the same compound in two papers.

For any compound not in the whitelist, resolve CAS/SMILES/InChIKey from PubChem or the paper's own SI before using it in a report. If it cannot be resolved, report the name and CAS only; do not hand-type a structure.

## Identity traps

1. **MDEA vs DMAE.** MDEA is `N-methyldiethanolamine` (two hydroxyethyl groups + N-methyl). DMAE is `2-(dimethylamino)ethanol` (one hydroxyethyl group). A past project error wrote MDEA as `CN(C)CCO`; the correct SMILES is `CN(CCO)CCO`.
2. **AMP vs 2-AP/1-AP.** AMP is 2-amino-2-methyl-1-propanol (`CC(C)(CO)N`). 2-AP and 1-AP are different isomers with the same formula C3H9NO. Do not map them to AMP.
3. **PZ vs piperazine derivatives.** PZ is unsubstituted piperazine. 1-methylpiperazine, 2-methylpiperazine, AEP, HEP, and PIP derivatives are different compounds.
4. **MEA vs MAE.** MEA is monoethanolamine (primary); MAE is 2-(methylamino)ethanol (secondary). Similar abbreviations, different structures.
5. **DEA vs DGA.** DEA is diethanolamine; DGA is diglycolamine (2-(2-aminoethoxy)ethanol). Both are C4H11NO2 but different connectivity.
6. **TEA vs TETA.** TEA is triethanolamine; TETA is triethylenetetramine. Different class and reactivity.
7. **"Amine" without a name.** If the paper says "a proprietary amine" or gives only a trade name and no CAS/structure, do not guess; mark the identity Unknown and do not emit a whitelist record.

## Reaction behaviour (summary)

| Amine type | Main CO2 route | Typical loading limit | Key caveat |
|---|---|---|---|
| Primary (MEA, AMP, DGA) | carbamate; hindered amines also bicarbonate | ~0.5 mol CO2/mol amine for pure carbamate; up to ~1.0 if bicarbonate contributes | carbamate stability and steric hindrance change the split; do not assume 0.5 or 1.0 without data |
| Secondary (DEA, PZ, MAE) | carbamate; PZ is a fast cyclic diamine | ~0.5 per amine site for carbamate | PZ has two secondary sites; speciation and loading basis must be stated |
| Tertiary (MDEA, TEA) | bicarbonate/carbonate via base catalysis | up to ~1.0 mol CO2/mol amine | no direct carbamate; slower kinetics; often used as a blend component |
| Polyamines (DETA, TETA) | mixed carbamate/bicarbonate at multiple sites | depends on degree of protonation | not in whitelist; do not treat as monoamine |

These are qualitative expectations. The actual product distribution depends on temperature, pressure, concentration, solvent, loading and pH. Use speciation data (NMR, FTIR, titration) or a validated model when the paper reports it; otherwise do not invent species fractions.

## Typical uses in papers

- **MEA:** benchmark solvent, 30 wt% aqueous, flue-gas CO2 capture, carbamate chemistry; often the reference against which blends are compared.
- **PZ:** rate promoter and blend component; high absorption rate; limited aqueous solubility; carbamate chemistry.
- **AMP:** sterically hindered primary amine; lower regeneration energy; bicarbonate-rich; often blended with PZ or MEA.
- **MDEA:** tertiary amine; low heat of absorption; slow kinetics; often blended with a primary/secondary amine.
- **DEA:** secondary baseline; carbamate; older capture processes.
- **DGA:** primary ether amine; carbamate; used in gas treating.
- **TEA:** tertiary; bicarbonate; rarely the main solvent in modern capture papers.

## Physical-property cautions

- Density and viscosity depend strongly on amine concentration and temperature. A value at 2 M and 40 °C is not the density of a 30 wt% blend at 313 K.
- Do not use a handbook density for a different concentration/temperature to convert a paper's mol/L to wt%. Only use a density explicitly reported for the same solution and temperature, or a validated correlation with its source and uncertainty.
- Molecular weight is a constant; it can be used in exact molality conversions.
- Boiling point, vapour pressure and degradation temperature are not needed for routine extraction unless the paper studies them.

## References

- PubChem entries for the CAS numbers above (identity, formula, MW, structure).
- Kohl, A. L., & Nielsen, R. B. *Gas Purification*, 5th ed., Gulf Publishing, 1997.
- Rochelle, G. T. "Amine scrubbing for CO2 capture." *Science* 325 (2009): 1652–1654.
- Wilcox, J. *Carbon Capture*, Springer, 2012.
- Project whitelist: `data/compound_whitelist.csv`.
