# Phase-2 Integration Report

> **Phase 3 update:** the Phase-2 7-paper regression (22/38, 76.7% completeness, 66.1% agreement) was superseded by Phase 3. After the multi-column VLE parser and rate-unit normalization, the corrected regression is **37/38, 95.9% completeness, 95.9% agreement**. See `docs/PHASE3_REPORT.md` and `docs/phase3_regression_comparison.md`.

## 1. Status analysis (before changes)

### Already implemented

- Database本体：11 张表，`data/ccus.sqlite` 当前 63 test / 73 performance / 17 source / 38 条 L2（其中 3 条 L3 来自 Phase 2 之前的 `batch_20261030_165128`；Phase 2 没有写库）。
- 论文处理脚本：`pdf_to_text.py`、`validate.py`、`import_jsonl.py`、`postcheck.py`、`export_gold_standard.py`。
- 采集链：Scopus/Unpaywall/CDP、PDF 复核。
- 前端/本地控制台：`web/`、`server/`。

### Only in the Skill, not wired into the extractor

- 动态知识路由（按论文类型选择 knowledge 模块）。
- 证据分类（Explicit/Contextual/Derived/External/Assumed/Unknown）。
- 快照契约（prompt/模型/知识版本、原始输出、验证结果）。
- VLE、单位、图表、SI 的专家阅读规则。

### Integrated but defective

- `server/extract.py` **无条件写 L3**，因为它不生成快照。
- 没有知识路由记录、没有 prompt/模型版本记录、没有证据分类结果。
- `source.excerpt` 没有持久化到 `source_location`（只有 `excerpt_path` 字段）。
- `pdf_to_text.py` 没有 OCR；扫描页直接跳过。
- `postcheck.py` 只检查 L2 快照路径存在，不检查快照内容/哈希。

### Completely missing

- 38 条 L2 的可重复回归评估器。
- 图表数字化工具与溯源。
- SI 自动发现/下载/解析/交接包。
- 数据库扩展建议文档。

## 2. What was changed

### B-flow: knowledge routing + snapshot + conditional QC

| File | Change |
|---|---|
| `server/skill_router.py` | 新增：按关键词选择最多 4 个 knowledge 模块，记录模块 SHA-256、选择原因；生成 knowledge context 与 prompt fingerprint。 |
| `server/provenance.py` | 新增：快照写入、excerpt 逐字/表格行匹配、数值出现率、证据分类、条件化 L2/L3 判定。 |
| `server/table_grid.py` | 新增：对多栏/无框线表格按 y 带和 x 坐标重建页面网格，作为 LLM 的定位辅助。 |
| `server/extract.py` | 接入知识路由和动态 prompt；要求模型输出 `evidence`；要求 VLE 逐行、pure CO2、fresh solution、rich loading 规则；JSON 截断时用抢救解析器恢复完整记录。 |
| `server/tasks.py` | 每篇论文写一份快照、一份批次 manifest；把 OCR/SI/表格网格状态写入快照；不再无条件 L3。 |
| `server/llm.py` | 新增非敏感 `config_snapshot()`，记录 provider/base_url/model/key_set。 |

### Snapshot contract

Each extraction writes `extractions/<batch>/raw/llm_<pdf>_<timestamp>.json` with:

- paper DOI/PDF path/PDF SHA-256;
- task ID, batch ID, timestamp, status/error;
- prompt system/user/combined SHA-256;
- Skill SHA-256 and version;
- selected knowledge modules + hashes + selection reason;
- model config and parameters;
- PDF parse mode (text/OCR), OCR pages/confidence/errors;
- SI manifest status and files;
- table-grid pages/chars;
- raw model output;
- normalized records + per-record verification + QC;
- `human_verified: false` and a note that machine verification is not human verification.

`extractions/<batch>/extraction_manifest.json` summarizes all papers, modules, prompt hashes, models and QC counts.

### Conditional QC instead of forced L3

- L2 only if: required fields present, recipe closed, performance present, excerpt/table row verified, numeric match ratio ≥ 0.5, and required evidence types are Explicit/Contextual/Derived.
- L3 if: missing fields, unverified excerpt, low numeric match, unknown/assumed required evidence, or simulation.
- L4 is still produced by `validate.py` for hard violations; the new code does not override it.
- L2 reasons include `llm_snapshot_machine_verified;human_audit_pending;...`.

### OCR

- `scripts/pdf_to_text.py` adds `--ocr auto|always|never` and `--ocr-dpi`.
- `auto` OCRs pages with <50 characters; text pages stay text.
- Uses RapidOCR + ONNX Runtime + pypdfium2 rendering; no system Tesseract.
- `parse_report.json` records OCR pages, average confidence, low-confidence count and errors.
- `server/tasks.py` reads the report and stores OCR status in the snapshot.

### SI

- `tools/fetch_si.py` discovers file-like SI links through the authorized CDP browser; filters ACS help/Google Scholar noise; downloads and parses PDF/CSV/XLSX/DOCX/ZIP; writes `si_manifest.json`.
- `server/tasks.py` loads parsed SI text for the matching DOI into the extraction prompt and stores the SI manifest in the snapshot.

### Chart digitization

- `tools/digitize_chart.py` extracts a PDF page region to PNG, calibrates linear/log axes from two pixel/value pairs, converts manual points or auto-detected colored markers to CSV, and writes provenance (image/CSV SHA-256, calibration, error estimate).

### Regression

- `evaluation/build_eval_set.py` builds `evaluation/eval_set_v1.json` from 38 L2 records, with PDF/snapshot integrity checks and `human_verified=false`.
- `evaluation/evaluate.py` reports coverage, per-field completeness, numeric agreement, recipe closure, QC outcomes, rejection reasons and failure samples.
- `evaluation/build_historical_candidate.py` provides a harness sanity fixture (38/38, not a model result).

## 3. Runbook

### Install

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt -r requirements-phase2.txt
```

`playwright` is only a client package; no browser binary is downloaded. CDP uses the system Chrome/Edge.

### Start the local console

```powershell
start_console.bat
```

or:

```powershell
.\.venv\Scripts\python.exe tools\build_web_db.py
.\.venv\Scripts\python.exe -m uvicorn server.app:app --host 127.0.0.1 --port 8765
```

### CLI checks

```powershell
# OCR (auto only scans low-text pages)
.\.venv\Scripts\python.exe scripts\pdf_to_text.py --pdf data\raw_pdfs\xxx.pdf --outdir extractions\test_parse --ocr auto

# SI discovery/download/parse
.\.venv\Scripts\python.exe tools\fetch_si.py --doi 10.1021/acs.iecr.4c03980

# Chart extraction + digitization
.\.venv\Scripts\python.exe tools\digitize_chart.py extract --pdf data\raw_pdfs\xxx.pdf --page 4 --bbox 0 0 2550 3300 --dpi 200 --out evaluation\artifacts\chart.png
.\.venv\Scripts\python.exe tools\digitize_chart.py digitize --image evaluation\artifacts\chart.png --calibration cal.json --auto-color "#ff0000"

# Regression
.\.venv\Scripts\python.exe evaluation\build_eval_set.py
.\.venv\Scripts\python.exe evaluation\evaluate.py --candidate extractions\<batch> --label run_name
```

## 4. Test results

| Test | Result |
|---|---|
| Historical fixture | 38/38, 100% completeness/agreement (harness sanity only) |
| Final 7-paper LLM regression | 22/38 coverage, 76.7% completeness, 66.1% agreement, 10 L2 / 12 L3 / 16 no-match |
| OCR text PDF | auto mode: 0 OCR pages, 44,876 chars, no regression |
| OCR synthetic scan | 1 page, avg confidence 0.9679; recognized MEA/AMP/MDEA, 0.609/0.875/0.520, 30 wt%, 40 |
| Chart synthetic known truth | 3/3 points recovered exactly (20/3, 50/6, 80/9); image/CSV hashes recorded |
| SI ACS paper | 1 SI PDF downloaded, 9 pages, 4,891 chars parsed; manifest written; SI text loaded into B prompt |
| B-flow integration | 1 paper preview → 1 L2 with snapshot, `validate.py` valid=1, postcheck passed |
| Database | No Phase-2 writes; postcheck 7/7 PASS, 38/38 L2 snapshots present |

## 5. Known limitations

1. **Multi-column VLE tables**: Shen & Li 1992 still only 12/27 points; table-grid helps but does not fully solve four side-by-side temperature groups. Needs a deterministic table parser or table-specific chunking.
2. **Unit normalization**: jece 2024 rates were extracted with a different scale (34.0 vs 0.00034). The prompt still needs a stronger rate-unit rule; the evaluator correctly reports the error.
3. **Water-lean reference rows**: d6gc 2026 returned 0 records despite a 30 wt% MEA reference; needs stronger section/table targeting.
4. **OCR** is approximate for subscripts, merged cells and table structure; OCR text must not be treated as exact original.
5. **Chart digitization** auto-detects colored markers only; overlapping/black curves require manual points or an external digitizer.
6. **SI** discovery is publisher-specific; HTML landing pages/login gates are recorded as failures, not bypassed.
7. **L2 is machine-verified, not human-verified.** The snapshot records `human_verified:false`; a human audit is still required for gold-standard claims.
8. **Schema gaps** remain; see `docs/database_extension_recommendations.md`. No schema change was made.

## 6. Acceptance checklist

- [x] Knowledge routing actually participates in LLM extraction and is recorded in the snapshot.
- [x] Every extraction has a snapshot with prompt/model/knowledge versions.
- [x] Unconditional L3 removed; L2 is conditional on machine-verified evidence.
- [x] 38-record L2 regression set and evaluator exist and run.
- [x] OCR handles scanned pages (RapidOCR), with confidence/provenance.
- [x] Chart digitization tool and provenance exist; automatic detection limited to colored markers.
- [x] SI discovery/download/parse/handoff exists and is loaded into B.
- [x] Evidence types are recorded; Unknown/Assumed do not silently become L2.
- [x] No database schema change or direct DB write from the extractor.
- [ ] Full 38/38 recall is not achieved; the 27-point VLE table and unit normalization remain open.
