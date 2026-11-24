"""Future human-verification interface.

Default is a dry run. `--apply` requires reviewer and basis, updates qc_record
to human_verified=1, and writes a sidecar with the review basis and snapshot
hash. It refuses to mark unknown tests verified.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REVIEW_DIR = ROOT / "data" / "control" / "human_review"


def main() -> None:
    ap = argparse.ArgumentParser(description="Mark one test as human-verified")
    ap.add_argument("--db", default="data/ccus.sqlite")
    ap.add_argument("--test-id", type=int, required=True)
    ap.add_argument("--reviewer", required=True)
    ap.add_argument("--basis", required=True, help="what was checked and against where")
    ap.add_argument("--review-dir", default=str(REVIEW_DIR))
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    db = Path(args.db)
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True) if not args.apply else sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT test_id,batch_id,qc_level,qc_reason,raw_data_path,raw_data_hash FROM test WHERE test_id=?",
        (args.test_id,),
    ).fetchone()
    if row is None:
        conn.close()
        raise SystemExit(f"test_id {args.test_id} not found")
    existing = conn.execute("SELECT * FROM qc_record WHERE test_id=?", (args.test_id,)).fetchone()
    review_time = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    print(json.dumps({
        "test_id": row["test_id"],
        "qc_level": row["qc_level"],
        "raw_data_path": row["raw_data_path"],
        "existing_human_verified": None if existing is None else existing["human_verified"],
        "reviewer": args.reviewer,
        "review_time": review_time,
        "basis": args.basis,
        "apply": args.apply,
    }, ensure_ascii=False, indent=2))
    if not args.apply:
        print("dry-run only; pass --apply to write qc_record and the review sidecar")
        conn.close()
        return
    review_dir = Path(args.review_dir)
    review_dir.mkdir(parents=True, exist_ok=True)
    review = {
        "test_id": row["test_id"],
        "batch_id": row["batch_id"],
        "reviewer": args.reviewer,
        "review_time": review_time,
        "basis": args.basis,
        "raw_data_path": row["raw_data_path"],
        "raw_data_hash": row["raw_data_hash"],
        "human_verified": 1,
        "previous": None if existing is None else dict(existing),
    }
    (review_dir / f"test_{row['test_id']}.json").write_bytes(
        json.dumps(review, ensure_ascii=False, indent=2).encode("utf-8")
    )
    try:
        with conn:
            if existing is None:
                conn.execute(
                    "INSERT INTO qc_record(test_id,qc_level,qc_reason,reviewer,review_time,human_verified) "
                    "VALUES(?,?,?,?,?,1)",
                    (row["test_id"], row["qc_level"], row["qc_reason"], args.reviewer, review_time),
                )
            else:
                conn.execute(
                    "UPDATE qc_record SET reviewer=?, review_time=?, human_verified=1 WHERE test_id=?",
                    (args.reviewer, review_time, row["test_id"]),
                )
        print(f"updated test#{row['test_id']} human_verified=1")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
