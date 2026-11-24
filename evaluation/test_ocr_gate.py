"""OCR quality-gate tests on real rendered pages plus explicit gate fixtures."""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server.ocr_gate import assess, summarize  # noqa: E402

ART = ROOT / "evaluation" / "artifacts" / "ocr"
OUT = ART / "phase5"
RUN = OUT / "run"
REPORT = ROOT / "evaluation" / "reports" / "ocr_gate_test.md"
PY = sys.executable


def parse_pdf(pdf: Path, outdir: Path, mode: str) -> dict:
    outdir.mkdir(parents=True, exist_ok=True)
    cmd = [PY, str(ROOT / "scripts/pdf_to_text.py"), "--pdf", str(pdf),
           "--outdir", str(outdir), "--ocr", mode]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    report = outdir / "parse_report.json"
    if not report.exists():
        return {"error": proc.stderr[-1000:] or proc.stdout[-1000:]}
    data = json.loads(report.read_text(encoding="utf-8"))
    return data[0] if data else {"error": "empty report"}


def main() -> None:
    if RUN.exists():
        shutil.rmtree(RUN, ignore_errors=True)
    RUN.mkdir(parents=True, exist_ok=True)
    checks = []

    known = ART / "known_scan.pdf"
    r = parse_pdf(known, RUN / "known", "auto")
    q = (r.get("ocr") or {}).get("quality") or {}
    checks.append({
        "name": "real_known_scan_auto",
        "ok": q.get("decision") == "pass" and r.get("chars", 0) > 0,
        "decision": q.get("decision"),
        "avg_confidence": q.get("avg_confidence"),
        "critical_conflicts": q.get("critical_conflicts"),
        "reasons": q.get("reasons"),
        "pages": [p.get("page") for p in q.get("pages") or []],
        "recognized_chars": r.get("chars"),
    })

    real = OUT / "jece_p6.pdf"
    r = parse_pdf(real, RUN / "real", "always")
    q = (r.get("ocr") or {}).get("quality") or {}
    checks.append({
        "name": "real_text_page_forced_ocr",
        "ok": q.get("decision") in ("pass", "review"),
        "decision": q.get("decision"),
        "avg_confidence": q.get("avg_confidence"),
        "critical_conflicts": q.get("critical_conflicts"),
        "reasons": q.get("reasons"),
        "critical_ocr": (q.get("pages") or [{}])[0].get("critical_ocr"),
    })

    blur = OUT / "jece_blur.pdf"
    r = parse_pdf(blur, RUN / "blur", "auto")
    q = (r.get("ocr") or {}).get("quality") or {}
    checks.append({
        "name": "degraded_scan_auto",
        "ok": q.get("decision") == "fail",
        "decision": q.get("decision"),
        "avg_confidence": q.get("avg_confidence"),
        "reasons": q.get("reasons"),
        "recognized_chars": r.get("chars"),
    })

    conflict = assess(
        "30 wt% MEA at 40 C, 101.325 kPa, loading 0.537, 34x10-5 mol",
        "80 wt% MEA at 40 C, 101.325 kPa, loading 0.537, 34x10-5 mol",
        [0.92, 0.94, 0.91],
        page=1,
    )
    checks.append({
        "name": "critical_field_conflict_fixture",
        "ok": conflict["decision"] == "review" and bool(conflict["conflicts"]),
        "decision": conflict["decision"],
        "conflicts": conflict["conflicts"],
        "reasons": conflict["reasons"],
    })

    low_conf = assess("30 wt% MEA at 40 C", "30 wt% MEA at 40 C", [0.51, 0.48], page=1)
    checks.append({
        "name": "low_confidence_fixture",
        "ok": low_conf["decision"] == "review",
        "decision": low_conf["decision"],
        "avg_confidence": low_conf["avg_confidence"],
        "reasons": low_conf["reasons"],
    })

    summary = summarize((r.get("ocr") or {}))
    checks.append({
        "name": "summarize_report",
        "ok": summary.get("decision") in ("pass", "review", "fail", "not_used"),
        "decision": summary.get("decision"),
        "pages": summary.get("pages"),
    })

    ok = all(c["ok"] for c in checks)
    payload = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "ok": ok,
        "checks": checks,
    }
    (ROOT / "evaluation" / "reports" / "ocr_gate_test.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        "# OCR quality-gate test",
        "",
        f"- Result: {'PASS' if ok else 'FAIL'}",
        "- OCR: RapidOCR (`rapidocr_onnxruntime`), page rendering pypdfium2.",
        "- `jece_p6.pdf` is one native-text page copied from the real jece paper; `jece_blur.pdf` is a degraded synthetic scan derived from it.",
        "",
        "| Check | Result | Decision | Detail |",
        "|---|---|---|---|",
    ]
    for c in checks:
        detail = {k: v for k, v in c.items() if k not in ("name", "ok", "decision")}
        lines.append(f"| {c['name']} | {'PASS' if c['ok'] else 'FAIL'} | {c.get('decision')} | `{json.dumps(detail, ensure_ascii=False)}` |")
    lines += [
        "",
        "The degraded scan is a stress fixture, not a genuine scanner corpus.",
        "`pass` means usable as-is; `review` means a human/again-OCR check is required; `fail` means B must stop.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
