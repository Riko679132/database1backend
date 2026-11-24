# Phase 5 专家推理链路

## 实际调用链

```
论文证据（正文/表格/上下文/SI）
  → skill_router 按关键词选择最多 4 个知识模块（记录 SHA-256）
  → LLM 提出候选记录 + evidence 提示
  → 确定性层：normalize / units / condition / VLE / reference profiles
  → provenance 证据分类与机器核验
  → reasoning 规则轨迹 + 一致性门控
  → decide_qc 输出 L1/L2/L3/L4（定义未改）
  → validate.py 唯一入闸门
```

知识模块不是只放在磁盘上：`skill_router.build_context()` 把选中模块截断后写入系统提示；`build_rule_context()` 再把该模块可用的规则 ID/名称写入提示。每次快照记录模块 ID、SHA-256、prompt 哈希和规则集哈希。

## 两类推理

### 确定性推导（程序计算）

| 规则 | 输入 | 公式 | 输出 |
|---|---|---|---|
| `R-DET-01` | `co2_vol_pct`, `total_pressure_kPa` | `P_CO2 = vol%/100 × P_total` | `co2_partial_kPa` |
| `R-DET-02` | `wt_a`, `wt_b`, `water_wt` | `total = wt_a+wt_b`；`water = 100−total`；闭合 ±0.1 | 配方闭合检查 |
| `R-DET-03` | 原始速率、原始单位 | 10^n / mmol / µmol / min / h / 胺或溶液基准 | 标准化速率 + 公式 |
| `R-DET-04` | 含 `mol solution` 或未知基准 | 不给密度/浓度时阻断 | `unit_normalization.status=blocked` |
| `R-DET-05` | `P_CO2`, `P_total` | `P_CO2 ≤ P_total` | 压力一致性 |
| `R-DET-06` | `gas_basis`, `P_H2O`, `y_H2O`, `water_activity` | 湿基：`y_wet·P_total`；干基：`y_dry·(P_total−P_H2O)`；干基缺 P_H2O → blocked | 水蒸气/干湿基校验 |

### 专家经验推断（LLM 候选 + 规则/证据检查）

| 规则 | 场景 | 处理 |
|---|---|---|
| `R-EXP-01` | 方法句明确 "fresh solution"、"pure CO2"、"atmospheric pressure" | 作为 `Contextual` 候选，仍须通过确定性与证据校验 |
| `R-EXP-02` | 专业默认假设 | 标 `Assumed`，必填字段不得进入 L2 |
| `R-XSEC-01` | 多栏/纵向 VLE 表 | 按列组/坐标关联行，保留原始行 |
| `R-XSEC-02` | 参比行散落在表/方法/结果 | 所有 profile 锚点命中才产出 |
| `R-XSEC-03` | 工况只写在方法段 | 只补缺失字段并记录方法证据 |
| `R-INF-01` | 必填字段仍为空 | 保持 null，L3/incomplete |

经验推断不会被包装成确定性结果：`Assumed` 不得升级为 L2；`Unknown` 保持 null；`Derived` 必须带公式和输入。

## 轨迹结构

快照 `records[].reasoning`：

```json
{
  "trace_version": "phase5-1.0",
  "rule_set": {"rule_set_version": "phase5-1.0", "rule_count": 21, "sha256": "..."},
  "knowledge_modules": [{"id": "co2_equilibrium", "sha256": "..."}],
  "module_rules": ["R-DET-01", "R-DET-05", "R-XSEC-01"],
  "steps": [
    {
      "rule_id": "R-EVD-01",
      "category": "evidence",
      "evidence_type": "Explicit",
      "field": "temperature_K",
      "value": 313.15,
      "source": {"loc_type": "table", "loc_label": "Table 3", "excerpt": "..."},
      "result": "accepted"
    },
    {
      "rule_id": "R-DET-03",
      "category": "deterministic",
      "field": "performance.initial_absorption_rate",
      "formula": "value_std = 34.0 * 1e-05",
      "formula_inputs": {"unit_original": "10-5 mol CO2/mol·s", "basis": "mol_amine"},
      "output": {"value": 0.00034, "unit": "mol_CO2/(mol_amine*s)"},
      "result": "pass"
    }
  ],
  "summary": {"steps": 12, "by_evidence": {"Explicit": 6, "Derived": 2}, "unknown_fields": []}
}
```

一致性门控只处理明确矛盾：分压与 `vol% × 总压` 不一致、质量不闭合、`P_CO2 > P_total`、仿真被标成 L2、Assumed 必填字段被升到 L2。命中才降到 L3 并追加 `reasoning_gate:*`；不会为提高指标而放宽或收紧分级定义。

## 五类案例实测

命令：`python evaluation/test_reasoning_chain.py`，报告 `evaluation/reports/reasoning_chain_test.md`。

| 案例 | 论文 | 结果 | 关键证据 |
|---|---|---|---|
| 显式提取 | apenergy 2016 | PASS / L2 | `R-EVD-01`，Table 3 原文摘录 |
| 跨章节关联 | d6gc 2026 | PASS / L2 | `R-XSEC-02`，Table 4 + 方法/结果句 |
| 确定性计算 | jece 2024 | PASS / L2 | `R-DET-03`，34.0 × 1e-5 = 0.00034 |
| 经验/上下文推断 | ie400825 2013 | PASS / L2 | `R-XSEC-03` + `R-EXP-01`，101.325 kPa / 20% CO2 |
| 信息不足 | jece 2024 纵向表 | PASS / L3 | `R-INF-01` + `R-EVD-05`，`initial_loading=null` |

另跑 43 条现有批次记录的一致性门控：0 条触发、0 条降级。

## 水蒸气/干湿基补充

- 湿基：`P_CO2 = y_CO2,wet × P_total`；即使 P_H2O 未知，也只做 `P_CO2 ≤ P_total`，水蒸气检查记 `not_assessable`。
- 干基且 P_H2O 已知：`P_CO2 = y_CO2,dry × (P_total − P_H2O)`。
- 干基且 P_H2O 未知：不生成 P_CO2，状态 `blocked_dry_basis_missing_p_h2o`，不拒收整条记录。
- 基未知：不假定湿基，不生成 P_CO2，状态 `blocked_basis_unknown`。
- 纯水饱和蒸气压只用于纯水，参数来源 NIST Antoine（1–100 °C，版本 `nist-antoine-water-1-100c`）；胺溶液必须给出水活度或经验证模型，否则 P_H2O 保持未知。
- `P_CO2 > P_total`、`P_CO2+P_H2O > P_total`、湿/干基分压不一致会把 L2 降到 L3，不静默改值。

## 限制

- 规则注册表只覆盖当前已实现的判断；不是通用推理引擎。
- 水蒸气校验在论文未给 `P_H2O(T)` 时标记 `not_evaluated`，没有用模型记忆补 Antoine 参数。
- 专家推断仍依赖 LLM 的证据提示；LLM 未给出的上下文不会被追溯补造。
- 规则来源文件在 `docs/PHASE5_RULE_CATALOG.md` 与 `server/rules.py` 中列出；新增规则必须先有知识来源和可执行实现。
