"""Manifest contract tests: build, validate, reject corruption, legacy fallback."""
from __future__ import annotations

import copy
import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server import paper_manifest as pm  # noqa: E402

OUT = ROOT / "evaluation" / "artifacts" / "manifests"
REPORT = ROOT / "evaluation" / "reports" / "manifest_test.md"


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    with_si = ROOT / "data/raw_pdfs/10.1021_acs.iecr.4c03980_119aaf3d.pdf"
    no_si = ROOT / "data/raw_pdfs/10.1021_je00005a025_0770ae31.pdf"
    results = []

    data = pm.build_manifest(with_si)
    check = pm.validate_manifest(data)
    pm.write_manifest(data, OUT)
    results.append(("build_SI_paper", check["ok"], {
        "paper_id": data["paper_id"],
        "doi_status": data["doi"]["status"],
        "pdf_sha256": data["pdf"]["sha256"][:16],
        "si_status": data["si"]["status"],
        "si_files": len(data["si"]["files"]),
        "errors": check["errors"],
    }))
    text, meta = pm.si_text(data)
    results.append(("load_SI_text", bool(text) and meta["status"] == "loaded", {
        "chars": len(text or ""),
        "parsed_files": sum(1 for f in meta["files"] if (f.get("parsed") or {}).get("path")),
    }))

    data2 = pm.build_manifest(no_si)
    check2 = pm.validate_manifest(data2)
    pm.write_manifest(data2, OUT)
    results.append(("build_no_SI_paper", check2["ok"], {
        "paper_id": data2["paper_id"],
        "si_status": data2["si"]["status"],
        "errors": check2["errors"],
    }))

    bad_pdf = copy.deepcopy(data)
    bad_pdf["pdf"]["sha256"] = "0" * 64
    c = pm.validate_manifest(bad_pdf)
    results.append(("reject_pdf_hash_mismatch", (not c["ok"]) and any("pdf.sha256" in e for e in c["errors"]), {
        "errors": c["errors"],
    }))

    bad_si = copy.deepcopy(data)
    bad_si["si"]["files"][0]["sha256"] = "0" * 64
    c = pm.validate_manifest(bad_si)
    results.append(("reject_SI_hash_mismatch", (not c["ok"]) and any("si.sha256" in e for e in c["errors"]), {
        "errors": c["errors"],
    }))

    bad_doc = copy.deepcopy(data)
    bad_doc["doi"] = {"value": None, "status": "present", "source": None}
    c = pm.validate_manifest(bad_doc)
    results.append(("reject_present_DOI_without_value", not c["ok"], {"errors": c["errors"]}))

    # A PDF whose name carries no DOI: missing DOI must remain missing, not be invented.
    fake_pdf = OUT / "unknown_paper.pdf"
    shutil.copyfile(no_si, fake_pdf)
    try:
        missing = pm.build_manifest(fake_pdf)
        c = pm.validate_manifest(missing)
        results.append(("missing_DOI_allowed", c["ok"] and missing["doi"]["status"] == "missing" and missing["doi"]["value"] is None, {
            "paper_id": missing["paper_id"],
            "doi": missing["doi"],
            "warnings": missing["warnings"],
        }))
    finally:
        fake_pdf.unlink(missing_ok=True)

    # Stored manifest is loaded; a PDF absent from the store falls back to a legacy manifest.
    stored, source = pm.load_for_pdf(no_si, outdir=OUT)
    results.append(("load_stored_manifest", source == "stored" and stored["paper_id"] == data2["paper_id"], {
        "source": source,
    }))
    all_pdfs = sorted((ROOT / "data/raw_pdfs").glob("*.pdf"))
    all_ok = True
    legacy_count = 0
    for pdf in all_pdfs:
        try:
            _, src = pm.load_for_pdf(pdf)
            legacy_count += 1 if src == "legacy" else 0
        except Exception as exc:  # noqa: BLE001
            all_ok = False
            results.append(("load_all_pdfs_error", False, {"pdf": pdf.name, "error": str(exc)}))
    results.append(("load_all_pdfs", all_ok, {
        "pdfs": len(all_pdfs),
        "legacy": legacy_count,
        "stored": len(all_pdfs) - legacy_count,
    }))
    empty = OUT / "empty"
    empty.mkdir(exist_ok=True)
    try:
        legacy, source = pm.load_for_pdf(no_si, outdir=empty)
        results.append(("legacy_manifest_fallback", source == "legacy" and legacy["legacy_generated"] is True, {
            "source": source,
            "warnings": legacy["warnings"],
        }))
    finally:
        shutil.rmtree(empty, ignore_errors=True)

    ok = all(x[1] for x in results)
    payload = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "manifest_version": pm.MANIFEST_VERSION,
        "ok": ok,
        "checks": [{"name": n, "ok": o, "detail": d} for n, o, d in results],
    }
    (ROOT / "evaluation" / "reports" / "manifest_test.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        "# A→B manifest contract test",
        "",
        f"- Manifest version: `{pm.MANIFEST_VERSION}`",
        f"- Result: {'PASS' if ok else 'FAIL'}",
        "",
        "| Check | Result | Detail |",
        "|---|---|---|",
    ]
    for name, passed, detail in results:
        lines.append(f"| {name} | {'PASS' if passed else 'FAIL'} | `{json.dumps(detail, ensure_ascii=False)}` |")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
