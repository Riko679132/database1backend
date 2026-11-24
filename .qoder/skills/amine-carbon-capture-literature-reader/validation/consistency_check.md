# Consistency Checks

## Goal

Find contradictions before they enter the database. A value can be individually plausible but inconsistent with another part of the same paper.

## Checks to run

### 1. Table vs text

- Does the abstract's headline value match the table?
- Does the results text quote the same number as the table?
- Does the table caption's condition match the text?
- If they differ, keep both and report the conflict; do not pick one silently.

### 2. Table vs figure

- Does the figure trend match the table trend?
- Is a table labelled "experimental" also plotted as symbols, or is it a model curve?
- Does the figure caption give a different temperature/composition?

### 3. Units and bases

- Are all rows in a table on the same basis (wt%/mol%, dry/wet, total/partial)?
- Does a footnote change the basis for some rows?
- Are the same quantities reported in different units in different sections?

### 4. Temperature and pressure

- Are temperatures consistently K or °C?
- Is the pressure total or partial? Is it absolute or gauge?
- Does `P_CO2 + P_H2O(T) ≤ P_total` hold?
- Does a VLE point at a given T use the correct P_CO2?

### 5. Loading and capacity

- Is the loading per total amine, per component, or per site?
- Is a "rich" loading actually an equilibrium loading?
- Is a "cyclic capacity" computed as rich − lean, or measured directly?
- Does a loading exceed the stoichiometric limit without explanation?

### 6. Mass and charge balance

- Recipe components sum to 100 ± 0.1 wt%.
- Gas-side and liquid-side CO2 balances agree within uncertainty.
- Charge balance (cations/anions) in speciation data is plausible.
- Species fractions sum to 1 (or 100%).

### 7. Replicates and uncertainty

- Are replicate values averaged? Is n reported?
- Is the uncertainty standard deviation, standard error, or a confidence interval?
- Does the table report an error that the text ignores?

### 8. Method consistency

- Is the data from an equilibrium method or a dynamic method?
- Is a rate compared with a capacity?
- Is a pilot capture efficiency compared with a lab VLE point?
- Is a model output presented as experimental data?

### 9. Cross-paper consistency (optional)

- If the paper compares its MEA baseline with literature, does the baseline match known values within the stated conditions?
- Do not use external data to override the paper; use it to flag suspicious values.

## Conflict handling

When a conflict is found:

1. Keep the original values and locations.
2. Add a conflict note to the extraction report.
3. If the conflict affects a field that must be unique, choose the value with the clearest definition and mark the other as a conflict; do not average.
4. If the conflict cannot be resolved, set the field to null and report.
5. Do not silently "correct" the paper.

## Red flags

- A table value that appears in no text/figure and has no caption condition.
- A "loading" that changes by a factor of 10 between sections.
- A "wt%" that is actually mol%.
- A pressure that is lower than the CO2 partial pressure.
- A regeneration energy lower than the heat of absorption.
- A capture efficiency of 100% at unrealistic conditions.
- A VLE point that is identical across temperatures.

## Reporting

In `extraction_report.md`, include:

```
Conflict: <field>
Location A: <table/page> value <...>
Location B: <text/figure/page> value <...>
Resolution: kept A / kept B / null
Reason: ...
```
