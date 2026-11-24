"""Evaluate false accepts against the Phase-4 negative set."""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
NEG = ROOT / "evaluation/negative_set_v1.json"
BATCH = ROOT / "extractions/batch_20261124_145027"
OUT_JSON = ROOT / "evaluation/reports/negative_eval.md.json"
OUT_MD = ROOT / "evaluation/reports/negative_eval.md"


def load_eval():
    spec = importlib.util.spec_from_file_location("ev", ROOT / "evaluation/evaluate.py")
    ev = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ev)
    return ev


def key_matches(neg_key, cand, metric):
    if neg_key is None:
        return False
    doi, amine_a, amine_b, wt_a, wt_b, t, p, m, value = neg_key
    if str(doi or "").lower() != str(cand.get("doi") or "").lower():
        return False
    if amine_a and cand.get("amine_a") and str(amine_a).lower() != str(cand["amine_a"]).lower():
        return False
    for a, b, tol in ((wt_a, cand.get("wt_a"), 0.2), (wt_b, cand.get("wt_b"), 0.2),
                      (t, cand.get("temperature_K"), 0.1), (p, cand.get("co2_partial_kPa"), 1.0)):
        if a is None:
            continue
        if b is None or not math.isclose(float(a), float(b), rel_tol=1e-6, abs_tol=tol):
            return False
    if m and m not in (cand.get("metrics") or {}):
        return False
    if m and value is not None:
        b = (cand.get("metrics") or {}).get(m)
        if b is None or not math.isclose(float(value), float(b), rel_tol=0.02, abs_tol=0.005):
            return False
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", action="append", default=[])
    args = ap.parse_args()
    batches = [Path(p) for p in args.candidate] or [BATCH]
    ev = load_eval()
    neg = json.loads(NEG.read_text(encoding="utf-8"))["samples"]
    flat = []
    for batch in batches:
        cands, rejected, _ = ev.load_candidates(batch)
        flat.extend(ev.flatten(c) for c in cands)
        flat.extend(ev.flatten(r) for r in rejected)
    outcomes = []
    for s in neg:
        matches = []
        for c in flat:
            if s.get("prefer_qc") and c.get("qc_level") != s["prefer_qc"]:
                continue
            if s.get("candidate_key"):
                metric = s["candidate_key"][7]
                if key_matches(s["candidate_key"], c, metric):
                    matches.append(c)
            elif s.get("match_by_doi") and str(c.get("doi") or "").lower() == str(s.get("doi") or "").lower():
                matches.append(c)
        if not matches:
            outcome = "FALSE_REJECT_BOUNDARY" if s.get("label") == "Boundary" else "correct_not_extracted"
            qc = None
        else:
            qc = matches[0].get("qc_level")
            label = s["label"]
            if label == "Boundary":
                if qc == "L4":
                    outcome = "FALSE_REJECT_BOUNDARY"
                elif qc in ("L1", "L2", "L3"):
                    outcome = "correct_boundary_kept_L2" if qc in ("L1", "L2") else "correct_boundary_kept_L3"
                else:
                    outcome = "FALSE_REJECT_BOUNDARY"
            elif label in ("Negative", "Out of Scope", "Duplicate"):
                outcome = "correct_reject_L4" if qc == "L4" else "FALSE_ACCEPT"
            elif label == "Insufficient Evidence":
                if qc == "L2":
                    outcome = "FALSE_ACCEPT"
                elif qc == "L3":
                    outcome = "correct_downgrade_L3"
                else:
                    outcome = "correct_reject_L4"
            elif label == "Model-derived":
                outcome = "FALSE_ACCEPT" if qc == "L2" else "correct_model_L3"
            else:
                outcome = "pending"
        outcomes.append({
            "sample_id": s["sample_id"],
            "doi": s.get("doi"),
            "label": s["label"],
            "qc_level": qc,
            "outcome": outcome,
            "reason": s.get("reason"),
        })
    counts = {}
    for o in outcomes:
        counts[o["outcome"]] = counts.get(o["outcome"], 0) + 1
    with_candidate = sum(1 for o in outcomes if o["qc_level"] is not None)
    false_l2 = sum(1 for o in outcomes if o["outcome"] == "FALSE_ACCEPT" and o["qc_level"] == "L2")
    false_any = sum(1 for o in outcomes if o["outcome"] == "FALSE_ACCEPT")
    false_reject_boundary = sum(1 for o in outcomes if o["outcome"] == "FALSE_REJECT_BOUNDARY")
    boundary_kept_l2 = sum(1 for o in outcomes if o["outcome"] == "correct_boundary_kept_L2")
    result = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "candidate_batches": [str(p) for p in batches],
        "negative_samples": len(neg),
        "with_candidate": with_candidate,
        "outcomes": counts,
        "false_accept_l2": false_l2,
        "false_accept_any": false_any,
        "false_reject_boundary": false_reject_boundary,
        "boundary_kept_l2": boundary_kept_l2,
        "false_accept_rate_l2_all": false_l2 / len(neg) if neg else 0.0,
        "false_accept_rate_l2_with_candidate": false_l2 / with_candidate if with_candidate else 0.0,
        "false_accept_rate_any_all": false_any / len(neg) if neg else 0.0,
        "false_accept_rate_any_with_candidate": false_any / with_candidate if with_candidate else 0.0,
        "human_verified": False,
        "rows": outcomes,
    }
    OUT_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Negative-set evaluation",
        "",
        f"- Negative samples: {len(neg)}",
        f"- With a candidate in the final batch: {with_candidate}",
        f"- Outcomes: {counts}",
        f"- False accept L2: {false_l2}",
        f"- False accept any L2/L3: {false_any}",
        f"- Boundary false rejects: {false_reject_boundary}",
        f"- Boundary kept as L2 (over-accept, not false reject): {boundary_kept_l2}",
        f"- FAR (L2, all negatives): {result['false_accept_rate_l2_all']:.1%}",
        f"- FAR (L2, negatives with candidate): {result['false_accept_rate_l2_with_candidate']:.1%}",
        "",
        "| ID | DOI | label | QC | outcome | reason |",
        "|---|---|---|---|---|---|",
    ]
    for o in outcomes:
        lines.append(f"| {o['sample_id']} | {o['doi']} | {o['label']} | {o['qc_level']} | {o['outcome']} | {o['reason']} |")
    lines += [
        "",
        "`Insufficient Evidence` allows L3 as a reference but flags L2 as false accept.",
        "`Out of Scope`/`Duplicate`/`Negative` allow no accepted record.",
        "`Model-derived` allows L3 but not L2.",
        "`Boundary` requires the candidate to remain available; L4 or absence is a false reject, L2 is over-acceptance.",
    ]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("negative_samples", "with_candidate", "outcomes", "false_accept_l2", "false_accept_any", "false_accept_rate_l2_all", "false_accept_rate_any_all")}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
