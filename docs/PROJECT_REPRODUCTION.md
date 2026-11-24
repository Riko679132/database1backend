# 项目复现与 Agent 交接说明

本文件面向要复现、继续开发或自动检查本项目的 Agent。人读版见根目录 `README.md`。

## 0. 一句话目标

把水相胺 CO₂ 捕集文献 PDF 变成**可追溯、可复现、可分级**的 L2 机器核验候选数据集；B 阶段不写数据库，C 阶段以 `scripts/validate.py` 为唯一入闸门。

## 1. 不可违反的项目约束

1. 不修改 `scripts/validate.py`、`scripts/preview.py`、`scripts/schema.sql`；`scripts/import_jsonl.py` 仅在“excerpt/qc_record 写入逻辑”补充时被显式授权修改，当前已恢复只读。
2. 不修改数据库 schema。
3. B 不 import/连接 `data/ccus.sqlite`；所有 B 产物写入 `extractions/`。
4. 不编造 DOI、CAS、SMILES、InChIKey、工况、数值、文献来源；原文没有就 `null`。
5. 没有密度不得把 `mol/L` 换算成 `wt%`；没有总压不得猜 `co2_partial_kPa`；没有 P_H2O 不得按干基用总压派生 P_CO2。
6. 仿真数据 `test_origin="simulation"` 永远 L3，不进入 L1/L2。
7. 不把“未人工核验”写成 `human_verified=1`。
8. 不提交密钥、PDF、SI、`extractions/`、`evaluation/artifacts/`。

## 2. 环境

### 2.1 已验证环境

- Windows 10/11 x64
- Python 3.11（本机 `D:\python3119\python.exe`；不要装 C 盘是本地约定）
- Node.js 20.19+ / 22.12+（仅前端源码需要）
- 两个 Python 环境，严格分离：
  - 根 `.venv`：scripts、server、evaluation、大部分 tools
  - `tools/.venv`：CDP 下载、pypdf PDF 校验、campus-paper-fetch

### 2.2 安装

```bat
D:\python3119\python.exe -m venv .venv
.venv\Scripts\pip.exe install -r requirements.txt -r requirements-server.txt -r requirements-phase2.txt

D:\python3119\python.exe -m venv tools\.venv
tools\.venv\Scripts\pip.exe install -r requirements-tools.txt
```

`requirements-phase2.txt` 包含 RapidOCR、pypdfium2、OpenCV、playwright 客户端等。不要执行 `playwright install`；CDP 连接系统 Chrome/Edge 的 9222 端口。

### 2.3 配置（API Key 必须自行接入）

```bat
copy config.example.yaml config.yaml
copy config.local.example.yaml config.local.yaml
```

`config.yaml` 只放非密钥配置；`config.local.yaml` 放密钥，已被 `.gitignore` 排除。

必须自行申请/填写：

| 配置 | 用途 | 说明 |
|---|---|---|
| `ai.api_key`, `ai.base_url`, `ai.model` | LLM 抽取 | DeepSeek 或任意 OpenAI 兼容服务 |
| `elsevier.api_key` | Scopus 检索 | Elsevier Developer Portal 申请 |
| `unpaywall.email` | 开放获取探测 | 填真实邮箱，Unpaywall 要求 |

也支持启动控制台后在「设置」页填写；效果写入 `config.local.yaml`。仓库不含任何真实 Key。

### 2.4 数据前置

```text
data/ccus.sqlite                 主库（首次由 scripts/init_db.py 创建）
data/compound_whitelist.csv      胺白名单
data/raw_pdfs/                   PDF（不入库）
data/raw_si/                     SI（不入库）
data/manifests/                  A→B manifest（派生，不入库）
```

首次：

```bat
.venv\Scripts\python.exe scripts\init_db.py
.venv\Scripts\python.exe tools\build_manifest.py
```

## 3. 目录与职责

```text
server/
  app.py                 FastAPI 控制台与 API
  tasks.py               B 流程编排：manifest→解析→抽取→快照→validate
  paper_manifest.py      A→B manifest 构建/校验/SI 加载
  extract.py             Prompt、LLM 调用、normalize
  skill_router.py        知识模块路由与规则上下文
  reasoning.py           规则轨迹、一致性门控
  rules.py               21 条可调用规则注册表
  gas_phase.py           水蒸气/干湿基/分压校验
  units.py               速率单位解析/换算/blocked
  vle_table_parser.py    多栏/纵向 VLE 表 + 论文 profile
  reference_case_parser.py 散落参比行 profile
  condition_profile.py   只写在方法段的工况 profile
  table_grid.py          PDF word-coordinate 表格重建
  provenance.py          证据分类、verify、QC、快照
  excerpt_store.py       per-record excerpt sidecar 与索引
  ocr_gate.py            OCR 质量门控
  llm.py                 OpenAI 兼容客户端与配置快照

scripts/
  pdf_to_text.py         原生文本 + OCR + parse_report
  validate.py            唯一入闸门（冻结）
  import_jsonl.py        入库 + excerpt_path + qc_record（已授权修改，只读）
  audit_log.py           审计
  init_db.py             建库
  fetch_elsevier.py      Scopus 检索
  fetch_fulltext.py      Unpaywall 下载
  web_crawler.py         网页采集

tools/
  build_manifest.py      A→B manifest 构建/校验
  trace_excerpt.py       DB test → excerpt（只读）
  backfill_qc_record.py  qc_record 回填（默认 dry-run）
  backfill_excerpt_path.py 旧 excerpt_path 回填（默认 dry-run）
  mark_human_verified.py 人工核验接口（默认 dry-run）
  provenance_report.py   溯源覆盖率报告（只读）
  export_gold_standard.py L2 导出（含 excerpt_path/human_verified）
  postcheck.py           七项硬指标
  verify_pdfs.py         PDF 完整性
  fetch_sd_cdp.py / fetch_pdf_cdp.py / fetch_si.py / digitize_chart.py

evaluation/
  eval_set_v1.json       38 条 L2 正样本
  negative_set_v1.json   28 条负样本/边界样本
  test_*.py              水蒸气/溯源/推理/VLE/OCR/manifest 测试
  evaluate.py            38 条回归
  evaluate_negative.py   负样本 FAR
  evaluate_metrics.py    P/R/F1
  reports/               测试报告（JSON/MD）
  artifacts/             测试 PDF/临时库（已 gitignore）
```

## 4. 数据流与契约

### 4.1 A→B manifest（v1.0）

```text
data/manifests/<paper_id>.json
```

关键字段：

```json
{
  "manifest_version": "1.0",
  "paper_id": "doi:10.xxxx/...",
  "doi": {"value": "...", "status": "present|missing|pending|failed", "source": "..."},
  "title": {"value": "...", "status": "present|missing", "source": "..."},
  "pdf": {"path": "data/raw_pdfs/....pdf", "sha256": "...", "status": "present"},
  "si": {"status": "present|missing|failed|pending", "files": [...]},
  "eligibility": {"verdict": "...", "priority": 1, "status": "present|missing", "source": "..."},
  "metadata": {"source": "...", "status": "..."},
  "download": {"status": "downloaded", "source": "local_file"}
}
```

校验：版本、paper_id、DOI 格式、路径在项目根内、PDF/SI SHA-256；SI 哈希不一致 fail closed；缺失 DOI/SI 允许。没有存储 manifest 时 B 生成 `legacy_generated` 并告警。

### 4.2 B 输出

```text
extractions/<batch_id>/
├─ parsed/<stem>.txt
├─ parsed/parse_report.json
├─ raw/llm_<stem>_<stamp>.json          每篇一个快照
├─ raw/excerpts/<record_id>.json        每条记录一个原文摘录
├─ raw/excerpt_index.json               record_id → sidecar/snapshot
├─ raw_agent.jsonl                      normalize 后记录
├─ valid.jsonl / valid_incomplete.jsonl / rejected.jsonl
└─ extraction_manifest.json             论文级清单
```

每条记录核心域：

```json
{
  "source": {"doi": "...", "loc_type": "table|text|figure", "loc_label": "...",
             "excerpt": "...", "excerpt_path": "extractions/.../raw/excerpts/....json",
             "excerpt_sha256": "..."},
  "recipe": {"recipe_type": "mono|binary", "amine_a": {...}, "amine_b": null,
             "wt_a": 30, "wt_b": null, "water_wt": 70, "total_amine_wt": 30},
  "test": {"temperature_K": 313.15, "co2_vol_pct": 15, "co2_partial_kPa": 15,
           "total_pressure_kPa": 101.325, "gas_basis": "wet|dry|unknown",
           "p_h2o_kPa": null, "y_h2o": null, "water_activity": null,
           "initial_loading": 0, "rich_loading": null, "lean_loading": null},
  "performance": [{"metric_name": "...", "value": 0.5, "unit": "...",
                   "value_original": 0.5, "unit_original": "..."}],
  "gas_phase": {"status": "...", "p_h2o_kPa": null, "water_vapour_check": "..."},
  "qc": {"qc_level": "L2|L3|L4", "qc_reason": "..."},
  "record_id": "..."
}
```

注意：`gas_basis/p_h2o_kPa/y_h2o/water_activity/gas_phase/record_id` 是 JSONL/快照/sidecar 字段，数据库 schema 没有对应列；`import_jsonl.py` 会忽略它们。

### 4.3 快照

`raw/llm_*.json` 至少包含：

- `paper_id`、DOI、PDF/SI 哈希、manifest 版本/哈希；
- Prompt/模型/知识模块/规则集版本与哈希；
- OCR/表格/SI/图表状态；
- `raw_model_output`；
- `records[]`：`raw_record`、`record`、`verification`、`qc`、`reasoning`；
- `human_verified: false`。

快照是 L2 的凭证；无快照的 L2 在 normalize 降 L3。

### 4.4 C 入库

```bat
.venv\Scripts\python.exe scripts\validate.py --input <batch>/raw_agent.jsonl --outdir <batch>
.venv\Scripts\python.exe scripts\import_jsonl.py --input <batch>/valid.jsonl --config config.yaml --batch-id <batch>
.venv\Scripts\python.exe scripts\import_jsonl.py --input <batch>/valid_incomplete.jsonl --config config.yaml --batch-id <batch>
.venv\Scripts\python.exe tools\postcheck.py --batch <batch>
```

`validate.py` 行为：

- 硬违规（recipe_type/excluded_system/concentration/mass_balance/binary_identity）→ `rejected.jsonl`，L4，永不入库；
- 软缺失（source 字段、temperature_K/co2_vol_pct/initial_loading）→ `valid_incomplete.jsonl`，L3，`incomplete_flag=true`；
- 仿真 → 强制 L3；
- 其余保留 B 的 QC。

`import_jsonl.py` 额外：

- `source_location.excerpt_path` 写入 sidecar 路径；
- 每条 test 插入 `qc_record`，`human_verified=0`，reviewer/review_time NULL。

## 5. 关键判定

### QC

| 级别 | 含义 |
|---|---|
| L1 | 作者原始数据点（B 不自动授予） |
| L2 | 机器核验、字段齐全、配方闭合、有快照；仍非人工金标准 |
| L3 | 缺字段/仿真/指标语义冲突/信息不足；参考用 |
| L4 | validate 硬违规；永不入库 |

### 证据

`Explicit / Contextual / Derived / External / Assumed / Unknown`。

- L2 必填字段只允许 Explicit/Contextual/Derived；
- Assumed 不得升 L2；Unknown 保持 null；
- 每条轨迹有 rule_id、证据类型、原文位置、公式/输入/输出或结果。

### 水蒸气

| 情况 | 行为 |
|---|---|
| 明确 P_H2O | 用原文；检查 `P_CO2+P_H2O<=P_total` |
| 湿基 y + P_total | `P_CO2=y_wet*P_total`；水蒸气仍 `not_assessable` |
| 干基 y + P_H2O | `P_CO2=y_dry*(P_total-P_H2O)` |
| 干基 y 无 P_H2O | 不生成 P_CO2，`blocked_dry_basis_missing_p_h2o` |
| 无信息/基未知 | 只做基础压力检查，`not_assessable`/`blocked_basis_unknown` |
| P_H2O 计算 | 纯水 NIST Antoine 1–100 °C；胺溶液需明确 `a_w` 或验证模型 |

## 6. 复现步骤

### 6.1 最小闭环（已有 PDF）

```bat
:: manifest
.venv\Scripts\python.exe tools\build_manifest.py

:: 启动控制台，选「批量入库 · 预览」；或直接调用 server.tasks.task_ingest_preview
start_console.bat
```

B 会：manifest 校验 → pdf_to_text/OCR → 知识路由 → LLM 候选 → 条件/VLE/参比补充 → normalize → verify → QC/推理 → 快照 → excerpt sidecar → validate。

### 6.2 严格 CLI 入库

```bat
.venv\Scripts\python.exe scripts\validate.py --input extractions/<batch>/raw_agent.jsonl --outdir extractions/<batch>
.venv\Scripts\python.exe scripts\import_jsonl.py --input extractions/<batch>/valid.jsonl --config config.yaml --batch-id <batch>
.venv\Scripts\python.exe scripts\import_jsonl.py --input extractions/<batch>/valid_incomplete.jsonl --config config.yaml --batch-id <batch>
.venv\Scripts\python.exe tools\postcheck.py --batch <batch>
.venv\Scripts\python.exe tools\export_gold_standard.py
```

### 6.3 测试矩阵

```bat
:: 核心
.venv\Scripts\python.exe evaluation\evaluate.py --candidate extractions\batch_20261124_145027 --label reproduce
.venv\Scripts\python.exe tools\postcheck.py

:: Phase 5
.venv\Scripts\python.exe evaluation\test_water_vapor.py
.venv\Scripts\python.exe evaluation\test_provenance.py
.venv\Scripts\python.exe evaluation\test_vle_profiles.py
.venv\Scripts\python.exe evaluation\test_reasoning_chain.py
.venv\Scripts\python.exe evaluation\test_manifest.py
.venv\Scripts\python.exe evaluation\test_ocr_gate.py
.venv\Scripts\python.exe evaluation\test_rate_units.py
.venv\Scripts\python.exe evaluation\test_metric_semantics.py
.venv\Scripts\python.exe evaluation\evaluate_negative.py --candidate extractions\batch_20261124_145027 --candidate extractions\20261027_04 --candidate extractions\20261027_05
.venv\Scripts\python.exe evaluation\evaluate_metrics.py
```

期望：

- 38/38 覆盖，97.25% 完整率/一致率，38 L2，0 false reject；
- 负样本 28，18 有候选，false accept L2=0，boundary false reject=0；
- VLE 27/27、1/1、2/2；
- postcheck 七项 PASS；
- 水蒸气 A–I PASS，真实库 63 条 0 anomaly；
- 溯源 63/63 可定位（37 快照、25 batch JSONL、1 旧 txt sidecar）。

## 7. 当前缺口（详细）

### G1 人工金标准未完成（高）

- 38 条 L2 全部是机器核验，`qc_record` 未回填，`human_verified` 未标记。
- 影响：不能把 L2 称为人工金标准；训练/对外交付需抽样人工复核。
- 下一步：`tools/backfill_qc_record.py --apply` 初始化 0；用 `tools/mark_human_verified.py --reviewer ... --basis ... --apply` 逐条核验；接前端审核页。
- 当前未执行主库写入。

### G2 旧库溯源字段未回填（高）

- 主库 63 条：`source_location.excerpt_path` 1/63，`qc_record` 0/63。
- `tools/trace_excerpt.py` 已能 63/63 定位：37 快照、25 旧 batch JSONL、1 旧 `.txt`。
- `tools/backfill_excerpt_path.py` 在主库副本上验证：59 条可新增 sidecar，3 条共享旧 location 无法直接绑定。
- 影响：直接 SQL/导出看不到 excerpt_path；但通过快照仍可追溯。
- 下一步：授权后对主库 `--apply`；对 3 条共享 location 人工拆分或接受快照回退。

### G3 水蒸气真实样本缺失（中高）

- 当前 29 篇 PDF 没有明确 P_H2O/湿基/干基组成的在范围论文；A–E 是代码级 fixture。
- 纯水 Antoine 已注明 NIST 来源/范围；胺溶液只支持明确 `a_w`，没有电解质活度系数模型。
- 影响：分压派生规则正确性只在 fixture 与真实库“无信息”场景验证，缺真实正例。
- 下一步：优先接入一篇明确气相组成的论文，人工核对 P_H2O/干湿基后加入 eval set。

### G4 A 侧 manifest 未自动写入（中）

- A 的 `fetch_elsevier/fulltext/CDP` 结束时不写 manifest；需手动 `tools/build_manifest.py`。
- B 有 legacy 兼容，但正式批次应先生成 manifest。
- 下一步：在 A 脚本结束调用 builder；把 manifest 生成加入控制台采集任务。

### G5 VLE 泛化有限（中）

- 只有 3 篇 profile：多栏、纵向 bar、嵌套单位；未覆盖更多出版社/版式。
- 通用算法仍要求表头含 `p/kPa + loading` 或 profile 声明列。
- 下一步：扩到 5–10 篇，先加预期点数测试再写 profile。

### G6 OCR 真实扫描语料不足（中）

- 已有真实渲染页、已知内容扫描页、退化压力页；没有大规模真实扫描仪基准。
- 置信度不是校准概率；未保存整页图像区域坐标。
- 下一步：采集真实扫描 PDF，人工标注关键字段，扩展 `test_ocr_gate.py`。

### G7 气相/水活度字段不落主表（中）

- `gas_basis/p_h2o_kPa/y_h2o/water_activity/gas_phase` 只在 JSONL/快照/sidecar；DB schema 无列。
- 按约束没有改 schema；下游若要 SQL 分析需读快照或后续加列（需单独授权）。

### G8 负样本与指标仍初步（中）

- 28 条负样本，其中 10 条无候选；标签机器生成，未人工确认。
- 38 条正样本来自 7 篇论文；P/R/F1 1.0/0.93 不能外推总体。
- 下一步：扩到 50+，人工确认标签，按论文分组报告。

### G9 人工核验未接前端（中）

- 只有 CLI：`mark_human_verified.py`、`trace_excerpt.py`、`backfill_*`。
- 下一步：控制台增加审核队列、excerpt 展示、reviewer/basis 表单。

### G10 配置/密钥运维（中）

- `config.yaml`/`config.local.yaml` 本地含真实 Key，已 gitignore；仓库无 Key。
- 新环境必须自行申请 AI/Scopus/Unpaywall；不要把 Key 写进 README、Issue、日志。
- 若 Key 曾进入公开仓库，立即轮换。

### G11 `source_location` 一 location 一 excerpt（低中）

- 新去重键已加 excerpt_path，但旧共享 location 61（3 条 test）仍只有一个字段；不能直接绑定三条不同摘录。
- 这些记录仍可通过快照/批次 JSONL 追溯；回填工具会跳过并报告 `shared_location_ambiguous`。

### G12 运行环境耦合 Windows（低）

- `start_console.bat`、`.venv\Scripts\python.exe`、`TOOLS_PY` 是 Windows 路径。
- Linux 部署需把 `server/tasks.py` 的 `TOOLS_PY` 改为 `tools/.venv/bin/python`，并用等价 uvicorn 命令。

## 8. 排障顺序

```text
0. manifest 是否通过（paper_id/PDF/SI SHA）
1. parse_report.json：文本/OCR 是否正常
2. extraction_manifest.json：论文状态
3. 快照 raw_model_output：LLM 原始输出
4. 快照 records[].raw_record：候选
5. verification：excerpt/numeric/recipe/required evidence
6. reasoning：命中的规则与阻断项
7. valid/incomplete/rejected：validate 最终判定
8. source_location.excerpt_path / trace_excerpt：原文
9. qc_record.human_verified：是否人工核验
```

常见问题：

- API 401/403：Key 未填、IP 不在 Scopus 白名单、Unpaywall 邮箱无效。
- 付费墙下载失败：CDP 9222 未启动、校园网/机构权限不足；不要重试超过 2 次。
- 中文乱码：设置 `PYTHONUTF8=1`。
- `import_jsonl.py` PermissionError：文件是只读冻结状态；如确需修改，先 `chmod u+w`，改完 `chmod u-w`。
- 旧 `.txt` excerpt 无哈希：`read_sidecar` 标 `legacy_text`，不要当作新 JSON sidecar。

## 9. Agent 复现检查清单

- [ ] `.venv` 与 `tools/.venv` 分离且依赖安装成功
- [ ] `config.yaml` 从 `config.example.yaml` 复制，`config.local.yaml` 自行填 Key
- [ ] `data/ccus.sqlite`、`data/compound_whitelist.csv` 存在
- [ ] `tools/build_manifest.py --check` 通过（29/29）
- [ ] 38 条 L2 回归 38/38、97.25%、0 false reject
- [ ] `postcheck.py` 七项 PASS
- [ ] 水蒸气/溯源/VLE/推理/OCR/manifest 测试通过
- [ ] 主库未被测试写入；`human_verified=1` 数量为 0（除非你显式执行人工核验）
- [ ] 没有把 Key、PDF、SI、extractions、evaluation/artifacts 提交到 Git
