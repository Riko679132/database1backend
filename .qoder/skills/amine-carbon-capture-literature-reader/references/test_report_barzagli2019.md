# Test Report — Barzagli et al. 2019 (and two negative controls)

## Test objective

Verify that the expert-reading workflow extracts more correct, traceable information than a naive field-matching extraction, and that every extracted value can be traced to a paper location and a snapshot.

## Paper

- **DOI:** 10.1021/acs.iecr.9b00552
- **Title:** Comparative Study of CO2 Capture by Aqueous and Nonaqueous 2-Amino-2-methyl-1-propanol Based Absorbents Carried Out by 13C NMR and Enthalpy Analysis
- **Authors:** Barzagli F.; Giorgi C.; Mani F.; Peruzzini M.
- **Journal/year:** Industrial & Engineering Chemistry Research, 2019, 58, 4364–4373.
- **PDF:** `data/raw_pdfs/10.1021_acs.iecr.9b00552_6a66ebd9.pdf`
- **Parsed text:** `extractions/autobatch_20261030/parsed/10.1021_acs.iecr.9b00552_6a66ebd9.txt`

## Paper map

| Item | Reading |
|---|---|
| Systems | 3.0 mol dm⁻³ AMP, AMP–EMEA, AMP–MDEA in water, EG–PrOH and EG–DEGMME; 30 wt% aqueous MEA reference |
| Research type | experiment + thermodynamics + NMR/enthalpy |
| Methods | batch loading with pure CO2 at 40 °C, 8 h; rate with pure CO2; heat by Gibbs–Helmholtz; continuous 15% CO2 capture efficiency in packed columns; 13C NMR |
| Main variables | amine/diluent, temperature, gas composition, loading |
| Reported metrics | CO2 loading (mol/mol), absorption rate, heat of absorption, capture efficiency |
| Boundary decision | only the 30 wt% aqueous MEA reference row is in scope; AMP/AMP-blend rows are 3.0 M and/or non-aqueous; out of scope |

## Evidence ledger (selected)

| Field | Raw value | Unit | Location | Type | Note |
|---|---|---|---|---|---|
| MEA concentration | 30 | wt% | Table 1 caption; p.4366 | Explicit | "Compared with 30 wt % Aqueous MEA" |
| MEA loading | 0.609 | mol CO2/mol amine | Table 1, MEA row | Explicit | batch, 40 °C |
| Temperature | 40 | °C | Section 2.2 | Explicit | 313.15 K |
| Gas | pure CO2 | – | Section 2.2 | Explicit | continuous stream, 15.0 dm³/h |
| Liquid volume | 0.025 | dm³ | Section 2.2 | Explicit | fresh sorbent |
| Equilibrium time | 8 | h | Section 2.2 | Explicit | stopped after 8 h |
| Total pressure | not stated | – | Section 2.2 | Unknown | do not assume 1 atm |
| CO2 vol% | 100 | vol% | Section 2.2 (pure CO2) | Explicit | not the 15% continuous experiment |
| Initial loading | 0 | mol/mol | Section 2.2 (fresh sorbent) | Contextual | not a direct number; determined by method |

## Extracted record (L2)

- **source:** DOI 10.1021/acs.iecr.9b00552; PDF hash recorded; location "p.4366 Table 1, MEA row".
- **recipe:** mono, MEA 30 wt%, water 70 wt%, total amine 30 wt%.
- **test:** 313.15 K, co2_vol_pct 100, co2_partial_kPa null, total_pressure_kPa null, initial_loading 0, rich_loading 0.609.
- **performance:** `equilibrium_loading` = 0.609 mol CO2/mol amine, `is_derived=0`.
- **qc:** L2; reason `table_discrete_point;batch_equilibrium_pure_CO2_8h;initial_loading_fresh_unloaded_solution;single_MEA_reference_row_30wt%`.
- **snapshot:** `extractions/autobatch_20261030/raw/barzagli2019_table1_snapshot.json`, SHA-256 `1c4f752992e9d1f88b7f9049b00f1ac71a337a8c8f08c0b335b4335a5307d101`.
- **JSONL:** `extractions/autobatch_20261030/raw_agent.jsonl`.

Validation result: `validate.py` → valid=1, incomplete=0, rejected=0; `postcheck.py` → all seven checks PASS; L2 snapshots 38/38; DB record test#60.

## Reasoning case 1 — the unit trap: 3.0 M AMP rows vs 30 wt% MEA

Table 1 contains:

```
AMP        0.875  0.723  0.607
AMP-EMEA   0.861  0.665  0.585
AMP-MDEA   0.813  0.456  0.398
MEA        0.609
```

A naive extractor sees nine AMP/AMP-blend values plus one MEA value and may emit ten records, or convert the 3.0 mol dm⁻³ concentrations to wt% using an assumed density. That is wrong on two counts:

- the AMP/AMP-blend rows are not in the project whitelist;
- the concentrations are 3.0 mol dm⁻³, and the paper does not give the density of those blends.

The expert workflow emits **one** in-scope record (30 wt% MEA) and lists the nine excluded rows with reasons in the snapshot. It does not invent a density to force the other rows into the recipe table.

## Reasoning case 2 — pure CO2 batch vs 15% continuous experiment

The methods contain two different gas experiments:

- Section 2.2: batch loading with **pure CO2**, 40 °C, 8 h — this is the source of Table 1's loading values.
- Section 2.5: continuous absorption–desorption with **15% CO2 in N2** — this is for capture-efficiency testing, not for Table 1's loading.

A naive extractor may see "15% CO2" in the methods and assign `co2_vol_pct=15` to every record. The expert workflow links the table to Section 2.2 and sets `co2_vol_pct=100`. This changes the meaning of the record and is exactly the kind of cross-section reasoning the skill is meant to enforce.

## Reasoning case 3 — initial loading is contextual, not assumed

Section 2.2 says "A volume of 0.025 dm³ of the tested sorbent was placed into a homemade glass absorber... reacted with a continuous stream of pure CO2... stopped after 8 h." It does not write "initial loading = 0", but the method unambiguously starts from a fresh unloaded sorbent. The workflow marks this **Contextual**, not **Assumed**, and records the determining sentence. A naive extractor either leaves it null (L3) or assumes 0 without evidence; both are less defensible.

## Reasoning case 4 — total pressure is not stated

The batch method does not state the total pressure. The workflow leaves `co2_partial_kPa` and `total_pressure_kPa` null. It does **not** assume 1 atm, even though the apparatus is likely near atmospheric. Because `temperature_K`, `co2_vol_pct` and `initial_loading` are present, the record can still be L2; the missing total pressure is documented rather than fabricated.

## Negative control A — ACS PZ blends

Paper: 10.1021/acs.iecr.1c04123, *Ind. Eng. Chem. Res.* 2022, 61, 1301–1312.

- Table 1 contains 18 rows of initial absorption rate, CO2 loading and increment for PZ + MEA/MDEA/AMP blends.
- The concentrations are 1 M total amine (mol/L), and the paper gives no solution density.
- A naive extractor would emit up to 18 records or convert 1 M to wt% with an assumed density.
- The expert workflow emits **zero** in-scope records: the concentration is mol/L without density, so the recipe cannot be closed in wt% (concentration red line). The reason is recorded in `extraction_todo_assessment.csv`.

## Negative control B — Wiley MEA VLE

Paper: 10.1155/2022/6278342, *Advances in Materials Science and Engineering* 2022.

- 20 wt% aqueous MEA, VLE at 298, 313, 333, 353 K, P_CO2 34.5–78.0 kPa.
- The measured VLE data appear only in Figures 2/3 (curves/symbols); Data Availability says the data are embargoed; no SI table is available.
- A naive extractor may estimate points from Figure 3 or assume 1 atm total pressure.
- The expert workflow emits **zero** records and marks the paper `figure_only_not_extracted` / `embargo_no_table`. It does not digitize or assume.

## What a naive extractor would miss or get wrong

| Issue | Naive field matching | Expert workflow |
|---|---|---|
| Table 1 AMP rows | emit 9 out-of-scope rows or invent density | exclude, with reasons |
| Gas composition | use 15% from the wrong section | use 100% pure CO2 from Section 2.2 |
| Initial loading | null or unstated assumption | Contextual 0 from fresh-sorbent method |
| Total pressure | assume 1 atm | leave null, document |
| ACS mol/L rows | emit 18 rows | zero, concentration red line |
| Wiley figure-only VLE | digitize/estimate | zero, figure-only/embargo |
| Evidence traceability | value without location | snapshot + excerpt + hash |

## Limitations found

1. **OCR was not available when this test was first run.** Phase 2 added `scripts/pdf_to_text.py --ocr auto` (RapidOCR); scanned pages can now be processed, but OCR text remains approximate and must be flagged.
2. **Chart digitization is semi-automatic.** Phase 2 added `tools/digitize_chart.py`; colored markers can be auto-detected after axis calibration, but overlapping/black curves still require manual points or an external digitizer.
3. **No SI in this test.** If the Barzagli SI contains raw VLE tables, it was not available in the local batch; the current record relies on the main-text Table 1. Phase 2 added `tools/fetch_si.py` and a SI handoff manifest.
4. **Table context can be ambiguous.** The pure-CO2 vs 15% distinction required reading Sections 2.2 and 2.5; the reasoning is documented in the snapshot, but a different reader could still disagree. The skill makes the assumption visible rather than hiding it.
5. **The phase-2 LLM path can now emit L2 conditionally.** `server/extract.py` selects knowledge modules, writes a snapshot and machine-verifies excerpt/numeric evidence; L2 still requires a snapshot and is marked `human_audit_pending`.
6. **Schema gaps** (see `schema_extension_recommendations.md`): gas basis, uncertainty type, method linkage, excerpt text, speciation, model parameters.

## Conclusion

On this paper, the expert workflow produced **one correct L2 record** from a table that a naive extractor would likely turn into ten rows (nine out of scope) and a wrong gas composition. The record is traceable to a table row, a method sentence, a snapshot and a SHA-256; it passed validation and postcheck. The negative controls show that the workflow can also say "no" for the right reasons, which is as important as extracting more data.
