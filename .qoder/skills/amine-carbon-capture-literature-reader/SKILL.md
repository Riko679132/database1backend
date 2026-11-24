---
name: amine-carbon-capture-literature-reader
description: Expert reading and structured extraction for aqueous amine CO2 capture papers (MEA, PZ, AMP, MDEA and their blends). Use when reading a paper PDF or parsed text to extract recipes, VLE/absorption/desorption data, operating conditions and performance metrics into the project JSONL + snapshot contract, and when checking tables, figures, units, derived parameters, evidence types and database-field mapping.
---

# Amine Carbon Capture Literature Reader

## What this skill does

Read a CO2-capture paper the way an experienced amine-solvent researcher would: build a paper map, link information across sections, separate explicit facts from contextual facts and assumptions, derive only what the data support, and emit evidence-backed records that can pass the project's validation gate.

This skill does not replace the database or the import scripts. It produces a **reading report + `raw_agent.jsonl` + raw snapshots**; `scripts/validate.py` remains the only gate and the frozen import scripts remain the only writers.

## Non-negotiable rules

1. **Never modify the database schema, existing fields or frozen scripts.** Do not write to `data/ccus.sqlite` directly. Only produce JSONL and snapshots for `validate.py` / `import_jsonl.py`.
2. **Never fabricate** DOI, CAS, SMILES, InChIKey, temperatures, pressures, concentrations or performance values. If the paper does not state it and it cannot be derived from stated data, use `null` and report the gap.
3. **Amine identity comes from the whitelist.** Resolve names/CAS against `data/compound_whitelist.csv`; for the current project that means MEA, PZ, AMP, MDEA only. Papers whose main solvent is outside the whitelist can be read and reported, but their records must not be emitted as in-scope data.
4. **Literature concentration boundary:** aqueous monoamine or two-component amine blend, total amine 20–50 wt%, no additive, salt, two-phase or slurry. `simulation` may exceed 50 wt% but is always L3.
5. **Concentration red line:** if the paper reports only mol/L or molality and gives no solution density, do not convert to wt%. Molality (mol/kg solvent) may be converted exactly with `wt% = m·M/(m·M+1000)` and must be flagged. Volumetric metrics (e.g. g-CO2/L-soln) stay in their original unit with a `_volumetric` suffix.
6. **L1/L2 require a raw snapshot** in `extractions/<batch>/raw/` plus its SHA-256 in `test.raw_data_path` / `test.raw_data_hash`. No snapshot means L3 at best.
7. **One test = one measurement point.** A VLE table row is one test; do not collapse a table into one record.
8. **Preserve original values and units.** Put the paper value in `value_original` / `unit_original`; put the standardized value in `value` / `unit`. Never silently overwrite a reported value.
9. **Figures are for locating and qualitative understanding, not pixel reading.** OCR is available through `scripts/pdf_to_text.py --ocr auto` (RapidOCR), but OCR text is approximate and must be flagged with tool, pages and confidence. Chart digitization is semi-automatic via `tools/digitize_chart.py`; it requires axis calibration and either manual points or colored-marker detection, and must record image/CSV hashes and error estimates. If a value exists only in a figure and cannot be digitized, mark `figure_only_not_extracted`; do not estimate from pixels.
10. **Simulation data is isolated.** `test_origin="simulation"`, `qc_level="L3"`, `qc_reason` starts with `simulation_data`, `performance.is_derived=1`. Simulation never enters the L1/L2 gold standard.

## Project contract

### Inputs

- A PDF in `data/raw_pdfs/` and/or its parsed text in `extractions/<batch>/parsed/`.
- Paper metadata from the A-stage handoff: DOI, title, authors, year, journal, PDF SHA-256, triage verdict. If no manifest exists, resolve DOI from the filename (`10.xxxx_...pdf`) and verify it against the PDF first page.
- `data/compound_whitelist.csv` for amine identity.
- The current schema in `scripts/schema.sql` for field names only; never change it.

### Outputs (batch directory)

```
extractions/<batch>/
├── raw_agent.jsonl                 # one JSON object per test
├── raw/<paper_slug>_snapshot.json # evidence snapshot for L1/L2
├── extraction_report.md            # paper map, evidence ledger, gaps, rejected rows
├── valid.jsonl                     # produced by scripts/validate.py
├── valid_incomplete.jsonl          # produced by validate.py if applicable
└── rejected.jsonl                  # produced by validate.py, never imported
```

### Validation

```powershell
.\.venv\Scripts\python.exe scripts\validate.py --input extractions\<batch>\raw_agent.jsonl --outdir extractions\<batch>
.\.venv\Scripts\python.exe tools\postcheck.py --batch <batch>
```

`postcheck` must pass all seven checks. If a record is rejected, keep it in `rejected.jsonl`, explain why in the report, and never import it.

## Reading workflow

### Step 0 — Load context

1. Read `data/compound_whitelist.csv` and the research boundary in `AGENTS.md`.
2. Read the parsed text, not only the abstract. Build a section map first (`grep` for `Introduction`, `Experimental`, `Results`, `Table`, `Figure`, `Conclusion`, `Supporting`).
3. Locate tables, figures, equations and supplementary-information links. Record page numbers and captions.
4. Check PDF quality: if the text is garbled or the page is a scan (average < 50 chars/page), stop and report; do not guess.

### Step 1 — Paper map

Before extracting any number, write down:

- Amine system(s): exact names, CAS if given, single or blend, solvent (water/organic), claimed wt% or molarity.
- Research type: experiment, model, simulation, review, property/degradation.
- Apparatus and method: equilibrium cell, bubble column, wetted wall, packed column, pilot, calorimeter, etc.
- Main variables: temperature, pressure, gas composition, amine concentration, blend ratio, loading.
- Reported metrics and their definitions.
- Conclusions and applicable range.

If the paper is a review, property/degradation study or non-aqueous system, record the boundary decision and stop unless it contains an in-scope aqueous amine data table.

### Step 2 — Evidence ledger

Create a table with one row per candidate data point:

| field | raw value | unit | location | evidence type | note |
|---|---|---|---|---|---|

Evidence types are defined in `validation/evidence_classification.md`:

- `Explicit` — stated in the paper.
- `Contextual` — unambiguously determined by the paper's own context (e.g. the method says a fresh 30 wt% solution was loaded).
- `Derived` — calculated from explicit inputs with a stated formula.
- `External` — taken from a cited reliable source; must include the source.
- `Assumed` — a professional assumption not stated by the paper.
- `Unknown` — not obtainable.

**Contextual is not Assumed.** If the paper only implies a value by convention, mark it `Assumed` and explain.

### Step 3 — Extract points

For each test point, capture:

- Source: DOI, title, authors, year, journal, PDF path/hash, table/figure/page and a short verbatim excerpt.
- Recipe: mono/binary, amine A/B, wt% of each component and water, total amine wt%, additive/salt/phase flags. If only molarity is given, keep the original unit in the report and do not invent wt%.
- Conditions: temperature (K), CO2 vol%, CO2 partial pressure (kPa), total pressure (kPa), gas flow, liquid volume, gas/liquid ratio, initial/rich/lean loading.
- Performance: metric name, value, unit, original value/unit, error/replicates if reported, definition, whether derived.
- QC: L1/L2/L3 and reason tags.

**VLE:** each `(T, P_CO2, loading)` row is a separate test. `co2_vol_pct` may be derived only when the paper states total pressure; otherwise leave it `null` and report that the VLE point cannot be a complete L2 record. Always check `P_CO2 + P_H2O(T) ≤ P_total`; if it fails, the stated total pressure is inconsistent and that temperature column must be discarded.

**Absorption capacity:** distinguish equilibrium capacity, rich loading, dynamic capacity, cyclic working capacity and absorption rate. They are not interchangeable.

### Step 4 — Reason about missing parameters

For every missing field, ask in this order:

1. Is it stated elsewhere in the paper?
2. Can it be calculated from explicit data with a formula in `formulas/`?
3. Is a reliable external source available (cite it)?
4. Is a professional assumption required? If yes, mark `Assumed` and state the impact.
5. Is it still unknown? Leave `null`.

Do not calculate a value merely to fill a field. A derived value must have a formula, inputs, units and assumptions recorded in the snapshot/report.

### Step 5 — Map to the database

Use `references/db_schema_map.md` for exact field names and mapping rules. Key points:

- `test` is the measurement point; `performance` rows hang off one `test`.
- `recipe` requires wt% and a closed mass balance (`wt_a + wt_b + water_wt = 100 ± 0.1`).
- `binary` requires the second amine's InChIKey; otherwise the record is a hard rejection.
- `source_location` records where the point came from; `source.excerpt` must be copied from the paper, not paraphrased.
- `qc_level`: L1 author raw data, L2 complete table/text point with snapshot, L3 incomplete or simulation, L4 hard violation/rejected.
- `metric_name` must be one of the project enum values; if a new metric is truly needed, record it as an extension request instead of silently inventing a name.

### Step 6 — Snapshot

For every L1/L2 record, write one snapshot JSON per source table/figure containing:

- DOI, title, authors, journal, year, PDF path and PDF SHA-256.
- Table/figure number, caption and page.
- Experimental conditions and the exact row text.
- Included rows and excluded rows, with reasons.
- Formulas, inputs and assumptions used for every derived value.
- Any conflicts with other sections.

Hash the snapshot file with SHA-256 and put the path/hash in `test.raw_data_path` / `test.raw_data_hash`.

### Step 7 — Validate and report

Run `validate.py`, then inspect `valid`, `valid_incomplete`, `rejected`. In `extraction_report.md` include:

- Paper map and boundary decision.
- Evidence ledger summary.
- Number of points extracted, derived, assumed and unknown.
- Rejected/out-of-scope rows and why.
- Table/figure/OCR limitations.
- Schema extension suggestions (do not modify the schema).

## Knowledge routing

Read only the files needed for the current paper:

| Question | File |
|---|---|
| Amine names, CAS, MW, class, reaction behaviour | `knowledge/amine_properties.md` |
| Carbamate/bicarbonate chemistry, speciation, temperature effects | `knowledge/amine_chemistry.md` |
| Single vs blended systems, ratio notations, solvent effects | `knowledge/mixed_amine_systems.md` |
| VLE, Henry's law, partial pressure, loading, water vapour | `knowledge/co2_equilibrium.md` |
| Kent–Eisenberg, Deshmukh–Mather, eNRTL, Pitzer | `knowledge/thermodynamic_models.md` |
| Static/dynamic/bubbling/pilot/calorimetry methods | `knowledge/experimental_methods.md` |
| Density, viscosity, capacity, rate, heat, degradation | `knowledge/physical_properties.md` |
| Concentration, loading, pressure, mass-balance formulas | `formulas/*.md` |
| Deterministic calculations | `scripts/calc.py` |
| Reading order, tables, figures, SI | `extraction/*.md` |
| Units, physical constraints, consistency, evidence types | `validation/*.md` |
| Exact DB fields and extension suggestions | `references/db_schema_map.md`, `references/schema_extension_recommendations.md` |
| Sources and citation policy | `references/knowledge_sources.md` |
| Phase-2 extraction lessons and known failure modes | `references/phase2_extraction_lessons.md` |
| Phase-3 multi-column VLE and rate-unit fixes | `references/phase3_lessons.md` |
| Phase-4 reference/condition profiles, metric semantics and negative set | `references/phase4_lessons.md` |
| Worked test case | `references/test_report_barzagli2019.md` |

## Metric names

Use the project enum:

`equilibrium_loading`, `cyclic_capacity`, `cyclic_capacity_volumetric`, `regeneration_energy`, `regeneration_heat`, `regeneration_efficiency`, `initial_absorption_rate`, `initial_desorption_rate`, `absorption_rate_volumetric`, `absorption_amount_volumetric`, `co2_removal_efficiency`, `cost_per_tonne_co2`, `iron_solubility`, `pka`, `model_prediction_deviation`, `annual_energy_consumption_reduction`, `aard_equilibrium_co2_partial_pressure`.

For a metric that does not fit, keep it in the reading report and propose an extension; do not force it into a wrong enum value.

## Output quality checklist

- [ ] Every record has DOI, PDF hash, location and verbatim excerpt.
- [ ] Recipe is closed to 100 ± 0.1 wt%; binary has two identities.
- [ ] One test per point; VLE rows not collapsed.
- [ ] Original units preserved; conversions have a formula and inputs.
- [ ] `initial_loading`, `co2_vol_pct`, `temperature_K` present for L2.
- [ ] L1/L2 records have a snapshot and hash.
- [ ] Derived values marked `is_derived=1` and explained.
- [ ] Figure-only values are marked and not estimated.
- [ ] Rejected/out-of-scope rows are reported, not silently dropped.
- [ ] No schema or database modification.

## Phase-2 runtime integration

The console extraction path now implements this skill's contract:

- `server/extract.py` selects knowledge modules by keyword and records their SHA-256.
- `server/provenance.py` writes an immutable snapshot per paper and performs machine verification of excerpt/numeric evidence.
- `server/table_grid.py` rebuilds multi-column/no-border table pages by coordinates; the grid is a locating aid, not a rewrite of the paper.
- `scripts/pdf_to_text.py --ocr auto` handles scanned pages with RapidOCR; OCR pages are recorded in `parse_report.json`.
- `tools/fetch_si.py` discovers/downloads/parses SI and writes a manifest; `server/tasks.py` loads parsed SI text into the extraction prompt.
- `tools/digitize_chart.py` extracts chart regions, calibrates axes and writes CSV + provenance; automatic detection is limited to colored markers.
- `evaluation/` builds the 38-record L2 regression set and reports coverage, completeness, agreement, recipe closure, QC outcomes and failure samples.

## Resources

- `knowledge/` — domain knowledge.
- `formulas/` — formula definitions and applicability.
- `scripts/calc.py` — deterministic concentration/loading/pressure calculations.
- `extraction/` — PDF, table, figure and SI reading rules.
- `validation/` — unit, physical, consistency and evidence checks.
- `references/` — DB mapping, extension recommendations, sources, phase-2 lessons, test report.
