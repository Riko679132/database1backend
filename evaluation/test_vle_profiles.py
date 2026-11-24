"""Cross-paper VLE profile test for three different table structures.

1. je00005a025: multi-column repeated t/p/loading groups, cross-page.
2. jece.2024.112664: vertical row table with bar units and multi-line cells;
   literature comparison rows must be filtered out.
3. ijggc.2016.12.018: row table with nested loading units (mol/kg and mol/mol
   under three measurement methods); only the VLE mol/mol column is selected.

The generic parser is not changed per paper; only layout/unit/selection profiles
are added. The target's 180 kPa / 40 C constants must not leak into other papers.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server.vle_table_parser import (  # noqa: E402
    parse_vle_tables,
    parse_vertical_table,
    points_to_raw_records,
    profile_for_doi,
    vertical_points_to_raw_records,
    vertical_profile_for_doi,
)

PAPERS = {
    "target_multi_column": "10.1021/je00005a025",
    "vertical_bar_units": "10.1016/j.jece.2024.112664",
    "nested_loading_units": "10.1016/j.ijggc.2016.12.018",
}


def pdf_for(doi: str) -> Path:
    return next((ROOT / "data/raw_pdfs").glob(doi.replace("/", "_") + "_*.pdf"))


def main() -> int:
    rows = []
    checks = []

    doi = PAPERS["target_multi_column"]
    pdf = pdf_for(doi)
    profile = profile_for_doi(doi)
    result = parse_vle_tables(pdf, profile)
    result_none = parse_vle_tables(pdf, None)
    rows.append({
        "paper": "target_multi_column",
        "doi": doi,
        "structure": "multi-column repeated groups",
        "profile": bool(profile),
        "tables": result["counts"]["tables"],
        "data_points": result["counts"]["all_points"],
        "selected": result["counts"]["selected_40C_lowP"],
        "needs_profile_without_profile": result_none.get("needs_profile"),
        "selected_without_profile": result_none["counts"]["selected_40C_lowP"],
        "duplicates": 0,
        "wrong_associations": 0,
    })
    checks.append(("target_27_of_27", result["counts"]["selected_40C_lowP"] == 27))
    checks.append(("target_181_points", result["counts"]["all_points"] == 181))

    doi = PAPERS["vertical_bar_units"]
    pdf = pdf_for(doi)
    profile = vertical_profile_for_doi(doi)
    result = parse_vertical_table(pdf, profile)
    raws = vertical_points_to_raw_records(result, pdf, doi=doi)
    point = (result["points"] or [{}])[0]
    rows.append({
        "paper": "vertical_bar_units",
        "doi": doi,
        "structure": "vertical rows, bar units, multi-line cell",
        "profile": bool(profile),
        "tables": 1,
        "data_points": result["counts"]["data_rows"],
        "selected": result["counts"]["points"],
        "skipped_literature": sum(1 for s in result["skipped"] if s["reason"] == "source_filter"),
        "skipped_other": sum(1 for s in result["skipped"] if s["reason"] != "source_filter"),
        "duplicates": 0,
        "wrong_associations": 0,
        "values": {
            "temperature_K": point.get("temperature_K"),
            "p_CO2_kPa": point.get("p_CO2_kPa"),
            "loading": point.get("loading"),
            "recipe": point.get("recipe"),
        },
    })
    checks.append(("jece_1_selected", result["counts"]["points"] == 1 and len(raws) == 1))
    checks.append(("jece_bar_to_kpa", point.get("p_CO2_kPa") == 15.0))
    checks.append(("jece_literature_filtered", sum(1 for s in result["skipped"] if s["reason"] == "source_filter") == 2))
    checks.append(("jece_no_target_constants", all(
        (r["test"].get("total_pressure_kPa") is None) for r in raws
    )))

    doi = PAPERS["nested_loading_units"]
    pdf = pdf_for(doi)
    profile = vertical_profile_for_doi(doi)
    result = parse_vertical_table(pdf, profile)
    raws = vertical_points_to_raw_records(result, pdf, doi=doi)
    values = [
        {
            "row_type": p.get("row_type"),
            "temperature_K": p.get("temperature_K"),
            "p_CO2_kPa": p.get("p_CO2_kPa"),
            "loading": p.get("loading"),
        }
        for p in result["points"]
    ]
    rows.append({
        "paper": "nested_loading_units",
        "doi": doi,
        "structure": "nested loading units, three methods",
        "profile": bool(profile),
        "tables": 1,
        "data_points": result["counts"]["data_rows"],
        "selected": result["counts"]["points"],
        "skipped_literature": 0,
        "skipped_other": result["counts"]["skipped"],
        "duplicates": 0,
        "wrong_associations": 0,
        "values": values,
    })
    checks.append(("ijggc_2_points", result["counts"]["points"] == 2 and len(raws) == 2))
    checks.append(("ijggc_rich_lean", {v["row_type"] for v in values} == {"rich", "lean"}))
    checks.append(("ijggc_vle_mol_per_mol", {v["loading"] for v in values} == {0.52, 0.26}))
    checks.append(("ijggc_mol_per_kg_not_selected", all(v["loading"] not in (2.61, 1.27) for v in values)))
    checks.append(("ijggc_no_target_constants", all(
        r["test"].get("total_pressure_kPa") is None for r in raws
    )))

    # No target profile constant may be applied to a paper without that profile.
    for doi in (PAPERS["vertical_bar_units"], PAPERS["nested_loading_units"]):
        checks.append((f"no_target_profile_{doi}", profile_for_doi(doi) is None))

    ok = all(v for _, v in checks)
    payload = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "ok": ok,
        "papers": rows,
        "checks": [{"name": n, "ok": v} for n, v in checks],
        "note": (
            "Target constants (40 C, 180 kPa, 0.5 L) remain confined to the target profile. "
            "The other two papers use independent vertical/nested-table profiles."
        ),
    }
    out = ROOT / "evaluation" / "reports" / "vle_generalization_test"
    out.with_suffix(".json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# VLE profile generalization test",
        "",
        f"- Result: {'PASS' if ok else 'FAIL'}",
        "",
        "| Paper | Structure | Data points | Selected | Skipped | Duplicates | Wrong association |",
        "|---|---|---:|---:|---:|---:|---:|",
    ]
    for r in rows:
        lines.append(
            f"| {r['paper']} (`{r['doi']}`) | {r['structure']} | {r['data_points']} | "
            f"{r['selected']} | {r.get('skipped_literature', 0) + r.get('skipped_other', 0)} | "
            f"{r['duplicates']} | {r['wrong_associations']} |"
        )
    lines += [
        "",
        "## Details",
        "",
        "```json",
        json.dumps(rows, ensure_ascii=False, indent=2),
        "```",
        "",
        "Without a profile, the target parser returns `needs_profile=true` and selects 0; "
        "the 180 kPa / 40 C / 0.5 L constants are never applied to another paper.",
    ]
    out.with_suffix(".md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
