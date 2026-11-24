"""Build the 27-point VLE checklist with before/after status.

Before: the Phase-2 LLM batch. After: the deterministic table parser integrated
in Phase 3. Matching ignores amine_b name because the historical eval set does
not carry that identity; it compares amine_a, wt_a, wt_b, T, P_CO2 and loading.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server.vle_table_parser import parse_vle_tables, profile_for_doi
DOI = "10.1021/je00005a025"
PDF = ROOT / "data/raw_pdfs/10.1021_je00005a025_0770ae31.pdf"
BEFORE = ROOT / "extractions/batch_20261124_140349"
OUT_MD = ROOT / "evaluation/reports/vle_27_point_checklist.md"
OUT_JSON = ROOT / "evaluation/reports/vle_27_point_checklist.json"


def key(amine_a, wt_a, wt_b, t, p, loading):
    return (
        str(amine_a or "").upper(),
        round(float(wt_a or 0), 3),
        round(float(wt_b or 0), 3),
        round(float(t or 0), 2),
        round(float(p or 0), 2),
        round(float(loading or 0), 3),
    )


def load_before():
    rows = []
    for name in ("valid.jsonl", "valid_incomplete.jsonl"):
        path = BEFORE / name
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("source", {}).get("doi") != DOI:
                continue
            rec = r.get("recipe") or {}
            test = r.get("test") or {}
            amine_a = (rec.get("amine_a") or {}).get("standard_name") if isinstance(rec.get("amine_a"), dict) else rec.get("amine_a")
            perf = next((p for p in r.get("performance") or [] if p.get("metric_name") == "equilibrium_loading"), None)
            rows.append({
                "amine_a": amine_a,
                "wt_a": rec.get("wt_a"),
                "wt_b": rec.get("wt_b"),
                "temperature_K": test.get("temperature_K"),
                "co2_partial_kPa": test.get("co2_partial_kPa"),
                "loading": perf.get("value") if perf else None,
                "qc": (r.get("qc") or {}).get("qc_level"),
            })
    return rows


def main() -> None:
    ev = json.loads((ROOT / "evaluation/eval_set_v1.json").read_text(encoding="utf-8"))
    expected = [s for s in ev["samples"] if s["doi"] == DOI]
    before = load_before()
    parsed = parse_vle_tables(PDF, profile_for_doi(DOI))
    tmap = {t["number"]: t["recipe"] for t in parsed["tables"]}
    after_points = []
    for p in parsed["selected_40C_lowP"]:
        rec = tmap[p["table"]]
        after_points.append({
            **p,
            "amine_a": rec.get("amine_a"),
            "wt_a": rec.get("wt_a"),
            "wt_b": rec.get("wt_b"),
        })
    after_map = {
        key(x["amine_a"], x["wt_a"], x["wt_b"], 313.15, x["p_CO2_kPa"], x["loading"]): x
        for x in after_points
    }
    before_map = {
        key(x["amine_a"], x["wt_a"], x["wt_b"], x["temperature_K"], x["co2_partial_kPa"], x["loading"]): x
        for x in before
    }

    rows = []
    for s in expected:
        r = s["recipe"]
        c = s["conditions"]
        k = key(r.get("amine_a"), r.get("wt_a"), r.get("wt_b"), c.get("temperature_K"), c.get("co2_partial_kPa"), s["loadings"].get("rich"))
        b = before_map.get(k)
        a = after_map.get(k)
        after_status = "matched_L2" if a else "missing"
        before_status = ("matched_" + str(b["qc"])) if b else "missing"
        pipeline = (
            f"PDF读=yes; 表格={a['table']}/组{a['group']}/p.{a['page']}; "
            f"LLM={'deterministic_parser(not_llm)' if a else 'no'}; "
            f"结构化={'yes' if a else 'no'}; 校验={'L2' if a else 'missing'}; "
            f"before={before_status}"
        )
        rows.append({
            "sample_id": s["sample_id"],
            "amine_a": r.get("amine_a"),
            "wt_a": r.get("wt_a"),
            "amine_b_inferred": a["table"] if a else None,
            "wt_b": r.get("wt_b"),
            "temperature_K": c.get("temperature_K"),
            "p_CO2_kPa": c.get("co2_partial_kPa"),
            "loading": s["loadings"].get("rich"),
            "before_status": before_status,
            "before_qc": b.get("qc") if b else None,
            "after_status": after_status,
            "after_table": a["table"] if a else None,
            "after_group": a["group"] if a else None,
            "after_page": a["page"] if a else None,
            "after_raw_row": a["raw_row"] if a else None,
            "pipeline_status": pipeline,
        })

    table_counts = {}
    for x in after_points:
        table_counts[x["table"]] = table_counts.get(x["table"], 0) + 1
    before_extra = [x for x in before if key(x["amine_a"], x["wt_a"], x["wt_b"], x["temperature_K"], x["co2_partial_kPa"], x["loading"]) not in {
        key(s["recipe"].get("amine_a"), s["recipe"].get("wt_a"), s["recipe"].get("wt_b"), s["conditions"].get("temperature_K"), s["conditions"].get("co2_partial_kPa"), s["loadings"].get("rich")) for s in expected
    }]

    payload = {
        "doi": DOI,
        "expected": len(expected),
        "after_selected": len(after_points),
        "after_matched": sum(1 for r in rows if r["after_status"] == "matched_L2"),
        "before_matched": sum(1 for r in rows if r["before_status"].startswith("matched")),
        "table_counts": table_counts,
        "before_extra_records": before_extra,
        "rows": rows,
        "parser_counts": parsed["counts"],
    }
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 27-Point VLE Checklist — Shen & Li 1992",
        "",
        f"- DOI: `{DOI}`",
        f"- Expected: {len(expected)} 40 °C low-pressure points (Table II 6, Table III 7, Table IV 7, Table V 7)",
        f"- Before Phase 3 (LLM batch): {payload['before_matched']}/27 matched; {len(before_extra)} extra high-pressure MDEA points",
        f"- After Phase 3 (deterministic parser): {payload['after_matched']}/27 matched; tables {table_counts}",
        f"- Parser counts: {parsed['counts']}",
        "",
        "The original 12/27 figure was inflated by six evaluator false matches: the LLM extracted six >180 kPa MDEA points and the evaluator matched them to Table V MEA points because amine identity was only a penalty. After requiring amine identity, the true before coverage is 6/27.",
        "",
        "| # | sample | amine | wt_a | wt_b | T (K) | P_CO2 (kPa) | loading | before | after | pipeline trace |",
        "|---:|---:|---|---:|---:|---:|---:|---:|---|---|---|",
    ]
    for i, r in enumerate(rows, 1):
        lines.append(
            f"| {i} | {r['sample_id']} | {r['amine_a']} | {r['wt_a']} | {r['wt_b']} | {r['temperature_K']} | {r['p_CO2_kPa']} | {r['loading']} | {r['before_status']} | {r['after_status']} | {r['pipeline_status']} |"
        )
    lines += [
        "",
        "## Missing and extra",
        "",
        f"- Missing after fix: {27 - payload['after_matched']}",
        f"- Extra before fix (>180 kPa or other non-reference points): {len(before_extra)}",
        "- The extra MDEA points are valid VLE observations but were outside the reference's 40 °C, ≤180 kPa selection; they remain L3 in the Phase-3 batch and are not counted as matched.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("expected", "before_matched", "after_matched", "table_counts", "parser_counts")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
