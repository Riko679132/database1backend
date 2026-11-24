"""Build the Phase-4 extra-candidate review and negative evaluation set."""
from __future__ import annotations

import csv
import importlib.util
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BATCH = ROOT / "extractions/batch_20261124_145027"
EVAL = ROOT / "evaluation/eval_set_v1.json"
ASSESS = ROOT / "data/raw_pdfs/extraction_todo_assessment.csv"
OUT_NEG = ROOT / "evaluation/negative_set_v1.json"
OUT_REVIEW_MD = ROOT / "evaluation/reports/extra_candidates_review.md"
OUT_REVIEW_JSON = ROOT / "evaluation/reports/extra_candidates_review.json"


def load_eval_module():
    spec = importlib.util.spec_from_file_location("ev", ROOT / "evaluation/evaluate.py")
    ev = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ev)
    return ev


def key_for(rec: dict, metric: str | None = None) -> list:
    return [
        rec.get("doi"),
        rec.get("amine_a"),
        rec.get("amine_b"),
        rec.get("wt_a"),
        rec.get("wt_b"),
        rec.get("temperature_K"),
        rec.get("co2_partial_kPa"),
        metric,
        round(float((rec.get("metrics") or {}).get(metric, 0)), 6) if metric else None,
    ]


def classify(extra: dict) -> tuple[str, str, str | None]:
    doi = extra.get("doi")
    metrics = extra.get("metrics") or {}
    for metric, value in metrics.items():
        unit = str((extra.get("units") or {}).get(metric) or "").lower()
        if metric == "regeneration_heat" and ("kj/mol" in unit or float(value) < 0):
            return (
                "Insufficient Evidence",
                "regeneration_heat label but unit/sign indicate heat of absorption/reaction (kJ/mol), not regeneration heat",
                metric,
            )
    if doi == "10.1021/je00005a025":
        return "Valid L3", "VLE point outside the 40 C low-pressure target (high P or other temperature)", None
    if doi == "10.1021/acs.iecr.9b00552" and "co2_removal_efficiency" in metrics:
        return "Valid L3", "pilot CO2 removal efficiency; missing initial loading/complete conditions", None
    if doi == "10.1016/j.ijggc.2016.12.018" and extra.get("temperature_K") == 353.15:
        return "Valid L3", "additional MEA VLE point at 353 K; missing total pressure/initial loading", None
    return "Pending Review", "extra candidate not matched to the 38-record reference; human review required", None


def main() -> None:
    ev = load_eval_module()
    samples = json.loads(EVAL.read_text(encoding="utf-8"))["samples"]
    cands, rejected, _ = ev.load_candidates(BATCH)
    flat = [ev.flatten(c) for c in cands]
    used = set()
    for s in samples:
        best, best_score = None, float("inf")
        for i, c in enumerate(flat):
            if i in used:
                continue
            score = ev.match_score(s, c)
            if score < best_score:
                best, best_score = i, score
        if best is not None and best_score <= 40:
            used.add(best)
    extras = []
    for i, c in enumerate(flat):
        if i in used:
            continue
        label, reason, metric = classify(c)
        extras.append({
            "doi": c["doi"],
            "amine_a": c["amine_a"],
            "amine_b": c["amine_b"],
            "wt_a": c["wt_a"],
            "wt_b": c["wt_b"],
            "temperature_K": c["temperature_K"],
            "co2_vol_pct": c["co2_vol_pct"],
            "co2_partial_kPa": c["co2_partial_kPa"],
            "total_pressure_kPa": c["total_pressure_kPa"],
            "metrics": c["metrics"],
            "qc_level": c["qc_level"],
            "qc_reason": c["qc_reason"],
            "label": label,
            "reason": reason,
            "metric_key": metric,
        })

    # Negative set: extras that are not "Valid L3"; plus L4 duplicate and out-of-scope DOIs.
    negatives = []
    for e in extras:
        if e["label"] not in ("Insufficient Evidence", "Duplicate", "Out of Scope", "Model-derived", "Pending Review"):
            continue
        metric = e["metric_key"]
        negatives.append({
            "sample_id": f"EXTRA-{len(negatives)+1:02d}",
            "doi": e["doi"],
            "label": e["label"],
            "reason": e["reason"],
            "candidate_key": key_for(e, metric),
            "match_by_doi": True,
            "human_verified": False,
            "evidence": {"qc_level": e["qc_level"], "qc_reason": e["qc_reason"]},
        })

    # L4 rejected record: duplicate/incomplete composition.
    for r in rejected:
        rec = ev.flatten(r)
        negatives.append({
            "sample_id": f"L4-{len(negatives)+1:02d}",
            "doi": rec["doi"],
            "label": "Duplicate",
            "reason": "L4 rejected record from a DOI that already has a valid L2 MEA record; wt/mass balance missing",
            "candidate_key": key_for(rec),
            "match_by_doi": True,
            "prefer_qc": "L4",
            "human_verified": False,
            "evidence": {"qc_level": rec["qc_level"], "qc_reason": rec["qc_reason"]},
        })

    # Out-of-scope DOIs from the assessment ledger (no candidate in the final batch).
    with ASSESS.open(encoding="utf-8-sig", newline="") as fh:
        out_rows = [r for r in csv.DictReader(fh) if str(r.get("in_scope", "")).lower() == "no"]
    for r in out_rows[:6]:
        negatives.append({
            "sample_id": f"OOS-{len(negatives)+1:02d}",
            "doi": r.get("doi"),
            "label": "Out of Scope",
            "reason": r.get("reason") or "assessment ledger marks the paper out of scope",
            "candidate_key": None,
            "match_by_doi": True,
            "human_verified": False,
            "evidence": {"ledger": "data/raw_pdfs/extraction_todo_assessment.csv"},
        })

    # Out-of-scope papers actually processed in the negative batch
    # (batch_20261124_145418); all returned 0 records.
    processed_oos = [
        ("10.1021/acs.iecr.1c04123", "1 M PZ/MEA/MDEA/AMP blends; mol/L without density; recipe cannot close"),
        ("10.1155/2022/6278342", "20 wt% MEA VLE only in figures; data embargo; no table"),
        ("10.1021/acs.iecr.4c03980", "iron solubility in MEA; no amine absorption performance data"),
        ("10.1016/j.ces.2017.02.036", "2-5 M amine blends; no wt%/density; recipe cannot close"),
    ]
    for doi, reason in processed_oos:
        negatives.append({
            "sample_id": f"OOS-PROC-{len(negatives)+1:02d}",
            "doi": doi,
            "label": "Out of Scope",
            "reason": reason,
            "candidate_key": None,
            "match_by_doi": True,
            "processed_batch": "batch_20261124_145418",
            "human_verified": False,
            "evidence": {"batch": "batch_20261124_145418", "records": 0},
        })

    # Phase 5: actual incomplete rows from the final batch. Missing required
    # fields are insufficient evidence, not "wrong data"; L3 is acceptable.
    incomplete_path = BATCH / "valid_incomplete.jsonl"
    if incomplete_path.exists():
        chosen = []
        seen_dois = set()
        for line in incomplete_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            doi = (raw.get("source") or {}).get("doi")
            if doi in seen_dois:
                continue
            seen_dois.add(doi)
            flat = ev.flatten(raw)
            metric = next(iter(flat.get("metrics") or {}), None)
            negatives.append({
                "sample_id": f"INC-{len(negatives)+1:02d}",
                "doi": doi,
                "label": "Insufficient Evidence",
                "reason": (
                    "actual batch record missing required field(s): "
                    + ";".join((raw.get("qc") or {}).get("qc_reason", "").split(";")[:4])
                ),
                "candidate_key": key_for(flat, metric),
                "match_by_doi": True,
                "human_verified": False,
                "evidence": {"qc_level": flat.get("qc_level"), "batch": BATCH.name},
            })
            chosen.append(doi)
            if len(chosen) >= 3:
                break

    # Phase 5: actual simulation rows already in historical batches. They are
    # model-derived; L3 is acceptable, L2 is a false accept.
    sim_batches = [ROOT / "extractions/20261027_04", ROOT / "extractions/20261027_05"]
    sim_specs = ["10.1016/j.ces.2026.124685", "10.1016/j.seppur.2026.139992"]
    for batch in sim_batches:
        path = batch / "valid_incomplete.jsonl"
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            raw = json.loads(line)
            doi = (raw.get("source") or {}).get("doi")
            if doi not in sim_specs or (raw.get("test") or {}).get("test_origin") != "simulation":
                continue
            flat = ev.flatten(raw)
            metric = next(iter(flat.get("metrics") or {}), None)
            negatives.append({
                "sample_id": f"SIM-{len(negatives)+1:02d}",
                "doi": doi,
                "label": "Model-derived",
                "reason": "actual simulation record from a historical batch; must stay L3",
                "candidate_key": key_for(flat, metric),
                "match_by_doi": True,
                "human_verified": False,
                "evidence": {"qc_level": flat.get("qc_level"), "batch": batch.name,
                             "test_origin": "simulation"},
            })
            sim_specs.remove(doi)
            break

    # Phase 5: boundary VLE points above the existing profile pressure range or
    # at another temperature. They must not be rejected; L3 is the expected
    # outcome, L2 would be over-acceptance but is not a false reject.
    boundary = []
    for e in extras:
        if e["doi"] != "10.1021/je00005a025" or e["qc_level"] != "L3":
            continue
        p = e.get("co2_partial_kPa")
        t = e.get("temperature_K")
        if (p is not None and float(p) > 180.0) or (t is not None and abs(float(t) - 313.15) > 0.5):
            metric = e.get("metric_key")
            boundary.append({
                "sample_id": f"BND-{len(boundary)+1:02d}",
                "doi": e["doi"],
                "label": "Boundary",
                "reason": (
                    f"VLE point outside the 40 C / <=180 kPa profile (T={t} K, P_CO2={p} kPa); "
                    "valid data must remain available as L3"
                ),
                "candidate_key": key_for(e, metric),
                "match_by_doi": True,
                "human_verified": False,
                "evidence": {"qc_level": e["qc_level"], "qc_reason": e["qc_reason"]},
            })
            if len(boundary) >= 5:
                break
    negatives.extend(boundary)

    # A known simulation paper: model-derived, never L1/L2.
    negatives.append({
        "sample_id": f"MODEL-{len(negatives)+1:02d}",
        "doi": "10.1016/j.ces.2026.124685",
        "label": "Model-derived",
        "reason": "simulation/modeling paper; not experimental L2 data",
        "candidate_key": None,
        "match_by_doi": True,
        "human_verified": False,
        "evidence": {"source": "triage DONE/simulation record"},
    })

    payload = {
        "negative_version": "v2",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "label_policy": {
            "Negative": "clearly not eligible; any accepted L2/L3 is a false accept",
            "Out of Scope": "outside the research boundary; any accepted L2/L3 is a false accept",
            "Duplicate": "same data already represented; accepted L2/L3 is a false accept",
            "Insufficient Evidence": "data are valid research content but missing required evidence; L2 is a false accept, L3 is an acceptable reference",
            "Model-derived": "model/simulation output; L2 is a false accept, L3 is acceptable",
            "Boundary": "valid VLE data outside the developed profile range; absence or L4 is a false reject, L3 is acceptable",
            "Pending Review": "excluded from false-accept metrics until human review",
            "Valid L3": "real data but outside the L2 target; not a negative",
        },
        "samples": negatives,
        "human_verified": False,
    }
    OUT_NEG.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    review = {
        "batch": BATCH.as_posix(),
        "extras": extras,
        "counts": {
            "extras": len(extras),
            "valid_l3": sum(1 for e in extras if e["label"] == "Valid L3"),
            "insufficient_evidence": sum(1 for e in extras if e["label"] == "Insufficient Evidence"),
            "pending_review": sum(1 for e in extras if e["label"] == "Pending Review"),
            "negative_samples": len(negatives),
            "boundary_samples": len(boundary),
            "insufficient_samples": sum(1 for s in negatives if s["label"] == "Insufficient Evidence"),
            "model_samples": sum(1 for s in negatives if s["label"] == "Model-derived"),
        },
    }
    OUT_REVIEW_JSON.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 多余候选记录人工判定表",
        "",
        f"- Batch: `{BATCH.as_posix()}`",
        f"- Extras: {len(extras)}",
        "",
        "| DOI | amine | wt_a | wt_b | T (K) | P_CO2 | metrics | QC | label | reason |",
        "|---|---|---:|---:|---:|---:|---|---|---|---|",
    ]
    for e in extras:
        lines.append(
            f"| {e['doi']} | {e['amine_a']} | {e['wt_a']} | {e['wt_b']} | {e['temperature_K']} | {e['co2_partial_kPa']} | {e['metrics']} | {e['qc_level']} | {e['label']} | {e['reason']} |"
        )
    lines += [
        "",
        "## 说明",
        "",
        "- `Valid L3`：真实数据但不在 27 点 L2 目标选择内（高压/其他温度/缺失条件），不作为负样本。",
        "- `Insufficient Evidence`：研究内容真实，但指标定义/单位/条件不足，不能作为 L2；L3 可作参考。",
        "- `Duplicate`：同一 DOI 已有有效 L2，多出的不完整记录不应新增。",
        "- `Out of Scope`：体系/浓度/单位边界外，任何接受都是 false accept。",
        "- `Boundary`：超出既有 VLE profile 范围的有效数据；不得因超出范围而拒收，L3 可接受。",
        "- `Pending Review`：尚未人工判定，排除在 false-accept 指标之外。",
    ]
    OUT_REVIEW_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(review["counts"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
