# 回归评估报告：final_regression_v1

- 时间：2026-11-24T14:05:25+0800
- 评估集：`D:\database1\evaluation\eval_set_v1.json`（38 条，7 篇）
- 候选：`D:\database1\extractions\batch_20261124_140349`
- 标签说明：Regression baseline only; human_verified=false for every sample.
- 模型：deepseek-chat
- Prompt SHA-256：12e3d313f520f83c, 3266a089c752eece, 4884c196011a91b5, 4aa53b7436625cbe, 99867e826db5a40e, bea940ffc22d569e, c3069bdeec655b31

## 总览

| 指标 | 值 |
|---|---|
| 覆盖率 | 22/38 |
| 字段完整率 | 76.7% |
| 数值容忍内一致率 | 66.1% |
| 配方闭合 | {'complete': 22} |
| QC 结果 | {'L2': 10, 'L3': 12, 'no_match': 16} |
| L2 被错误降级/拒收 | 28 |
| 候选多余记录 | 8 |

## 分字段

| 字段 | 应有 | 已填 | 完整率 | 容忍内 | 一致率 | 缺失 | 超差 |
|---|---:|---:|---:|---:|---:|---:|---:|
| CO2 分压 kPa | 21 | 13 | 61.9% | 7 | 33.3% | 8 | 6 |
| CO2 vol% | 22 | 10 | 45.5% | 10 | 45.5% | 12 | 0 |
| 初始负载 | 22 | 10 | 45.5% | 10 | 45.5% | 12 | 0 |
| 温度 K | 22 | 22 | 100.0% | 22 | 100.0% | 0 | 0 |
| 总压 kPa | 18 | 4 | 22.2% | 4 | 22.2% | 14 | 0 |
| lean loading | 4 | 3 | 75.0% | 3 | 75.0% | 1 | 0 |
| rich loading | 21 | 21 | 100.0% | 15 | 71.4% | 0 | 6 |
| performance.absorption_amount_volumetric | 1 | 0 | 0.0% | 0 | 0.0% | 1 | 0 |
| performance.absorption_rate_volumetric | 1 | 0 | 0.0% | 0 | 0.0% | 1 | 0 |
| performance.cyclic_capacity | 4 | 3 | 75.0% | 3 | 75.0% | 1 | 0 |
| performance.cyclic_capacity_volumetric | 1 | 0 | 0.0% | 0 | 0.0% | 1 | 0 |
| performance.equilibrium_loading | 13 | 13 | 100.0% | 7 | 53.8% | 0 | 6 |
| performance.initial_absorption_rate | 3 | 3 | 100.0% | 0 | 0.0% | 0 | 3 |
| performance.initial_desorption_rate | 3 | 3 | 100.0% | 0 | 0.0% | 0 | 3 |
| performance.pka | 1 | 0 | 0.0% | 0 | 0.0% | 1 | 0 |
| performance.regeneration_efficiency | 4 | 3 | 75.0% | 3 | 75.0% | 1 | 0 |
| 总胺 wt% | 22 | 22 | 100.0% | 22 | 100.0% | 0 | 0 |
| 水 wt% | 22 | 22 | 100.0% | 22 | 100.0% | 0 | 0 |
| 胺 A wt% | 22 | 22 | 100.0% | 22 | 100.0% | 0 | 0 |

## 分论文

| DOI | 应有 | 匹配 | 容忍内字段 | 字段数 |
|---|---:|---:|---:|---:|
| 10.1016/j.apenergy.2016.03.043 | 4 | 4 | 32 | 36 |
| 10.1016/j.ijggc.2016.12.018 | 1 | 1 | 8 | 12 |
| 10.1016/j.jece.2024.112664 | 3 | 3 | 30 | 39 |
| 10.1021/acs.iecr.9b00552 | 1 | 1 | 8 | 8 |
| 10.1021/ie400825u | 1 | 1 | 6 | 12 |
| 10.1021/je00005a025 | 27 | 12 | 66 | 120 |
| 10.1039/d6gc02196d | 1 | 0 | 0 | 0 |

## 失败样本

- `24` 10.1016/j.jece.2024.112664 qc=L2 score=6.0 missing=['conditions.co2_partial_kPa'] outside=['performance.initial_absorption_rate', 'performance.initial_desorption_rate']
- `25` 10.1016/j.jece.2024.112664 qc=L2 score=6.0 missing=['conditions.co2_partial_kPa'] outside=['performance.initial_absorption_rate', 'performance.initial_desorption_rate']
- `26` 10.1016/j.jece.2024.112664 qc=L2 score=6.0 missing=['conditions.co2_partial_kPa'] outside=['performance.initial_absorption_rate', 'performance.initial_desorption_rate']
- `27` 10.1016/j.apenergy.2016.03.043 qc=L2 score=2.0 missing=['conditions.co2_partial_kPa'] outside=[]
- `28` 10.1016/j.apenergy.2016.03.043 qc=L2 score=2.0 missing=['conditions.co2_partial_kPa'] outside=[]
- `29` 10.1016/j.apenergy.2016.03.043 qc=L2 score=2.0 missing=['conditions.co2_partial_kPa'] outside=[]
- `30` 10.1016/j.apenergy.2016.03.043 qc=L2 score=2.0 missing=['conditions.co2_partial_kPa'] outside=[]
- `31` 10.1021/je00005a025 qc=L3 score=4.0 missing=['conditions.co2_vol_pct', 'conditions.total_pressure_kPa', 'conditions.initial_loading'] outside=[]
- `32` 10.1021/je00005a025 qc=L3 score=4.0 missing=['conditions.co2_vol_pct', 'conditions.total_pressure_kPa', 'conditions.initial_loading'] outside=[]
- `33` 10.1021/je00005a025 qc=L3 score=4.0 missing=['conditions.co2_vol_pct', 'conditions.total_pressure_kPa', 'conditions.initial_loading'] outside=[]
- `34` 10.1021/je00005a025 qc=L3 score=4.0 missing=['conditions.co2_vol_pct', 'conditions.total_pressure_kPa', 'conditions.initial_loading'] outside=[]
- `35` 10.1021/je00005a025 qc=L3 score=4.0 missing=['conditions.co2_vol_pct', 'conditions.total_pressure_kPa', 'conditions.initial_loading'] outside=[]
- `36` 10.1021/je00005a025 qc=L3 score=4.0 missing=['conditions.co2_vol_pct', 'conditions.total_pressure_kPa', 'conditions.initial_loading'] outside=[]
- `51` 10.1021/je00005a025 qc=L3 score=35.902 missing=['conditions.co2_vol_pct', 'conditions.total_pressure_kPa', 'conditions.initial_loading'] outside=['conditions.co2_partial_kPa', 'loadings.rich', 'performance.equilibrium_loading']
- `52` 10.1021/je00005a025 qc=L3 score=35.992 missing=['conditions.co2_vol_pct', 'conditions.total_pressure_kPa', 'conditions.initial_loading'] outside=['conditions.co2_partial_kPa', 'loadings.rich', 'performance.equilibrium_loading']
- `53` 10.1021/je00005a025 qc=L3 score=35.969 missing=['conditions.co2_vol_pct', 'conditions.total_pressure_kPa', 'conditions.initial_loading'] outside=['conditions.co2_partial_kPa', 'loadings.rich', 'performance.equilibrium_loading']
- `54` 10.1021/je00005a025 qc=L3 score=35.959 missing=['conditions.co2_vol_pct', 'conditions.total_pressure_kPa', 'conditions.initial_loading'] outside=['conditions.co2_partial_kPa', 'loadings.rich', 'performance.equilibrium_loading']
- `55` 10.1021/je00005a025 qc=L3 score=35.796 missing=['conditions.co2_vol_pct', 'conditions.total_pressure_kPa', 'conditions.initial_loading'] outside=['conditions.co2_partial_kPa', 'loadings.rich', 'performance.equilibrium_loading']
- `56` 10.1021/je00005a025 qc=L3 score=35.731 missing=['conditions.co2_vol_pct', 'conditions.total_pressure_kPa', 'conditions.initial_loading'] outside=['conditions.co2_partial_kPa', 'loadings.rich', 'performance.equilibrium_loading']
- `58` 10.1016/j.ijggc.2016.12.018 qc=L2 score=10.0 missing=['conditions.total_pressure_kPa', 'loadings.lean', 'performance.cyclic_capacity', 'performance.regeneration_efficiency'] outside=[]
- `59` 10.1021/ie400825u qc=L2 score=22.0 missing=['conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'performance.absorption_rate_volumetric', 'performance.absorption_amount_volumetric', 'performance.cyclic_capacity_volumetric', 'performance.pka'] outside=[]
- `3` 10.1039/d6gc02196d qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.regeneration_efficiency', 'performance.regeneration_heat'] outside=[]
- `37` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]
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
- `57` 10.1021/je00005a025 qc=None score=None missing=['recipe.wt_a', 'recipe.wt_b', 'recipe.water_wt', 'recipe.total_amine_wt', 'conditions.temperature_K', 'conditions.co2_vol_pct', 'conditions.co2_partial_kPa', 'conditions.total_pressure_kPa', 'conditions.initial_loading', 'loadings.rich', 'loadings.lean', 'performance.equilibrium_loading'] outside=[]

## 说明

- 本报告的比较对象是历史 L2 导出（human_verified=false），不是独立人工复核结果。
- 字段完整率只统计标准答案中非空字段；不能用推测值提高该指标。
- 数值容忍按字段设置：温度 ±0.1 K、CO2 vol% ±0.5、压力 ±1%/±1 kPa、负载 ±0.01、wt% ±0.2，性能默认 ±2%。
- 38 条全为 L2 正样本，因此 false_accept 需要额外的负样本集才能统计。
- 候选多余记录未计入完整率，但可能表示过度抽取；需要结合论文边界人工复核。
