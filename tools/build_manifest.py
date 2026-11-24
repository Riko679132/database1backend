"""Build and validate A -> B paper manifests.

Examples:
    python tools/build_manifest.py
    python tools/build_manifest.py --check
    python tools/build_manifest.py --pdf data/raw_pdfs/10.1021_je00005a025_0770ae31.pdf
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server import paper_manifest as pm  # noqa: E402


def _print_result(result: dict) -> None:
    print(f"manifest_version={result.get('manifest_version')} count={result.get('count')}")
    for entry in result.get("entries") or []:
        print(f"  {entry['paper_id']}  si={entry['si_status']}  {entry['pdf']}")
    for err in result.get("errors") or []:
        print(f"  [ERROR] {err.get('pdf')}: {err.get('error')}")


def _check(outdir: Path) -> int:
    errors = []
    warnings = []
    seen = set()
    for path in sorted(outdir.glob("*.json")):
        if path.name == "index.json":
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except ValueError as exc:
            errors.append(f"{path.name}: invalid JSON ({exc})")
            continue
        check = pm.validate_manifest(data, root=ROOT)
        if not check["ok"]:
            errors.extend(f"{path.name}: {e}" for e in check["errors"])
        warnings.extend(f"{path.name}: {w}" for w in check["warnings"])
        pid = data.get("paper_id")
        if pid in seen:
            errors.append(f"{path.name}: duplicate paper_id {pid}")
        seen.add(pid)
    print(f"checked={len(seen)} errors={len(errors)} warnings={len(warnings)}")
    for e in errors:
        print("  [ERROR]", e)
    for w in warnings:
        print("  [WARN]", w)
    return 0 if not errors else 1


def main() -> None:
    ap = argparse.ArgumentParser(description="A->B paper manifest builder")
    ap.add_argument("--pdf", action="append", default=[], help="PDF path; repeatable")
    ap.add_argument("--outdir", default=str(pm.MANIFEST_DIR))
    ap.add_argument("--check", action="store_true", help="validate stored manifests only")
    ap.add_argument("--json", action="store_true", help="print full index/result JSON")
    args = ap.parse_args()
    outdir = Path(args.outdir)
    if not outdir.is_absolute():
        outdir = ROOT / outdir

    if args.check and not args.pdf:
        raise SystemExit(_check(outdir))

    if args.pdf:
        known = pm._known_dois(ROOT)
        triage = pm._triage(ROOT)
        assessment = pm._assessment(ROOT)
        entries, errors = [], []
        for raw in args.pdf:
            pdf = Path(raw)
            if not pdf.is_absolute():
                pdf = ROOT / pdf
            try:
                data = pm.build_manifest(pdf, root=ROOT, known=known, triage=triage, assessment=assessment)
            except pm.ManifestError as exc:
                errors.append({"pdf": pdf.name, "error": str(exc)})
                continue
            check = pm.validate_manifest(data, root=ROOT)
            if not check["ok"]:
                errors.append({"pdf": pdf.name, "error": "; ".join(check["errors"])})
                continue
            path = pm.write_manifest(data, outdir)
            entries.append({
                "paper_id": data["paper_id"],
                "pdf": data["pdf"]["path"],
                "si_status": data["si"]["status"],
                "manifest": path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.as_posix(),
            })
        result = {"count": len(entries), "entries": entries, "errors": errors}
    else:
        result = pm.build_all(root=ROOT, outdir=outdir)

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print_result(result)
    raise SystemExit(0 if not result.get("errors") else 1)


if __name__ == "__main__":
    main()
