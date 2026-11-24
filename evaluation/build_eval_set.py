"""Build the 38-record L2 regression set from gold_standard_L2.json.

The gold standard is the project's historical L2 export. It is a regression
baseline, not an independently re-verified answer key: the generated file marks
human_verified=false so the evaluator and reports do not overclaim.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLD = ROOT / "gold_standard_L2.json"
OUT_JSON = ROOT / "evaluation" / "eval_set_v1.json"
OUT_CSV = ROOT / "evaluation" / "eval_set_v1.csv"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def main() -> None:
    data = json.loads(GOLD.read_text(encoding="utf-8"))
    records = data.get("records") or []
    samples = []
    missing_pdf = []
    missing_snapshot = []
    hash_mismatch = []
    for r in records:
        src = r.get("source") or {}
        pdf = ROOT / (src.get("pdf_path") or "")
        snap = ROOT / ((r.get("qc") or {}).get("raw_data_path") or "")
        expected_hash = (r.get("qc") or {}).get("raw_data_hash")
        actual_snap_hash = sha256_file(snap)
        if not pdf.exists():
            missing_pdf.append(src.get("doi"))
        if not snap.exists():
            missing_snapshot.append(src.get("doi"))
        if expected_hash and actual_snap_hash and expected_hash != actual_snap_hash:
            hash_mismatch.append({"doi": src.get("doi"), "expected": expected_hash, "actual": actual_snap_hash})
        recipe = dict(r.get("recipe") or {})
        recipe["amine_a"] = (r.get("compound") or {}).get("standard_name")
        recipe["amine_b"] = None
        recipe["recipe_id"] = recipe.get("recipe_id")
        samples.append(
            {
                "sample_id": str(r.get("test_id")),
                "test_id": r.get("test_id"),
                "batch_id": r.get("batch_id"),
                "doi": src.get("doi"),
                "pdf_path": src.get("pdf_path"),
                "pdf_sha256": src.get("pdf_hash"),
                "raw_data_path": (r.get("qc") or {}).get("raw_data_path"),
                "raw_data_hash": expected_hash,
                "recipe": recipe,
                "conditions": r.get("conditions") or {},
                "loadings": r.get("loadings") or {},
                "performance": r.get("performance") or [],
                "qc_level": (r.get("qc") or {}).get("qc_level"),
                "label_source": "historical L2 export: gold_standard_L2.json",
                "human_verified": False,
                "known_caveats": [
                    "Historical L2 label; not independently re-verified in phase 2.",
                ],
            }
        )
    payload = {
        "eval_version": "v1",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "source_file": GOLD.relative_to(ROOT).as_posix(),
        "record_count": len(samples),
        "doi_count": len({s["doi"] for s in samples}),
        "label_policy": "Regression baseline only; human_verified=false for every sample.",
        "integrity": {
            "missing_pdf": missing_pdf,
            "missing_snapshot": missing_snapshot,
            "hash_mismatch": hash_mismatch,
        },
        "samples": samples,
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    import csv

    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([
            "sample_id", "test_id", "doi", "pdf_path", "amine_a", "amine_b",
            "wt_a", "wt_b", "water_wt", "temperature_K", "co2_vol_pct",
            "initial_loading", "metric_names", "qc_level", "human_verified",
        ])
        for s in samples:
            rec = s["recipe"]
            cond = s["conditions"]
            metrics = ";".join(p.get("metric_name", "") for p in s["performance"])
            w.writerow([
                s["sample_id"], s["test_id"], s["doi"], s["pdf_path"],
                (rec.get("amine_a") or {}).get("standard_name") if isinstance(rec.get("amine_a"), dict) else rec.get("amine_a"),
                (rec.get("amine_b") or {}).get("standard_name") if isinstance(rec.get("amine_b"), dict) else rec.get("amine_b"),
                rec.get("wt_a"), rec.get("wt_b"), rec.get("water_wt"),
                cond.get("temperature_K"), cond.get("co2_vol_pct"), cond.get("initial_loading"),
                metrics, s["qc_level"], s["human_verified"],
            ])
    print(json.dumps({
        "records": len(samples),
        "dois": payload["doi_count"],
        "missing_pdf": len(missing_pdf),
        "missing_snapshot": len(missing_snapshot),
        "hash_mismatch": len(hash_mismatch),
        "out_json": OUT_JSON.relative_to(ROOT).as_posix(),
        "out_csv": OUT_CSV.relative_to(ROOT).as_posix(),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
