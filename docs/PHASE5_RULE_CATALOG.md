# Phase 5 可调用规则清单

规则集版本：`phase5-1.0`，共 21 条。

每条规则都绑定现有代码或知识文件；规则不产生论文没有的数值。

| rule_id | 名称 | 类别 | 适用范围 | 输入 | 判断/公式 | 输出 | 知识来源 | 例外 |
|---|---|---|---|---|---|---|---|---|
| R-EVD-01 | Explicit paper evidence | evidence | a value stated verbatim in text, table or caption | field; value; excerpt | keep the paper value; attach loc_type/loc_label/excerpt | evidence_type=Explicit | `validation/evidence_classification.md` | a value only inferred from surrounding text is Contextual, not Explicit |
| R-EVD-02 | Contextual evidence | evidence | a value fixed by an explicit method/context sentence without a standalone row | field; value; context | accept as Contextual only when the context uniquely fixes the value | evidence_type=Contextual | `validation/evidence_classification.md` | two plausible contexts -> Unknown/null |
| R-EVD-03 | Derived evidence | evidence | a value computed by a declared formula from explicit inputs | formula; inputs | recompute and compare; store inputs, formula, units and result | evidence_type=Derived | `formulas/concentration_conversion.md` | missing density/concentration blocks mol/L -> wt% conversion |
| R-EVD-04 | Assumed evidence | evidence | a professional assumption not stated by the paper | field; assumption; reason | never upgrade an Assumed required field to L2 | evidence_type=Assumed; qc must remain L3 or lower | `validation/evidence_classification.md` | none for required fields |
| R-EVD-05 | Unknown evidence | evidence | the paper does not determine the field | field | keep null; do not fill from convention or external memory | evidence_type=Unknown; value=null | `validation/evidence_classification.md` | none |
| R-DET-01 | CO2 partial pressure from gas composition | deterministic | ideal gas mixture with stated total pressure | co2_vol_pct; total_pressure_kPa | P_CO2 = co2_vol_pct / 100 * total_pressure_kPa | co2_partial_kPa | `formulas/partial_pressure.md` | do not assume 1 atm when total pressure is absent; dry/wet basis must be stated |
| R-DET-02 | Recipe mass balance | deterministic | aqueous monoamine or two-component amine recipe | wt_a; wt_b; water_wt | total_amine = wt_a + wt_b; water = 100 - total_amine; sum must be 100 +/- 0.1 | total_amine_wt; water_wt | `formulas/mass_balance.md` | additive/salt/two-phase systems are out of scope |
| R-DET-03 | Rate unit normalization | deterministic | molar rate with convertible amine/solution basis and time unit | value_original; unit_original | apply 10^n/mmol/umol scale and time conversion; keep original values | value; unit; unit_normalization | `validation/unit_validation.md` | mol solution basis or unknown basis is blocked |
| R-DET-04 | Blocked unit conversion | deterministic | rate basis needs density/concentration that the paper does not provide | unit_original | leave the original value; flag conversion blocked | unit_normalization.status=blocked | `formulas/concentration_conversion.md` | never invent a density |
| R-DET-05 | Pressure consistency | deterministic | a point with CO2 partial pressure and total pressure | co2_partial_kPa; total_pressure_kPa | require 0 <= P_CO2 <= P_total; detailed water-vapour balance is R-DET-06 | reasoning check status | `formulas/partial_pressure.md` | a stated total pressure inconsistent with P_CO2 is flagged, not silently adjusted |
| R-DET-06 | Water vapour and dry/wet gas balance | deterministic | gas composition with a declared wet/dry basis, P_H2O, or water activity | gas_basis; co2_vol_pct; p_h2o_kPa; y_h2o; water_activity; co2_partial_kPa; total_pressure_kPa; temperature_K | wet: P_CO2=y_CO2,wet*P_total; dry: P_CO2=y_CO2,dry*(P_total-P_H2O); dry without P_H2O -> blocked, no P_CO2; P_H2O from pure water only with water activity or a verified model | gas-phase status; water_vapour_check; derived P_CO2 or blocked | `formulas/water_vapor.md` | do not use pure-water saturation pressure for an amine solution without water activity; missing water-vapour data -> not_assessable, not a rejection |
| R-EXP-01 | Context resolves a condition | expert_judgement | fresh solvent, pure CO2, atmospheric test, one-column table context | context; field | propose the condition as Contextual; deterministic checks and evidence verification still apply | candidate field value with evidence_type=Contextual | `knowledge/experimental_methods.md` | do not turn a convention into a paper fact |
| R-EXP-02 | Assumption stays an assumption | expert_judgement | professional default used to interpret a paper | assumption; reason | mark Assumed and forbid L2 for required fields | evidence_type=Assumed; qc<=L3 | `validation/evidence_classification.md` | not applicable to non-required descriptive fields |
| R-XSEC-01 | Cross-section VLE table association | expert_judgement | multi-column table with repeated t/p/loading groups | header groups; row coordinates; paper profile | assign each numeric token to its column group, carry temperature down, keep the row excerpt | deterministic VLE records | `knowledge/co2_equilibrium.md` | no profile -> needs_profile, select 0; never apply another paper's apparatus constants |
| R-XSEC-02 | Scattered reference-row association | expert_judgement | a baseline recipe/performance split across table, methods and results | recipe regex; temperature/pressure regex; performance regex | collect the pieces only when every declared evidence anchor matches | reference-row record | `knowledge/experimental_methods.md` | any missing anchor -> no record |
| R-XSEC-03 | Methods condition profile | expert_judgement | test conditions stated in methods but absent from a data table | method text; profile conditions | fill only missing condition fields and record the method evidence | condition fields with evidence | `knowledge/experimental_methods.md` | never infer an unstated total pressure |
| R-QC-01 | Simulation isolation | quality_control | test_origin=simulation | test_origin | force L3, mark performance is_derived=1, never enter L1/L2 | qc_level=L3; simulation_data tag | `validation/consistency_check.md` | 60 wt% simulation is allowed but still L3 |
| R-QC-02 | Metric semantics | quality_control | metric label contradicts unit, sign or definition | metric_name; unit; value; metric_definition | downgrade to L3 and record the mismatch | qc_level=L3; metric_semantics_downgrade | `validation/consistency_check.md` | do not silently rename the metric |
| R-INF-01 | Insufficient evidence | quality_control | a required field is null after all rules | temperature_K; co2_vol_pct; initial_loading | keep null, mark incomplete/L3, list the missing field | qc_level=L3; incomplete_flag | `validation/consistency_check.md` | information shortage is not a negative label |
| R-OCR-01 | OCR quality gate | quality_control | page text obtained by RapidOCR | ocr confidence; native text; critical scientific fields | pass normal pages; send low-confidence/conflicting pages to review; fail closed when OCR text is unusable | ocr_gate decision per page | `knowledge/experimental_methods.md` | confidence is not a calibrated probability |
| R-MAN-01 | A->B manifest identity | quality_control | paper handoff from A to B | paper_id; doi; pdf.sha256; si.sha256 | validate schema, path containment and hashes before parsing | manifest validation result | `docs/PHASE5_MANIFEST.md` | missing DOI/SI is allowed; hash mismatch is fatal |

## 规则与知识模块的动态绑定

| 知识模块 | 触发的规则 |
|---|---|
| `amine_properties` | R-EVD-01, R-DET-02 |
| `amine_chemistry` | R-EVD-02, R-QC-02 |
| `mixed_amine_systems` | R-DET-02 |
| `co2_equilibrium` | R-DET-01, R-DET-05, R-XSEC-01 |
| `thermodynamic_models` | R-QC-01, R-QC-02 |
| `experimental_methods` | R-EXP-01, R-XSEC-02, R-XSEC-03, R-OCR-01 |
| `physical_properties` | R-EVD-03 |

## 证据类型

`Explicit / Contextual / Derived / External / Assumed / Unknown` 六类保持不变；Assumed 必填字段不得进入 L2，Unknown 保持 null。

## 程序入口

- 注册表：`server/rules.py`
- 轨迹：`server/reasoning.py:trace_record`
- 一致性门控：`server/reasoning.py:consistency_issues/apply_consistency`
- 知识路由：`server/skill_router.py:select_modules/build_context/build_rule_context`
- 水蒸气：`server/gas_phase.py`
