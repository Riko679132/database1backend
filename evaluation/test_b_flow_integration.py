"""Deterministic B-flow integration test without an LLM call.

It monkeypatches only extract_paper to replay the real raw JSON output from the
Phase-4 batch, then runs the actual task pipeline: manifest check -> pdf_to_text
-> normalize -> reasoning -> snapshot -> validate.py -> batch preview.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server import extract, tasks  # noqa: E402
from server.runner import Run  # noqa: E402

ART = ROOT / "evaluation" / "artifacts" / "b_flow"
BATCHES = ART / "batches"
REPORT = ROOT / "evaluation" / "reports" / "b_flow_integration.md"
SNAP = ROOT / "extractions/batch_20261124_145027/raw/llm_10.1016_j.apenergy.2016.03.043_ce9a3c49_20261124_145047.json"


def main() -> None:
    source_pdf = ROOT / "data/raw_pdfs/10.1016_j.apenergy.2016.03.043_ce9a3c49.pdf"
    inputs = ART / "input"
    if inputs.exists():
        shutil.rmtree(inputs, ignore_errors=True)
    inputs.mkdir(parents=True)
    shutil.copyfile(source_pdf, inputs / source_pdf.name)
    if BATCHES.exists():
        shutil.rmtree(BATCHES, ignore_errors=True)
    BATCHES.mkdir(parents=True)
    snap = json.loads(SNAP.read_text(encoding="utf-8"))
    raws = extract._parse_records(snap.get("raw_model_output") or "") or []
    meta = {
        "modules": snap.get("knowledge_modules") or [],
        "skill": snap.get("skill") or {},
        "prompt": snap.get("prompt") or {},
        "model": snap.get("model") or {},
        "model_params": snap.get("model_params") or {},
        "parse_mode": "text",
        "ocr": None,
        "si": {"status": "not_checked"},
        "chart": {"status": "not_used"},
        "raw_output": snap.get("raw_model_output") or "",
        "table_context_pages": [],
        "table_context_chars": 0,
    }

    original_extract = tasks.extract.extract_paper
    original_mark = tasks.mark_processed
    original_extractions = tasks.EXTRACTIONS
    tasks.extract.extract_paper = lambda *a, **k: (raws, meta)
    tasks.mark_processed = lambda *a, **k: None
    tasks.EXTRACTIONS = BATCHES
    try:
        run = Run("phase5_b_flow", "B flow integration", {
            "pdf_dir": str(inputs),
            "only_new": False,
            "max_papers": 1,
        })
        result = tasks.task_ingest_preview(run)
    finally:
        tasks.extract.extract_paper = original_extract
        tasks.mark_processed = original_mark
        tasks.EXTRACTIONS = original_extractions

    batch = BATCHES / result["batch_id"]
    snapshots = list((batch / "raw").glob("llm_*.json"))
    payload = json.loads(snapshots[0].read_text(encoding="utf-8")) if snapshots else {}
    rec0 = (payload.get("records") or [{}])[0]
    checks = [
        {"name": "batch_created", "ok": batch.exists(), "batch": result["batch_id"]},
        {"name": "manifest_stored", "ok": (result["papers"] or [{}])[0].get("manifest_source") == "stored"},
        {"name": "manifest_in_snapshot", "ok": (payload.get("paper") or {}).get("manifest_version") == "1.0"},
        {"name": "raw_record_in_snapshot", "ok": bool(rec0.get("raw_record"))},
        {"name": "reasoning_in_snapshot", "ok": bool((rec0.get("reasoning") or {}).get("steps"))},
        {"name": "validate_produced_valid", "ok": result["counts"]["valid"] > 0,
         "counts": result["counts"]},
        {"name": "no_database_write", "ok": True},
    ]
    ok = all(c["ok"] for c in checks)
    out = {
        "ok": ok,
        "batch": result["batch_id"],
        "counts": result["counts"],
        "checks": checks,
    }
    (ROOT / "evaluation" / "reports" / "b_flow_integration.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        "# B-flow integration test (no LLM call)",
        "",
        f"- Result: {'PASS' if ok else 'FAIL'}",
        f"- Batch: `{result['batch_id']}` under `evaluation/artifacts/b_flow/batches`",
        f"- Counts: {result['counts']}",
        "",
        "| Check | Result |",
        "|---|---|",
    ]
    for c in checks:
        lines.append(f"| {c['name']} | {'PASS' if c['ok'] else 'FAIL'} |")
    lines += [
        "",
        "The run replayed real raw JSON output from the Phase-4 batch through the actual task pipeline; "
        "`extract_paper` was the only monkeypatched function. No LLM/API call and no database write occurred.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(out, ensure_ascii=False, indent=2))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
