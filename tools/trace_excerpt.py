"""Resolve a database test row to its excerpt sidecar or snapshot record.

Read-only. It handles both new records (source_location.excerpt_path set) and
older records (NULL excerpt_path), falling back to the snapshot.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server import excerpt_store  # noqa: E402


def _load_test(db: Path, test_id: int) -> dict:
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        """
        SELECT t.*, s.doi, s.title, s.pdf_path,
               l.loc_type, l.loc_label, l.loc_detail, l.excerpt_path,
               q.qc_level AS qc_record_level, q.human_verified, q.reviewer, q.review_time,
               c.standard_name AS amine, r.wt_a, r.wt_b
        FROM test t
        LEFT JOIN source s ON s.source_id = t.source_id
        LEFT JOIN source_location l ON l.location_id = t.location_id
        LEFT JOIN qc_record q ON q.test_id = t.test_id
        LEFT JOIN recipe r ON r.recipe_id = t.recipe_id
        LEFT JOIN compound c ON c.compound_id = r.amine_a_id
        WHERE t.test_id = ?
        """,
        (test_id,),
    ).fetchone()
    if row is None:
        conn.close()
        raise SystemExit(f"test_id {test_id} not found")
    data = dict(row)
    perf = [dict(x) for x in conn.execute(
        "SELECT metric_name, value, unit FROM performance WHERE test_id=?", (test_id,)
    )]
    data["metrics"] = {p["metric_name"]: p["value"] for p in perf if p["metric_name"]}
    conn.close()
    return data


def resolve(db: Path, test_id: int, root: Path = ROOT) -> dict:
    t = _load_test(db, test_id)
    warnings = []
    sidecar_path = t.get("excerpt_path")
    result = {
        "test_id": test_id,
        "doi": t.get("doi"),
        "loc_type": t.get("loc_type"),
        "loc_label": t.get("loc_label"),
        "loc_detail": t.get("loc_detail"),
        "raw_data_path": t.get("raw_data_path"),
        "raw_data_hash": t.get("raw_data_hash"),
        "human_verified": t.get("human_verified"),
        "verified_status": (
            "not_recorded" if t.get("human_verified") is None
            else ("verified" if int(t.get("human_verified")) == 1 else "unverified")
        ),
        "reviewer": t.get("reviewer"),
        "review_time": t.get("review_time"),
        "sidecar": None,
        "snapshot": None,
        "excerpt": None,
        "fields": [],
        "references": [],
        "warnings": warnings,
    }
    if sidecar_path:
        side = excerpt_store.read_sidecar(sidecar_path, root=root)
        result["sidecar"] = side
        if side.get("status") == "ok":
            data = side.get("data") or {}
            result.update({
                "excerpt": data.get("excerpt") or side.get("excerpt"),
                "record_id": data.get("record_id"),
                "fields": data.get("fields") or [],
                "references": data.get("references") or [],
                "source": "sidecar",
                "sidecar_format": side.get("format") or "json",
            })
            return result
        warnings.append(f"excerpt sidecar {side.get('status')}: {sidecar_path}")
    else:
        warnings.append("source_location.excerpt_path is NULL (legacy record)")

    raw_path = t.get("raw_data_path")
    if raw_path:
        p = Path(raw_path)
        if not p.is_absolute():
            p = root / p
        if not p.exists():
            warnings.append(f"snapshot missing: {raw_path}")
            result["snapshot"] = {"status": "missing", "path": raw_path}
        else:
            snap = json.loads(p.read_text(encoding="utf-8"))
            result["snapshot"] = {"status": "ok", "path": raw_path,
                                  "sha256": snap.get("paper", {}).get("pdf_sha256")}
            match = excerpt_store.resolve_from_snapshot(
                snap,
                record_id=result.get("record_id"),
                test={
                    "doi": t.get("doi"), "amine": t.get("amine"),
                    "wt_a": t.get("wt_a"), "temperature_K": t.get("temperature_K"),
                    "co2_partial_kPa": t.get("co2_partial_kPa"),
                    "initial_loading": t.get("initial_loading"),
                    "metrics": t.get("metrics") or {},
                },
            )
            if match.get("status") == "ok":
                rec = match.get("record") or {}
                result.update({
                    "excerpt": match.get("excerpt") or (rec.get("source") or {}).get("excerpt"),
                    "record_id": rec.get("record_id"),
                    "fields": [
                        {"field": "record", "value": (rec.get("source") or {}).get("loc_label") or match.get("loc_label")}
                    ],
                    "references": [],
                    "source": "snapshot",
                    "match": match.get("match"),
                })
                return result
            warnings.append(f"snapshot record {match.get('status')}")
    else:
        warnings.append("raw_data_path is NULL")

    batch_id = t.get("batch_id")
    if batch_id:
        match = excerpt_store.resolve_from_batch(
            root / "extractions" / batch_id,
            {
                "doi": t.get("doi"), "amine": t.get("amine"),
                "wt_a": t.get("wt_a"), "temperature_K": t.get("temperature_K"),
                "co2_partial_kPa": t.get("co2_partial_kPa"),
                "initial_loading": t.get("initial_loading"),
                "metrics": t.get("metrics") or {},
            },
        )
        if match.get("status") == "ok":
            result.update({
                "excerpt": match.get("excerpt"),
                "source": "batch_jsonl",
                "match": match.get("match"),
                "loc_label": match.get("loc_label") or result.get("loc_label"),
                "batch_jsonl": f"extractions/{batch_id}",
            })
            return result
        warnings.append(f"batch jsonl {match.get('status')}")

    result["status"] = "unresolved"
    return result


def main() -> None:
    ap = argparse.ArgumentParser(description="Trace a DB test row to its excerpt")
    ap.add_argument("--db", default="data/ccus.sqlite")
    ap.add_argument("--test-id", type=int, required=True)
    ap.add_argument("--root", default=str(ROOT))
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    result = resolve(Path(args.db), args.test_id, Path(args.root))
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"test_id={result['test_id']} doi={result.get('doi')}")
        print(f"loc={result.get('loc_type')} {result.get('loc_label')}")
        print(f"source={result.get('source')} human_verified={result.get('human_verified')}")
        print("warnings:", "; ".join(result.get("warnings") or []) or "none")
        print("excerpt:")
        print(result.get("excerpt") or "[NOT FOUND]")
    raise SystemExit(0 if result.get("excerpt") else 1)


if __name__ == "__main__":
    main()
