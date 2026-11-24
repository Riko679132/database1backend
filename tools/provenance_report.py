"""Read-only provenance coverage report for database test rows."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
import sys
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from server import excerpt_store  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default="data/ccus.sqlite")
    ap.add_argument("--quality", default="L2")
    ap.add_argument("--strict", action="store_true")
    args = ap.parse_args()
    conn = sqlite3.connect(f"file:{args.db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    where = "WHERE t.qc_level=?" if args.quality else ""
    params = (args.quality,) if args.quality else ()
    rows = conn.execute(
        f"""
        SELECT t.test_id, t.raw_data_path, t.raw_data_hash, l.excerpt_path,
               q.human_verified
        FROM test t
        LEFT JOIN source_location l ON l.location_id=t.location_id
        LEFT JOIN qc_record q ON q.test_id=t.test_id
        {where}
        ORDER BY t.test_id
        """,
        params,
    ).fetchall()
    report = {
        "db": args.db,
        "quality_filter": args.quality or "all",
        "tests": len(rows),
        "snapshot_present": 0,
        "excerpt_path_present": 0,
        "sidecar_ok": 0,
        "sidecar_missing_or_bad": 0,
        "qc_record_present": 0,
        "human_verified_1": 0,
        "issues": [],
    }
    for r in rows:
        raw = Path(r["raw_data_path"]) if r["raw_data_path"] else None
        if raw and not raw.is_absolute():
            raw = ROOT / raw
        if raw and raw.exists():
            report["snapshot_present"] += 1
        else:
            report["issues"].append({"test_id": r["test_id"], "issue": "snapshot_missing",
                                     "path": r["raw_data_path"]})
        if r["excerpt_path"]:
            report["excerpt_path_present"] += 1
            side = excerpt_store.read_sidecar(r["excerpt_path"], root=ROOT)
            if side.get("status") == "ok":
                report["sidecar_ok"] += 1
            else:
                report["sidecar_missing_or_bad"] += 1
                report["issues"].append({"test_id": r["test_id"], "issue": "sidecar_" + side.get("status"),
                                         "path": r["excerpt_path"]})
        else:
            report["issues"].append({"test_id": r["test_id"], "issue": "excerpt_path_null",
                                     "path": None})
        if r["human_verified"] is not None:
            report["qc_record_present"] += 1
            if int(r["human_verified"]) == 1:
                report["human_verified_1"] += 1
        else:
            report["issues"].append({"test_id": r["test_id"], "issue": "qc_record_missing",
                                     "path": None})
    conn.close()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.strict:
        raise SystemExit(0 if not report["issues"] else 1)


if __name__ == "__main__":
    main()
