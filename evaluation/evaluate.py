"""Evaluate an extraction batch against the 38-record L2 regression set.

Metrics:
- coverage: expected samples with a matched candidate
- field completeness: present / expected non-null fields
- numeric agreement: within field-specific tolerance
- recipe closure: complete / partial / unclosed / missing
- QC outcomes: L2 / L3 / L4 / missing (false reject of an L2 reference)
- rejection reason counts
"""
from __future__ import annotations

import argparse
import json
import math
import time
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

FIELD_LABELS = {
    "recipe.wt_a": "胺 A wt%",
    "recipe.wt_b": "胺 B wt%",
    "recipe.water_wt": "水 wt%",
    "recipe.total_amine_wt": "总胺 wt%",
    "conditions.temperature_K": "温度 K",
    "conditions.co2_vol_pct": "CO2 vol%",
    "conditions.co2_partial_kPa": "CO2 分压 kPa",
    "conditions.total_pressure_kPa": "总压 kPa",
    "conditions.initial_loading": "初始负载",
    "loadings.rich": "rich loading",
    "loadings.lean": "lean loading",
}


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out


def load_candidates(path: Path) -> tuple[list[dict], list[dict], dict]:
    rejected: list[dict] = []
    manifest: dict = {}
    if path.is_dir():
        manifest_path = path / "extraction_manifest.json"
        if manifest_path.exists():
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except ValueError:
                manifest = {}
        candidates = []
        for name in ("valid.jsonl", "valid_incomplete.jsonl"):
            candidates.extend(read_jsonl(path / "validated" / name))
        if not candidates:
            for name in ("valid.jsonl", "valid_incomplete.jsonl"):
                candidates.extend(read_jsonl(path / name))
        if not candidates:
            candidates.extend(read_jsonl(path / "raw_agent.jsonl"))
        rejected = read_jsonl(path / "validated" / "rejected.jsonl") or read_jsonl(path / "rejected.jsonl")
    else:
        candidates = read_jsonl(path)
    return candidates, rejected, manifest


def amine_name(value) -> str | None:
    if isinstance(value, dict):
        return value.get("standard_name")
    return str(value) if value else None


def flatten(rec: dict) -> dict:
    src = rec.get("source") or {}
    recipe = rec.get("recipe") or {}
    test = rec.get("test") or {}
    perf = rec.get("performance") or []
    metrics = {}
    units = {}
    for item in perf:
        if isinstance(item, dict) and item.get("metric_name") and item.get("value") is not None:
            try:
                metrics[item["metric_name"]] = float(item["value"])
                units[item["metric_name"]] = item.get("unit")
            except (TypeError, ValueError):
                pass
    return {
        "doi": src.get("doi"),
        "recipe_type": recipe.get("recipe_type"),
        "amine_a": amine_name(recipe.get("amine_a")),
        "amine_b": amine_name(recipe.get("amine_b")),
        "wt_a": recipe.get("wt_a"),
        "wt_b": recipe.get("wt_b"),
        "water_wt": recipe.get("water_wt"),
        "total_amine_wt": recipe.get("total_amine_wt"),
        "temperature_K": test.get("temperature_K"),
        "co2_vol_pct": test.get("co2_vol_pct"),
        "co2_partial_kPa": test.get("co2_partial_kPa"),
        "total_pressure_kPa": test.get("total_pressure_kPa"),
        "initial_loading": test.get("initial_loading"),
        "rich_loading": test.get("rich_loading"),
        "lean_loading": test.get("lean_loading"),
        "metrics": metrics,
        "units": units,
        "qc_level": (rec.get("qc") or {}).get("qc_level"),
        "qc_reason": (rec.get("qc") or {}).get("qc_reason"),
        "raw": rec,
    }


def expected_fields(sample: dict) -> dict:
    recipe = sample.get("recipe") or {}
    cond = sample.get("conditions") or {}
    load = sample.get("loadings") or {}
    fields = {
        "recipe.wt_a": recipe.get("wt_a"),
        "recipe.wt_b": recipe.get("wt_b"),
        "recipe.water_wt": recipe.get("water_wt"),
        "recipe.total_amine_wt": recipe.get("total_amine_wt"),
        "conditions.temperature_K": cond.get("temperature_K"),
        "conditions.co2_vol_pct": cond.get("co2_vol_pct"),
        "conditions.co2_partial_kPa": cond.get("co2_partial_kPa"),
        "conditions.total_pressure_kPa": cond.get("total_pressure_kPa"),
        "conditions.initial_loading": cond.get("initial_loading"),
        "loadings.rich": load.get("rich"),
        "loadings.lean": load.get("lean"),
    }
    for p in sample.get("performance") or []:
        if p.get("metric_name") and p.get("value") is not None:
            fields[f"performance.{p['metric_name']}"] = p.get("value")
    return fields


def candidate_fields(cand: dict) -> dict:
    out = {
        "recipe.wt_a": cand.get("wt_a"),
        "recipe.wt_b": cand.get("wt_b"),
        "recipe.water_wt": cand.get("water_wt"),
        "recipe.total_amine_wt": cand.get("total_amine_wt"),
        "conditions.temperature_K": cand.get("temperature_K"),
        "conditions.co2_vol_pct": cand.get("co2_vol_pct"),
        "conditions.co2_partial_kPa": cand.get("co2_partial_kPa"),
        "conditions.total_pressure_kPa": cand.get("total_pressure_kPa"),
        "conditions.initial_loading": cand.get("initial_loading"),
        "loadings.rich": cand.get("rich_loading"),
        "loadings.lean": cand.get("lean_loading"),
    }
    for metric, value in (cand.get("metrics") or {}).items():
        out[f"performance.{metric}"] = value
    return out


def tolerance(field: str, expected: float) -> float:
    if field.endswith("temperature_K"):
        return 0.1
    if field.endswith("co2_vol_pct"):
        return 0.5
    if field.endswith("co2_partial_kPa") or field.endswith("total_pressure_kPa"):
        return max(1.0, abs(expected) * 0.01)
    if field.endswith("loading") or field.endswith("rich") or field.endswith("lean"):
        return 0.01
    if field.startswith("recipe.wt") or field.endswith("water_wt") or field.endswith("total_amine_wt"):
        return 0.2
    if field.startswith("performance."):
        metric = field.split(".", 1)[1]
        if metric in ("regeneration_efficiency", "co2_removal_efficiency"):
            return 1.0
        if metric == "pka":
            return 0.05
        return max(0.005, abs(expected) * 0.02)
    return max(0.005, abs(expected) * 0.02)


def match_score(sample: dict, cand: dict) -> float:
    if (sample.get("doi") or "").lower() != (cand.get("doi") or "").lower():
        return math.inf
    exp = sample.get("recipe") or {}
    score = 0.0
    # Different amine identity is not a weak penalty; it is a different system.
    if exp.get("amine_a") and cand.get("amine_a") and str(exp["amine_a"]).lower() != str(cand["amine_a"]).lower():
        return math.inf
    if exp.get("amine_b") and cand.get("amine_b") and exp["amine_b"] != cand["amine_b"]:
        score += 20
    for key in ("wt_a", "wt_b", "water_wt"):
        e, c = exp.get(key), cand.get(key)
        if e is None:
            continue
        score += 10 if c is None else min(abs(float(e) - float(c)) / 0.2, 20)
    exp_metrics = {
        p.get("metric_name"): p.get("value")
        for p in sample.get("performance") or []
        if p.get("metric_name") and p.get("value") is not None
    }
    cand_metrics = cand.get("metrics") or {}
    for metric, value in exp_metrics.items():
        if metric not in cand_metrics:
            score += 5
        else:
            # Keep unit-scale errors matchable, then report them as outside tolerance.
            score += min(abs(float(value) - float(cand_metrics[metric])) / max(abs(float(value)), 1e-12), 1.0) * 2
    cond = sample.get("conditions") or {}
    for key, scale in (("temperature_K", 0.5), ("co2_vol_pct", 1.0),
                       ("co2_partial_kPa", 10.0), ("initial_loading", 0.05)):
        e, c = cond.get(key), cand.get(key)
        if e is None:
            continue
        score += 2 if c is None else min(abs(float(e) - float(c)) / scale, 10)
    return score


def recipe_state(cand: dict) -> str:
    rtype = cand.get("recipe_type")
    is_mono = rtype == "mono" or (rtype is None and cand.get("amine_b") is None)
    required = [cand.get("wt_a"), cand.get("water_wt")]
    if not is_mono:
        required.insert(1, cand.get("wt_b"))
    if not any(v is not None for v in required):
        return "missing"
    if any(v is None for v in required):
        return "partial"
    try:
        total = sum(float(v) for v in required)
    except (TypeError, ValueError):
        return "partial"
    return "complete" if abs(total - 100.0) <= 0.1 else "unclosed"


def summarize_candidate_meta(manifest: dict) -> dict:
    papers = manifest.get("papers") or []
    models = sorted({p.get("model") for p in papers if p.get("model")})
    prompts = sorted({p.get("prompt_sha256") for p in papers if p.get("prompt_sha256")})
    modules = sorted({tuple(p.get("modules") or []) for p in papers})
    return {
        "batch_id": manifest.get("batch_id"),
        "papers": len(papers),
        "models": models,
        "prompt_sha256": prompts,
        "module_sets": [list(x) for x in modules],
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--eval-set", default=str(ROOT / "evaluation" / "eval_set_v1.json"))
    ap.add_argument("--candidate", required=True, help="batch directory or JSONL file")
    ap.add_argument("--outdir", default=str(ROOT / "evaluation" / "reports"))
    ap.add_argument("--label", default="run")
    args = ap.parse_args()

    eval_set = json.loads(Path(args.eval_set).read_text(encoding="utf-8"))
    samples = eval_set.get("samples") or []
    candidate_path = (ROOT / args.candidate).resolve() if not Path(args.candidate).is_absolute() else Path(args.candidate)
    raw_candidates, rejected, manifest = load_candidates(candidate_path)
    candidates = [flatten(r) for r in raw_candidates]

    used: set[int] = set()
    matches: list[tuple[dict, dict, float]] = []
    unmatched: list[dict] = []
    for sample in samples:
        best_i, best_score = None, math.inf
        for i, cand in enumerate(candidates):
            if i in used:
                continue
            s = match_score(sample, cand)
            if s < best_score:
                best_i, best_score = i, s
        if best_i is not None and best_score <= 40:
            used.add(best_i)
            matches.append((sample, candidates[best_i], best_score))
        else:
            unmatched.append(sample)

    field_stats: dict[str, dict] = defaultdict(lambda: {"expected": 0, "present": 0, "within": 0, "outside": 0, "missing": 0})
    failures = []
    qc_outcomes = Counter()
    recipe_states = Counter()
    reason_counter = Counter()
    per_doi: dict[str, dict] = defaultdict(lambda: {"expected": 0, "matched": 0, "within": 0, "fields": 0})

    for sample, cand, score in matches:
        per_doi[sample["doi"]]["expected"] += 1
        per_doi[sample["doi"]]["matched"] += 1
        qc_outcomes[cand.get("qc_level") or "missing"] += 1
        recipe_states[recipe_state(cand)] += 1
        reason = cand.get("qc_reason") or ""
        for part in str(reason).split(";"):
            if part:
                reason_counter[part] += 1
        exp_fields = expected_fields(sample)
        cand_fields = candidate_fields(cand)
        missing_fields = []
        outside_fields = []
        for key, exp_val in exp_fields.items():
            if exp_val is None:
                continue
            st = field_stats[key]
            st["expected"] += 1
            per_doi[sample["doi"]]["fields"] += 1
            cand_val = cand_fields.get(key)
            if cand_val is None:
                st["missing"] += 1
                missing_fields.append(key)
                continue
            st["present"] += 1
            try:
                if abs(float(exp_val) - float(cand_val)) <= tolerance(key, float(exp_val)):
                    st["within"] += 1
                    per_doi[sample["doi"]]["within"] += 1
                else:
                    st["outside"] += 1
                    outside_fields.append(key)
            except (TypeError, ValueError):
                st["outside"] += 1
                outside_fields.append(key)
        if missing_fields or outside_fields:
            failures.append({
                "sample_id": sample["sample_id"],
                "doi": sample["doi"],
                "match_score": round(score, 3),
                "qc_level": cand.get("qc_level"),
                "missing_fields": missing_fields,
                "outside_tolerance": outside_fields,
            })

    for sample in unmatched:
        per_doi[sample["doi"]]["expected"] += 1
        qc_outcomes["no_match"] += 1
        failures.append({
            "sample_id": sample["sample_id"],
            "doi": sample["doi"],
            "match_score": None,
            "qc_level": None,
            "missing_fields": list(expected_fields(sample).keys()),
            "outside_tolerance": [],
        })

    for rec in rejected:
        reason = (rec.get("qc") or {}).get("qc_reason") or "unknown"
        for part in str(reason).split(";"):
            if part:
                reason_counter["rejected:" + part] += 1

    total_expected = sum(s["expected"] for s in field_stats.values())
    total_present = sum(s["present"] for s in field_stats.values())
    total_within = sum(s["within"] for s in field_stats.values())
    completeness = total_present / total_expected if total_expected else 0.0
    agreement = total_within / total_expected if total_expected else 0.0
    false_reject = sum(1 for s in samples if s["sample_id"] in {u["sample_id"] for u in unmatched}) + sum(
        1 for sample, cand, _ in matches if cand.get("qc_level") != "L2"
    )
    extra_candidates = [c for i, c in enumerate(candidates) if i not in used]

    result = {
        "label": args.label,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "eval_set": args.eval_set,
        "candidate": str(candidate_path),
        "label_caveat": eval_set.get("label_policy"),
        "candidate_meta": summarize_candidate_meta(manifest),
        "counts": {
            "expected_samples": len(samples),
            "matched": len(matches),
            "unmatched": len(unmatched),
            "candidate_records": len(candidates),
            "extra_candidate_records": len(extra_candidates),
            "rejected_records": len(rejected),
        },
        "field_completeness": {
            "overall": round(completeness, 4),
            "present": total_present,
            "expected": total_expected,
            "per_field": {
                k: {
                    **v,
                    "completeness": round(v["present"] / v["expected"], 4) if v["expected"] else None,
                    "agreement": round(v["within"] / v["expected"], 4) if v["expected"] else None,
                }
                for k, v in sorted(field_stats.items())
            },
        },
        "numeric_agreement": {
            "overall": round(agreement, 4),
            "within": total_within,
            "expected": total_expected,
        },
        "recipe_closure": dict(recipe_states),
        "qc_outcomes": dict(qc_outcomes),
        "false_reject_l2": false_reject,
        "false_accept_note": "The 38-record set contains only L2 positives; false-accept requires a negative eval set.",
        "rejection_reasons": dict(reason_counter.most_common()),
        "per_doi": {k: dict(v) for k, v in sorted(per_doi.items())},
        "failures": failures,
    }

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    json_path = outdir / f"{args.label}_{stamp}.json"
    md_path = outdir / f"{args.label}_{stamp}.md"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        f"# 回归评估报告：{args.label}",
        "",
        f"- 时间：{result['created_at']}",
        f"- 评估集：`{args.eval_set}`（{len(samples)} 条，{len({s['doi'] for s in samples})} 篇）",
        f"- 候选：`{candidate_path}`",
        f"- 标签说明：{result['label_caveat']}",
        f"- 模型：{', '.join(result['candidate_meta']['models']) or '未记录'}",
        f"- Prompt SHA-256：{', '.join(x[:16] for x in result['candidate_meta']['prompt_sha256']) or '未记录'}",
        "",
        "## 总览",
        "",
        "| 指标 | 值 |",
        "|---|---|",
        f"| 覆盖率 | {len(matches)}/{len(samples)} |",
        f"| 字段完整率 | {completeness:.1%} |",
        f"| 数值容忍内一致率 | {agreement:.1%} |",
        f"| 配方闭合 | {result['recipe_closure']} |",
        f"| QC 结果 | {result['qc_outcomes']} |",
        f"| L2 被错误降级/拒收 | {false_reject} |",
        f"| 候选多余记录 | {len(extra_candidates)} |",
        "",
        "## 分字段",
        "",
        "| 字段 | 应有 | 已填 | 完整率 | 容忍内 | 一致率 | 缺失 | 超差 |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for key, v in sorted(field_stats.items()):
        label = FIELD_LABELS.get(key, key)
        comp = f"{v['present'] / v['expected']:.1%}" if v["expected"] else "-"
        agr = f"{v['within'] / v['expected']:.1%}" if v["expected"] else "-"
        lines.append(f"| {label} | {v['expected']} | {v['present']} | {comp} | {v['within']} | {agr} | {v['missing']} | {v['outside']} |")
    lines += ["", "## 分论文", "", "| DOI | 应有 | 匹配 | 容忍内字段 | 字段数 |", "|---|---:|---:|---:|---:|"]
    for doi, v in sorted(per_doi.items()):
        lines.append(f"| {doi} | {v['expected']} | {v['matched']} | {v['within']} | {v['fields']} |")
    lines += ["", "## 失败样本", ""]
    if failures:
        for f in failures[:50]:
            lines.append(f"- `{f['sample_id']}` {f['doi']} qc={f['qc_level']} score={f['match_score']} missing={f['missing_fields']} outside={f['outside_tolerance']}")
    else:
        lines.append("- 无")
    lines += [
        "",
        "## 说明",
        "",
        "- 本报告的比较对象是历史 L2 导出（human_verified=false），不是独立人工复核结果。",
        "- 字段完整率只统计标准答案中非空字段；不能用推测值提高该指标。",
        "- 数值容忍按字段设置：温度 ±0.1 K、CO2 vol% ±0.5、压力 ±1%/±1 kPa、负载 ±0.01、wt% ±0.2，性能默认 ±2%。",
        "- 38 条全为 L2 正样本，因此 false_accept 需要额外的负样本集才能统计。",
        "- 候选多余记录未计入完整率，但可能表示过度抽取；需要结合论文边界人工复核。",
    ]
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({
        "report_json": str(json_path),
        "report_md": str(md_path),
        "coverage": f"{len(matches)}/{len(samples)}",
        "completeness": round(completeness, 4),
        "agreement": round(agreement, 4),
        "qc": dict(qc_outcomes),
        "false_reject_l2": false_reject,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
