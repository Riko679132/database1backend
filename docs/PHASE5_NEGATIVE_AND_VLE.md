# Phase 5 负样本扩充与 VLE 泛化

## 负样本集 v2

由 `evaluation/build_negative_set.py` 生成，`evaluation/negative_set_v1.json` 为当前文件（版本字段 `v2`）。在 Phase 4 的 18 条基础上新增 10 条真实困难样本：

| 类别 | 数量 | 来源 | 判定 |
|---|---:|---|---|
| 信息不足 | 3 | 最终批次 `valid_incomplete.jsonl`（ijggc、iecr.9b00552） | 缺必填字段；L3 可接受，L2 为 false accept |
| 模型/仿真 | 2 | 历史批次 `20261027_04/05` 的真实 simulation 记录 | 只能 L3；L2 为 false accept |
| 边界 VLE | 5 | je00005a025 高压（208.5–1241 kPa）或 333 K 点 | 不得拒收；L3 可接受，缺失/L4 为 false reject |
| 原有 | 18 | Phase 4 | 见 `negative_eval.md` |
| **合计** | **28** | | |

标签定义：

- `Negative` / `Out of Scope` / `Duplicate`：任何 L2/L3 接受都是 false accept；
- `Insufficient Evidence`：数据真实但证据不足；L2 false accept，L3 可接受；
- `Model-derived`：仿真/模型输出；L2 false accept，L3 可接受；
- `Boundary`：超出既有 VLE profile 范围的有效数据；缺失或 L4 是 false reject，L3 可接受，L2 记为 over-acceptance 但不计 false reject；
- `Pending Review`：未人工判定，排除出 FAR。

### 评估结果

命令：

```powershell
python evaluation/evaluate_negative.py `
  --candidate extractions/batch_20261124_145027 `
  --candidate extractions/20261027_04 `
  --candidate extractions/20261027_05
```

- 样本 28；有候选记录 18；
- 结果：`correct_downgrade_L3` 9、`correct_reject_L4` 1、`correct_not_extracted` 10、`correct_model_L3` 3、`correct_boundary_kept_L3` 5；
- false accept L2：0；false accept L2/L3：0；
- boundary false reject：0；boundary kept as L2：0；
- FAR（L2，全部负样本）：0.0%；有候选分母：0.0%。

### 指标与分母

`evaluation/evaluate_metrics.py`，报告 `evaluation/reports/comprehensive_metrics.md`：

| 视角 | TP | FN | FP | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| 接受级（匹配正样本且保持 L2） | 38 | 0 | 0 | 100% | 100% | 1.000 |
| 严格字段级（所有字段齐全且在容差内） | 33 | 5 | 0 | 100% | 86.8% | 0.930 |

严格失败 5 条：3 条 jece 记录缺 `co2_partial_kPa`（表 3 未给总压，按要求保持 null）；1 条 d6gc 缺总压/lean/部分指标；1 条 iecr.9b00552 缺体积基指标。这些是信息不足，不是错误。

注意：38 条正样本来自 7 篇论文，28 条负样本含 10 条无候选记录，标签未经人工核验；上述指标为初步结果，不能外推为总体准确率。

## VLE profile 泛化

通用算法与论文 profile 分离：

- 通用层：`server/vle_table_parser.py` 的坐标分行、列分配、表头检测、单位换算、行过滤；
- profile 层：页面、表号、列 x 坐标、单位、温度/压力条件、行筛选、配方证据 regex；
- 目标论文的 40 °C / 180 kPa / 0.5 L 常量只存在于 `PROFILES["10.1021/je00005a025"]`，无 profile 时 `needs_profile=true` 且选择 0 点。

命令：`python evaluation/test_vle_profiles.py`，报告 `evaluation/reports/vle_generalization_test.md`。

| 论文 | 结构 | 原始数据点 | 成功提取 | 漏提 | 重复 | 错误关联 |
|---|---|---:|---:|---:|---:|---:|
| je00005a025 | 多栏并列、跨页续表 | 181 | 27（40 °C、≤180 kPa） | 0（目标范围） | 0 | 0 |
| jece.2024.112664 | 纵向行、bar 单位、多行单元格 | 3 行（2 条文献对比） | 1（This work） | 0 | 0 | 0 |
| ijggc.2016.12.018 | 嵌套负载单位（mol/kg 与 mol/mol） | 2 行 | 2（VLE mol/mol） | 0 | 0 | 0 |

关键校验：

- jece：`0.15 bar → 15.0 kPa`；文献行 `[24]`、`[25]` 被 `source_filter` 跳过；未把 180 kPa/40 °C 带入；
- ijggc：只选 VLE mol/mol 列（0.52 / 0.26），未误取 mol/kg 列（2.61 / 1.27）；rich/lean 正确；
- 三篇都记录 `data_rows / points / skipped / duplicates / wrong_associations`。

限制：jece/ijggc 的 profile 是本阶段新增的结构配置，未用于修改通用算法；这不是“新论文零配置自动解析”的证明。当前通用算法仍要求表头含 `p/kPa + loading` 或由 profile 声明列结构。
