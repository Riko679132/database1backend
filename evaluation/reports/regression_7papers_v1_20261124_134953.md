# 回归评估报告：regression_7papers_v1

- 时间：2026-11-24T13:49:53+0800
- 评估集：`D:\database1\evaluation\eval_set_v1.json`（38 条，7 篇）
- 候选：`D:\database1\extractions\batch_20261124_134842`
- 标签说明：Regression baseline only; human_verified=false for every sample.
- 模型：deepseek-chat
- Prompt SHA-256：1045cb521aa24d47, 2a60ed745e88cf9d, 2b1d4697b6bc20ed, 6d1495a64b3980d2, 7eaa5b54cf631dd2, ac9a7f47ec501614, feaef2c8a1569c53

## 总览

| 指标 | 值 |
|---|---|
| 覆盖率 | 4/38 |
| 字段完整率 | 70.7% |
| 数值容忍内一致率 | 56.1% |
| 配方闭合 | {'complete': 4} |
| QC 结果 | {'L3': 4, 'no_match': 34} |
| L2 被错误降级/拒收 | 38 |
| 候选多余记录 | 1 |

## 分字段

| 字段 | 应有 | 已填 | 完整率 | 容忍内 | 一致率 | 缺失 | 超差 |
|---|---:|---:|---:|---:|---:|---:|---:|
| CO2 分压 kPa | 4 | 4 | 100.0% | 3 | 75.0% | 0 | 1 |
| CO2 vol% | 4 | 0 | 0.0% | 0 | 0.0% | 4 | 0 |
| 初始负载 | 4 | 0 | 0.0% | 0 | 0.0% | 4 | 0 |
| 温度 K | 4 | 4 | 100.0% | 4 | 100.0% | 0 | 0 |
| 总压 kPa | 4 | 0 | 0.0% | 0 | 0.0% | 4 | 0 |
| rich loading | 4 | 4 | 100.0% | 2 | 50.0% | 0 | 2 |
| performance.equilibrium_loading | 4 | 4 | 100.0% | 2 | 50.0% | 0 | 2 |
| 总胺 wt% | 4 | 4 | 100.0% | 4 | 100.0% | 0 | 0 |
| 水 wt% | 4 | 4 | 100.0% | 4 | 100.0% | 0 | 0 |
| 胺 A wt% | 4 | 4 | 100.0% | 3 | 75.0% | 0 | 1 |
| 胺 B wt% | 1 | 1 | 100.0% | 1 | 100.0% | 0 | 0 |

## 分论文

| DOI | 应有 | 匹配 | 容忍内字段 | 字段数 |
|---|---:|---:|---:|---:|
| 10.1016/j.apenergy.2016.03.043 | 4 | 0 | 0 | 0 |
| 10.1016/j.ijggc.2016.12.018 | 1 | 0 | 0 | 0 |
| 10.1016/j.jece.2024.112664 | 3 | 0 | 0 | 0 |
| 10.1021/acs.iecr.9b00552 | 1 | 0 | 0 | 0 |
| 10.1021/ie400825u | 1 | 0 | 0 | 0 |
| 10.1021/je00005a025 | 27 | 4 | 23 | 41 |
| 10.1039/d6gc02196d | 1 | 0 | 0 | 0 |

## 失败样本

- `31` 10.1021/je00005a025 qc=L3 score=4.0 missing=['conditions.co2_vol_pct', 'conditions.total_pressure_kPa', 'conditions.initial_loading'] outside=[]
- `32` 10.1021/je00005a025 qc=L3 score=5.138 missing=['conditions.co2_vol_pct', 'conditions.total_pressure_kPa', 'conditions.initial_loading'] outside=['loadings.rich', 'performance.equilibrium_loading']
- `33` 10.1021/je00005a025 qc=L3 score=24.719 missing=['conditions.co2_vol_pct', 'conditions.total_pressure_kPa', 'conditions.initial_loading'] outside=['recipe.wt_a', 'conditions.co2_partial_kPa', 'loadings.rich', 'performance.equilibrium_loading']
- `37` 10.1021/je00005a025 qc=L3 score=4.0 missing=['conditions.co2_vol_pct', 'conditions.total_pressure_kPa', 'conditions.initial_loading'] outside=[]
- `3` 10.1039/d6gc02196d qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.regeneration_efficiency', 'performance.regeneration_heat'] outside=[]
- `24` 10.1016/j.jece.2024.112664 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.cyclic_capacity', 'performance.regeneration_efficiency', 'performance.initial_absorption_rate', 'performance.initial_desorption_rate'] outside=[]
- `25` 10.1016/j.jece.2024.112664 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.cyclic_capacity', 'performance.regeneration_efficiency', 'performance.initial_absorption_rate', 'performance.initial_desorption_rate'] outside=[]
- `26` 10.1016/j.jece.2024.112664 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.cyclic_capacity', 'performance.regeneration_efficiency', 'performance.initial_absorption_rate', 'performance.initial_desorption_rate'] outside=[]
- `27` 10.1016/j.apenergy.2016.03.043 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean'] outside=[]
- `28` 10.1016/j.apenergy.2016.03.043 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean'] outside=[]
- `29` 10.1016/j.apenergy.2016.03.043 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean'] outside=[]
- `30` 10.1016/j.apenergy.2016.03.043 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean'] outside=[]
- `34` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
- `35` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
- `36` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
- `38` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
- `39` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
- `40` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
- `41` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
- `42` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
- `43` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
- `44` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
- `45` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
- `46` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
- `47` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
- `48` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
- `49` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
- `50` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
- `51` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
- `52` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
- `53` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
- `54` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
- `55` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
- `56` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
- `57` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
- `58` 10.1016/j.ijggc.2016.12.018 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.cyclic_capacity', 'performance.regeneration_efficiency'] outside=[]
- `59` 10.1021/ie400825u qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.absorption_rate_volumetric', 'performance.absorption_amount_volumetric', 'performance.cyclic_capacity_volumetric', 'performance.pka'] outside=[]
- `60` 10.1021/acs.iecr.9b00552 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]

## 说明

- 本报告的比较对象是历史 L2 导出（human_verified=false），不是独立人工复核结果。
- 字段完整率只统计标准答案中非空字段；不能用推测值提高该指标。
- 数值容忍按字段设置：温度 ±0.1 K、CO2 vol% ±0.5、压力 ±1%/±1 kPa、负载 ±0.01、wt% ±0.2，性能默认 ±2%。
- 38 条全为 L2 正样本，因此 false_accept 需要额外的负样本集才能统计。
- 候选多余记录未计入完整率，但可能表示过度抽取；需要结合论文边界人工复核。
