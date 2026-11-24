"""Stable per-record excerpt sidecars.

The database has no `source.excerpt` column. `source_location.excerpt_path`
already exists, so B writes one immutable JSON sidecar per record and links it
through that field. The snapshot and the sidecar both carry the record_id and
hashes, so a database row can be traced without guessing a temporary filename.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import time
from pathlib import Path

from .settings import ROOT

EXCERPT_VERSION = "phase5-1.0"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(text.encode("utf-8"))


def rel_path(path: Path, root: Path = ROOT) -> str:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except (ValueError, OSError):
        return path.as_posix()


def _record_key(rec: dict) -> list:
    recipe = rec.get("recipe") or {}
    test = rec.get("test") or {}
    a = recipe.get("amine_a") or {}
    b = recipe.get("amine_b") or {}
    return [
        (rec.get("source") or {}).get("doi"),
        a.get("standard_name"), b.get("standard_name"),
        recipe.get("wt_a"), recipe.get("wt_b"),
        test.get("temperature_K"), test.get("co2_partial_kPa"),
        sorted((p.get("metric_name"), p.get("value")) for p in rec.get("performance") or []),
    ]


def record_id(batch_id: str, paper_id: str, rec: dict, index: int) -> str:
    payload = {
        "batch_id": batch_id,
        "paper_id": paper_id,
        "index": index,
        "key": _record_key(rec),
        "loc_label": (rec.get("source") or {}).get("loc_label"),
        "excerpt": (rec.get("source") or {}).get("excerpt"),
    }
    return sha256_bytes(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8"))[:24]


def _evidence_items(raw: dict) -> list[dict]:
    ev = raw.get("evidence")
    if isinstance(ev, list):
        return [x for x in ev if isinstance(x, dict) and x.get("field")]
    if isinstance(ev, dict):
        out = []
        for field, value in ev.items():
            if isinstance(value, dict):
                out.append({"field": field, **value})
            elif isinstance(value, str):
                out.append({"field": field, "type": value})
        return out
    return []


def _record_fields(rec: dict, raw: dict) -> list[dict]:
    evidence = {}
    for item in _evidence_items(raw):
        field = str(item.get("field"))
        evidence.setdefault(field, {
            "evidence_type": str(item.get("type") or "Unknown"),
            "note": str(item.get("note") or "")[:300],
        })
    out = []
    test = rec.get("test") or {}
    recipe = rec.get("recipe") or {}
    for field in ("temperature_K", "co2_vol_pct", "co2_partial_kPa", "total_pressure_kPa",
                  "gas_basis", "p_h2o_kPa", "y_h2o", "water_activity",
                  "initial_loading", "rich_loading", "lean_loading"):
        if test.get(field) is not None:
            out.append({"field": field, "value": test.get(field), **evidence.get(field, {"evidence_type": "Unknown"})})
    for field in ("wt_a", "wt_b", "water_wt", "total_amine_wt"):
        if recipe.get(field) is not None:
            out.append({"field": field, "value": recipe.get(field), **evidence.get(field, {"evidence_type": "Unknown"})})
    for perf in rec.get("performance") or []:
        metric = perf.get("metric_name")
        if metric and perf.get("value") is not None:
            key = f"performance.{metric}"
            out.append({"field": key, "value": perf.get("value"), **evidence.get(key, {"evidence_type": "Unknown"})})
    return out


def _references(raw: dict, rec: dict) -> list[dict]:
    src = rec.get("source") or {}
    excerpt = str(src.get("excerpt") or "")
    refs = []
    for item in _evidence_items(raw):
        refs.append({
            "field": item.get("field"),
            "evidence_type": str(item.get("type") or "Unknown"),
            "note": str(item.get("note") or "")[:300],
            "loc_type": src.get("loc_type"),
            "loc_label": src.get("loc_label"),
            "excerpt": excerpt,
        })
    if excerpt and not any(r.get("field") == "source.excerpt" for r in refs):
        refs.append({
            "field": "source.excerpt",
            "evidence_type": "Explicit",
            "note": "record source excerpt",
            "loc_type": src.get("loc_type"),
            "loc_label": src.get("loc_label"),
            "excerpt": excerpt,
        })
    return refs


def write_records(
    batch_dir: Path,
    pairs: list[tuple],
    *,
    batch_id: str,
    paper_id: str,
    snapshot_path: Path,
    snapshot_hash: str,
) -> list[dict]:
    """Write one excerpt sidecar per record and link it into the record."""
    excerpt_dir = batch_dir / "raw" / "excerpts"
    excerpt_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    snap_rel = rel_path(snapshot_path)
    for index, pair in enumerate(pairs):
        raw, rec = pair[0], pair[1]
        rid = rec.get("record_id") or record_id(batch_id, paper_id, rec, index)
        rec["record_id"] = rid
        src = rec.setdefault("source", {})
        excerpt = str(src.get("excerpt") or "")
        payload = {
            "excerpt_version": EXCERPT_VERSION,
            "record_id": rid,
            "batch_id": batch_id,
            "paper_id": paper_id,
            "doi": src.get("doi"),
            "snapshot_path": snap_rel,
            "snapshot_sha256": snapshot_hash,
            "loc_type": src.get("loc_type"),
            "loc_label": src.get("loc_label"),
            "excerpt": excerpt,
            "excerpt_sha256": sha256_text(excerpt),
            "fields": _record_fields(rec, raw),
            "references": _references(raw, rec),
            "gas_phase": rec.get("gas_phase"),
            "human_verified": False,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        }
        if not excerpt:
            payload["status"] = "missing_excerpt"
        else:
            payload["status"] = "ok"
        data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        path = excerpt_dir / f"{rid}.json"
        path.write_bytes(data)
        digest = sha256_bytes(data)
        if excerpt:
            src["excerpt_path"] = rel_path(path)
            src["excerpt_sha256"] = digest
        entries.append({
            "record_id": rid,
            "paper_id": paper_id,
            "doi": src.get("doi"),
            "snapshot_path": snap_rel,
            "snapshot_sha256": snapshot_hash,
            "excerpt_path": rel_path(path) if excerpt else None,
            "excerpt_sha256": digest if excerpt else None,
            "loc_type": src.get("loc_type"),
            "loc_label": src.get("loc_label"),
            "status": payload["status"],
        })
    _update_index(batch_dir, entries)
    return entries


def _update_index(batch_dir: Path, entries: list[dict]) -> None:
    path = batch_dir / "raw" / "excerpt_index.json"
    current = {}
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("records"), dict):
                current = data["records"]
        except ValueError:
            current = {}
    for entry in entries:
        current[entry["record_id"]] = entry
    payload = {
        "excerpt_version": EXCERPT_VERSION,
        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "records": current,
    }
    path.write_bytes(json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"))


def read_sidecar(path: str | Path, root: Path = ROOT) -> dict:
    p = Path(path)
    if not p.is_absolute():
        p = root / p
    if not p.exists():
        return {"status": "missing", "path": rel_path(p, root)}
    text = p.read_text(encoding="utf-8", errors="replace")
    if p.suffix.lower() != ".json":
        # Early batches stored a plain-text excerpt next to the snapshot.
        return {
            "status": "ok",
            "format": "legacy_text",
            "path": rel_path(p, root),
            "excerpt": text,
            "data": {"excerpt": text, "status": "legacy_text"},
        }
    try:
        data = json.loads(text)
    except ValueError as exc:
        return {"status": "corrupt_json", "path": rel_path(p, root), "error": str(exc)}
    if not isinstance(data, dict):
        return {"status": "corrupt_shape", "path": rel_path(p, root)}
    expected = data.get("excerpt_sha256")
    actual = sha256_text(str(data.get("excerpt") or ""))
    if expected and expected != actual:
        return {"status": "hash_mismatch", "path": rel_path(p, root),
                "expected": expected, "actual": actual}
    return {"status": "ok", "path": rel_path(p, root), "data": data}


def _num(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _record_score(candidate: dict, test: dict) -> float:
    rec = candidate.get("record") or candidate
    score = 0.0
    src = rec.get("source") or {}
    if str(src.get("doi") or "").lower() != str(test.get("doi") or "").lower():
        return math.inf
    recipe = rec.get("recipe") or {}
    amine = (recipe.get("amine_a") or {}).get("standard_name")
    if amine and test.get("amine") and str(amine).lower() != str(test["amine"]).lower():
        return math.inf
    for key, tol in (("wt_a", 0.2), ("temperature_K", 0.1), ("co2_partial_kPa", 1.0), ("initial_loading", 0.02)):
        a, b = recipe.get(key, rec.get("test", {}).get(key)), test.get(key)
        if a is None or b is None:
            continue
        score += min(abs(float(a) - float(b)) / max(tol, 1e-9), 10.0)
    metrics = {p.get("metric_name"): p.get("value") for p in rec.get("performance") or []}
    for metric, value in (test.get("metrics") or {}).items():
        if metric not in metrics:
            score += 5
        elif value is not None:
            score += min(abs(float(metrics[metric]) - float(value)) / max(abs(float(value)), 1e-9), 1.0) * 2
    return score


def _row_matches(test: dict, row: dict) -> bool:
    amine = row.get("amine") or row.get("name_full") or row.get("name")
    if amine and test.get("amine") and str(amine).lower().split()[0] != str(test["amine"]).lower().split()[0]:
        return False
    targets = []
    for key in ("rich_loading", "lean_loading"):
        if test.get(key) is not None:
            targets.append(float(test[key]))
    for metric in ("equilibrium_loading", "cyclic_capacity"):
        value = (test.get("metrics") or {}).get(metric)
        if value is not None:
            targets.append(float(value))
    if not targets:
        return bool(amine and test.get("amine"))
    for key in ("co2_loading", "rich_loading", "lean_loading", "loading", "alpha", "cyclic_capacity"):
        value = row.get(key)
        if value is None:
            continue
        try:
            value = float(value)
        except (TypeError, ValueError):
            continue
        if any(abs(value - target) <= 0.02 for target in targets):
            return True
    return False


def _resolve_old_snapshot(snapshot: dict, test: dict) -> dict | None:
    """Resolve paper-level Phase-3/4 snapshots that have whitelist_rows or tables."""
    if isinstance(snapshot.get("whitelist_rows"), list):
        rows = snapshot["whitelist_rows"]
        lines = snapshot.get("raw_text_lines") or []
        for idx, row in enumerate(rows):
            if _row_matches(test, row):
                line = lines[idx] if idx < len(lines) else json.dumps(row, ensure_ascii=False)
                caption = snapshot.get("table_caption") or snapshot.get("table") or ""
                return {
                    "status": "ok",
                    "match": "whitelist_row",
                    "excerpt": f"{caption} | {line}".strip(" |"),
                    "loc_label": snapshot.get("table") or snapshot.get("table_caption"),
                    "row": row,
                }
    tables = snapshot.get("tables")
    if isinstance(tables, dict):
        for table_no, table in tables.items():
            if not isinstance(table, dict):
                continue
            for row in table.get("rows_40C_p_kPa_alpha") or []:
                if isinstance(row, (list, tuple)) and len(row) >= 2:
                    p, alpha = float(row[0]), float(row[1])
                    p_test = test.get("co2_partial_kPa")
                    targets = [test.get("rich_loading"), test.get("lean_loading"),
                               (test.get("metrics") or {}).get("equilibrium_loading")]
                    targets = [float(x) for x in targets if x is not None]
                    if p_test is not None and abs(p - float(p_test)) <= 1.0 and any(abs(alpha - t) <= 0.02 for t in targets):
                        caption = table.get("caption") or f"Table {table_no}"
                        page = table.get("pdf_page")
                        return {
                            "status": "ok",
                            "match": "table_row",
                            "excerpt": f"{caption}; p_CO2={p} kPa, loading={alpha} (Table {table_no}, p.{page})",
                            "loc_label": f"Table {table_no}, p.{page}",
                            "row": {"p_kPa": p, "loading": alpha},
                        }
    # Later hand-built snapshots store one exact row/text.
    for key in ("raw_row_text", "raw_table_row"):
        value = snapshot.get(key)
        if value:
            caption = snapshot.get("table_caption") or snapshot.get("table") or ""
            return {
                "status": "ok",
                "match": key,
                "excerpt": f"{caption} | {value}".strip(" |"),
                "loc_label": snapshot.get("table") or snapshot.get("table_caption"),
            }
    table_text = snapshot.get("raw_table_text")
    if table_text:
        lines = [line.strip() for line in str(table_text).splitlines() if line.strip()]
        targets = [test.get("rich_loading"), test.get("lean_loading")]
        targets = [float(x) for x in targets if x is not None]
        chosen = None
        for line in lines:
            if any(str(round(t, 2)) in line or str(round(t, 3)) in line for t in targets):
                chosen = line
                break
        if chosen is None:
            amine = str(test.get("amine") or "").upper()
            chosen = next((line for line in lines if amine and amine in line.upper()), None)
        if chosen:
            caption = snapshot.get("table_caption") or snapshot.get("table") or ""
            return {
                "status": "ok",
                "match": "raw_table_text_row",
                "excerpt": f"{caption} | {chosen}".strip(" |"),
                "loc_label": snapshot.get("table") or snapshot.get("table_caption"),
            }
    return None


def resolve_from_batch(batch_dir: Path, test: dict) -> dict:
    """Fallback for legacy L3/simulation rows without raw_data_path."""
    best, best_score = None, math.inf
    for name in ("raw_agent.jsonl", "valid.jsonl", "valid_incomplete.jsonl", "rejected.jsonl"):
        path = batch_dir / name
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            score = _record_score({"record": rec}, test)
            if score < best_score:
                best, best_score = rec, score
    if best is None or best_score > 8:
        return {"status": "record_not_matched", "file": "batch_jsonl"}
    src = best.get("source") or {}
    return {
        "status": "ok",
        "match": "batch_jsonl",
        "score": best_score,
        "excerpt": src.get("excerpt"),
        "loc_label": src.get("loc_label"),
        "loc_type": src.get("loc_type"),
    }


def resolve_from_snapshot(snapshot: dict, *, record_id: str | None = None, test: dict | None = None) -> dict:
    records = snapshot.get("records") or []
    if record_id:
        for item in records:
            rec = item.get("record") or {}
            if rec.get("record_id") == record_id:
                return {"status": "ok", "record": rec, "match": "record_id",
                        "excerpt": (rec.get("source") or {}).get("excerpt"),
                        "loc_label": (rec.get("source") or {}).get("loc_label")}
    if records and test:
        best, best_score = None, math.inf
        for item in records:
            score = _record_score(item, test)
            if score < best_score:
                best, best_score = item, score
        if best is not None and best_score <= 8:
            rec = best.get("record") or {}
            return {
                "status": "ok",
                "record": rec,
                "match": "field_match",
                "score": best_score,
                "excerpt": (rec.get("source") or {}).get("excerpt"),
                "loc_label": (rec.get("source") or {}).get("loc_label"),
            }
    # A single normalized record stored directly as the snapshot.
    if snapshot.get("source") and snapshot.get("test"):
        rec = snapshot
        return {
            "status": "ok",
            "record": rec,
            "match": "direct_record",
            "excerpt": (rec.get("source") or {}).get("excerpt"),
            "loc_label": (rec.get("source") or {}).get("loc_label"),
        }
    if test:
        old = _resolve_old_snapshot(snapshot, test)
        if old:
            return old
    return {"status": "record_not_matched"}
