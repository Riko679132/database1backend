# 回归评估报告：historical_fixture

- 时间：2026-11-24T14:03:40+0800
- 评估集：`D:\database1\evaluation\eval_set_v1.json`（38 条，7 篇）
- 候选：`D:\database1\evaluation\historical_l2_candidate.jsonl`
- 标签说明：Regression baseline only; human_verified=false for every sample.
- 模型：未记录
- Prompt SHA-256：未记录

## 总览

| 指标 | 值 |
|---|---|
| 覆盖率 | 38/38 |
| 字段完整率 | 100.0% |
| 数值容忍内一致率 | 100.0% |
| 配方闭合 | {'complete': 38} |
| QC 结果 | {'L2': 38} |
| L2 被错误降级/拒收 | 0 |
| 候选多余记录 | 0 |

## 分字段

| 字段 | 应有 | 已填 | 完整率 | 容忍内 | 一致率 | 缺失 | 超差 |
|---|---:|---:|---:|---:|---:|---:|---:|
| CO2 分压 kPa | 37 | 37 | 100.0% | 37 | 100.0% | 0 | 0 |
| CO2 vol% | 38 | 38 | 100.0% | 38 | 100.0% | 0 | 0 |
| 初始负载 | 38 | 38 | 100.0% | 38 | 100.0% | 0 | 0 |
| 温度 K | 38 | 38 | 100.0% | 38 | 100.0% | 0 | 0 |
| 总压 kPa | 33 | 33 | 100.0% | 33 | 100.0% | 0 | 0 |
| lean loading | 4 | 4 | 100.0% | 4 | 100.0% | 0 | 0 |
| rich loading | 36 | 36 | 100.0% | 36 | 100.0% | 0 | 0 |
| performance.absorption_amount_volumetric | 1 | 1 | 100.0% | 1 | 100.0% | 0 | 0 |
| performance.absorption_rate_volumetric | 1 | 1 | 100.0% | 1 | 100.0% | 0 | 0 |
| performance.cyclic_capacity | 4 | 4 | 100.0% | 4 | 100.0% | 0 | 0 |
| performance.cyclic_capacity_volumetric | 1 | 1 | 100.0% | 1 | 100.0% | 0 | 0 |
| performance.equilibrium_loading | 28 | 28 | 100.0% | 28 | 100.0% | 0 | 0 |
| performance.initial_absorption_rate | 3 | 3 | 100.0% | 3 | 100.0% | 0 | 0 |
| performance.initial_desorption_rate | 3 | 3 | 100.0% | 3 | 100.0% | 0 | 0 |
| performance.pka | 1 | 1 | 100.0% | 1 | 100.0% | 0 | 0 |
| performance.regeneration_efficiency | 5 | 5 | 100.0% | 5 | 100.0% | 0 | 0 |
| performance.regeneration_heat | 1 | 1 | 100.0% | 1 | 100.0% | 0 | 0 |
| 总胺 wt% | 38 | 38 | 100.0% | 38 | 100.0% | 0 | 0 |
| 水 wt% | 38 | 38 | 100.0% | 38 | 100.0% | 0 | 0 |
| 胺 A wt% | 38 | 38 | 100.0% | 38 | 100.0% | 0 | 0 |
| 胺 B wt% | 14 | 14 | 100.0% | 14 | 100.0% | 0 | 0 |

## 分论文

| DOI | 应有 | 匹配 | 容忍内字段 | 字段数 |
|---|---:|---:|---:|---:|
| 10.1016/j.apenergy.2016.03.043 | 4 | 4 | 36 | 36 |
| 10.1016/j.ijggc.2016.12.018 | 1 | 1 | 12 | 12 |
| 10.1016/j.jece.2024.112664 | 3 | 3 | 39 | 39 |
| 10.1021/acs.iecr.9b00552 | 1 | 1 | 8 | 8 |
| 10.1021/ie400825u | 1 | 1 | 12 | 12 |
| 10.1021/je00005a025 | 27 | 27 | 284 | 284 |
| 10.1039/d6gc02196d | 1 | 1 | 9 | 9 |

## 失败样本

- 无

## 说明

- 本报告的比较对象是历史 L2 导出（human_verified=false），不是独立人工复核结果。
- 字段完整率只统计标准答案中非空字段；不能用推测值提高该指标。
- 数值容忍按字段设置：温度 ±0.1 K、CO2 vol% ±0.5、压力 ±1%/±1 kPa、负载 ±0.01、wt% ±0.2，性能默认 ±2%。
- 38 条全为 L2 正样本，因此 false_accept 需要额外的负样本集才能统计。
- 候选多余记录未计入完整率，但可能表示过度抽取；需要结合论文边界人工复核。
