# Phase 5 OCR 质量门控

## 流程

1. `scripts/pdf_to_text.py` 优先使用 PDF 原生文本；仅当页面文本 < 50 字符（`--ocr auto`）或强制 `--ocr always` 时渲染页面并调用 RapidOCR。
2. 每页记录：原生文本、OCR 文本、逐行置信度、低置信度比例、关键科研字段、原生/OCR 数值冲突。
3. `server/ocr_gate.py:assess` 给出页面决策：
   - `pass`：可直接使用；
   - `review`：需要人工或再次 OCR 核对；
   - `fail`：OCR 文本不可信，B 必须停止。
4. `ocr.quality` 汇总到 `parse_report.json`；`server/tasks.py` 读取后：
   - `fail` 且原生文本 < 500 字符 → 不抽取，记录 `ocr_review_required`，进入人工复核；
   - `fail` 但原生文本仍可用 → 继续抽取，`parse_mode=ocr_review`，快照与批次清单带 `ocr_gate`；
   - `review` → 继续抽取但标记复核；
   - `pass`/`not_used` → 正常。

## 关键字段检查

| 字段 | 示例 | 归一化 |
|---|---|---|
| 温度 | `40 °C`, `313.15 K` | °C → K |
| 压力 | `0.15 bar`, `101.325 kPa`, `1 atm` | bar/MPa/atm → kPa |
| 浓度 | `30 wt%`, `5 M`, `2 mol/L` | 数值 + 单位 |
| CO2 负载 | `loading 0.537` | 数值 |
| 速率前缀 | `10-5`, `1e-5` | 指数 |
| 化学式 | MEA / PZ / AMP / MDEA / CO2 / H2O | 大写名称 |

冲突判定：同一字段原生文本与 OCR 都有值且集合完全不相交 → `critical_field_conflicts`。OCR 缺失原生文本中的关键字段 → `critical_fields_missing_in_ocr`。

## 决策阈值

| 条件 | 决策 |
|---|---|
| OCR 无文本 | `fail`（有原生文本且是 OCR 错误时 `review`） |
| 平均置信度 < 0.35 | `fail` |
| 平均置信度 < 0.55 | `review` |
| 低置信度比例 > 0.25 | `review` |
| 关键字段冲突 ≥ 1 | `review`；≥2 且平均置信度 < 0.55 → `fail` |
| 关键字段缺失 | `review` |

置信度不是校准概率；阈值用于分诊，不宣称 OCR 无需人工抽查。

## 实测

命令：`python evaluation/test_ocr_gate.py`，报告 `evaluation/reports/ocr_gate_test.md`。

| 样本 | 类型 | 结果 |
|---|---|---|
| `known_scan.pdf` | 真实渲染的已知内容扫描页 | `pass`，avg_conf 0.9679，冲突 0 |
| `jece_p6.pdf` | 真实论文文本页 + 强制 OCR | `pass`，avg_conf 0.9928，冲突 0 |
| `jece_blur.pdf` | 由真实页面退化得到的模糊扫描 | `fail`，OCR 无文本 / 无置信度 |
| 冲突 fixture | 原生 30 wt% vs OCR 80 wt% | `review`，concentration 冲突 |
| 低置信度 fixture | 0.51 / 0.48 | `review` |

`jece_blur.pdf` 是压力测试样本，不是真实扫描仪语料；真实扫描件基准仍需扩充。

## 溯源

`parse_report.json` 的 `ocr.quality.pages[]` 保留每页决策、置信度、低置信度比例、关键字段集合、冲突和原因；`pdf_parse.ocr` 与 `ocr_gate` 写入抽取快照。关键页面可回到 PDF 页码复核，但当前不保存整页图像区域坐标。

## 仍需人工复核的情况

- 低置信度或关键字段冲突页面；
- 化学下标、合并单元格、多栏表被 OCR 打散；
- 模糊/低分辨率扫描件（当前直接 `fail`）；
- OCR 识别出文本但表格结构仍需用 word-grid 复核的页面。
