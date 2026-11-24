# CCUS 胺法碳捕集文献数据系统

把 PDF 文献变成**可追溯、可复现、可分级**的胺法 CO₂ 捕集实验数据库。

当前定位：水相单胺/双组分胺、总胺 20–50 wt%、无添加剂/盐/两相/浆料；产出到 L2 机器核验金标准候选为止，不训练模型、不做配方优化。

## 一、整体架构

```text
A 检索与获取                 B 解析与抽取                     C 入库与导出
─────────────               ───────────────                 ────────────
Scopus 检索                  manifest 校验                    validate.py
Unpaywall / CDP 下载    →    PDF 文本 / OCR              →    import_jsonl.py
PDF 完整性复核               LLM 候选 + 规则/公式              audit_log.py
SI 发现与解析                证据分类 + QC + 快照              postcheck.py
筛选 triage                  valid / incomplete / rejected     金标准导出 / 前端快照
        │                            │                              │
        └──────── PDF + manifest ────┘                              │
                                                                     ▼
                                                              data/ccus.sqlite
```

- **A→B 只靠** PDF + `data/manifests/*.json`（DOI、PDF/SI 哈希、筛选结论）。
- **B 不写数据库**，只写 `extractions/<batch>/`：解析文本、快照、JSONL、校验结果。
- **C 是唯一入库通道**，`scripts/validate.py` 是唯一入闸门；B 的 L2 只是候选，最终以 validate 结果为准。
- **前端只读 C 的公开快照**，不直接访问数据库。

## 二、目录速览

```text
config.example.yaml       无密钥配置模板（复制为 config.yaml）
config.local.example.yaml 密钥模板（复制为 config.local.yaml）
data/                     数据库、白名单、PDF、SI（PDF/SI/DB 不入库）
scripts/                  解析、校验、导入、审计、检索、下载
server/                   FastAPI 控制台、B 流程编排、知识路由、推理、快照
tools/                    manifest、VLE 数字化、PDF 复核、证据追踪、导出
evaluation/               38 条 L2 回归、负样本、OCR/VLE/水蒸气/溯源测试
docs/                     Phase 2–5 设计、验收和缺口说明
web/                      检索前端（静态快照 + sql.js）
```

## 三、快速启动（Windows）

本项目在 Windows + Python 3.11 下开发；Python 不要装在 C 盘是本地约定，不是代码要求。

```bat
:: 1. 根环境
D:\python3119\python.exe -m venv .venv
.venv\Scripts\pip.exe install -r requirements.txt -r requirements-server.txt -r requirements-phase2.txt

:: 2. tools 环境（CDP 下载/PDF 校验独立）
D:\python3119\python.exe -m venv tools\.venv
tools\.venv\Scripts\pip.exe install -r requirements-tools.txt

:: 3. 配置
copy config.example.yaml config.yaml
copy config.local.example.yaml config.local.yaml
:: 填写 config.local.yaml 里的 API Key；或启动后在「设置」页填写

:: 4. 初始化数据库（首次）
.venv\Scripts\python.exe scripts\init_db.py

:: 5. 生成 A→B manifest（建议每次新增 PDF 后执行）
.venv\Scripts\python.exe tools\build_manifest.py

:: 6. 启动控制台
start_console.bat
```

打开 `http://127.0.0.1:8765/`。工作台可执行检索、下载、批量入库预览、确认入库、postcheck 和导出。

> 没有 `web/dist` 时，`start_console.bat` 会尝试用 Node 构建前端；Node 只在前端源码修改时需要。

## 四、API Key 需要自行接入

仓库**不包含任何真实密钥**。以下三项需要你自己申请并填入 `config.local.yaml` 或控制台「设置」：

| 服务 | 用途 | 配置项 |
|---|---|---|
| DeepSeek 或任意 OpenAI 兼容服务 | LLM 结构化抽取 | `ai.api_key`、`ai.base_url`、`ai.model` |
| Elsevier Scopus API | 文献检索元数据 | `elsevier.api_key` |
| Unpaywall | 开放获取 PDF 探测 | `unpaywall.email`（填你的邮箱） |

`config.local.yaml` 和 `config.yaml` 已在 `.gitignore` 中排除；不要把密钥提交到 Git，也不要贴到公开 Issue。若密钥曾进入聊天或公开仓库，请立即轮换。

## 五、当前能做到什么

- A：Scopus 检索、Unpaywall/CDP 下载、PDF 复核、SI 发现与解析、triage 分档。
- B：文本/OCR 解析、动态知识路由、LLM 候选、确定性分压/单位/质量平衡、多栏与纵向 VLE 表、参散落比行、条件 profile、证据分类、快照、推理轨迹、水蒸气/干湿基校验。
- C：validate 三路分流（valid / valid_incomplete / rejected）、导入、审计、postcheck、L2 金标准导出、前端只读快照。
- 回归现状：38/38 L2 覆盖、97.25% 字段完整率/一致率、0 false reject；负样本 28 条、FAR 0；VLE 三篇 27/27、1/1、2/2；postcheck 七项 PASS。

## 六、当前缺口（简版）

1. **人工金标准仍未完成**：38 条 L2 都是机器核验，`human_verified` 未标记；不能当最终人工金标准。
2. **A→B manifest 仍需手动构建**：A 脚本尚未自动写 manifest；B 有 legacy 兼容，但正式流程应先跑 `tools/build_manifest.py`。
3. **旧库溯源未回填**：主库 63 条中 `source_location.excerpt_path` 只有 1 条、`qc_record` 0 行；`trace_excerpt` 已能 63/63 定位，但直接字段仍为空。回填工具存在，默认 dry-run。
4. **VLE 只有 3 篇 profile**：通用算法+profile 可复用，但不是零配置通用解析器；新结构论文仍需 profile。
5. **OCR 缺真实扫描仪语料**：已有渲染页、已知扫描页和退化压力样本；未做大规模真实扫描件基准。
6. **水蒸气真实样本缺失**：当前语料没有明确 P_H2O/湿基/干基组成的论文；A–E 是代码级 fixture，真实库只验证了“缺信息不拒收”。
7. **气相字段不落主表**：`gas_basis/p_h2o_kPa/y_h2o/water_activity` 只在 JSONL/快照/sidecar；未改 schema。
8. **人工核验/回填未接前端**：目前是 CLI 工具，主库未执行回填。
9. **指标仍是初步**：38 条正样本来自 7 篇论文，28 条负样本含 10 条无候选记录，标签未经人工核验，不能外推总体准确率。

## 七、文档

- 人读架构与流程：[docs/PHASE5_ACCEPTANCE.md](docs/PHASE5_ACCEPTANCE.md)
- 水蒸气与溯源补充：[docs/PHASE5_SUPPLEMENT_REPORT.md](docs/PHASE5_SUPPLEMENT_REPORT.md)
- 复现与 gap 详解（agent 读）：[docs/PROJECT_REPRODUCTION.md](docs/PROJECT_REPRODUCTION.md)
- manifest 规范：[docs/PHASE5_MANIFEST.md](docs/PHASE5_MANIFEST.md)
- 推理链与规则：[docs/PHASE5_REASONING.md](docs/PHASE5_REASONING.md)、[docs/PHASE5_RULE_CATALOG.md](docs/PHASE5_RULE_CATALOG.md)
- OCR 门控：[docs/PHASE5_OCR_GATE.md](docs/PHASE5_OCR_GATE.md)
- 负样本与 VLE：[docs/PHASE5_NEGATIVE_AND_VLE.md](docs/PHASE5_NEGATIVE_AND_VLE.md)

## 八、安全与数据边界

- 不修改 `scripts/validate.py`、`preview.py`、`schema.sql`；`import_jsonl.py` 仅因溯源补充被显式授权修改，并已恢复只读。
- B 不连接数据库、不写库；C 的 `validate.py` 是唯一入闸门。
- 不编造 DOI/CAS/SMILES/数值/工况；缺失保持 null。
- 没有密度不把 mol/L 换算成 wt%；没有总压不猜分压；仿真数据永不进入 L1/L2。
- `data/raw_pdfs/`、`data/raw_si/`、`extractions/`、`evaluation/artifacts/` 不入库，避免版权 PDF 和原文摘录外泄。
