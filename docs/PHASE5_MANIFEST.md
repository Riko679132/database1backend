# Phase 5 A→B Manifest 规范（v1.0）

## 目的

A 阶段（检索、筛选、下载、复核 PDF）与 B 阶段（PDF 解析、抽取、校验）之间不再依赖散落的文件名和临时约定，而是通过一个版本化、可校验的 paper manifest 交接。manifest 不移动、不改写 A 的任何产物。

## 文件位置与身份

- 单篇：`data/manifests/<paper_id 安全化>.json`
- 索引：`data/manifests/index.json`
- `paper_id`：有 DOI 时为 `doi:<小写 DOI>`；无 DOI 时为 `pdf:<PDF sha256 前 16 位>`。
- DOI 可缺失，但必须保留 `status`，不得为满足格式而编造。
- 生成器：`python tools/build_manifest.py`（全部）、`--pdf FILE`（单篇）、`--check`（只校验）。

`data/manifests/` 是派生交接物，已加入 `.gitignore`；规范、生成器和测试随仓库发布。

## 字段与约束

```json
{
  "manifest_version": "1.0",
  "paper_id": "doi:10.1021/je00005a025",
  "created_at": "2026-11-24T21:31:44+0800",
  "doi": {"value": "10.1021/je00005a025", "status": "present", "source": "elsevier|filename|none"},
  "title": {"value": "...", "status": "present|missing", "source": "elsevier|triage|null"},
  "pdf": {"path": "data/raw_pdfs/....pdf", "sha256": "...", "bytes": 123, "status": "present"},
  "si": {
    "status": "present|missing|failed|pending",
    "manifest_path": "data/raw_si/<doi>/si_manifest.json",
    "si_found": true,
    "files": [
      {"path": "data/raw_si/...", "type": "pdf", "sha256": "...",
       "expected_sha256": "...", "bytes": 0, "status": "present",
       "parsed": {"kind": "pdf_text", "path": "...", "sha256": "...", "chars": 0}}
    ],
    "warnings": [],
    "human_verified": false
  },
  "eligibility": {
    "verdict": "in_scope|out_of_scope|experiment|model_and_experiment|...|pending",
    "priority": 1,
    "reason": "A 阶段筛选理由",
    "status": "present|missing",
    "source": "assessment_csv|triage_v2"
  },
  "metadata": {"source": "elsevier|triage|filename|none", "status": "present|missing",
               "year": 1992, "journal": "..."},
  "download": {"status": "downloaded|failed|pending", "source": "local_file|unpaywall|cdp|manual",
               "path": "data/raw_pdfs/....pdf"},
  "legacy_generated": false,
  "warnings": []
}
```

状态词：

| 状态 | 含义 |
|---|---|
| `present` / `downloaded` | 来源存在且可用 |
| `missing` | 来源本身没有该信息/文件 |
| `failed` | 获取失败或完整性校验失败 |
| `pending` | 尚未核验 |

## 校验规则

`server/paper_manifest.py:validate_manifest` 在 B 启动时执行：

1. `manifest_version` 必须受支持；
2. `paper_id` 必须以 `doi:` 或 `pdf:` 开头；
3. DOI 为 `present` 时必须非空且形如 `10.xxxx/...`；为空时状态不得为 `present`；
4. PDF/SI 路径必须是相对项目根的路径或项目根内的绝对路径；
5. PDF 为 `present` 时文件必须存在且 SHA-256 完全一致；
6. SI 为 `present` 的每个文件必须存在且 SHA-256 一致；
7. SI 任一文件 `failed` 或哈希不一致，整个 manifest 校验失败（fail closed）；
8. DOI/SI 缺失不是错误；只记录 `missing`/`warnings`；
9. 多篇 manifest 的 `paper_id` 不得重复。

校验失败时 B 记录 `manifest_invalid` 并跳过该 PDF，不会静默使用错误文件。

## B 阶段接入

`server/tasks.py:task_ingest_preview` 对每篇 PDF：

1. `paper_manifest.load_for_pdf(pdf)` 读取已保存 manifest；没有则生成 `legacy_generated` 兼容对象并告警；
2. 校验 PDF/SI 哈希和路径；
3. 通过 `manifest.si` 加载 SI 解析文本，不再直接猜 SI 目录；
4. 把 `paper_id`、manifest 版本、manifest 哈希写入抽取快照；
5. manifest 的筛选结论是 A 的建议，不替代 B 的研究边界判断；`out_of_scope` 只记录，不自动删文件。

## 测试结果

`evaluation/test_manifest.py`，报告 `evaluation/reports/manifest_test.md`：

- 29/29 本地 PDF 可加载 manifest（29 stored，0 legacy）；
- SI 论文 `10.1021/acs.iecr.4c03980` 的 SI 文件与解析文本 SHA-256 校验通过；
- 篡改 PDF SHA → 拒绝；
- 篡改 SI SHA → 拒绝；
- DOI 状态为 `present` 但值为空 → 拒绝；
- 无 DOI 的 PDF → `doi.status=missing`，允许通过并保留缺失状态；
- 空 manifest 目录 → 生成 `legacy_generated` 兼容对象，允许历史数据继续处理。

## 兼容性

- 旧 A 产物（`elsevier_results*.json`、`triage_v2.csv`、`extraction_todo_assessment.csv`、`data/raw_si/*/si_manifest.json`、DOI 文件名）作为构建输入，不要求迁移。
- 旧 PDF 没有 manifest 时自动生成兼容对象；要获得完整 DOI/SI 关联，先运行 `python tools/build_manifest.py`。
- 不修改数据库 schema，不写数据库。
