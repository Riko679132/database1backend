# Phase 5 验收报告

日期：2026-11-24。水蒸气与溯源补充见 [PHASE5_SUPPLEMENT_REPORT.md](file:///D:/database1/docs/PHASE5_SUPPLEMENT_REPORT.md)。数据库未改动：`test=63`、`performance=73`、`source=17`、L2=38，`postcheck.py` 七项全 PASS。

## 一、交付物

| 交付 | 文件 |
|---|---|
| A→B manifest 规范 | `docs/PHASE5_MANIFEST.md`、`server/paper_manifest.py`、`tools/build_manifest.py` |
| manifest 测试 | `evaluation/test_manifest.py`、`evaluation/reports/manifest_test.md` |
| 推理链路说明 | `docs/PHASE5_REASONING.md`、`server/reasoning.py` |
| 规则清单 | `docs/PHASE5_RULE_CATALOG.md`、`server/rules.py`（21 条） |
| 推理案例测试 | `evaluation/test_reasoning_chain.py`、`evaluation/reports/reasoning_chain_test.md` |
| OCR 质量门控 | `docs/PHASE5_OCR_GATE.md`、`server/ocr_gate.py`、`scripts/pdf_to_text.py` |
| OCR 测试 | `evaluation/test_ocr_gate.py`、`evaluation/reports/ocr_gate_test.md` |
| 负样本扩充 | `evaluation/build_negative_set.py`、`negative_set_v1.json`（v2 标签） |
| 负样本报告 | `evaluation/reports/negative_eval.md` |
| P/R/F1 | `evaluation/evaluate_metrics.py`、`evaluation/reports/comprehensive_metrics.md` |
| VLE 泛化 | `server/vle_table_parser.py`、`evaluation/test_vle_profiles.py`、`evaluation/reports/vle_generalization_test.md` |
| B 流程集成 | `evaluation/test_b_flow_integration.py`、`evaluation/reports/b_flow_integration.md` |
| 全量回归 | `evaluation/reports/phase5_final_20261124_214812.md` |

## 二、实际测试结果

### 1. 38 条 L2 回归

```
coverage 38/38, completeness 97.25%, agreement 97.25%
QC: L2=38, false_reject_l2=0
```

字段完整率/一致率仍是 97.25%，未因 Phase 5 改动下降。严格字段级指标见下：33/38 全字段齐全且在容差内；5 条失败均为论文本身未给总压/部分指标，不是抽取错误。

### 2. 负样本与边界

`negative_set_v1.json`（v2 标签）共 28 条：Phase 4 的 18 条 + 新增 10 条（3 条实际信息不足、2 条历史 simulation、5 条边界 VLE）。

```
有候选 18 / 28
correct_downgrade_L3 9
correct_reject_L4 1
correct_not_extracted 10
correct_model_L3 3
correct_boundary_kept_L3 5
false accept L2 0; false accept any L2/L3 0
boundary false reject 0
FAR (all negatives) 0%; FAR (with candidate) 0%
```

边界 5 条（MDEA 208.5–1241 kPa、333 K）全部保留为 L3，没有因超出 profile 被拒收。

### 3. P/R/F1（初步，未人工核验）

| 视角 | TP | FN | FP | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|
| 接受级（匹配且 L2） | 38 | 0 | 0 | 100% | 100% | 1.000 |
| 严格字段级 | 33 | 5 | 0 | 100% | 86.8% | 0.930 |

严格失败：3 条 jece 缺 `co2_partial_kPa`（表 3 无总压，按要求 null）；1 条 d6gc 缺总压/lean/部分指标；1 条 iecr.9b00552 缺体积基指标。分母与范围见 `comprehensive_metrics.md`；正样本只有 7 篇，负样本含 10 条无候选记录，不能外推为总体准确率。

### 4. A→B manifest

- 29/29 本地 PDF 加载成功（29 stored、0 legacy）；
- SI 论文 `10.1021/acs.iecr.4c03980` 的 SI 文件/解析文本哈希一致；
- 篡改 PDF SHA → 拒绝；篡改 SI SHA → 拒绝；`present` DOI 空值 → 拒绝；
- 无 DOI PDF → `doi.status=missing`，允许处理；
- 空 manifest 目录 → `legacy_generated` 兼容，历史 PDF 不被阻断；
- B 集成测试：manifest 写入快照，`validate.py` 产出 8 条 valid，无数据库写入。

### 5. 专家推理链路

五类案例全部 PASS：

| 案例 | 论文 | 关键结果 |
|---|---|---|
| 显式提取 | apenergy 2016 | `R-EVD-01`，Table 3 原文摘录，L2 |
| 跨章节关联 | d6gc 2026 | `R-XSEC-02`，Table 4 + 方法/结果句，L2 |
| 确定性计算 | jece 2024 | `R-DET-03`，34.0 → 0.00034，公式/输入/输出齐全 |
| 经验/上下文推断 | ie400825 2013 | `R-XSEC-03` + `R-EXP-01`，101.325 kPa / 20% CO2，L2 |
| 信息不足 | jece 2024 纵向表 | `R-INF-01` + `R-EVD-05`，`initial_loading=null`，L3 |

另对 43 条现有记录跑一致性门控：0 条触发、0 条降级。快照 `records[].reasoning` 保存每一步的 rule_id、类别、证据类型、公式/输入/输出、原文位置与结果。

### 6. OCR 质量门控

| 样本 | 结果 |
|---|---|
| 真实扫描页 `known_scan.pdf` | pass，avg_conf 0.9679，冲突 0 |
| 真实文本页 `jece_p6.pdf` + 强制 OCR | pass，avg_conf 0.9928，冲突 0 |
| 退化扫描 `jece_blur.pdf` | fail，OCR 无文本/无置信度 |
| 冲突 fixture（30 vs 80 wt%） | review，concentration 冲突 |
| 低置信度 fixture（0.51/0.48） | review |

B 对 `fail` 页面：原生文本不足时停止并记 `ocr_review_required`；原生文本仍可用时继续但标 `parse_mode=ocr_review` 并写入快照。对 `review` 页面继续但标 `parse_mode=ocr_review`。

### 7. VLE 泛化

| 论文 | 结构 | 原始点 | 提取 | 漏提 | 重复 | 错误关联 |
|---|---|---:|---:|---:|---:|---:|
| je00005a025 | 多栏并列、跨页 | 181 | 27（40 °C、≤180 kPa） | 0 | 0 | 0 |
| jece.2024.112664 | 纵向行、bar 单位、多行单元格 | 3 行 | 1（This work；2 条文献行过滤） | 0 | 0 | 0 |
| ijggc.2016.12.018 | 嵌套 mol/kg 与 mol/mol | 2 行 | 2（VLE mol/mol） | 0 | 0 | 0 |

目标论文的 40 °C / 180 kPa / 0.5 L 常量未进入其他论文；无 profile 时 `needs_profile=true` 且选 0 点。

## 三、六个问题的直接回答

### 1. 专家推理链路是否真正贯通，而非仅增加了知识文件？

**是，已贯通到实际 B 流程，但不是通用推理引擎。** 证据：知识模块进入系统提示并记录 SHA；规则上下文进入提示；`tasks.py` 对每条记录执行确定性检查、一致性门控和 `trace_record`；快照保存规则轨迹；五类真实论文案例通过；43 条现有记录门控 0 误伤。限制：规则是当前 21 条可执行规则，不是任意论文的自动知识图谱；专家推断仍依赖 LLM 给出的证据提示。

### 2. 推理结论能否追溯到原文、公式或规则？

**重要科学字段可以。** 每条轨迹步骤含 `rule_id`、类别、证据类型、结果；显式/上下文步骤含 `loc_type/loc_label/excerpt`；推导步骤含公式、输入和输出；缺失字段保留 `R-INF-01`/`R-EVD-05`。限制：标题、作者等非科学字段不做逐步追踪；快照保存摘录但不保存整页图像坐标；`source.excerpt` 仍未落数据库主表（按要求没改 schema）。

### 3. OCR 是否具备自动质量门控能力？哪些仍需人工复核？

**具备 pass/review/fail 三档门控。** 正常页自动通过；低置信度、关键字段冲突、关键字段缺失进入 `review`；OCR 无文本/极低置信度进入 `fail`。仍需人工复核：低置信度或冲突页、化学下标/合并单元格/多栏表、模糊扫描件、OCR 能出字但表格结构仍需 word-grid 核对的页面。置信度不是校准概率，未做大规模真实扫描仪语料验证。

### 4. A→B 交接是否已稳定？

**格式和校验已稳定，A 侧自动写入尚未完成。** v1.0 manifest 覆盖 paper_id/DOI/PDF/SI/筛选/元数据/下载状态；哈希不一致 fail closed；29/29 PDF 通过；缺失 DOI/SI 允许且保留状态；旧数据有 legacy 兼容。缺口：现有 A 脚本不会自动写 manifest，需要先运行 `tools/build_manifest.py`；未运行时 B 生成 legacy 对象并告警，因此不是“零操作自动交接”。

### 5. VLE 解析是否具有跨论文复用能力？

**具备“通用算法 + 论文 profile”的复用架构，尚不是零配置通用解析器。** 通用层处理分行、列分配、单位换算、行过滤；三篇结构不同的论文分别达到 27/27、1/1（2 条文献行过滤）、2/2；目标常量未泄漏。缺口：另外两篇仍需论文专属 profile；当前通用检测仍要求表头含 `p/kPa + loading` 或由 profile 声明列结构；未做 10 篇以上随机 VLE 论文的独立泛化。

### 6. 当前系统是否具备进入小规模真实论文试运行的条件？

**具备“小规模、人工在环”的试运行条件；不具备无人值守生产条件。** 可以开始 10–20 篇真实论文试运行，但必须：先跑 manifest builder；对 OCR `review/fail` 页人工核对；对 L2 抽样人工复核；VLE 新论文先加 profile；保留 `extraction_manifest.json` 与快照；不得把未人工核验的 L2 当最终金标准。无人值守前还缺：A 侧原生 manifest、更多 VLE profile、真实扫描仪基准、人工金标准 38/38（当前 0/38 人工核验）。

## 四、未完成与风险

| 项目 | 状态 | 风险/下一步 |
|---|---|---|
| 人工金标准 | 0/38 人工核验 | Phase 5 不阻塞；试运行需抽样人工复核 |
| A 侧 manifest 自动生成 | 未完成 | 在 `fetch_elsevier/fulltext/CDP` 结束时调用 builder |
| VLE 通用解析 | 3 篇 profile | 扩到 5–10 篇不同出版社/版式 |
| OCR 真实扫描语料 | 仅渲染页/合成退化页 | 增加真实扫描仪样本与人工标注 |
| 水蒸气校验 | 仅 `P_CO2 ≤ P_total` | 论文未给 P_H2O 时保持 not_evaluated，未编造 Antoine 参数 |
| 完整 DB 级溯源 | 快照 sidecar | `source.excerpt` 未入库；`qc_record.human_verified` 未使用（未改 schema） |
| 体积基指标命名 | 部分保留原单位 | 还需统一 `*_volumetric` 映射与 blocked 规则 |
| 负样本规模 | 28 条，初步 | 扩到 50+ 并人工确认标签 |
| 规则引擎 | 21 条可执行规则 | 不是通用推理引擎；新增规则须有知识来源和实现 |

## 五、建议

1. 先跑 `python tools/build_manifest.py`，再试运行 10–20 篇；保留每篇 manifest 与快照。
2. 试运行只让 L2 进入人工抽检队列；L3 作为参考，不混入金标准。
3. OCR `review/fail` 页必须人工看原页；不要用 OCR 文本直接覆盖原生文本。
4. 新 VLE 论文先写 profile，并在 `test_vle_profiles.py` 增加预期点数后再入库。
5. 达到“无人值守”前，至少补齐：A 侧 manifest 自动写入、50+ 负样本、5+ VLE profile、真实扫描仪基准、38 条 L2 人工核验。
