"""Backfill excerpt sidecars/paths for legacy rows (dry-run by default).

It resolves each legacy test through the snapshot or batch JSONL, writes a new
sidecar under data/control/excerpts, and with --apply points
source_location.excerpt_path at it. It never marks human verification.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
    sys.path.insert(0, str(ROOT / "tools"))

from server import excerpt_store  # noqa: E402
import trace_excerpt  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Backfill legacy excerpt_path (dry-run by default)")
    ap.add_argument("--db", default="data/ccus.sqlite")
    ap.add_argument("--outdir", default="data/control/excerpts")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    db = Path(args.db)
    outdir = Path(args.outdir)
    if not outdir.is_absolute():
        outdir = ROOT / outdir
    outdir.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT t.test_id,t.batch_id,l.location_id,l.excerpt_path
        FROM test t LEFT JOIN source_location l ON l.location_id=t.location_id
        WHERE l.excerpt_path IS NULL
        ORDER BY t.test_id
        """
    ).fetchall()
    conn.close()
    if args.limit:
        rows = rows[:args.limit]
    print(f"rows without excerpt_path: {len(rows)}")
    loc_counts = Counter(r["location_id"] for r in rows)
    resolved = []
    failed = []
    for r in rows:
        if loc_counts[r["location_id"]] > 1:
            failed.append({"test_id": r["test_id"], "reason": "shared_location_ambiguous"})
            continue
        info = trace_excerpt.resolve(db, r["test_id"], ROOT)
        if not info.get("excerpt"):
            failed.append({"test_id": r["test_id"], "warnings": info.get("warnings")})
            continue
        resolved.append((r, info))
    print(f"resolvable: {len(resolved)}; unresolved: {len(failed)}")
    for r, info in resolved[:10]:
        print(f"  test#{r['test_id']} source={info.get('source')} chars={len(info.get('excerpt') or '')}")
    if not args.apply:
        print("dry-run only; pass --apply to write sidecars and update excerpt_path")
        return
    conn = sqlite3.connect(db)
    try:
        with conn:
            for r, info in resolved:
                payload = {
                    "excerpt_version": "legacy-resolved-1.0",
                    "test_id": r["test_id"],
                    "batch_id": r["batch_id"],
                    "excerpt": info.get("excerpt"),
                    "excerpt_sha256": excerpt_store.sha256_text(info.get("excerpt") or ""),
                    "source": info.get("source"),
                    "match": info.get("match"),
                    "snapshot_path": info.get("raw_data_path"),
                    "snapshot_sha256": info.get("raw_data_hash"),
                    "loc_type": info.get("loc_type"),
                    "loc_label": info.get("loc_label"),
                    "human_verified": False,
                    "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                }
                path = outdir / f"test_{r['test_id']}.json"
                path.write_bytes(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))
                rel = excerpt_store.rel_path(path)
                conn.execute("UPDATE source_location SET excerpt_path=? WHERE location_id=?",
                             (rel, r["location_id"]))
        print(f"updated {len(resolved)} source_location.excerpt_path rows; human verification unchanged")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
