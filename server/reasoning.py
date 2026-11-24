"""Explainable reasoning trace for one extracted record.

The trace does not replace extraction or validation. It records which rule was
applied, on which inputs, with which formula/evidence type and result, so every
field can be traced back to the paper, a formula, a rule or an explicit
assumption.
"""
from __future__ import annotations

import re
from typing import Any

from . import gas_phase, rules

TRACE_VERSION = "phase5-1.0"
REQUIRED = ("temperature_K", "co2_vol_pct", "initial_loading")
EVIDENCE_RULE = {
    "Explicit": "R-EVD-01",
    "Contextual": "R-EVD-02",
    "Derived": "R-EVD-03",
    "Assumed": "R-EVD-04",
    "Unknown": "R-EVD-05",
}
FORMULAS = {
    "co2_partial_kPa": (
        "P_CO2 = co2_vol_pct / 100 * total_pressure_kPa",
        ["co2_vol_pct", "total_pressure_kPa"],
    ),
    "water_wt": ("water_wt = 100 - (wt_a + wt_b)", ["wt_a", "wt_b"]),
    "total_amine_wt": ("total_amine_wt = wt_a + wt_b", ["wt_a", "wt_b"]),
}


def _evidence_items(raw: dict) -> list[dict]:
    ev = raw.get("evidence")
    out = []
    if isinstance(ev, list):
        for item in ev:
            if isinstance(item, dict) and item.get("field"):
                out.append(item)
    elif isinstance(ev, dict):
        for field, value in ev.items():
            if isinstance(value, str):
                out.append({"field": field, "type": value, "note": ""})
            elif isinstance(value, dict):
                out.append({"field": field, **value})
    return out


def _lookup(record: dict, field: str) -> Any:
    if field.startswith("performance."):
        metric = field.split(".", 1)[1]
        for perf in record.get("performance") or []:
            if perf.get("metric_name") == metric:
                return perf.get("value")
        return None
    if field.startswith("source."):
        return (record.get("source") or {}).get(field.split(".", 1)[1])
    if field in (record.get("test") or {}):
        return (record.get("test") or {}).get(field)
    if field in (record.get("recipe") or {}):
        return (record.get("recipe") or {}).get(field)
    for perf in record.get("performance") or []:
        if perf.get("metric_name") == field:
            return perf.get("value")
    return None


def _source_ref(raw: dict) -> dict:
    src = raw.get("source") or {}
    excerpt = str(src.get("excerpt") or "")
    return {
        "loc_type": src.get("loc_type"),
        "loc_label": src.get("loc_label"),
        "excerpt": excerpt[:400],
    }


def _formula_for(field: str, record: dict, raw: dict) -> tuple[str | None, list[str]]:
    if field in FORMULAS:
        formula, inputs = FORMULAS[field]
        return formula, [f for f in inputs if _lookup(record, f) is not None]
    if field.startswith("performance."):
        metric = field.split(".", 1)[1]
        for perf in record.get("performance") or []:
            if perf.get("metric_name") == metric:
                return (
                    "see metric_definition and unit_normalization",
                    ["value_original", "unit_original"],
                )
    return None, []


def _evidence_step(item: dict, record: dict, raw: dict) -> dict:
    field = str(item.get("field"))
    etype = str(item.get("type") or "Unknown").strip().capitalize()
    if etype not in EVIDENCE_RULE:
        etype = "Unknown"
    value = _lookup(record, field)
    formula, inputs = _formula_for(field, record, raw)
    step = {
        "rule_id": EVIDENCE_RULE[etype],
        "category": "evidence",
        "evidence_type": etype,
        "field": field,
        "value": value,
        "note": str(item.get("note") or "")[:200],
        "formula": formula,
        "formula_inputs": {k: _lookup(record, k) for k in inputs},
        "source": _source_ref(raw),
        "knowledge": rules.RULES_BY_ID[EVIDENCE_RULE[etype]]["knowledge"],
    }
    if etype == "Explicit":
        step["result"] = "accepted" if value is not None else "value_missing"
    elif etype == "Contextual":
        step["result"] = "accepted_as_context" if value is not None else "context_without_value"
    elif etype == "Derived":
        step["result"] = "derived_recorded" if value is not None else "derivation_missing"
    elif etype == "Assumed":
        step["result"] = "assumption_not_paper_fact"
    else:
        step["result"] = "kept_null" if value is None else "unknown_but_value_present"
    return step


def _deterministic_steps(raw: dict, record: dict) -> tuple[list[dict], list[dict]]:
    steps: list[dict] = []
    issues: list[dict] = []
    test = record.get("test") or {}
    recipe = record.get("recipe") or {}
    src = _source_ref(raw)

    vol = test.get("co2_vol_pct")
    total = test.get("total_pressure_kPa")
    pco2 = test.get("co2_partial_kPa")
    gas_pre = record.get("gas_phase") or gas_phase.assess(test)
    basis = gas_pre.get("basis") or "unknown"
    p_h2o = gas_pre.get("p_h2o_kPa")
    if vol is not None and total is not None and pco2 is not None:
        expected = None
        formula = None
        if basis == "wet":
            expected = round(float(vol) / 100.0 * float(total), 4)
            formula = FORMULAS["co2_partial_kPa"][0]
        elif basis == "dry" and p_h2o is not None:
            expected = round(float(vol) / 100.0 * (float(total) - float(p_h2o)), 4)
            formula = "P_CO2 = co2_vol_pct/100 * (total_pressure_kPa - p_h2o_kPa)"
        step = {
            "rule_id": "R-DET-01",
            "category": "deterministic",
            "evidence_type": "Derived",
            "field": "co2_partial_kPa",
            "formula": formula,
            "formula_inputs": {
                "co2_vol_pct": vol, "total_pressure_kPa": total,
                "gas_basis": basis, "p_h2o_kPa": p_h2o,
            },
            "output": {"value": expected, "unit": "kPa"},
            "recorded_value": pco2,
            "source": src,
            "knowledge": rules.RULES_BY_ID["R-DET-01"]["knowledge"],
            "result": "not_assessable_basis_or_p_h2o_missing" if expected is None else "pending",
        }
        if expected is not None:
            delta = abs(float(pco2) - expected)
            ok = delta <= max(0.2, abs(expected) * 0.01)
            step["result"] = "pass" if ok else "mismatch"
            if not ok:
                issues.append({
                    "rule_id": "R-DET-01",
                    "blocking": True,
                    "reason": "derived_partial_pressure_mismatch",
                    "detail": f"recorded={pco2}, expected={expected}, basis={basis}",
                })
        steps.append(step)

    wt_a = recipe.get("wt_a")
    wt_b = recipe.get("wt_b")
    if wt_a is not None:
        calc_total = round(float(wt_a) + float(wt_b or 0), 4)
        calc_water = round(100.0 - calc_total, 4)
        total_amine = recipe.get("total_amine_wt")
        water = recipe.get("water_wt")
        total_ok = total_amine is None or abs(float(total_amine) - calc_total) <= 0.11
        water_ok = water is None or abs(float(water) - calc_water) <= 0.11
        steps.append({
            "rule_id": "R-DET-02",
            "category": "deterministic",
            "evidence_type": "Derived",
            "field": "recipe.water_wt",
            "formula": FORMULAS["water_wt"][0],
            "formula_inputs": {"wt_a": wt_a, "wt_b": wt_b},
            "output": {"total_amine_wt": calc_total, "water_wt": calc_water},
            "recorded_value": {"total_amine_wt": total_amine, "water_wt": water},
            "source": src,
            "knowledge": rules.RULES_BY_ID["R-DET-02"]["knowledge"],
            "result": "pass" if total_ok and water_ok else "mismatch",
        })
        if not total_ok:
            issues.append({
                "rule_id": "R-DET-02",
                "blocking": True,
                "reason": "total_amine_mass_balance_mismatch",
                "detail": f"recorded={total_amine}, expected={calc_total}",
            })
        if not water_ok:
            issues.append({
                "rule_id": "R-DET-02",
                "blocking": True,
                "reason": "water_mass_balance_mismatch",
                "detail": f"recorded={water}, expected={calc_water}",
            })

    if pco2 is not None and total is not None:
        ok = float(pco2) <= float(total) + 0.01
        steps.append({
            "rule_id": "R-DET-05",
            "category": "deterministic",
            "field": "pressure_consistency",
            "formula": "P_CO2 <= P_total; water-vapour balance is handled by R-DET-06",
            "formula_inputs": {"co2_partial_kPa": pco2, "total_pressure_kPa": total},
            "source": src,
            "knowledge": rules.RULES_BY_ID["R-DET-05"]["knowledge"],
            "result": "pass" if ok else "mismatch",
        })
        if not ok:
            issues.append({
                "rule_id": "R-DET-05",
                "blocking": True,
                "reason": "co2_partial_exceeds_total_pressure",
                "detail": f"P_CO2={pco2}, P_total={total}",
            })

    gas = record.get("gas_phase") or gas_phase.assess(test)
    gas_step = {
        "rule_id": "R-DET-06",
        "category": "deterministic",
        "field": "gas_phase_balance",
        "formula": (
            "wet: P_CO2=y_CO2,wet*P_total; dry: P_CO2=y_CO2,dry*(P_total-P_H2O); "
            "P_CO2+P_H2O <= P_total"
        ),
        "formula_inputs": gas.get("inputs"),
        "output": {
            "status": gas.get("status"),
            "derivation": gas.get("derivation"),
            "p_co2_kPa": gas.get("p_co2_kPa"),
            "p_h2o_kPa": gas.get("p_h2o_kPa"),
            "p_h2o_source": gas.get("p_h2o_source"),
        },
        "checks": gas.get("checks"),
        "source": src,
        "knowledge": rules.RULES_BY_ID["R-DET-06"]["knowledge"],
        "result": gas.get("status"),
    }
    steps.append(gas_step)
    for anomaly in gas.get("anomalies") or []:
        if anomaly.get("code") == "p_co2_exceeds_total":
            continue
        issues.append({
            "rule_id": "R-DET-06",
            "blocking": True,
            "reason": anomaly.get("code"),
            "detail": anomaly.get("detail"),
        })

    for perf in record.get("performance") or []:
        norm = perf.get("unit_normalization") or {}
        status = norm.get("status")
        if status == "converted":
            steps.append({
                "rule_id": "R-DET-03",
                "category": "deterministic",
                "field": f"performance.{perf.get('metric_name')}",
                "formula": norm.get("formula") or "original value * scale / time",
                "formula_inputs": {
                    "value_original": norm.get("original_value"),
                    "unit_original": norm.get("original_unit"),
                    "scale": norm.get("scale"),
                    "time_unit": norm.get("time_unit"),
                    "basis": norm.get("basis"),
                },
                "output": {"value": perf.get("value"), "unit": perf.get("unit")},
                "source": src,
                "knowledge": rules.RULES_BY_ID["R-DET-03"]["knowledge"],
                "result": "pass",
            })
        elif status in ("blocked", "unparsed", "missing_unit"):
            steps.append({
                "rule_id": "R-DET-04",
                "category": "deterministic",
                "field": f"performance.{perf.get('metric_name')}",
                "formula": None,
                "formula_inputs": {"unit_original": norm.get("unit") or perf.get("unit_original")},
                "output": {"status": status, "reason": norm.get("reason")},
                "source": src,
                "knowledge": rules.RULES_BY_ID["R-DET-04"]["knowledge"],
                "result": "blocked",
            })
    return steps, issues


def _cross_section_step(record: dict, context: dict) -> dict | None:
    src = record.get("source") or {}
    method = src.get("extraction_method") or context.get("extraction_method")
    if method == "deterministic_vle_table":
        return {
            "rule_id": "R-XSEC-01",
            "category": "expert_judgement",
            "evidence_type": "Explicit",
            "field": "table_column_group_association",
            "formula": "assign numeric token -> nearest t/p/loading column group; carry T down",
            "formula_inputs": {"profile": context.get("vle_profile")},
            "source": {"loc_type": src.get("loc_type"), "loc_label": src.get("loc_label"),
                       "excerpt": str(src.get("excerpt") or "")[:400]},
            "knowledge": rules.RULES_BY_ID["R-XSEC-01"]["knowledge"],
            "result": "applied",
        }
    if method == "deterministic_vle_vertical":
        return {
            "rule_id": "R-XSEC-01",
            "category": "expert_judgement",
            "evidence_type": "Explicit",
            "field": "vertical_table_row_association",
            "formula": "assign words to profile columns; merge multi-line cells; convert declared units",
            "formula_inputs": {"profile": context.get("vle_profile")},
            "source": {"loc_type": src.get("loc_type"), "loc_label": src.get("loc_label"),
                       "excerpt": str(src.get("excerpt") or "")[:400]},
            "knowledge": rules.RULES_BY_ID["R-XSEC-01"]["knowledge"],
            "result": "applied",
        }
    if method == "deterministic_reference_profile":
        return {
            "rule_id": "R-XSEC-02",
            "category": "expert_judgement",
            "evidence_type": "Contextual",
            "field": "reference_row_from_scattered_text",
            "formula": "all declared profile anchors must match before a record is emitted",
            "formula_inputs": {"profile": context.get("reference_profile")},
            "source": {"loc_type": src.get("loc_type"), "loc_label": src.get("loc_label"),
                       "excerpt": str(src.get("excerpt") or "")[:400]},
            "knowledge": rules.RULES_BY_ID["R-XSEC-02"]["knowledge"],
            "result": "applied",
        }
    return None


def _qc_steps(raw: dict, record: dict) -> list[dict]:
    steps = []
    test = record.get("test") or {}
    qc = record.get("qc") or {}
    reason = str(qc.get("qc_reason") or "")
    if test.get("test_origin") == "simulation":
        steps.append({
            "rule_id": "R-QC-01",
            "category": "quality_control",
            "field": "test_origin",
            "formula": "simulation -> L3, performance is_derived=1",
            "formula_inputs": {"test_origin": "simulation"},
            "result": "applied",
            "qc_level": qc.get("qc_level"),
            "knowledge": rules.RULES_BY_ID["R-QC-01"]["knowledge"],
        })
    if "metric_semantics" in reason:
        steps.append({
            "rule_id": "R-QC-02",
            "category": "quality_control",
            "field": "performance.metric_semantics",
            "formula": "label/unit/sign contradiction -> L3",
            "formula_inputs": {"qc_reason": reason[:300]},
            "result": "applied",
            "qc_level": qc.get("qc_level"),
            "knowledge": rules.RULES_BY_ID["R-QC-02"]["knowledge"],
        })
    missing = [f for f in REQUIRED if (record.get("test") or {}).get(f) is None]
    if missing:
        steps.append({
            "rule_id": "R-INF-01",
            "category": "quality_control",
            "field": "missing_required_fields",
            "formula": "keep null; incomplete/L3",
            "formula_inputs": {"missing": missing},
            "result": "applied",
            "qc_level": qc.get("qc_level"),
            "knowledge": rules.RULES_BY_ID["R-INF-01"]["knowledge"],
        })
    return steps


def consistency_issues(raw: dict, record: dict) -> list[dict]:
    _, issues = _deterministic_steps(raw, record)
    qc = record.get("qc") or {}
    if (record.get("test") or {}).get("test_origin") == "simulation" and qc.get("qc_level") in ("L1", "L2"):
        issues.append({
            "rule_id": "R-QC-01",
            "blocking": True,
            "reason": "simulation_record_not_isolated",
            "detail": f"qc_level={qc.get('qc_level')}",
        })
    evidence = {str(i.get("field")): str(i.get("type") or "").capitalize() for i in _evidence_items(raw)}
    if qc.get("qc_level") == "L2":
        assumed = [f for f in REQUIRED if evidence.get(f) == "Assumed" and (record.get("test") or {}).get(f) is not None]
        if assumed:
            issues.append({
                "rule_id": "R-EVD-04",
                "blocking": True,
                "reason": "assumed_required_field_upgraded_to_l2",
                "detail": ",".join(assumed),
            })
    return issues


def apply_consistency(record: dict, issues: list[dict]) -> tuple[str, str]:
    qc = record.get("qc") or {}
    level = qc.get("qc_level")
    reason = str(qc.get("qc_reason") or "")
    if not issues:
        return level, reason
    blocking = any(i.get("blocking") for i in issues)
    if blocking and level in ("L1", "L2"):
        level = "L3"
    tags = [f"reasoning_gate:{i['reason']}" for i in issues]
    merged = ";".join(dict.fromkeys([p for p in (reason.split(";") if reason else []) if p] + tags))
    record["qc"] = {"qc_level": level, "qc_reason": merged}
    return level, merged


def trace_record(
    raw: dict,
    record: dict,
    verification: dict | None = None,
    *,
    context: dict | None = None,
    modules: list[dict] | None = None,
) -> dict:
    context = context or {}
    steps = []
    for item in _evidence_items(raw):
        steps.append(_evidence_step(item, record, raw))
    det, _issues = _deterministic_steps(raw, record)
    steps.extend(det)
    xsec = _cross_section_step(record, context)
    if xsec:
        steps.append(xsec)
    if context.get("condition_profile"):
        steps.append({
            "rule_id": "R-XSEC-03",
            "category": "expert_judgement",
            "evidence_type": "Contextual",
            "field": "condition_profile",
            "formula": "fill only missing conditions when declared method phrases match",
            "formula_inputs": context.get("condition_profile"),
            "result": "applied",
            "knowledge": rules.RULES_BY_ID["R-XSEC-03"]["knowledge"],
        })
    contextual = [s["field"] for s in steps if s.get("evidence_type") == "Contextual"]
    if contextual:
        steps.append({
            "rule_id": "R-EXP-01",
            "category": "expert_judgement",
            "evidence_type": "Contextual",
            "field": "contextual_conditions",
            "formula": "context sentence fixes the value; verification still applies",
            "formula_inputs": {"fields": contextual},
            "result": "candidate_accepted",
            "knowledge": rules.RULES_BY_ID["R-EXP-01"]["knowledge"],
        })
    assumed = [s["field"] for s in steps if s.get("evidence_type") == "Assumed"]
    if assumed:
        steps.append({
            "rule_id": "R-EXP-02",
            "category": "expert_judgement",
            "evidence_type": "Assumed",
            "field": "assumptions",
            "formula": "Assumed required fields cannot reach L2",
            "formula_inputs": {"fields": assumed},
            "result": "not_paper_fact",
            "knowledge": rules.RULES_BY_ID["R-EXP-02"]["knowledge"],
        })
    steps.extend(_qc_steps(raw, record))

    unknown = sorted({s["field"] for s in steps if s.get("evidence_type") == "Unknown"})
    return {
        "trace_version": TRACE_VERSION,
        "rule_set": rules.catalog_manifest(),
        "knowledge_modules": [
            {"id": m.get("id"), "sha256": m.get("sha256")}
            for m in (modules or [])
        ],
        "module_rules": rules.rules_for_modules([m.get("id") for m in (modules or []) if m.get("id")]),
        "verification": {
            "verified": (verification or {}).get("verified"),
            "numeric_match_ratio": (verification or {}).get("numeric_match_ratio"),
            "required_evidence_ok": (verification or {}).get("required_evidence_ok"),
            "reasons": (verification or {}).get("reasons") or [],
        },
        "steps": steps,
        "summary": {
            "steps": len(steps),
            "by_category": {
                c: sum(1 for s in steps if s.get("category") == c)
                for c in sorted({s.get("category") for s in steps})
            },
            "by_evidence": {
                e: sum(1 for s in steps if s.get("evidence_type") == e)
                for e in sorted({s.get("evidence_type") for s in steps if s.get("evidence_type")})
            },
            "unknown_fields": unknown,
            "assumptions": assumed,
            "formula_steps": sum(1 for s in steps if s.get("formula")),
        },
    }
