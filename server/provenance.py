"""Snapshot and evidence provenance for LLM extraction.

Every extraction attempt gets an immutable JSON snapshot containing the paper
identity, prompt/model/knowledge versions, raw model output, evidence types,
machine verification and the resulting QC decision. The snapshot is a file,
not a database change.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

EVIDENCE_TYPES = {"Explicit", "Contextual", "Derived", "External", "Assumed", "Unknown"}
REQUIRED_FIELDS = ("temperature_K", "co2_vol_pct", "initial_loading")
ALLOWED_REQUIRED_EVIDENCE = {"Explicit", "Contextual", "Derived"}


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def _norm(text: str) -> str:
    text = (text or "").lower()
    text = text.replace("−", "-").replace("–", "-").replace("—", "-")
    text = re.sub(r"[^0-9a-z.]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_text(text: str) -> str:
    return _norm(text)


def _num_tokens(value: float) -> set[str]:
    out = set()
    for fmt in ("{:.0f}", "{:.1f}", "{:.2f}", "{:.3f}", "{:.4f}", "{:g}"):
        try:
            out.add(fmt.format(value))
        except (ValueError, TypeError):
            pass
    return {x for x in out if x}


def _present_in_text(token: str, norm_text: str) -> bool:
    return re.search(rf"(?<![\d.]){re.escape(token)}(?![\d.])", norm_text) is not None


def _excerpt_match(excerpt: str, norm_text: str) -> bool:
    ex = _norm(excerpt)
    if len(ex) < 20:
        return False
    if ex in norm_text:
        return True
    words = ex.split()
    if len(words) < 5:
        return False
    shingles = {" ".join(words[i:i + 5]) for i in range(len(words) - 4)}
    if not shingles:
        return False
    hits = sum(1 for s in shingles if s in norm_text)
    return hits / len(shingles) >= 0.75


def _table_row_excerpt_ok(source: dict, excerpt: str, norm_text: str) -> bool:
    """Table captions + row labels are often not contiguous in extracted text."""
    if str(source.get("loc_type") or "") != "table" or not source.get("loc_label"):
        return False
    if len(excerpt.strip()) < 8:
        return False
    nums = re.findall(r"\d+(?:\.\d+)?", excerpt)
    if not nums:
        return False
    return all(_present_in_text(n, norm_text) for n in nums[:6])


def _value_evidence(raw: dict) -> dict[str, str]:
    """Read the model's evidence hints, if present."""
    ev = raw.get("evidence")
    out: dict[str, str] = {}
    if isinstance(ev, dict):
        for k, v in ev.items():
            t = str(v).strip().capitalize()
            if t in EVIDENCE_TYPES:
                out[str(k)] = t
    elif isinstance(ev, list):
        for item in ev:
            if isinstance(item, dict):
                field = str(item.get("field") or "").strip()
                t = str(item.get("type") or "").strip().capitalize()
                if field and t in EVIDENCE_TYPES:
                    out[field] = t
    return out


def classify_evidence(raw: dict, normalized: dict, norm_text: str) -> dict[str, str]:
    """Prefer model evidence; fill gaps with text-match heuristics."""
    hints = _value_evidence(raw)
    out: dict[str, str] = {}
    test = normalized.get("test") or {}
    recipe = normalized.get("recipe") or {}
    for field in (*REQUIRED_FIELDS, "co2_partial_kPa", "total_pressure_kPa", "rich_loading", "lean_loading"):
        value = test.get(field)
        if value is None:
            continue
        out[field] = hints.get(field) or ("Explicit" if any(_present_in_text(t, norm_text) for t in _num_tokens(float(value))) else "Unknown")
    for field in ("wt_a", "wt_b", "water_wt", "total_amine_wt"):
        value = recipe.get(field)
        if value is None:
            continue
        out[field] = hints.get(field) or ("Explicit" if any(_present_in_text(t, norm_text) for t in _num_tokens(float(value))) else "Unknown")
    for perf in normalized.get("performance") or []:
        value = perf.get("value")
        metric = str(perf.get("metric_name") or "")
        if value is None or not metric:
            continue
        out[f"performance.{metric}"] = hints.get(f"performance.{metric}") or (
            "Explicit" if any(_present_in_text(t, norm_text) for t in _num_tokens(float(value))) else "Unknown"
        )
    if raw.get("source", {}).get("excerpt"):
        src = raw["source"]
        excerpt = str(src.get("excerpt") or "")
        ok = _excerpt_match(excerpt, norm_text) or _table_row_excerpt_ok(src, excerpt, norm_text)
        out["source.excerpt"] = hints.get("source.excerpt") or ("Explicit" if ok else "Unknown")
    return out


def verify_record(raw: dict, normalized: dict, norm_text: str) -> dict:
    source = raw.get("source") or normalized.get("source") or {}
    excerpt = str(source.get("excerpt") or "")
    excerpt_ok = _excerpt_match(excerpt, norm_text)
    table_row_excerpt = False
    if not excerpt_ok:
        table_row_excerpt = _table_row_excerpt_ok(source, excerpt, norm_text)
        excerpt_ok = table_row_excerpt
    evidence = classify_evidence(raw, normalized, norm_text)

    missing_required = [f for f in REQUIRED_FIELDS if (normalized.get("test") or {}).get(f) is None]
    recipe = normalized.get("recipe") or {}
    wt_a = recipe.get("wt_a") or 0
    wt_b = recipe.get("wt_b") or 0
    water = recipe.get("water_wt") or 0
    recipe_closed = abs(wt_a + wt_b + water - 100.0) <= 0.1
    has_performance = bool(normalized.get("performance"))

    numeric_values: list[float] = []
    test = normalized.get("test") or {}
    for f in ("temperature_K", "co2_vol_pct", "co2_partial_kPa", "total_pressure_kPa",
              "initial_loading", "rich_loading", "lean_loading"):
        if test.get(f) is not None:
            numeric_values.append(float(test[f]))
    for f in ("wt_a", "wt_b", "water_wt", "total_amine_wt"):
        if recipe.get(f) is not None:
            numeric_values.append(float(recipe[f]))
    for perf in normalized.get("performance") or []:
        if perf.get("value") is not None:
            numeric_values.append(float(perf["value"]))
    matched = sum(
        1 for v in numeric_values
        if any(_present_in_text(t, norm_text) for t in _num_tokens(v))
    )
    ratio = matched / len(numeric_values) if numeric_values else 0.0
    required_evidence_ok = all(
        evidence.get(f, "Unknown") in ALLOWED_REQUIRED_EVIDENCE for f in REQUIRED_FIELDS
    )
    verified = (
        excerpt_ok
        and not missing_required
        and recipe_closed
        and has_performance
        and ratio >= 0.5
        and required_evidence_ok
    )
    reasons: list[str] = []
    if not excerpt_ok:
        reasons.append("excerpt_not_verbatim_in_text")
    if missing_required:
        reasons.extend(f"missing_{f}" for f in missing_required)
    if not recipe_closed:
        reasons.append("recipe_not_closed")
    if not has_performance:
        reasons.append("no_performance")
    if ratio < 0.5:
        reasons.append(f"numeric_match_ratio_{ratio:.2f}")
    if not required_evidence_ok:
        reasons.append("required_evidence_unknown_or_assumed")
    return {
        "excerpt_match": excerpt_ok,
        "table_row_excerpt": table_row_excerpt,
        "numeric_match_ratio": round(ratio, 4),
        "missing_required": missing_required,
        "recipe_closed": recipe_closed,
        "has_performance": has_performance,
        "required_evidence_ok": required_evidence_ok,
        "verified": verified,
        "reasons": reasons,
        "evidence": evidence,
    }


def metric_semantics(normalized: dict) -> list[str]:
    """Catch metric labels whose definition contradicts units/sign/description."""
    reasons = []
    for perf in normalized.get("performance") or []:
        metric = str(perf.get("metric_name") or "")
        unit = str(perf.get("unit") or "").lower().replace("_", " ")
        definition = str(perf.get("metric_definition") or "").lower()
        value = perf.get("value")
        if metric == "regeneration_heat":
            if "kj/mol" in unit or "kj mole" in unit or (value is not None and float(value) < 0):
                reasons.append("metric_definition_mismatch_regeneration_heat_is_heat_of_absorption")
            elif not any(x in unit for x in ("gj/t", "kj/kg", "mj/t")):
                reasons.append("regeneration_heat_unit_not_mass_basis")
            elif "absorption" in definition or "reaction" in definition:
                reasons.append("regeneration_heat_definition_says_absorption_or_reaction")
    return list(dict.fromkeys(reasons))


def decide_qc(normalized: dict, verification: dict) -> tuple[str, str]:
    test = normalized.get("test") or {}
    recipe = normalized.get("recipe") or {}
    origin = str(test.get("test_origin") or "literature")
    if origin == "simulation":
        return "L3", "simulation_data;llm_snapshot"
    if recipe.get("additive_flag") or recipe.get("salt_flag") or recipe.get("phase_flag"):
        return "L3", "excluded_system_pending_validation;llm_snapshot"
    semantic = metric_semantics(normalized)
    if semantic:
        return "L3", ";".join(["metric_semantics_downgrade", *semantic])
    if verification.get("verified"):
        evidence = verification.get("evidence") or {}
        tags = ";".join(
            f"{k}:{v}" for k, v in evidence.items()
            if k in REQUIRED_FIELDS and v in ALLOWED_REQUIRED_EVIDENCE
        )
        reason = "llm_snapshot_machine_verified;human_audit_pending"
        if tags:
            reason += ";" + tags
        return "L2", reason
    reasons = ["llm_snapshot_unverified", *verification.get("reasons", [])]
    return "L3", ";".join(dict.fromkeys(reasons))


def make_snapshot_payload(
    *,
    batch_id: str,
    pdf: Path,
    pdf_hash: str,
    parsed_text_path: Path | None,
    parsed_text_hash: str,
    raw_records: list[dict],
    normalized_records: list[dict],
    modules: list[dict],
    skill_meta: dict,
    prompt_meta: dict,
    model_info: dict,
    model_params: dict,
    parse_mode: str,
    ocr_meta: dict | None,
    si_meta: dict | None,
    chart_meta: dict | None,
    raw_output: str,
    status: str,
    table_meta: dict | None = None,
    verifications: list[dict] | None = None,
    reasonings: list[dict] | None = None,
    skipped: list[dict] | None = None,
    error: str | None = None,
    manifest: dict | None = None,
) -> dict:
    per_record = []
    for idx, rec in enumerate(normalized_records):
        v = (verifications or [])[idx] if verifications and idx < len(verifications) else {}
        r = (reasonings or [])[idx] if reasonings and idx < len(reasonings) else None
        per_record.append({
            "raw_record": (raw_records[idx] if idx < len(raw_records) else None),
            "record": rec,
            "verification": v,
            "qc": rec.get("qc"),
            "reasoning": r,
        })
    doi = ""
    if raw_records:
        doi = str((raw_records[0].get("source") or {}).get("doi") or "")
    paper_id = (manifest or {}).get("paper_id") or f"pdf:{pdf_hash[:16]}"
    return {
        "snapshot_version": "phase5-1.0",
        "task_id": f"{batch_id}:{pdf.stem}:{pdf_hash[:8]}",
        "batch_id": batch_id,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "status": status,
        "error": error,
        "paper": {
            "paper_id": paper_id,
            "doi": doi,
            "pdf_path": pdf.as_posix(),
            "pdf_sha256": pdf_hash,
            "manifest_version": (manifest or {}).get("manifest_version"),
            "manifest_sha256": (
                hashlib.sha256(json.dumps(manifest, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
                if manifest else None
            ),
        },
        "manifest": manifest,
        "parsed_text": {
            "path": parsed_text_path.as_posix() if parsed_text_path else None,
            "sha256": parsed_text_hash,
        },
        "prompt": prompt_meta,
        "skill": skill_meta,
        "knowledge_modules": modules,
        "model": model_info,
        "model_params": model_params,
        "pdf_parse": {
            "mode": parse_mode,
            "ocr": ocr_meta or {"status": "not_used"},
        },
        "supplementary_information": si_meta or {"status": "not_checked"},
        "chart_digitization": chart_meta or {"status": "not_used"},
        "table_grid": table_meta or {"status": "not_used"},
        "raw_model_output": raw_output,
        "records": per_record,
        "skipped": skipped or [],
        "human_verified": False,
        "note": "LLM extraction snapshot; machine-verified does not equal human verification.",
    }


def write_snapshot(batch_dir: Path, payload: dict, pdf_stem: str) -> tuple[Path, str]:
    raw_dir = batch_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    path = raw_dir / f"llm_{pdf_stem}_{stamp}.json"
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    data = text.encode("utf-8")
    # Write bytes so Windows does not translate \n to \r\n; the hash must match the file.
    path.write_bytes(data)
    return path, hashlib.sha256(data).hexdigest()


def apply_qc(record: dict, verification: dict, snapshot_path: Path, snapshot_hash: str) -> dict:
    level, reason = decide_qc(record, verification)
    record.setdefault("test", {})["raw_data_path"] = snapshot_path.as_posix()
    record["test"]["raw_data_hash"] = snapshot_hash
    record["qc"] = {"qc_level": level, "qc_reason": reason}
    return record
