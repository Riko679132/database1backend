"""Initialize missing qc_record rows without marking anything human-verified.

Default is a read-only dry run. `--apply` inserts one qc_record per test that
has none, using the test's existing qc_level/qc_reason and human_verified=0.
It does not modify test/source/test rows and does not invent reviewers.
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="Backfill qc_record rows (dry-run by default)")
    ap.add_argument("--db", default="data/ccus.sqlite")
    ap.add_argument("--apply", action="store_true", help="write the missing rows")
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()
    db = Path(args.db)
    if not db.exists():
        raise SystemExit(f"db not found: {db}")
    conn = sqlite3.connect(f"file:{db}?mode=ro", uri=True) if not args.apply else sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT t.test_id, t.qc_level, t.qc_reason, t.test_origin
        FROM test t LEFT JOIN qc_record q ON q.test_id = t.test_id
        WHERE q.qc_id IS NULL
        ORDER BY t.test_id
        """
    ).fetchall()
    if args.limit:
        rows = rows[:args.limit]
    print(f"tests without qc_record: {len(rows)}")
    for r in rows[:20]:
        print(f"  test#{r['test_id']} {r['test_origin']} {r['qc_level']} {str(r['qc_reason'])[:80]}")
    if not args.apply:
        print("dry-run only; pass --apply to insert qc_record with human_verified=0")
        conn.close()
        return
    try:
        with conn:
            for r in rows:
                conn.execute(
                    "INSERT INTO qc_record(test_id,qc_level,qc_reason,reviewer,review_time,human_verified) "
                    "VALUES(?,?,?,?,?,0)",
                    (r["test_id"], r["qc_level"], r["qc_reason"], None, None),
                )
        print(f"inserted {len(rows)} qc_record rows; human_verified=0, reviewer=NULL")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
