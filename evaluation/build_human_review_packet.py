"""Build the human-review packet for the 38 L2 samples.

This does not perform human review. It produces a review-ready packet with
original evidence, historical labels, final extracted values, priority and
blank human-verification fields. human_verified stays false.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BATCH = ROOT / "extractions/batch_20261124_145027"
EVAL = ROOT / "evaluation/eval_set_v1.json"
OUT_JSON = ROOT / "evaluation/human_review_packet_v1.json"
OUT_CSV = ROOT / "evaluation/human_review_packet_v1.csv"


def load_eval():
    spec = importlib.util.spec_from_file_location("ev", ROOT / "evaluation/evaluate.py")
    ev = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ev)
    return ev


def priority(sample, cand):
    doi = sample["doi"]
    if doi == "10.1021/je00005a025":
        return 1
    if doi == "10.1039/d6gc02196d":
        return 1
    if doi == "10.1016/j.jece.2024.112664":
        return 2
    if (sample.get("recipe") or {}).get("recipe_type") == "binary":
        return 2
    if any("rate" in p.get("metric_name", "") for p in sample.get("performance") or []):
        return 3
    return 4


def main() -> None:
    ev = load_eval()
    samples = json.loads(EVAL.read_text(encoding="utf-8"))["samples"]
    cands, rejected, _ = ev.load_candidates(BATCH)
    flat = [ev.flatten(c) for c in cands] + [ev.flatten(r) for r in rejected]
    used = set()
    matches = {}
    for s in samples:
        best, score = None, float("inf")
        for i, c in enumerate(flat):
            if i in used:
                continue
            sc = ev.match_score(s, c)
            if sc < score:
                best, score = i, sc
        if best is not None and score <= 40:
            used.add(best)
            matches[s["sample_id"]] = flat[best]
    rows = []
    for s in samples:
        c = matches.get(s["sample_id"])
        rows.append({
            "sample_id": s["sample_id"],
            "doi": s["doi"],
            "pdf_path": s.get("pdf_path"),
            "snapshot_path": (c.get("raw", {}).get("test") or {}).get("raw_data_path") if c else None,
            "amine_a": (s.get("recipe") or {}).get("amine_a"),
            "amine_b": (s.get("recipe") or {}).get("amine_b"),
            "wt_a": (s.get("recipe") or {}).get("wt_a"),
            "wt_b": (s.get("recipe") or {}).get("wt_b"),
            "temperature_K": (s.get("conditions") or {}).get("temperature_K"),
            "co2_vol_pct": (s.get("conditions") or {}).get("co2_vol_pct"),
            "co2_partial_kPa": (s.get("conditions") or {}).get("co2_partial_kPa"),
            "initial_loading": (s.get("conditions") or {}).get("initial_loading"),
            "historical_metrics": {p.get("metric_name"): p.get("value") for p in s.get("performance") or []},
            "final_metrics": c.get("metrics") if c else None,
            "final_qc": c.get("qc_level") if c else None,
            "priority": priority(s, c),
            "agent_precheck": "matched_final_batch" if c else "not_matched",
            "human_verified": False,
            "review_status": "pending",
            "human_verdict": None,
            "reviewer": None,
            "review_time": None,
            "disputed_fields": [],
            "notes": None,
        })
    OUT_JSON.write_text(json.dumps({
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "batch": BATCH.as_posix(),
        "samples": rows,
        "human_verified_count": 0,
        "note": "Review packet only; no human review was performed. Historical-label agreement is not human accuracy.",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([
            "sample_id", "doi", "priority", "amine_a", "amine_b", "wt_a", "wt_b",
            "temperature_K", "co2_vol_pct", "co2_partial_kPa", "initial_loading",
            "historical_metrics", "final_metrics", "final_qc", "agent_precheck",
            "human_verified", "review_status", "human_verdict", "reviewer",
            "review_time", "disputed_fields", "notes",
        ])
        for r in rows:
            w.writerow([
                r["sample_id"], r["doi"], r["priority"], r["amine_a"], r["amine_b"],
                r["wt_a"], r["wt_b"], r["temperature_K"], r["co2_vol_pct"],
                r["co2_partial_kPa"], r["initial_loading"],
                json.dumps(r["historical_metrics"], ensure_ascii=False),
                json.dumps(r["final_metrics"], ensure_ascii=False),
                r["final_qc"], r["agent_precheck"], r["human_verified"],
                r["review_status"], "", "", "", "", "",
            ])
    print(json.dumps({"samples": len(rows), "human_verified": 0, "out_json": OUT_JSON.relative_to(ROOT).as_posix(), "out_csv": OUT_CSV.relative_to(ROOT).as_posix()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
