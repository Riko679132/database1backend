# Database Extension Recommendations

**No schema change was made in Phase 2.** This document records gaps found while wiring the Skill, OCR, chart digitization and SI handling into the extractor.

For each item: current field, problem, suggested addition, example, value, compatibility.

## 1. Gas-phase basis and balance gas

- **Current:** `test.co2_vol_pct`, `co2_partial_kPa`, `total_pressure_kPa`.
- **Problem:** 15 vol% dry vs wet, CO2 in N2 vs flue gas, O2/SO2/H2O cannot be represented. A point may be misinterpreted across papers.
- **Suggested:** `gas_basis` (dry/wet), `balance_gas`, `h2o_vol_pct`, `o2_vol_pct`, `so2_ppm`.
- **Example:** 15 vol% CO2, N2 balance, dry basis, 0 ppm SO2.
- **Value:** makes gas conditions comparable and prevents dry/wet mixing.
- **Compatibility:** additive nullable columns; existing rows remain valid with null.

## 2. Error type

- **Current:** `performance.error_value`, `repeat_count`.
- **Problem:** an error of 0.01 could be SD, standard error, confidence interval or range. Chart/OCR/model errors have different meanings.
- **Suggested:** `error_type` (SD/SE/CI/range/pixel/OCR/model), `error_basis` (absolute/relative), `error_note`.
- **Example:** `error_value=0.01`, `error_type=SD`, `repeat_count=3`.
- **Value:** prevents false precision and supports uncertainty propagation.
- **Compatibility:** additive nullable fields.

## 3. Method linkage

- **Current:** `method` table exists; `test.method_id` exists; `import_jsonl.py` does not create method rows.
- **Problem:** apparatus, analysis method, loading definition and rate definition can be lost.
- **Suggested:** define a method block in JSONL and populate `method`; set `test.method_id`.
- **Example:** reactor_type=static cell; analysis_method=BaCl2 titration; loading_definition=mol CO2/mol amine.
- **Value:** makes test results comparable and reproducible.
- **Compatibility:** no table change; add importer support and optional JSONL field.

## 4. Excerpt text

- **Current:** `source_location.excerpt_path` exists; `import_jsonl.py` does not persist `source.excerpt` text.
- **Problem:** the DB can point to a location but cannot show the verbatim sentence without the snapshot/JSONL.
- **Suggested:** `excerpt_text` (TEXT) or a provenance/excerpt table with `source_location_id`, `text`, `sha256`.
- **Example:** "Table 1 ... MEA 0.609".
- **Value:** direct audit of every value; supports web detail view.
- **Compatibility:** additive column/table; existing `excerpt_path` remains.

## 5. Species distribution

- **Current:** `performance` stores scalar metrics only.
- **Problem:** NMR/FTIR speciation (MEA, MEACOO−, MEAH+, HCO3−, CO32−, PZ species) is a vector, not a scalar; cannot be stored structurally.
- **Suggested:** `species_concentration` table: `test_id`, `species_name`, `value`, `unit`, `method`, `loading`, `source_location_id`.
- **Example:** MEAH+ 0.42 mol/L, MEACOO− 0.31 mol/L at loading 0.45.
- **Value:** enables mechanistic analysis and model validation.
- **Compatibility:** additive table; no existing data migration.

## 6. Model parameters

- **Current:** no storage for equilibrium constants, interaction parameters or kinetic constants.
- **Problem:** model-based records cannot be reproduced; model version/parameters are lost.
- **Suggested:** `model_parameter` table: `model_name`, `model_version`, `parameter_name`, `value`, `unit`, `temperature_range`, `source_doi`, `source_location`.
- **Example:** Kent–Eisenberg K5 coefficients at 313 K; eNRTL binary interaction parameter.
- **Value:** reproducibility and model comparison.
- **Compatibility:** additive table; simulation records remain L3.

## 7. SI provenance

- **Current:** `source` has one `pdf_path`/`pdf_hash`.
- **Problem:** SI files have their own path/hash/type and may contain the raw data; the DB cannot trace them.
- **Suggested:** `source_supplementary` table or `source.supplementary_path/hash/type` fields.
- **Example:** `data/raw_si/10.1021_.../si_01.pdf`, SHA-256, 9 pages.
- **Value:** L1 SI data becomes traceable; prevents "SI not found" ambiguity.
- **Compatibility:** additive; current SI manifest remains as the file-level source of truth.

## 8. Chart digitization provenance

- **Current:** no table for image, calibration, digitized points or error.
- **Problem:** a digitized value cannot be reproduced or audited.
- **Suggested:** `figure_digitization` table: `test_id`, `figure_label`, `image_path`, `image_sha256`, `tool`, `axis_calibration_json`, `points_csv`, `csv_sha256`, `error_estimate`, `human_verified`.
- **Example:** Figure 3, 3 points, x scale 0.1667 value/px, y scale 0.025 value/px.
- **Value:** separates measured, digitized and assumed values; supports error reporting.
- **Compatibility:** additive table; figure-only records can remain L3 until digitization is verified.

## 9. Metric enum expansion

- **Current enum:** 17 metric names (equilibrium_loading, cyclic_capacity, regeneration_heat, etc.).
- **Problem:** heat of absorption, mass-transfer coefficient, pressure drop, amine loss, degradation products and model parameters have no appropriate enum.
- **Suggested additions:** `heat_of_absorption`, `mass_transfer_coefficient`, `liquid_side_mass_transfer_coefficient`, `pressure_drop`, `foaming_height`, `amine_loss`, `degradation_product_concentration`, `speciation_fraction`, `model_parameter`.
- **Example:** ΔH_abs = −83.24 kJ/mol CO2 (do not label as regeneration_heat).
- **Value:** prevents semantically wrong labels and downstream aggregation errors.
- **Compatibility:** additive enum values; existing metrics unchanged; update importer/validator/docs together.

## Migration principle

All suggestions are additive. Do not drop/rename existing fields. If a migration is approved later:

1. add nullable columns/tables;
2. backfill only what is provable from snapshots;
3. keep `excerpt_path`, `raw_data_path/hash` and existing metric names;
4. add a compatibility view for old queries;
5. rerun the 38-record regression and `postcheck.py`.
