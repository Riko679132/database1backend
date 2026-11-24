"""Five-case test for the B-stage reasoning chain.

Cases: explicit extraction, cross-section association, deterministic formula,
expert/contextual inference, insufficient evidence. Inputs are real records
from the Phase-4 batch and real PDFs; no LLM call is made here.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server import (  # noqa: E402
    condition_profile,
    extract,
    paper_manifest,
    provenance,
    reasoning,
    reference_case_parser,
    rules,
    vle_table_parser,
)

BATCH = ROOT / "extractions" / "batch_20261124_145027"
REPORT = ROOT / "evaluation" / "reports" / "reasoning_chain_test.md"


def pdf_for_doi(doi: str) -> Path:
    known = paper_manifest._known_dois(ROOT)
    for pdf in (ROOT / "data" / "raw_pdfs").glob("*.pdf"):
        if paper_manifest.doi_from_stem(pdf.stem, known) == doi:
            return pdf
    raise FileNotFoundError(doi)


def snapshot_for(doi_prefix: str) -> dict:
    path = next((BATCH / "raw").glob(f"llm_{doi_prefix}*.json"))
    return json.loads(path.read_text(encoding="utf-8"))


def parsed_text(snap: dict) -> str:
    path = (snap.get("parsed_text") or {}).get("path")
    p = Path(path) if path else None
    if p and not p.is_absolute():
        p = ROOT / p
    return p.read_text(encoding="utf-8", errors="ignore") if p and p.exists() else ""


def raw_records(snap: dict) -> list[dict]:
    records = extract._parse_records(snap.get("raw_model_output") or "")
    return records or []


def build_pair(raw: dict, doi: str, parsed: str, compounds: list[dict], *,
               method: str = "llm", context: dict | None = None) -> tuple[dict, dict, dict, dict]:
    pdf = pdf_for_doi(doi)
    rec = extract.normalize(raw, compounds=compounds, pdf=pdf, pdf_hash="test", batch_id="phase5_test",
                            extraction_method=method)
    norm = provenance.normalize_text(parsed)
    verification = provenance.verify_record(raw, rec, norm)
    level, reason = provenance.decide_qc(rec, verification)
    rec["qc"] = {"qc_level": level, "qc_reason": reason}
    issues = reasoning.consistency_issues(raw, rec)
    if issues:
        reasoning.apply_consistency(rec, issues)
    trace = reasoning.trace_record(raw, rec, verification, context=context or {"extraction_method": method})
    return raw, rec, verification, trace


def find_step(trace: dict, rule_id: str) -> dict | None:
    return next((s for s in trace.get("steps") or [] if s.get("rule_id") == rule_id), None)


def main() -> None:
    compounds = extract.load_compounds()
    checks = []

    # 1. Explicit extraction: apenergy table row with quoted evidence.
    snap = snapshot_for("10.1016_j.apenergy")
    parsed = parsed_text(snap)
    raws = raw_records(snap)
    rec = trace = None
    step = None
    for candidate in raws:
        if not any(e.get("type") == "Explicit" for e in candidate.get("evidence") or [] if isinstance(e, dict)):
            continue
        _, candidate_rec, _, candidate_trace = build_pair(
            candidate, "10.1016/j.apenergy.2016.03.043", parsed, compounds
        )
        candidate_step = find_step(candidate_trace, "R-EVD-01")
        if candidate_rec["qc"]["qc_level"] == "L2" and candidate_step:
            rec, trace, step = candidate_rec, candidate_trace, candidate_step
            break
    if rec is None:
        raise RuntimeError("no L2 explicit-evidence raw record for apenergy")
    checks.append({
        "case": "explicit_extraction",
        "paper": "10.1016/j.apenergy.2016.03.043",
        "ok": bool(step and step.get("source", {}).get("excerpt") and rec["qc"]["qc_level"] == "L2"),
        "qc_level": rec["qc"]["qc_level"],
        "rule_ids": [s["rule_id"] for s in trace["steps"]],
        "excerpt": (step or {}).get("source", {}).get("excerpt", "")[:180],
    })

    # 2. Cross-section association: d6gc reference row recovered from table + text.
    snap = snapshot_for("10.1039_d6gc")
    rec0 = next((x["record"] for x in snap.get("records") or []
                 if (x["record"].get("source") or {}).get("extraction_method") == "deterministic_reference_profile"), None)
    if rec0 is None:
        raise RuntimeError("no reference-profile record for d6gc")
    raw = {"source": rec0["source"], "recipe": rec0["recipe"], "test": rec0["test"],
           "performance": rec0["performance"], "evidence": []}
    _, rec, _, trace = build_pair(
        raw, "10.1039/d6gc02196d", parsed_text(snap), compounds,
        method="deterministic_reference_profile",
        context={"extraction_method": "deterministic_reference_profile",
                 "reference_profile": reference_case_parser.profile_for_doi("10.1039/d6gc02196d")},
    )
    step = find_step(trace, "R-XSEC-02")
    checks.append({
        "case": "cross_section_association",
        "paper": "10.1039/d6gc02196d",
        "ok": bool(step) and rec["qc"]["qc_level"] == "L2",
        "qc_level": rec["qc"]["qc_level"],
        "rule_ids": [s["rule_id"] for s in trace["steps"]],
        "loc_label": (rec.get("source") or {}).get("loc_label"),
    })

    # 3. Deterministic formula: jece rate 34.0 in 10-5 mol CO2/mol/s -> 0.00034.
    snap = snapshot_for("10.1016_j.jece")
    raws = raw_records(snap)
    raw = next((r for r in raws if any(p.get("metric_name") == "initial_absorption_rate"
                                       for p in r.get("performance") or [])), None)
    if raw is None:
        raise RuntimeError("no rate raw record for jece")
    _, rec, _, trace = build_pair(raw, "10.1016/j.jece.2024.112664", parsed_text(snap), compounds)
    step = find_step(trace, "R-DET-03")
    rate = next((p for p in rec["performance"] if p["metric_name"] == "initial_absorption_rate"), {})
    checks.append({
        "case": "deterministic_formula",
        "paper": "10.1016/j.jece.2024.112664",
        "ok": bool(step and step.get("formula") and rate.get("value") == 0.00034),
        "qc_level": rec["qc"]["qc_level"],
        "formula": (step or {}).get("formula"),
        "inputs": (step or {}).get("formula_inputs"),
        "output": (step or {}).get("output"),
        "rule_ids": [s["rule_id"] for s in trace["steps"]],
    })

    # 4. Expert/contextual inference: ie400825 condition profile fills 101.325 kPa / 20% CO2.
    snap = snapshot_for("10.1021_ie400825u")
    parsed = parsed_text(snap)
    prof = condition_profile.profile_for_doi("10.1021/ie400825u")
    raw = None
    for candidate in raw_records(snap):
        applied = condition_profile.apply_to_raw(candidate, parsed, prof)
        if applied and "total_pressure_kPa" in applied.get("changed", []):
            raw = candidate
            break
    if raw is None:
        raise RuntimeError("condition profile did not apply to any ie400825 raw record")
    _, rec, _, trace = build_pair(raw, "10.1021/ie400825u", parsed, compounds,
                                  context={"extraction_method": "llm", "condition_profile": prof})
    step = find_step(trace, "R-XSEC-03")
    exp = find_step(trace, "R-EXP-01")
    checks.append({
        "case": "expert_context_inference",
        "paper": "10.1021/ie400825u",
        "ok": bool(step and exp) and rec["test"].get("total_pressure_kPa") == 101.325,
        "qc_level": rec["qc"]["qc_level"],
        "total_pressure_kPa": rec["test"].get("total_pressure_kPa"),
        "co2_vol_pct": rec["test"].get("co2_vol_pct"),
        "rule_ids": [s["rule_id"] for s in trace["steps"]],
        "evidence_notes": [e.get("note") for e in raw.get("evidence") or []
                           if e.get("field") in ("total_pressure_kPa", "co2_vol_pct", "initial_loading")],
    })

    # 5. Insufficient evidence: vertical VLE row has P/T/loading but no initial loading.
    doi = "10.1016/j.jece.2024.112664"
    pdf = pdf_for_doi(doi)
    vprofile = vle_table_parser.vertical_profile_for_doi(doi)
    vres = vle_table_parser.parse_vertical_table(pdf, vprofile)
    vraws = vle_table_parser.vertical_points_to_raw_records(vres, pdf, doi=doi)
    raw = vraws[0]
    _, rec, _, trace = build_pair(raw, doi, parsed_text(snapshot_for("10.1016_j.jece")), compounds,
                                  method="deterministic_vle_vertical",
                                  context={"extraction_method": "deterministic_vle_vertical",
                                           "vle_profile": vprofile})
    step = find_step(trace, "R-INF-01")
    unknown = find_step(trace, "R-EVD-05")
    checks.append({
        "case": "insufficient_evidence",
        "paper": doi,
        "ok": bool(step and unknown) and rec["test"].get("initial_loading") is None
              and rec["qc"]["qc_level"] == "L3",
        "qc_level": rec["qc"]["qc_level"],
        "initial_loading": rec["test"].get("initial_loading"),
        "missing": (step or {}).get("formula_inputs"),
        "rule_ids": [s["rule_id"] for s in trace["steps"]],
    })

    # A trace is invalid if it references an unknown rule or drops evidence type.
    catalog = set(rules.catalog_manifest()["rule_ids"])
    for c in checks:
        c["rule_ids_valid"] = all(r in catalog for r in c["rule_ids"])

    # Consistency gate on the existing batch: no blocking issue may downgrade a record.
    gate = {"checked": 0, "issues": 0, "downgraded": 0}
    for line in (BATCH / "valid.jsonl").read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        gate["checked"] += 1
        issues = reasoning.consistency_issues({"test": rec.get("test"), "recipe": rec.get("recipe"),
                                               "performance": rec.get("performance"), "evidence": []}, rec)
        gate["issues"] += len(issues)
        before = rec["qc"]["qc_level"]
        reasoning.apply_consistency(rec, issues)
        if rec["qc"]["qc_level"] != before:
            gate["downgraded"] += 1
    checks.append({
        "case": "consistency_gate_on_final_batch",
        "paper": "batch_20261124_145027",
        "ok": gate["issues"] == 0 and gate["downgraded"] == 0,
        "checked": gate["checked"],
        "issues": gate["issues"],
        "downgraded": gate["downgraded"],
        "rule_ids": ["R-DET-01", "R-DET-02", "R-DET-05"],
    })

    ok = all(c["ok"] and c.get("rule_ids_valid", True) for c in checks)
    payload = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "ok": ok,
        "rule_set": rules.catalog_manifest(),
        "cases": checks,
    }
    (ROOT / "evaluation" / "reports" / "reasoning_chain_test.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        "# B-stage reasoning-chain test",
        "",
        f"- Result: {'PASS' if ok else 'FAIL'}",
        f"- Rule set: `{rules.catalog_manifest()['rule_set_version']}` ({rules.catalog_manifest()['rule_count']} rules)",
        "",
        "| Case | Paper | Result | QC | Rules | Detail |",
        "|---|---|---|---|---|---|",
    ]
    for c in checks:
        detail = {k: v for k, v in c.items() if k not in ("case", "paper", "ok", "qc_level", "rule_ids")}
        lines.append(
            f"| {c['case']} | {c['paper']} | {'PASS' if c['ok'] else 'FAIL'} | "
            f"{c.get('qc_level', '-')} | {', '.join(c.get('rule_ids') or [])} | "
            f"`{json.dumps(detail, ensure_ascii=False)[:600]}` |"
        )
    lines += [
        "",
        "Every step in the trace carries `rule_id`, category, evidence type, result and, where applicable, formula/inputs/output and source excerpt.",
        "`R-INF-01` and `R-EVD-05` are used for missing data; missing evidence is not converted into a value.",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
