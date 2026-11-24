"""Record-level precision/recall/F1 with explicit denominators.

This is a small, not-human-verified evaluation. Two views are reported:
- acceptance level: matched positive record kept at L2, extra L2 records as FP;
- strict field level: matched positive L2 with every expected field present and
  inside its tolerance, so a missing/out-of-tolerance field counts as FN.
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EVAL = ROOT / "evaluation/eval_set_v1.json"
NEG = ROOT / "evaluation/negative_set_v1.json"
NEG_REPORT = ROOT / "evaluation/reports/negative_eval.md.json"
BATCH = ROOT / "extractions/batch_20261124_145027"
OUT = ROOT / "evaluation/reports/comprehensive_metrics.md"


def load_ev():
    spec = importlib.util.spec_from_file_location("ev", ROOT / "evaluation/evaluate.py")
    ev = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ev)
    return ev


def main() -> None:
    ev = load_ev()
    samples = json.loads(EVAL.read_text(encoding="utf-8"))["samples"]
    raw_candidates, _, _ = ev.load_candidates(BATCH)
    candidates = [ev.flatten(r) for r in raw_candidates]
    used = set()
    matched = []
    unmatched = []
    for sample in samples:
        best_i, best_score = None, math.inf
        for i, cand in enumerate(candidates):
            if i in used:
                continue
            score = ev.match_score(sample, cand)
            if score < best_score:
                best_i, best_score = i, score
        if best_i is not None and best_score <= 40:
            used.add(best_i)
            matched.append((sample, candidates[best_i], best_score))
        else:
            unmatched.append(sample)

    strict_tp = 0
    strict_failures = []
    for sample, cand, _ in matched:
        if cand.get("qc_level") != "L2":
            strict_failures.append({"sample_id": sample["sample_id"], "reason": "not_L2"})
            continue
        exp = ev.expected_fields(sample)
        cand_fields = ev.candidate_fields(cand)
        bad = []
        for key, value in exp.items():
            if value is None:
                continue
            got = cand_fields.get(key)
            if got is None:
                bad.append(f"{key}:missing")
            else:
                try:
                    if abs(float(value) - float(got)) > ev.tolerance(key, float(value)):
                        bad.append(f"{key}:outside")
                except (TypeError, ValueError):
                    bad.append(f"{key}:invalid")
        if bad:
            strict_failures.append({"sample_id": sample["sample_id"], "reason": ",".join(bad)})
        else:
            strict_tp += 1

    extra = [c for i, c in enumerate(candidates) if i not in used]
    extra_l2 = [c for c in extra if c.get("qc_level") == "L2"]
    neg = json.loads(NEG.read_text(encoding="utf-8"))["samples"]
    neg_report = json.loads(NEG_REPORT.read_text(encoding="utf-8")) if NEG_REPORT.exists() else {}
    fp_negative = int(neg_report.get("false_accept_l2", 0))

    tp_accept = sum(1 for _, c, _ in matched if c.get("qc_level") == "L2")
    fn_accept = len(samples) - tp_accept
    fp_accept = len(extra_l2) + fp_negative
    tn = len(neg) - fp_negative
    precision_accept = tp_accept / (tp_accept + fp_accept) if (tp_accept + fp_accept) else 0.0
    recall_accept = tp_accept / (tp_accept + fn_accept) if (tp_accept + fn_accept) else 0.0
    f1_accept = (
        2 * precision_accept * recall_accept / (precision_accept + recall_accept)
        if (precision_accept + recall_accept) else 0.0
    )
    fp_strict = len(extra_l2) + fp_negative
    precision_strict = strict_tp / (strict_tp + fp_strict) if (strict_tp + fp_strict) else 0.0
    recall_strict = strict_tp / len(samples) if samples else 0.0
    f1_strict = (
        2 * precision_strict * recall_strict / (precision_strict + recall_strict)
        if (precision_strict + recall_strict) else 0.0
    )

    result = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "caveat": "Preliminary: 38 L2 positive samples and 28 negative/boundary samples; labels are not human-verified.",
        "positive_samples": len(samples),
        "negative_samples": len(neg),
        "negative_with_candidate": int(neg_report.get("with_candidate", 0)),
        "acceptance_level": {
            "TP": tp_accept, "FN": fn_accept, "FP": fp_accept, "TN": tn,
            "extra_L2_candidates": len(extra_l2),
            "negative_false_accept_L2": fp_negative,
            "precision": round(precision_accept, 4),
            "recall": round(recall_accept, 4),
            "f1": round(f1_accept, 4),
            "false_accept_rate_all_negatives": round(fp_negative / len(neg), 4) if neg else 0.0,
            "false_accept_rate_with_candidate": round(fp_negative / neg_report.get("with_candidate", 1), 4)
            if neg_report.get("with_candidate") else 0.0,
        },
        "strict_field_level": {
            "TP": strict_tp, "FN": len(samples) - strict_tp, "FP": fp_strict,
            "precision": round(precision_strict, 4),
            "recall": round(recall_strict, 4),
            "f1": round(f1_strict, 4),
            "failures": strict_failures,
        },
        "unmatched_positive": [s["sample_id"] for s in unmatched],
        "extra_candidates": len(extra),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    (OUT.with_suffix(".json")).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [
        "# Comprehensive precision / recall / F1",
        "",
        f"- {result['caveat']}",
        f"- Positive samples: {len(samples)} (38 L2 reference)",
        f"- Negative/boundary samples: {len(neg)}; with candidate: {result['negative_with_candidate']}",
        "",
        "## Acceptance level (record kept at L2)",
        "",
        "| TP | FN | FP | TN | Precision | Recall | F1 | FAR (all negatives) | FAR (with candidate) |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        f"| {tp_accept} | {fn_accept} | {fp_accept} | {tn} | {precision_accept:.1%} | {recall_accept:.1%} | {f1_accept:.3f} | "
        f"{result['acceptance_level']['false_accept_rate_all_negatives']:.1%} | "
        f"{result['acceptance_level']['false_accept_rate_with_candidate']:.1%} |",
        "",
        "FP = extra L2 candidates not matched to a positive + negative false accepts. "
        "TN counts all negative samples, including those with no candidate record.",
        "",
        "## Strict field level (all expected fields present and within tolerance)",
        "",
        "| TP | FN | FP | Precision | Recall | F1 |",
        "|---:|---:|---:|---:|---:|---:|",
        f"| {strict_tp} | {len(samples) - strict_tp} | {fp_strict} | {precision_strict:.1%} | "
        f"{recall_strict:.1%} | {f1_strict:.3f} |",
        "",
        "Strict failures:",
    ]
    for f in strict_failures:
        lines.append(f"- `{f['sample_id']}`: {f['reason']}")
    lines += [
        "",
        "## Scope limits",
        "",
        "- The positive set covers 7 papers; it is not a random sample of the literature.",
        "- Negative labels are machine-derived and include 10 samples with no candidate record.",
        "- Boundary samples are valid VLE points outside the current profile range; they are excluded from FAR and checked for false reject.",
        "- No human verification has been performed; these metrics are preliminary.",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if strict_tp > 0 else 1)


if __name__ == "__main__":
    main()
