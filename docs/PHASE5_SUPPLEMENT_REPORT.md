# Phase 5 补充验收：水蒸气校验与证据溯源

日期：2026-11-24。未修改数据库 schema，未写入主库；主库仍为 `test=63`、`performance=73`、`source=17`、`qc_record=0`。

## 一、修改前的具体局限

### 1. 水蒸气校验

修改前只有 [server/reasoning.py](file:///D:/database1/server/reasoning.py) 中的 `R-DET-05`：

```
P_CO2 <= P_total
```

以及 normalize 中的旧派生：

```
co2_partial_kPa = co2_vol_pct / 100 * total_pressure_kPa
```

问题是：

- 没有 `gas_basis`（湿基/干基/未知），旧派生实际上默认把体积分数当湿基；
- 没有 `p_h2o_kPa`、`y_h2o`、`water_activity` 字段；
- 干基组成 + P_H2O 未知时，仍可能用总压直接派生 P_CO2；
- 没有 `P_CO2 + P_H2O <= P_total`、组分和 > 总压、湿/干基分压不一致检查；
- 没有纯水饱和蒸气压的参数来源和适用温度范围约束。

### 2. excerpt / human_verified

- `source` 表没有 `excerpt` 字段；
- `source_location.excerpt_path` 存在，但 `import_jsonl.py` 只读取 JSONL 顶层的 `source.excerpt_path`，而 B 从未写这个键，所以绝大多数为 NULL（主库 63 条中只有 1 条旧 `.txt` 摘录）；
- 快照中已有 `source.excerpt`，但没有稳定的 per-record sidecar/record_id；
- `qc_record` 表存在且 `human_verified DEFAULT 0`，但 `import_jsonl.py` 从不插入 qc_record，主库 0 行；
- 导出没有带 `excerpt_path` / `human_verified`。

## 二、水蒸气分层校验

新增 [server/gas_phase.py](file:///D:/database1/server/gas_phase.py)，并在 [server/reasoning.py](file:///D:/database1/server/reasoning.py) 增加 `R-DET-06`。

| 情况 | 条件 | 处理 | 状态 |
|---|---|---|---|
| A 显式 P_H2O | 论文给 P_H2O，可能还给 P_CO2/P_total | 用原文值，检查 `P_CO2+P_H2O<=P_total` | `assessed` / `anomaly` |
| B 湿基 | 明确湿基 y_CO2 + P_total | `P_CO2=y_CO2,wet*P_total`；P_H2O 未知时水蒸气检查 `not_assessable` | `derived_wet_basis` |
| C 干基 + P_H2O | 明确干基 y_CO2、P_H2O、P_total | `P_CO2=y_CO2,dry*(P_total-P_H2O)` | `derived_dry_basis_with_p_h2o` |
| D 干基缺 P_H2O | 明确干基，但没有 P_H2O | 不生成 P_CO2；不以总压代替干气总压 | `blocked_dry_basis_missing_p_h2o` |
| E 无信息/基未知 | 没有 P_H2O/水活度/基 | 只做 `0<=P_CO2<=P_total`；水蒸气检查 `not_assessable` | `assessed` / `blocked_basis_unknown` |
| 异常 | P_CO2>P_total；组分和>总压；湿/干基分压不一致 | L2→L3，不静默改值 | `anomaly` |

说明：

- 缺失水蒸气信息不会拒收整条记录，只记 `not_assessable`。
- 干基缺 P_H2O 时，`co2_partial_kPa` 保持 null；如果论文另外直接报告 P_CO2，则保留原值，不覆盖。
- `P_CO2+P_H2O>P_total`、`P_CO2>P_total` 由一致性门控降为 L3，不进入 L4。
- 试剂体系未知时，不假定湿基，不生成 P_CO2。

### P_H2O 计算边界

纯水饱和蒸气压在 [server/gas_phase.py](file:///D:/database1/server/gas_phase.py) 中实现：

```
log10(P/mmHg) = 8.07131 - 1730.63/(233.426 + T/°C)
P/kPa = P/mmHg * 0.133322387415
```

- 来源：NIST Chemistry WebBook，Antoine 方程，https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Mask=4&Type=ANTOINE；
- 适用温度：1–100 °C（保守下界；NIST 表覆盖更宽）；
- 版本：`nist-antoine-water-1-100c`；
- 超范围返回 `out_of_range`，不计算。

胺溶液：

- 只有论文明确给出水活度 `a_w` 时才计算 `P_H2O = a_w * P_sat(T)`；
- 没有水活度/验证过的热力学模型时，`P_H2O` 保持未知；
- 不把纯水饱和蒸气压当作胺溶液上方的实际水蒸气分压。

### 水蒸气测试结果

命令：`python evaluation/test_water_vapor.py`，报告 [water_vapor_test.md](file:///D:/database1/evaluation/reports/water_vapor_test.md)。

- A 显式 P_H2O：pass，L2 保持；
- B 湿基：P_CO2=15.19875 kPa；
- C 干基 + P_H2O：P_CO2=14.08875 kPa；
- D 干基缺 P_H2O：`co2_partial_kPa=null`，状态 `blocked_dry_basis_missing_p_h2o`；
- E 无信息：水蒸气 `not_assessable`，L2 保持，不拒收；
- F 基未知且无 P_CO2：不推导，状态 `blocked_basis_unknown`；
- G P_CO2>P_total：L2→L3；
- H 组分和>总压：L2→L3；
- I 湿基分压不一致：L2→L3；
- 纯水 100 °C ≈101.34 kPa、25 °C ≈3.16 kPa；400 K 超范围；
- 无水的 63 条真实数据库记录扫描：0 个异常，10 条 `not_assessable`、37 条 `assessed`、16 条 `blocked_basis_unknown`，没有误拒收。

当前语料中没有一篇论文明确给出 P_H2O / 湿基或干基组成，因此 A–E 是代码级真实路径的 fixture；真实库扫描用于验证“缺信息不拒收”。下一篇含明确气相组成的论文可用于补充真实案例。

## 三、source.excerpt 与 sidecar

### 新记录

B 在 [server/tasks.py](file:///D:/database1/server/tasks.py) 写快照后，为每条记录生成：

- 稳定 `record_id`；
- `extractions/<batch>/raw/excerpts/<record_id>.json`；
- 批次级 `excerpt_index.json`；
- `source.excerpt_path`（相对项目根）；
- `source.excerpt_sha256`；
- 快照中的 `record_id`、sidecar 中的 `snapshot_path/snapshot_sha256`。

sidecar 包含：原文 excerpt、loc_type/loc_label、字段值/证据类型、多个 `references`、gas_phase、creation time、`human_verified=false`。

`import_jsonl.py` 现在：

- 把 `source.excerpt_path` 写入 `source_location.excerpt_path`；
- `source_location` 去重键加入 excerpt_path，避免同一表/配方多行记录共享一个摘录；
- 旧行 excerpt_path 为空且未被 test 引用时才补写，避免把新摘录挂到旧记录上；
- 每条 test 插入 `qc_record`，`human_verified=0`、reviewer/review_time 为 NULL。

### 旧记录

新增 [tools/trace_excerpt.py](file:///D:/database1/tools/trace_excerpt.py)，只读解析：

1. `source_location.excerpt_path` 是 JSON sidecar → 直接读取并校验 excerpt SHA；
2. 旧 `.txt` 摘录 → 作为 `legacy_text` 读取；
3. 否则读 `test.raw_data_path` 快照：
   - Phase 2 的 `records[]` 按 record_id/字段匹配；
   - 旧 `whitelist_rows` / `raw_text_lines` 匹配行；
   - 旧 `tables` 的 p/α 行匹配；
4. 没有快照的旧 L3/simulation → 回退到 `extractions/<batch_id>/raw_agent.jsonl` 等文件按字段匹配；
5. sidecar 缺失/损坏会明确 warning，并回退快照，不静默丢失。

### 溯源测试结果

命令：`python evaluation/test_provenance.py`，报告 [provenance_test.md](file:///D:/database1/evaluation/reports/provenance_test.md)。

- 临时库导入 8 条 B-flow 记录：8 条 test、8 条 qc_record、8 条 source_location.excerpt_path；
- 8 条 sidecar 哈希与快照哈希一致；
- 同一论文 8 条记录 excerpt/record_id 不串行；
- 8 条 test → sidecar → excerpt 全部可解析；
- 数据库备份副本重新加载后仍可解析；
- 篡改 sidecar → 报 `hash_mismatch`，回退快照；
- 删除 sidecar → 报 `missing`，回退快照；
- 主库 63 条记录：**63/63 可定位 excerpt**：37 条快照、25 条旧批次 JSONL、1 条旧 `.txt` sidecar（无哈希，按 `legacy_text` 读取，属于旧格式）；38/38 L2 全部可定位；
- 导出保留 `excerpt_path`、`human_verified`、`reviewer`、`review_time` 字段。

主库未写入：`excerpt_path` 仍只有 1/63，`qc_record` 仍 0 行；这是“不写主库”的边界。

补充回填工具 [tools/backfill_excerpt_path.py](file:///D:/database1/tools/backfill_excerpt_path.py)：

- 默认 dry-run；主库 dry-run 显示 62 条无 excerpt_path，59 条可解析、3 条共享旧 location 不能直接绑定；
- 在主库副本上 `--apply` 实测：新增 59 个 sidecar、`source_location.excerpt_path` 从 1 增至 60；主库 SHA-256 前后一致；
- 3 条共享旧 location 仍通过快照/批次 JSONL 可追溯，未自动拆分；

## 四、qc_record.human_verified

- schema 已存在：`qc_record.qc_id/test_id/qc_level/qc_reason/reviewer/review_time/human_verified DEFAULT 0`；
- 新导入：`import_jsonl.py` 每条 test 创建 qc_record，`human_verified=0`，reviewer/review_time NULL；
- 主库旧 63 条：qc_record 0 行，`trace_excerpt` 报 `not_recorded`，不伪造 0/1；
- 回填工具：[tools/backfill_qc_record.py](file:///D:/database1/tools/backfill_qc_record.py)，默认 dry-run，`--apply` 只插入 0，不标记已核验；
- 人工核验接口：[tools/mark_human_verified.py](file:///D:/database1/tools/mark_human_verified.py)，默认 dry-run；`--apply` 需要 reviewer+basis，更新 qc_record 并写 `data/control/human_review/test_<id>.json`；
- 临时库测试：回填 8 条全部 human_verified=0；人工核验接口测试后 1 条变为 1，review 文件存在；
- 主库 38 条 L2 **没有**人工核验，未被标记为已核验。

## 五、回归与 postcheck

| 测试 | 结果 |
|---|---|
| 水蒸气专项 | PASS（A–I + 纯水 + 水活度 + 真实库 63 条扫描） |
| 溯源专项 | PASS（8 条临时库 + 63/63 主库定位 + 备份/损坏/缺失/回填/导出） |
| VLE 泛化 | PASS（27/27、1/1、2/2） |
| 38 条 L2 回归 | 38/38，完整率/一致率 97.25%，0 false reject |
| 推理链五案例 | PASS（含新增 R-DET-06） |
| rate / metric 单元测试 | 15/15、5/5 |
| postcheck | 七项全 PASS |
| 主库计数 | test 63、performance 73、source 17、qc_record 0、L2 38（未变） |

## 六、仍未解决

1. **主库旧数据未迁移**：excerpt_path 1/63、qc_record 0/63。原因是本轮不写主库；`trace_excerpt` 已能通过快照/批次 JSONL 定位全部 63 条，但直接字段仍为空。需要用户授权后执行回填。
2. **旧快照不是 per-record**：25 条 L3/simulation 通过 `batch_id + raw_agent.jsonl` 字段匹配定位，存在极小概率同体系重复记录歧义；当前 63 条实测全部唯一匹配。
3. **真实水蒸气论文样本缺失**：当前 29 篇 PDF 中没有明确给出 P_H2O / 湿基 / 干基组成的在范围论文；A–E 为代码级 fixture，真实库只验证了“无信息不拒收”。下一批应优先补一篇明确气相组成的论文。
4. **水活度模型**：只实现了“论文给 a_w”的乘法；未实现任何电解质/活度系数模型，也未用纯水饱和蒸气压替代溶液。
5. **字段不落主表**：`gas_basis/p_h2o_kPa/y_h2o/water_activity` 在 JSONL/快照/sidecar 中，数据库 schema 无对应列；按要求不改 schema。
6. **source_location 一 location 一 excerpt_path**：新去重键已避免多记录共享，但旧共享 location 61 仍是历史状态；未迁移。
7. **人工核验 UI/流程**：只有 CLI 接口，未接入控制台页面；38 条 L2 仍 0 人工核验。

## 七、结论

- 水蒸气校验已从单一 `P_CO2<=P_total` 扩展为显式 P_H2O、湿基、干基+P_H2O、干基缺 P_H2O、无信息五层；缺信息不拒收，干基缺 P_H2O 不生成 P_CO2。
- 只有纯水/明确水活度时才计算 P_H2O；胺溶液无活度/模型时保持未知。
- 新记录可通过 `test.location_id → source_location.excerpt_path → sidecar → snapshot` 定位原文；旧记录可通过快照或批次 JSONL 定位，当前 63/63 实测可定位。
- `qc_record.human_verified` 已在新导入中初始化为 0；旧记录未写入，未虚构核验。
- 38 条 L2、VLE、postcheck 均未回归。
