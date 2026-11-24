# Knowledge Update and Citation Verification Log

## Phase-1 knowledge files

| File | Status |
|---|---|
| `knowledge/amine_properties.md` | Created; four whitelist identities copied from `data/compound_whitelist.csv`; other amines described with CAS/formula/MW and a "verify structure" rule. |
| `knowledge/amine_chemistry.md` | Created; reaction routes and speciation caveats; textbook/review sources. |
| `knowledge/mixed_amine_systems.md` | Created; ratio/basis conversions and boundary rules. |
| `knowledge/co2_equilibrium.md` | Created; VLE definitions, partial pressure, water-vapour check. |
| `knowledge/thermodynamic_models.md` | Created; Kent–Eisenberg, Deshmukh–Mather, eNRTL, Pitzer and applicability limits. |
| `knowledge/experimental_methods.md` | Created; method-to-metric mapping and common method errors. |
| `knowledge/physical_properties.md` | Created; density/viscosity/capacity/rate/heat definitions. |
| `formulas/*.md` | Created; concentration, loading, partial pressure, mass balance, correlations. |
| `scripts/calc.py` | Created and tested; deterministic conversions. |
| `extraction/*.md` | Created; PDF/table/figure/SI reading rules. |
| `validation/*.md` | Created; unit/physical/consistency/evidence rules. |
| `references/db_schema_map.md` | Created from `scripts/schema.sql`; no schema change. |
| `references/schema_extension_recommendations.md` | Created; proposals only. |
| `references/test_report_barzagli2019.md` | Created; real-paper test and negative controls. |

## Phase-2 updates

- Added `references/phase2_extraction_lessons.md` with actual regression findings:
  - conditional L2 with machine-verified snapshot;
  - 27-point VLE table still incomplete (12/27);
  - rate-unit scale errors;
  - missing co2_vol_pct/initial_loading on VLE points;
  - water-lean reference row missed;
  - SI publisher-specific behavior;
  - snapshot CRLF hash bug and fix.
- Updated `SKILL.md`:
  - OCR is now available (`--ocr auto`, RapidOCR);
  - chart digitization is semi-automatic (`tools/digitize_chart.py`);
  - phase-2 runtime integration and regression harness documented;
  - correction: only L1/L2 require snapshots; L3/simulation do not.
- Updated `references/test_report_barzagli2019.md` limitations to reflect OCR/SI/chart availability and conditional L2.

## Verification status

### Verified

- Four whitelist compounds: CAS, formula, MW, SMILES, InChIKey from `data/compound_whitelist.csv`.
- Formula behavior: `calc.py` samples for 30 wt% MEA, molality, partial pressure, loading, cyclic capacity, recipe closure.
- DB field names: copied from `scripts/schema.sql`; no invented fields.
- Protocol/tool behavior: `pdf_to_text.py`, `validate.py`, `postcheck.py`, `import_jsonl.py` inspected directly.
- Actual test artifacts: 38-record eval set, 7-paper regression batch, OCR/chart/SI runs.

### Reliable source, not independently cross-validated in Phase 2

- Textbook/review statements in `knowledge_sources.md` (Kohl & Nielsen, Rochelle 2009, Wilcox 2012).
- Model descriptions and applicability limits (Kent–Eisenberg, Deshmukh–Mather, eNRTL, Pitzer).

### Removed or downgraded during verification

- Rows for 2-AP/1-AP/MAE with uncertain CAS mapping were removed from the properties table; the file now instructs resolving isomers from the paper/PubChem.
- Two uncertain citations (Zhang & Rochelle; Xu et al.) were removed rather than presented as verified.
- Any knowledge statement that could not be sourced is marked as a rule/caveat, not as a measured value.

### Unresolved / to verify

- More amine identities (DEA/TEA/DGA/DETA/TETA structures) need PubChem cross-checks before being used for a DB record.
- Model parameter sets and their temperature/concentration ranges need source-level verification before use.
- Publisher-specific SI link patterns (Wiley, Elsevier, RSC, Springer) need a link-pattern matrix.
- OCR confidence calibration and chart digitization error propagation are not independently validated.

## Citation policy

- No CAS/SMILES/InChIKey/DOI/MW from memory.
- Resolve identities via PubChem or the paper/SI.
- Cite the original paper for experimental values; do not present a review's secondary table as raw data.
- Mark unverified knowledge as "verify" and do not let it drive an L2 decision.
