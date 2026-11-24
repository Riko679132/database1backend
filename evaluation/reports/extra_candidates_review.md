# 多余候选记录人工判定表

- Batch: `D:/database1/extractions/batch_20261124_145027`
- Extras: 15

| DOI | amine | wt_a | wt_b | T (K) | P_CO2 | metrics | QC | label | reason |
|---|---|---:|---:|---:|---:|---|---|---|---|
| 10.1016/j.apenergy.2016.03.043 | MEA | 30.0 | None | 313.15 | None | {'regeneration_heat': -85.13} | L3 | Insufficient Evidence | regeneration_heat label but unit/sign indicate heat of absorption/reaction (kJ/mol), not regeneration heat |
| 10.1016/j.apenergy.2016.03.043 | MDEA | 30.0 | None | 313.15 | None | {'regeneration_heat': -52.51} | L3 | Insufficient Evidence | regeneration_heat label but unit/sign indicate heat of absorption/reaction (kJ/mol), not regeneration heat |
| 10.1016/j.apenergy.2016.03.043 | AMP | 30.0 | None | 313.15 | None | {'regeneration_heat': -80.91} | L3 | Insufficient Evidence | regeneration_heat label but unit/sign indicate heat of absorption/reaction (kJ/mol), not regeneration heat |
| 10.1016/j.apenergy.2016.03.043 | PZ | 30.0 | None | 313.15 | None | {'regeneration_heat': -80.58} | L3 | Insufficient Evidence | regeneration_heat label but unit/sign indicate heat of absorption/reaction (kJ/mol), not regeneration heat |
| 10.1021/ie400825u | MDEA | 30.0 | None | 313.15 | 101.325 | {'regeneration_heat': 58.5} | L3 | Insufficient Evidence | regeneration_heat label but unit/sign indicate heat of absorption/reaction (kJ/mol), not regeneration heat |
| 10.1016/j.ijggc.2016.12.018 | MEA | 30.0 | None | 353.15 | 1.0 | {'equilibrium_loading': 0.28} | L3 | Valid L3 | additional MEA VLE point at 353 K; missing total pressure/initial loading |
| 10.1021/acs.iecr.9b00552 | MEA | 30.0 | None | None | None | {'regeneration_heat': -83.24} | L3 | Insufficient Evidence | regeneration_heat label but unit/sign indicate heat of absorption/reaction (kJ/mol), not regeneration heat |
| 10.1021/acs.iecr.9b00552 | MEA | 30.0 | None | 313.15 | None | {'co2_removal_efficiency': 99.4} | L3 | Valid L3 | pilot CO2 removal efficiency; missing initial loading/complete conditions |
| 10.1021/je00005a025 | MDEA | 30.0 | None | 313.15 | 208.5 | {'equilibrium_loading': 0.919} | L3 | Valid L3 | VLE point outside the 40 C low-pressure target (high P or other temperature) |
| 10.1021/je00005a025 | MDEA | 30.0 | None | 313.15 | 455.0 | {'equilibrium_loading': 0.99} | L3 | Valid L3 | VLE point outside the 40 C low-pressure target (high P or other temperature) |
| 10.1021/je00005a025 | MDEA | 30.0 | None | 313.15 | 834.0 | {'equilibrium_loading': 1.016} | L3 | Valid L3 | VLE point outside the 40 C low-pressure target (high P or other temperature) |
| 10.1021/je00005a025 | MDEA | 30.0 | None | 313.15 | 1241.0 | {'equilibrium_loading': 1.065} | L3 | Valid L3 | VLE point outside the 40 C low-pressure target (high P or other temperature) |
| 10.1021/je00005a025 | MDEA | 30.0 | None | 313.15 | 1593.0 | {'equilibrium_loading': 1.082} | L3 | Valid L3 | VLE point outside the 40 C low-pressure target (high P or other temperature) |
| 10.1021/je00005a025 | MDEA | 30.0 | None | 313.15 | 1979.0 | {'equilibrium_loading': 1.108} | L3 | Valid L3 | VLE point outside the 40 C low-pressure target (high P or other temperature) |
| 10.1021/je00005a025 | MDEA | 30.0 | None | 333.15 | 1.1 | {'equilibrium_loading': 0.189} | L3 | Valid L3 | VLE point outside the 40 C low-pressure target (high P or other temperature) |

## 说明

- `Valid L3`：真实数据但不在 27 点 L2 目标选择内（高压/其他温度/缺失条件），不作为负样本。
- `Insufficient Evidence`：研究内容真实，但指标定义/单位/条件不足，不能作为 L2；L3 可作参考。
- `Duplicate`：同一 DOI 已有有效 L2，多出的不完整记录不应新增。
- `Out of Scope`：体系/浓度/单位边界外，任何接受都是 false accept。
- `Boundary`：超出既有 VLE profile 范围的有效数据；不得因超出范围而拒收，L3 可接受。
- `Pending Review`：尚未人工判定，排除在 false-accept 指标之外。
