# Evidence Classification

## Why classify

The database must distinguish a paper's measurement from a calculation, an external lookup and a professional guess. A value that looks the same in a table can have very different reliability.

## Categories

| Type | Definition | Allowed in L1/L2? | Required record |
|---|---|---|---|
| **Explicit** | The paper states the value and its conditions. | Yes, if conditions are complete. | Location + verbatim excerpt |
| **Contextual** | The paper does not state it in one place, but the paper's own text unambiguously determines it. | Yes, only if the determination is truly unambiguous. | Location of the determining text + reasoning |
| **Derived** | Calculated from explicit inputs with a stated formula. | Yes, if inputs are L1/L2 and the derivation is recorded. | Formula, inputs, units, assumptions |
| **External** | Taken from a cited reliable source (handbook, database, another paper). | Usually no for L1/L2; use only to fill non-critical context or with a clear flag. | Full source (author/year/table/DOI) |
| **Assumed** | A professional assumption not stated by the paper. | No for L2; may be used for L3 with a flag. | Assumption statement + impact |
| **Unknown** | Cannot be determined from the paper or a reliable derivation. | No. | Leave null; report the gap |

## Rules

1. **Contextual is not Assumed.** If the paper says "a fresh 30 wt% solution was loaded", then initial loading = 0 is Contextual. If the paper only implies it by common practice, it is Assumed.
2. **Derived needs a formula and inputs.** A number produced by a model or a rule of thumb is not a paper fact.
3. **External needs a citation.** "Known from literature" is not a citation.
4. **Assumed needs an impact statement.** Say which field it affects and how it changes the conclusion.
5. **Unknown is a valid result.** Leaving a field null is better than inventing a value.

## Examples

| Situation | Classification | Why |
|---|---|---|
| Table row: 30 wt% MEA, 313 K, 15 vol% CO2, loading 0.50 | Explicit | all conditions in table/caption |
| Methods: "0.025 dm3 of fresh solution was placed in the absorber" → initial loading 0 | Contextual | paper states fresh solution, though not as a number |
| P_CO2 = 15 vol% × 101.325 kPa = 15.2 kPa | Derived | explicit inputs + formula |
| Density taken from a handbook for 30 wt% MEA at 313 K | External | not measured in this paper; cite source |
| Assume total pressure = 1 atm because most flue gas is atmospheric | Assumed | paper did not state it |
| A figure's curve value without a table/digitizer | Unknown | cannot be read reliably |
| Model-predicted loading from eNRTL | Derived/External | model output, not experimental |

## How to record

In the snapshot/report:

```
field: initial_loading
value: 0
type: Contextual
evidence: "A volume of 0.025 dm3 of the tested sorbent was placed into a homemade glass absorber..."
location: Section 2.2, p.4365
```

For Derived:

```
field: co2_partial_kPa
value: 15.199
type: Derived
formula: P_CO2 = y_CO2 × P_total
inputs: y=0.15, P_total=101.325 kPa
```

## QC implications

- A record with an Assumed field should not be L2; use L3 and add the assumption to `qc_reason`.
- A record with an External field should be flagged; external data are not a substitute for a paper measurement.
- A record with an Unknown required field is L3 or should not be emitted.
- The `qc_reason` should contain machine-readable tags, e.g. `derived_co2_partial_pressure`, `assumed_total_pressure`, `figure_only_not_extracted`.

## Anti-patterns

- Calling a convention "contextual" to avoid marking it assumed.
- Calling a model output "derived" without stating the model.
- Filling a required field with an external value and calling it L2.
- Using a figure estimate as an explicit value.
- Hiding an assumption in the methods section of the report while the JSONL has no flag.
