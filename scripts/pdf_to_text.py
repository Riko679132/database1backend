"""
pdf_to_text.py —— PDF 全文解析（文本层 + 可选 OCR）

用法:
    单篇: python scripts/pdf_to_text.py --pdf data/raw_pdfs/xxx.pdf [--outdir extractions/parsed] [--ocr auto]
    批量: python scripts/pdf_to_text.py --indir data/raw_pdfs        [--outdir extractions/parsed] [--ocr auto]

行为:
    1. 用 pdfplumber 逐页 extract_text()；
    2. 每个 PDF 生成同名 .txt，页与页之间用 "--- Page N ---" 分隔；
    3. --ocr auto（默认）：文本层少于 50 字符的页面用 RapidOCR 识别；always/never 可强制；
    4. 输出 sha256 / 页数 / 字符数 / OCR 页面 / OCR 平均置信度；
    5. 每次运行末尾输出 parse_report.json；
    6. 不触碰数据库，不修改原 PDF。
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.ocr_gate import assess as assess_ocr  # noqa: E402


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _ocr_page(pdf_path, page_no, dpi):
    """Render one page and OCR it. Returns (text, confidences, error)."""
    try:
        import numpy as np
        import pypdfium2 as pdfium
        from rapidocr_onnxruntime import RapidOCR
    except Exception as exc:  # noqa: BLE001
        return "", [], f"ocr_unavailable: {exc}"
    try:
        doc = pdfium.PdfDocument(str(pdf_path))
        page = doc[page_no - 1]
        image = page.render(scale=dpi / 72.0).to_pil().convert("RGB")
        arr = np.array(image)[:, :, ::-1]  # RGB -> BGR for OpenCV/RapidOCR
        result, _ = RapidOCR()(arr)
        lines, confs = [], []
        for item in result or []:
            if len(item) >= 3:
                lines.append(str(item[1]))
                try:
                    confs.append(float(item[2]))
                except (TypeError, ValueError):
                    pass
        return "\n".join(lines), confs, None
    except Exception as exc:  # noqa: BLE001
        return "", [], f"ocr_failed: {exc}"


def extract_one(pdf_path, out_path, ocr_mode="auto", ocr_dpi=200):
    """把单个 PDF 解析为 txt。返回 dict 报告项。"""
    pages = []
    ocr_pages = []
    ocr_conf = []
    ocr_errors = []
    page_quality = []
    with pdfplumber.open(pdf_path) as pdf:
        n_pages = len(pdf.pages)
        for i, page in enumerate(pdf.pages, 1):
            try:
                txt = page.extract_text() or ""
            except Exception as e:
                txt = f"[page {i} extract failed: {e}]"
            use_ocr = ocr_mode == "always" or (ocr_mode == "auto" and len(txt.strip()) < 50)
            if use_ocr:
                ocr_text, confs, err = _ocr_page(pdf_path, i, ocr_dpi)
                detail = assess_ocr(
                    txt, ocr_text, confs, page=i, errors=[err] if err else None
                )
                page_quality.append(detail)
                if err:
                    ocr_errors.append(f"page {i}: {err}")
                    pages.append(f"--- Page {i} ---\n{txt}")
                else:
                    ocr_pages.append(i)
                    ocr_conf.extend(confs)
                    pages.append(f"--- Page {i} (OCR) ---\n{ocr_text}")
            else:
                pages.append(f"--- Page {i} ---\n{txt}")
    text = "\n\n".join(pages)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(text, encoding="utf-8")
    n_chars = len(text)
    avg_conf = round(sum(ocr_conf) / len(ocr_conf), 4) if ocr_conf else None
    low_conf = sum(1 for c in ocr_conf if c < 0.6)
    decisions = [p["decision"] for p in page_quality]
    if "fail" in decisions:
        gate_decision = "fail"
    elif "review" in decisions:
        gate_decision = "review"
    elif decisions:
        gate_decision = "pass"
    else:
        gate_decision = "not_used"
    gate_reasons = []
    for p in page_quality:
        for reason in p.get("reasons") or []:
            if reason not in gate_reasons:
                gate_reasons.append(reason)
    quality = {
        "tool": "rapidocr_onnxruntime",
        "dpi": ocr_dpi,
        "mode": ocr_mode,
        "decision": gate_decision,
        "reasons": gate_reasons,
        "pages": page_quality,
        "avg_confidence": avg_conf,
        "low_confidence_items": low_conf,
        "critical_conflicts": sum(len(p.get("conflicts") or []) for p in page_quality),
    }
    return {
        "pdf": str(pdf_path),
        "txt": str(out_path),
        "sha256": sha256_file(pdf_path),
        "pages": n_pages,
        "chars": n_chars,
        "needs_ocr": n_chars < 50 * max(n_pages, 1),
        "status": "ok",
        "ocr": {
            "mode": ocr_mode,
            "tool": "rapidocr_onnxruntime",
            "dpi": ocr_dpi,
            "pages": ocr_pages,
            "avg_confidence": avg_conf,
            "low_confidence_items": low_conf,
            "errors": ocr_errors,
            "quality": quality,
        },
    }


def collect_pdfs(pdf_arg, indir_arg):
    if pdf_arg:
        return [Path(pdf_arg)]
    return sorted(Path(indir_arg).glob("*.pdf"))


def main():
    ap = argparse.ArgumentParser(description="PDF 全文解析（骨架）")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--pdf", help="单个 PDF 文件路径")
    g.add_argument("--indir", help="包含 PDF 的目录（批量）")
    ap.add_argument("--outdir", default="extractions/parsed",
                    help="txt 输出目录（默认 extractions/parsed）")
    ap.add_argument("--ocr", choices=["auto", "always", "never"], default="auto",
                    help="OCR 策略：auto=仅低文本页，always=全部，never=关闭（默认 auto）")
    ap.add_argument("--ocr-dpi", type=int, default=200, help="OCR 渲染 DPI（默认 200）")
    args = ap.parse_args()

    files = collect_pdfs(args.pdf, args.indir)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    results = []
    for f in files:
        try:
            r = extract_one(f, outdir / (f.stem + ".txt"), args.ocr, args.ocr_dpi)
        except Exception as e:
            r = {"pdf": str(f), "status": "failed", "error": str(e)}
        results.append(r)
        ocr = r.get("ocr") or {}
        quality = ocr.get("quality") or {}
        tag = ""
        if ocr.get("pages"):
            conf = ocr.get("avg_confidence")
            tag = f"  [OCR pages={ocr['pages']} avg_conf={conf} gate={quality.get('decision')}]"
        elif r.get("needs_ocr"):
            tag = "  [needs_ocr]"
        print(f"  {r['status']:>7}  {f.name}  "
              f"pages={r.get('pages','-')}  chars={r.get('chars','-')}{tag}")

    report_path = outdir / "parse_report.json"
    # 逐篇调用时会重复运行本脚本，报告按 pdf 路径合并而不是整体覆盖，
    # 否则一个批次里只有最后一次运行的那篇留档。
    merged = {}
    if report_path.exists():
        try:
            for r in json.loads(report_path.read_text(encoding="utf-8")):
                merged[r.get("pdf")] = r
        except Exception:
            pass
    for r in results:
        merged[r.get("pdf")] = r
    report_path.write_text(
        json.dumps(list(merged.values()), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    n_ok = sum(1 for r in results if r["status"] == "ok")
    n_ocr = sum(1 for r in results if (r.get("ocr") or {}).get("pages"))
    print(f"共 {len(files)} 个 PDF：成功 {n_ok}，OCR 处理 {n_ocr} 篇，"
          f"本批次报告累计 {len(merged)} 篇 → {report_path}")


if __name__ == "__main__":
    main()
