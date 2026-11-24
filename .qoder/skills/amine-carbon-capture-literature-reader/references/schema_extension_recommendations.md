# Schema Extension Recommendations

These are **recommendations only**. Do not modify the database schema or existing fields as part of the reading task. Record gaps in the extraction report and raise them as a separate change request.

## High priority

### 1. Preserve the excerpt text or an excerpt file path

- Current: `source_location` has `excerpt_path`, but `import_jsonl.py` does not store `source.excerpt` text.
- Impact: the DB can point to a location but cannot show the verbatim sentence without opening the snapshot/JSONL.
- Suggestion: either store the excerpt text in a new provenance table/column, or require a generated excerpt file and set `excerpt_path`.

### 2. Gas-phase basis and balance gas

- Current: `test` has `co2_vol_pct`, `co2_partial_kPa`, `total_pressure_kPa`, but no dry/wet basis, balance gas, O2/SO2/H2O content.
- Impact: 15 vol% dry vs wet, or CO2 in N2 vs flue gas, can change the meaning of a point.
- Suggestion: add `gas_basis`, `balance_gas`, `h2o_vol_pct`, `o2_vol_pct`, `so2_ppm`.

### 3. Uncertainty type and replicates

- Current: `performance.error_value`, `repeat_count` exist, but no error type (SD/SE/CI/range).
- Impact: an error of 0.01 could be SD, SE or a range.
- Suggestion: add `error_type`, `error_basis` (absolute/relative).

### 4. Method/apparatus linkage

- Current: `method` table exists, but `import_jsonl.py` does not create method rows; `test.method_id` is optional.
- Impact: apparatus, analysis method, loading definition and rate definition can be lost.
- Suggestion: define a method JSONL block and populate `method`, then set `test.method_id`.

### 5. Figure-digitization provenance

- Current: no table for digitization tool, calibration, error, or digitized points.
- Impact: if figures are ever digitized, the values are not reproducible.
- Suggestion: add a `figure_digitization` provenance table (figure id, tool, axis calibration, error, digitized file hash).

## Medium priority

### 6. Speciation data

- Current: `performance` can store a scalar metric, but not a species concentration vector.
- Impact: NMR/FTIR speciation (MEA, MEACOO−, MEAH+, HCO3−, CO32−, PZ species) cannot be stored structurally.
- Suggestion: add `species_concentration` (test_id, species_name, value, unit, method, loading).

### 7. Model parameters

- Current: no table for equilibrium constants, interaction parameters, kinetic constants or model version.
- Impact: model-based records cannot be reproduced.
- Suggestion: add `model_parameter` (model_name, parameter_name, value, unit, temperature_range, source).

### 8. Supplementary-information provenance

- Current: `source` has one `pdf_path`/`pdf_hash`; the SI is separate.
- Impact: an L1 SI table cannot be traced to its own file/hash.
- Suggestion: add `supplementary_path`, `supplementary_hash`, `supplementary_table_label`.

### 9. Derived-value provenance

- Current: `raw_data_path`/`hash` point to a snapshot, but the DB does not store formula/inputs per derived value.
- Impact: a derived metric cannot be recomputed from the DB alone.
- Suggestion: add a `derivation` record (field, formula, inputs, assumptions, snapshot id).

### 10. Metric enum expansion

Possible additions if the project needs them:

- `heat_of_absorption`
- `mass_transfer_coefficient`
- `liquid_side_mass_transfer_coefficient`
- `pressure_drop`
- `foaming_height`
- `amine_loss`
- `degradation_product_concentration`
- `speciation_fraction`
- `model_parameter`

Do not add a metric to the enum without a downstream agreement; otherwise use the closest existing metric and record the exact definition in `metric_definition`.

## Low priority

### 11. Raw text/page coordinates

- Current: `source_location` stores a label, not page coordinates.
- Suggestion: add `page`, `bbox`, `table_row`, `table_column` for exact location.

### 12. Rejected-row ledger

- Current: `rejected.jsonl` lives in the batch directory, not the DB.
- Suggestion: add `rejected_record` or a QC ledger table if rejection analysis is needed across batches.

## How to raise a gap

In `extraction_report.md`:

```
Gap: <what cannot be stored>
Example: <paper, field, value>
Impact: <what analysis is blocked>
Suggestion: <new field/table, type, unit>
Do not implement without approval.
```
