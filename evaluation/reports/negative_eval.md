# Negative-set evaluation

- Negative samples: 28
- With a candidate in the final batch: 18
- Outcomes: {'correct_downgrade_L3': 9, 'correct_reject_L4': 1, 'correct_not_extracted': 10, 'correct_model_L3': 3, 'correct_boundary_kept_L3': 5}
- False accept L2: 0
- False accept any L2/L3: 0
- Boundary false rejects: 0
- Boundary kept as L2 (over-accept, not false reject): 0
- FAR (L2, all negatives): 0.0%
- FAR (L2, negatives with candidate): 0.0%

| ID | DOI | label | QC | outcome | reason |
|---|---|---|---|---|---|
| EXTRA-01 | 10.1016/j.apenergy.2016.03.043 | Insufficient Evidence | L3 | correct_downgrade_L3 | regeneration_heat label but unit/sign indicate heat of absorption/reaction (kJ/mol), not regeneration heat |
| EXTRA-02 | 10.1016/j.apenergy.2016.03.043 | Insufficient Evidence | L3 | correct_downgrade_L3 | regeneration_heat label but unit/sign indicate heat of absorption/reaction (kJ/mol), not regeneration heat |
| EXTRA-03 | 10.1016/j.apenergy.2016.03.043 | Insufficient Evidence | L3 | correct_downgrade_L3 | regeneration_heat label but unit/sign indicate heat of absorption/reaction (kJ/mol), not regeneration heat |
| EXTRA-04 | 10.1016/j.apenergy.2016.03.043 | Insufficient Evidence | L3 | correct_downgrade_L3 | regeneration_heat label but unit/sign indicate heat of absorption/reaction (kJ/mol), not regeneration heat |
| EXTRA-05 | 10.1021/ie400825u | Insufficient Evidence | L3 | correct_downgrade_L3 | regeneration_heat label but unit/sign indicate heat of absorption/reaction (kJ/mol), not regeneration heat |
| EXTRA-06 | 10.1021/acs.iecr.9b00552 | Insufficient Evidence | L3 | correct_downgrade_L3 | regeneration_heat label but unit/sign indicate heat of absorption/reaction (kJ/mol), not regeneration heat |
| L4-07 | 10.1016/j.ijggc.2016.12.018 | Duplicate | L4 | correct_reject_L4 | L4 rejected record from a DOI that already has a valid L2 MEA record; wt/mass balance missing |
| OOS-08 | 10.1039/d5ta10129h | Out of Scope | None | correct_not_extracted | 综述/二次数据, 数值均为转引他文, 违反'仅取原始测量'原则; 可作为引文挖掘线索定位原始文献 |
| OOS-09 | 10.1021/jacs.6c06590 | Out of Scope | None | correct_not_extracted | 主体系明确非水(无水添加); 仅含 MEA/吗啉对照, 需二次核查对照是否为水性, 潜在增补价值有限 |
| OOS-10 | 10.1016/j.fuel.2025.134712 | Out of Scope | None | correct_not_extracted | 标题即 non-aqueous amines; 研究对象为喷雾雾化工艺(闪沸/液滴), 无平衡态吸收性能; 双重边界外 |
| OOS-11 | 10.1039/d4gc05489j | Out of Scope | None | correct_not_extracted | 固体水凝胶吸附剂(amine carriers), 非水性胺溶液吸收; 属吸附/材料体系, 研究边界外 |
| OOS-12 | 10.1007/s43153-023-00348-5 | Out of Scope | None | correct_not_extracted | 氨基酸为盐形态(salt_flag); PDF 实为预印本(DOI 10.21203/rs.3.rs-1724921/v1)未经同行评审; DEA/ARG 均不在白名单 |
| OOS-13 | 10.25130/tjes.31.1.22 | Out of Scope | None | correct_not_extracted | 深共熔溶剂(DES)体系=边界外; 文中 MEA 仅作传质系数对照(0.152 mol/bar·L·min), 无浓度/CO2分压/loading, 不可入库 |
| OOS-PROC-14 | 10.1021/acs.iecr.1c04123 | Out of Scope | None | correct_not_extracted | 1 M PZ/MEA/MDEA/AMP blends; mol/L without density; recipe cannot close |
| OOS-PROC-15 | 10.1155/2022/6278342 | Out of Scope | None | correct_not_extracted | 20 wt% MEA VLE only in figures; data embargo; no table |
| OOS-PROC-16 | 10.1021/acs.iecr.4c03980 | Out of Scope | None | correct_not_extracted | iron solubility in MEA; no amine absorption performance data |
| OOS-PROC-17 | 10.1016/j.ces.2017.02.036 | Out of Scope | None | correct_not_extracted | 2-5 M amine blends; no wt%/density; recipe cannot close |
| INC-18 | 10.1016/j.ijggc.2016.12.018 | Insufficient Evidence | L3 | correct_downgrade_L3 | actual batch record missing required field(s): test_initial_loading;llm_snapshot_unverified;missing_initial_loading;required_evidence_unknown_or_assumed |
| INC-19 | 10.1021/acs.iecr.9b00552 | Insufficient Evidence | L3 | correct_downgrade_L3 | actual batch record missing required field(s): test_temperature_K;test_co2_vol_pct;test_initial_loading;metric_semantics_downgrade |
| INC-20 | 10.1021/je00005a025 | Insufficient Evidence | L3 | correct_downgrade_L3 | actual batch record missing required field(s): test_co2_vol_pct;test_initial_loading;llm_snapshot_unverified;missing_co2_vol_pct |
| SIM-21 | 10.1016/j.ces.2026.124685 | Model-derived | L3 | correct_model_L3 | actual simulation record from a historical batch; must stay L3 |
| SIM-22 | 10.1016/j.seppur.2026.139992 | Model-derived | L3 | correct_model_L3 | actual simulation record from a historical batch; must stay L3 |
| BND-01 | 10.1021/je00005a025 | Boundary | L3 | correct_boundary_kept_L3 | VLE point outside the 40 C / <=180 kPa profile (T=313.15 K, P_CO2=208.5 kPa); valid data must remain available as L3 |
| BND-02 | 10.1021/je00005a025 | Boundary | L3 | correct_boundary_kept_L3 | VLE point outside the 40 C / <=180 kPa profile (T=313.15 K, P_CO2=455.0 kPa); valid data must remain available as L3 |
| BND-03 | 10.1021/je00005a025 | Boundary | L3 | correct_boundary_kept_L3 | VLE point outside the 40 C / <=180 kPa profile (T=313.15 K, P_CO2=834.0 kPa); valid data must remain available as L3 |
| BND-04 | 10.1021/je00005a025 | Boundary | L3 | correct_boundary_kept_L3 | VLE point outside the 40 C / <=180 kPa profile (T=313.15 K, P_CO2=1241.0 kPa); valid data must remain available as L3 |
| BND-05 | 10.1021/je00005a025 | Boundary | L3 | correct_boundary_kept_L3 | VLE point outside the 40 C / <=180 kPa profile (T=313.15 K, P_CO2=1593.0 kPa); valid data must remain available as L3 |
| MODEL-28 | 10.1016/j.ces.2026.124685 | Model-derived | L3 | correct_model_L3 | simulation/modeling paper; not experimental L2 data |

`Insufficient Evidence` allows L3 as a reference but flags L2 as false accept.
`Out of Scope`/`Duplicate`/`Negative` allow no accepted record.
`Model-derived` allows L3 but not L2.
`Boundary` requires the candidate to remain available; L4 or absence is a false reject, L2 is over-acceptance.
