# B-stage reasoning-chain test

- Result: PASS
- Rule set: `phase5-1.0` (21 rules)

| Case | Paper | Result | QC | Rules | Detail |
|---|---|---|---|---|---|
| explicit_extraction | 10.1016/j.apenergy.2016.03.043 | PASS | L2 | R-EVD-01, R-EVD-01, R-EVD-03, R-EVD-01, R-EVD-02, R-EVD-01, R-EVD-03, R-EVD-01, R-DET-01, R-DET-02, R-DET-05, R-DET-06, R-EXP-01 | `{"excerpt": "Table 3 CO2 loading of CO2 in aqueous amine solution at 30 wt%, 40 °C and 1 bar (15% CO2 and 85% N2). 1 Monoethanolamine (MEA) 30 0.58", "rule_ids_valid": true}` |
| cross_section_association | 10.1039/d6gc02196d | PASS | L2 | R-DET-02, R-DET-06, R-XSEC-02, R-EXP-01 | `{"loc_label": "pp.10540-10544, Table 4 (MEA 30 wt%) and regeneration results text", "rule_ids_valid": true}` |
| deterministic_formula | 10.1016/j.jece.2024.112664 | PASS | L2 | R-EVD-01, R-EVD-01, R-EVD-02, R-EVD-01, R-EVD-05, R-EVD-03, R-EVD-01, R-EVD-01, R-EVD-01, R-EVD-01, R-EVD-01, R-EVD-01, R-DET-02, R-DET-06, R-DET-03, R-DET-03, R-EXP-01 | `{"formula": "value_std = 34.0 * 1e-05", "inputs": {"value_original": 34.0, "unit_original": "10-5 mol CO2/mol·s", "scale": 1e-05, "time_unit": "s", "basis": "mol_amine"}, "output": {"value": 0.00034, "unit": "mol_CO2/(mol_amine*s)"}, "rule_ids_valid": true}` |
| expert_context_inference | 10.1021/ie400825u | PASS | L2 | R-EVD-01, R-EVD-01, R-EVD-02, R-EVD-01, R-EVD-05, R-EVD-03, R-EVD-01, R-EVD-01, R-EVD-01, R-EVD-01, R-EVD-01, R-EVD-02, R-DET-02, R-DET-06, R-DET-04, R-XSEC-03, R-EXP-01 | `{"total_pressure_kPa": 101.325, "co2_vol_pct": 20.0, "evidence_notes": ["Gas 20% CO2:80% N2", "fresh solution batch absorption", "method: atmospheric pressure", "method: 20% CO2 / 80% N2", "fresh 50 mL solution at start"], "rule_ids_valid": true}` |
| insufficient_evidence | 10.1016/j.jece.2024.112664 | PASS | L3 | R-EVD-01, R-EVD-03, R-EVD-01, R-EVD-01, R-EVD-05, R-EVD-01, R-EVD-01, R-DET-02, R-DET-06, R-XSEC-01, R-INF-01 | `{"initial_loading": null, "missing": {"missing": ["co2_vol_pct", "initial_loading"]}, "rule_ids_valid": true}` |
| consistency_gate_on_final_batch | batch_20261124_145027 | PASS | - | R-DET-01, R-DET-02, R-DET-05 | `{"checked": 43, "issues": 0, "downgraded": 0}` |

Every step in the trace carries `rule_id`, category, evidence type, result and, where applicable, formula/inputs/output and source excerpt.
`R-INF-01` and `R-EVD-05` are used for missing data; missing evidence is not converted into a value.
