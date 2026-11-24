"""End-to-end provenance test on a temporary database.

Covers: import -> test/source_location/qc_record -> excerpt sidecar -> snapshot;
same-paper multiple records; backup copy; missing/corrupt sidecar; legacy
snapshot fallback; qc_record initialization/backfill; human-review interface;
gold-standard export fields.
"""
from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server import excerpt_store  # noqa: E402

ART = ROOT / "evaluation" / "artifacts" / "provenance"
REPORT = ROOT / "evaluation" / "reports" / "provenance_test.md"
PY = sys.executable


def latest_b_flow_batch() -> Path:
    batches = sorted((ROOT / "evaluation" / "artifacts" / "b_flow" / "batches").glob("batch_*"))
    for batch in reversed(batches):
        if (batch / "raw_agent.jsonl").exists():
            return batch
    raise RuntimeError("no B-flow batch with raw_agent.jsonl")


def make_config(path: Path, db: Path) -> None:
    backup = path.parent / "backup"
    backup.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "database:\n"
        f"  path: {db.as_posix()}\n"
        f"  backup_dir: {backup.as_posix()}\n"
        f"  lock_file: {(path.parent / 'db.lock').as_posix()}\n",
        encoding="utf-8",
    )


def init_db(db: Path) -> None:
    conn = sqlite3.connect(db)
    conn.executescript((ROOT / "scripts" / "schema.sql").read_text(encoding="utf-8"))
    conn.commit()
    conn.close()


def run_import(batch: Path, db: Path) -> str:
    cfg = ART / "run" / "config.yaml"
    make_config(cfg, db)
    proc = subprocess.run(
        [PY, str(ROOT / "scripts/import_jsonl.py"), "--input", str(batch / "raw_agent.jsonl"),
         "--config", str(cfg), "--batch-id", "provenance_test"],
        cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    if proc.returncode != 0:
        raise RuntimeError(proc.stdout + "\n" + proc.stderr)
    return proc.stdout


def main() -> None:
    if ART.exists():
        shutil.rmtree(ART)
    (ART / "run").mkdir(parents=True)
    batch = latest_b_flow_batch()
    db = ART / "run" / "provenance.sqlite"
    init_db(db)
    output = run_import(batch, db)
    raw_records = [json.loads(x) for x in (batch / "raw_agent.jsonl").read_text(encoding="utf-8").splitlines() if x.strip()]

    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    tests = conn.execute(
        """
        SELECT t.test_id,t.source_id,t.location_id,t.raw_data_path,t.raw_data_hash,
               s.doi,l.excerpt_path,l.loc_label,q.qc_level,q.qc_reason,q.human_verified,q.reviewer
        FROM test t LEFT JOIN source s ON s.source_id=t.source_id
        LEFT JOIN source_location l ON l.location_id=t.location_id
        LEFT JOIN qc_record q ON q.test_id=t.test_id
        ORDER BY t.test_id
        """
    ).fetchall()
    checks = []
    checks.append({"name": "imported_tests", "ok": len(tests) == len(raw_records),
                   "tests": len(tests), "raw_records": len(raw_records), "import_output": output[-200:]})
    checks.append({"name": "qc_record_initialized", "ok": all(
        t["human_verified"] == 0 and t["reviewer"] is None for t in tests
    ), "qc_rows": len(tests)})
    checks.append({"name": "excerpt_path_set", "ok": all(t["excerpt_path"] for t in tests),
                   "with_path": sum(1 for t in tests if t["excerpt_path"])})
    sidecars = []
    for t in tests:
        side = excerpt_store.read_sidecar(t["excerpt_path"], root=ROOT)
        sidecars.append(side)
        assert side.get("status") == "ok", (t["test_id"], side)
        data = side["data"]
        assert data.get("snapshot_sha256") == t["raw_data_hash"], (t["test_id"], "snapshot hash")
    checks.append({"name": "sidecar_hashes", "ok": True, "sidecars": len(sidecars)})
    by_record = {r.get("record_id"): r for r in raw_records}
    matched = 0
    for t, side in zip(tests, sidecars):
        data = side["data"]
        raw = by_record.get(data.get("record_id"))
        if raw and (raw.get("source") or {}).get("excerpt") == data.get("excerpt"):
            matched += 1
    checks.append({"name": "same_paper_records_not_crosslinked", "ok": matched == len(tests),
                   "matched": matched})
    same_doi = {}
    for t in tests:
        same_doi.setdefault(t["doi"], []).append(t["excerpt_path"])
    distinct_ok = all(len(set(paths)) == len(paths) for paths in same_doi.values())
    checks.append({"name": "distinct_sidecars_per_record", "ok": distinct_ok,
                   "groups": len(same_doi)})
    conn.close()

    # Trace new records through sidecars.
    sys.path.insert(0, str(ROOT / "tools"))
    import trace_excerpt
    traced = [trace_excerpt.resolve(db, t["test_id"], ROOT) for t in tests[:3]]
    checks.append({"name": "trace_new_records", "ok": all(
        x.get("source") == "sidecar" and x.get("excerpt") for x in traced
    ), "traced": [
        {"test_id": x["test_id"], "source": x.get("source"), "chars": len(x.get("excerpt") or "")} for x in traced
    ]})

    # Backup copy still resolves relative paths.
    copy_db = ART / "run" / "provenance_copy.sqlite"
    shutil.copyfile(db, copy_db)
    copied = trace_excerpt.resolve(copy_db, tests[0]["test_id"], ROOT)
    checks.append({"name": "backup_reload", "ok": bool(copied.get("source") == "sidecar" and copied.get("excerpt"))})

    # Corrupt and missing sidecars must be reported, with snapshot fallback.
    corrupt = ART / "run" / "corrupt.json"
    corrupt.write_text(json.dumps({"record_id": "x", "excerpt": "tampered", "excerpt_sha256": "0" * 64}), encoding="utf-8")
    conn = sqlite3.connect(db)
    conn.execute("UPDATE source_location SET excerpt_path=? WHERE location_id=?", (str(corrupt), tests[0]["location_id"]))
    conn.commit()
    conn.close()
    bad = trace_excerpt.resolve(db, tests[0]["test_id"], ROOT)
    checks.append({"name": "corrupt_sidecar_reported", "ok": bool(any("hash_mismatch" in w for w in bad.get("warnings") or [])
                   and bad.get("excerpt")), "warnings": bad.get("warnings"), "source": bad.get("source")})
    conn = sqlite3.connect(db)
    conn.execute("UPDATE source_location SET excerpt_path=? WHERE location_id=?",
                 (str(ART / "run" / "missing.json"), tests[0]["location_id"]))
    conn.commit()
    conn.close()
    missing = trace_excerpt.resolve(db, tests[0]["test_id"], ROOT)
    checks.append({"name": "missing_sidecar_reported", "ok": bool(any("missing" in w for w in missing.get("warnings") or [])
                   and missing.get("excerpt")), "warnings": missing.get("warnings"), "source": missing.get("source")})

    # Legacy main-database snapshots: direct record, whitelist_rows, tables.
    legacy = {}
    for tid in (3, 24, 27, 31):
        r = trace_excerpt.resolve(ROOT / "data/ccus.sqlite", tid, ROOT)
        legacy[tid] = {"source": r.get("source"), "match": r.get("match"),
                       "chars": len(r.get("excerpt") or ""), "warnings": r.get("warnings")}
    checks.append({"name": "legacy_snapshot_fallback", "ok": all(v["chars"] > 0 for v in legacy.values()),
                   "legacy": legacy})

    # Every existing row must resolve, including old paper-level snapshots and
    # legacy L3/simulation rows whose batch has raw JSONL but no snapshot.
    main = sqlite3.connect(f"file:{ROOT / 'data/ccus.sqlite'}?mode=ro", uri=True)
    l2_ids = [r[0] for r in main.execute("select test_id from test where qc_level='L2' order by test_id")]
    all_ids = [r[0] for r in main.execute("select test_id from test order by test_id")]
    main.close()
    resolved = {}
    for tid in all_ids:
        r = trace_excerpt.resolve(ROOT / "data/ccus.sqlite", tid, ROOT)
        if r.get("excerpt"):
            resolved[tid] = r.get("source")
    checks.append({"name": "all_L2_traceable", "ok": all(tid in resolved for tid in l2_ids),
                   "l2": len(l2_ids), "resolved_l2": sum(1 for tid in l2_ids if tid in resolved),
                   "sources_l2": {k: list(resolved.get(t) for t in l2_ids).count(k) for k in set(resolved.get(t) for t in l2_ids)}})
    checks.append({"name": "all_tests_traceable", "ok": len(resolved) == len(all_ids),
                   "tests": len(all_ids), "resolved": len(resolved),
                   "sources": {k: list(resolved.values()).count(k) for k in set(resolved.values())}})

    # qc_record backfill on a temp copy (not the main DB).
    backfill_db = ART / "run" / "backfill.sqlite"
    shutil.copyfile(db, backfill_db)
    conn = sqlite3.connect(backfill_db)
    conn.execute("DELETE FROM qc_record")
    conn.commit()
    conn.close()
    proc = subprocess.run([PY, str(ROOT / "tools/backfill_qc_record.py"), "--db", str(backfill_db)],
                          cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    dry = json.loads(proc.stdout.splitlines()[0].split(":", 1)[1]) if proc.stdout.startswith("tests without") else None
    proc2 = subprocess.run([PY, str(ROOT / "tools/backfill_qc_record.py"), "--db", str(backfill_db), "--apply"],
                           cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    conn = sqlite3.connect(backfill_db)
    n_qc = conn.execute("select count(*) from qc_record").fetchone()[0]
    n_unverified = conn.execute("select count(*) from qc_record where human_verified=0 and reviewer is null").fetchone()[0]
    conn.close()
    checks.append({"name": "qc_record_backfill_temp", "ok": proc.returncode == 0 and proc2.returncode == 0
                   and n_qc == len(tests) and n_unverified == n_qc, "dry_count": dry,
                   "qc_rows": n_qc, "unverified": n_unverified})

    # Future human-review interface on the temp DB only.
    review_dir = ART / "run" / "human_review"
    proc = subprocess.run([
        PY, str(ROOT / "tools/mark_human_verified.py"), "--db", str(backfill_db),
        "--test-id", str(tests[0]["test_id"]), "--reviewer", "test_reviewer",
        "--basis", "fixture check", "--review-dir", str(review_dir), "--apply",
    ], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    conn = sqlite3.connect(backfill_db)
    hv = conn.execute("select human_verified,reviewer from qc_record where test_id=?", (tests[0]["test_id"],)).fetchone()
    conn.close()
    review_file = review_dir / f"test_{tests[0]['test_id']}.json"
    checks.append({"name": "human_review_interface_temp", "ok": proc.returncode == 0 and hv == (1, "test_reviewer")
                   and review_file.exists(), "qc": hv, "review_file": review_file.exists()})

    # Legacy excerpt backfill works on a copy; the main DB stays byte-identical.
    import hashlib
    main_db = ROOT / "data/ccus.sqlite"
    before = hashlib.sha256(main_db.read_bytes()).hexdigest()
    main_copy = ART / "run" / "main_copy.sqlite"
    shutil.copyfile(main_db, main_copy)
    bdir = ART / "run" / "main_copy_excerpts"
    proc = subprocess.run([PY, str(ROOT / "tools/backfill_excerpt_path.py"), "--db", str(main_copy),
                           "--outdir", str(bdir), "--apply"], cwd=ROOT, capture_output=True,
                          text=True, encoding="utf-8", errors="replace")
    conn = sqlite3.connect(main_copy)
    n_paths = conn.execute("select count(*) from source_location where excerpt_path is not null").fetchone()[0]
    conn.close()
    after = hashlib.sha256(main_db.read_bytes()).hexdigest()
    checks.append({"name": "excerpt_backfill_main_copy", "ok": proc.returncode == 0 and n_paths >= 59
                   and before == after, "paths": n_paths, "sidecars": len(list(bdir.glob("*.json"))),
                   "main_db_unchanged": before == after})

    # Export keeps excerpt_path and human_verified fields.
    export_dir = ART / "run" / "export"
    proc = subprocess.run([PY, str(ROOT / "tools/export_gold_standard.py"), "--db", str(db),
                           "--outdir", str(export_dir)], cwd=ROOT, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    exported = json.loads((export_dir / "gold_standard_L2.json").read_text(encoding="utf-8"))
    has_fields = all("excerpt_path" in (r["source"]) and "human_verified" in (r["qc"])
                     for r in exported["records"])
    checks.append({"name": "export_fields", "ok": proc.returncode == 0 and has_fields,
                   "l2_records": exported["n_tests"]})

    ok = all(c["ok"] for c in checks)
    payload = {"created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "ok": ok,
               "batch": str(batch), "checks": checks}
    (ROOT / "evaluation" / "reports" / "provenance_test.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        "# Provenance test (temporary database)",
        "",
        f"- Result: {'PASS' if ok else 'FAIL'}",
        f"- B-flow batch: `{batch.as_posix()}`",
        "",
        "| Check | Result | Detail |",
        "|---|---|---|",
    ]
    for c in checks:
        detail = {k: v for k, v in c.items() if k not in ("name", "ok")}
        lines.append(f"| {c['name']} | {'PASS' if c['ok'] else 'FAIL'} | `{json.dumps(detail, ensure_ascii=False)[:500]}` |")
    lines += [
        "",
        "The temporary database is under `evaluation/artifacts/provenance/run`; the main `data/ccus.sqlite` was not written.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
