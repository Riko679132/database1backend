"""Create a self-consistency candidate from the historical L2 export.

This is a harness sanity check, not a model extraction result. It proves the
evaluator can match and score the 38-record set; do not report it as model
performance.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GOLD = ROOT / "gold_standard_L2.json"
OUT = ROOT / "evaluation" / "historical_l2_candidate.jsonl"


def main() -> None:
    data = json.loads(GOLD.read_text(encoding="utf-8"))
    with OUT.open("w", encoding="utf-8") as fh:
        for r in data.get("records") or []:
            src = r.get("source") or {}
            compound = r.get("compound") or {}
            recipe = r.get("recipe") or {}
            cond = r.get("conditions") or {}
            load = r.get("loadings") or {}
            rec = {
                "source": {
                    "doi": src.get("doi"),
                    "title": src.get("title"),
                    "authors": src.get("authors"),
                    "year": src.get("year"),
                    "journal": src.get("journal"),
                    "pdf_path": src.get("pdf_path"),
                    "pdf_hash": src.get("pdf_hash"),
                    "loc_type": src.get("loc_type"),
                    "loc_label": src.get("loc_label"),
                    "excerpt": "historical L2 fixture",
                },
                "recipe": {
                    "recipe_type": recipe.get("recipe_type"),
                    "amine_a": {
                        "standard_name": compound.get("standard_name"),
                        "inchikey": compound.get("inchikey"),
                        "cas_no": compound.get("cas_no"),
                        "smiles": compound.get("smiles"),
                    },
                    "amine_b": None,
                    "wt_a": recipe.get("wt_a"),
                    "wt_b": recipe.get("wt_b"),
                    "water_wt": recipe.get("water_wt"),
                    "total_amine_wt": recipe.get("total_amine_wt"),
                    "additive_flag": 0,
                    "salt_flag": 0,
                    "phase_flag": 0,
                },
                "test": {
                    "test_origin": "literature",
                    "batch_id": r.get("batch_id"),
                    "temperature_K": cond.get("temperature_K"),
                    "co2_vol_pct": cond.get("co2_vol_pct"),
                    "co2_partial_kPa": cond.get("co2_partial_kPa"),
                    "total_pressure_kPa": cond.get("total_pressure_kPa"),
                    "gas_flow": cond.get("gas_flow"),
                    "liquid_volume": cond.get("liquid_volume"),
                    "gas_liquid_ratio": cond.get("gas_liquid_ratio"),
                    "initial_loading": cond.get("initial_loading"),
                    "rich_loading": load.get("rich"),
                    "lean_loading": load.get("lean"),
                },
                "performance": r.get("performance") or [],
                "qc": {"qc_level": "L2", "qc_reason": "historical_fixture"},
            }
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(OUT.relative_to(ROOT).as_posix())


if __name__ == "__main__":
    main()
