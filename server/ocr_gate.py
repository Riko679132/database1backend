"""OCR quality gate: confidence, critical scientific fields and native-text conflicts.

The gate does not replace OCR or human review. It only separates:
    pass   the page is usable as-is
    review a human/again-OCR check is required
    fail   the OCR text is not trustworthy; B must stop
"""
from __future__ import annotations

import re

NUM = r"(\d+(?:\.\d+)?)"
TEMP_RE = re.compile(rf"(?<![\d.]){NUM}\s*(°\s*C|◦\s*C|oC|C|K)(?!\w)", re.I)
PRESS_RE = re.compile(rf"{NUM}\s*(kPa|bar|MPa|atm)(?!\w)", re.I)
CONC_RE = re.compile(rf"{NUM}\s*(wt\.?\s*%|mass\s*%|mol\s*/\s*L|M)(?!\w)", re.I)
LOAD_RE = re.compile(rf"(?:loading|α|CO2\s*loading)[^0-9]{{0,24}}{NUM}", re.I)
SCALE_RE = re.compile(rf"{NUM}\s*(?:[x×*]\s*)?10\s*[-−^]?\s*(\d+)", re.I)
FORMULAS = ("MEA", "PZ", "AMP", "MDEA", "DEA", "TEA", "DGA", "CO2", "H2O")


def _clean(text: str) -> str:
    return (
        (text or "")
        .replace("\u200b", " ")
        .replace("−", "-")
        .replace("–", "-")
        .replace("×", "x")
        .replace("◦", "°")
    )


def _temp_k(num: str, unit: str) -> float:
    value = float(num)
    return value + 273.15 if "c" in unit.lower() else value


def _press_kpa(num: str, unit: str) -> float:
    value = float(num)
    unit = unit.lower()
    if unit == "bar":
        return value * 100.0
    if unit == "mpa":
        return value * 1000.0
    if unit == "atm":
        return value * 101.325
    return value


def critical_values(text: str) -> dict[str, set[str]]:
    body = _clean(text)
    out: dict[str, set[str]] = {}
    temps = {f"{_temp_k(n, u):.2f}K" for n, u in TEMP_RE.findall(body)}
    press = {f"{_press_kpa(n, u):.3f}kPa" for n, u in PRESS_RE.findall(body)}
    conc = set()
    for n, u in CONC_RE.findall(body):
        unit = re.sub(r"\s+", "", u.lower())
        conc.add(f"{float(n):.4g}{unit}")
    loads = {f"{float(n):.4g}" for n in LOAD_RE.findall(body)}
    scales = {f"{float(n):.4g}e-{int(e)}" for n, e in SCALE_RE.findall(body)}
    formulas = {name.upper() for name in FORMULAS if re.search(rf"\b{name}\b", body, re.I)}
    for key, value in (
        ("temperature", temps), ("pressure", press), ("concentration", conc),
        ("loading", loads), ("rate_scale", scales), ("formula", formulas),
    ):
        if value:
            out[key] = value
    return out


def conflicts(native: dict[str, set[str]], ocr: dict[str, set[str]]) -> list[dict]:
    out = []
    for key in sorted(set(native) & set(ocr)):
        if native[key] and ocr[key] and native[key].isdisjoint(ocr[key]):
            out.append({
                "field": key,
                "native": sorted(native[key])[:8],
                "ocr": sorted(ocr[key])[:8],
            })
    return out


def assess(
    native_text: str,
    ocr_text: str,
    confidences: list[float] | None,
    *,
    page: int | None = None,
    errors: list[str] | None = None,
) -> dict:
    conf = [float(c) for c in (confidences or []) if isinstance(c, (int, float))]
    avg = round(sum(conf) / len(conf), 4) if conf else None
    low = sum(1 for c in conf if c < 0.6)
    low_ratio = round(low / len(conf), 4) if conf else None
    native = critical_values(native_text)
    ocr = critical_values(ocr_text)
    conflict_rows = conflicts(native, ocr)
    missing = sorted(k for k in native if k not in ocr)
    reasons = []
    decision = "pass"
    if errors:
        reasons.append("ocr_error")
        decision = "review"
    if not (ocr_text or "").strip():
        reasons.append("empty_ocr_text")
        if not errors:
            decision = "fail"
    if avg is None:
        reasons.append("missing_confidence")
        if decision == "pass":
            decision = "review"
    else:
        if avg < 0.35:
            reasons.append(f"avg_confidence_{avg:.2f}")
            decision = "fail"
        elif avg < 0.55:
            reasons.append(f"low_avg_confidence_{avg:.2f}")
            if decision == "pass":
                decision = "review"
    if low_ratio is not None and low_ratio > 0.25:
        reasons.append(f"low_confidence_ratio_{low_ratio:.2f}")
        if decision == "pass":
            decision = "review"
    if conflict_rows:
        reasons.append(f"critical_field_conflicts_{len(conflict_rows)}")
        if len(conflict_rows) >= 2 and avg is not None and avg < 0.55:
            decision = "fail"
        elif decision == "pass":
            decision = "review"
    if missing:
        reasons.append("critical_fields_missing_in_ocr:" + ",".join(missing))
        if decision == "pass":
            decision = "review"
    return {
        "page": page,
        "decision": decision,
        "avg_confidence": avg,
        "low_confidence_items": low,
        "low_confidence_ratio": low_ratio,
        "critical_native": {k: sorted(v)[:8] for k, v in native.items()},
        "critical_ocr": {k: sorted(v)[:8] for k, v in ocr.items()},
        "conflicts": conflict_rows,
        "missing_critical": missing,
        "reasons": reasons,
    }


def summarize(ocr_meta: dict | None) -> dict:
    if not ocr_meta:
        return {"decision": "not_used", "reasons": []}
    quality = ocr_meta.get("quality")
    if not isinstance(quality, dict):
        pages = ocr_meta.get("pages") or []
        if not pages:
            return {"decision": "not_used", "reasons": []}
        return {
            "decision": "review",
            "reasons": ["legacy_ocr_report_without_quality_gate"],
            "pages": pages,
        }
    pages = quality.get("pages") or []
    decisions = [p.get("decision") for p in pages]
    if "fail" in decisions:
        decision = "fail"
    elif "review" in decisions:
        decision = "review"
    elif decisions:
        decision = "pass"
    else:
        decision = "not_used"
    reasons = []
    for p in pages:
        for r in p.get("reasons") or []:
            if r not in reasons:
                reasons.append(r)
    return {
        "decision": decision,
        "reasons": reasons,
        "pages": [p.get("page") for p in pages],
        "pages_review": sum(1 for d in decisions if d == "review"),
        "pages_fail": sum(1 for d in decisions if d == "fail"),
        "critical_conflicts": sum(len(p.get("conflicts") or []) for p in pages),
        "avg_confidence": quality.get("avg_confidence"),
        "tool": quality.get("tool"),
    }
