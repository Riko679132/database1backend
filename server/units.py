"""Deterministic rate-unit semantics and conversion.

The LLM may correctly copy a paper value and its unit, e.g. 34.0 in
`10-5 mol CO2/(mol amine*s)`, but the database needs 0.00034 in
`mol_CO2/(mol_amine*s)`. This module parses scale prefixes, numerator,
denominator basis and time unit, and applies the conversion only when the
basis is convertible without extra data.
"""
from __future__ import annotations

import re

RATE_METRICS = {
    "initial_absorption_rate",
    "initial_desorption_rate",
    "absorption_rate_volumetric",
    "absorption_amount_volumetric",
}

TIME_TO_S = {"s": 1.0, "sec": 1.0, "secs": 1.0, "min": 60.0, "mins": 60.0, "h": 3600.0, "hr": 3600.0, "hrs": 3600.0}


def _clean(text: str) -> str:
    return (
        (text or "")
        .replace("\u200b", "")
        .replace("−", "-")
        .replace("–", "-")
        .replace("×", "x")
        .replace("·", "*")
        .replace("⋅", "*")
        .replace("³", "3")
        .replace("μ", "u")
    )


def parse_scale(unit: str) -> tuple[float, str]:
    """Return (scale, unit_without_scale)."""
    u = _clean(unit)
    m = re.search(r"(?:([\d.]+)\s*)?x\s*10\s*\^?\s*([-+]?\d+)", u, re.I)
    if m:
        factor = float(m.group(1) or 1.0) * (10.0 ** int(m.group(2)))
        return factor, (u[:m.start()] + " " + u[m.end():])
    m = re.search(r"\b10\s*\^?\s*([-+]?\d+)", u)
    if m:
        return 10.0 ** int(m.group(1)), (u[:m.start()] + " " + u[m.end():])
    m = re.search(r"\b1e([-+]?\d+)\b", u, re.I)
    if m:
        return 10.0 ** int(m.group(1)), (u[:m.start()] + " " + u[m.end():])
    if re.search(r"\bmmol\b", u, re.I):
        return 1e-3, re.sub(r"\bmmol\b", "mol", u, flags=re.I)
    if re.search(r"\bumol\b", u, re.I):
        return 1e-6, re.sub(r"\bumol\b", "mol", u, flags=re.I)
    return 1.0, u


def _basis(denominator: str) -> str:
    d = re.sub(r"[()]", " ", denominator.lower())
    d = re.sub(r"\s+", " ", d).strip()
    if "mol solution" in d or "mol_solution" in d:
        return "mol_solution"
    if "kg solution" in d or "kg_solution" in d or "kg soln" in d:
        return "kg_solution"
    if "kg amine" in d or "kg_amine" in d:
        return "kg_amine"
    if "g amine" in d or "g_amine" in d:
        return "g_amine"
    if "l solution" in d or "l_solution" in d or "liter solution" in d or "litre solution" in d:
        return "L_solution"
    if re.search(r"\bm\s*3\b", d) or "m3" in d:
        return "m3"
    if re.search(r"\bmol\b", d):
        # In a rate unit "mol CO2 / (mol*s)" the denominator mol is amine.
        return "mol_amine"
    return "unknown"


def _time_unit(denominator: str) -> str | None:
    d = _clean(denominator).lower()
    for token in ("min", "hr", "sec", "h", "s"):
        if re.search(rf"\b{token}s?\b", d):
            return "s" if token in ("sec", "s") else ("min" if token == "min" else "h")
    return None


def normalize_rate(metric_name: str, value: float | None, unit: str | None) -> dict:
    if metric_name not in RATE_METRICS:
        return {"status": "not_rate"}
    if value is None:
        return {"status": "missing_value"}
    if not unit:
        return {"status": "missing_unit"}
    scale, rest = parse_scale(unit)
    parts = re.split(r"[/]", rest)
    if len(parts) < 2:
        return {"status": "unparsed", "reason": "no denominator", "unit": unit}
    numerator = parts[0]
    denominator = "/".join(parts[1:])
    if "mol" not in numerator.lower():
        return {"status": "unparsed", "reason": "numerator is not a molar amount", "unit": unit}
    basis = _basis(denominator)
    time = _time_unit(denominator)
    if time is None:
        return {"status": "blocked", "reason": "time unit not recognized", "unit": unit, "scale": scale, "basis": basis}
    if basis == "unknown" or basis in ("mol_solution",):
        return {
            "status": "blocked",
            "reason": f"basis {basis} needs concentration/density or is not amine-basis",
            "unit": unit,
            "scale": scale,
            "basis": basis,
        }
    time_s = TIME_TO_S[time]
    if basis == "mol_amine":
        factor = scale / time_s
        canonical = "mol_CO2/(mol_amine*s)"
    elif basis == "kg_amine":
        factor = scale / time_s
        canonical = "mol_CO2/(kg_amine*s)"
    elif basis == "g_amine":
        factor = scale * 1000.0 / time_s
        canonical = "mol_CO2/(kg_amine*s)"
    elif basis == "kg_solution":
        factor = scale / time_s
        canonical = "mol_CO2/(kg_solution*s)"
    elif basis == "L_solution":
        factor = scale / time_s
        canonical = "mol_CO2/(L_solution*s)"
    elif basis == "m3":
        factor = scale / time_s
        canonical = "mol_CO2/(m3*s)"
    else:
        return {"status": "blocked", "reason": f"unknown basis {basis}", "unit": unit}
    return {
        "status": "converted",
        "value": float(value) * factor,
        "unit": canonical,
        "original_value": float(value),
        "original_unit": unit,
        "scale": scale,
        "time_unit": time,
        "basis": basis,
        "factor": factor,
        "formula": f"value_std = {value} * {factor:g}",
    }


def apply_to_performance(perf: dict) -> dict:
    """Normalize one performance dict in place and return the conversion record."""
    metric = str(perf.get("metric_name") or "")
    if metric not in RATE_METRICS:
        return {"status": "not_rate"}
    original_unit = perf.get("unit_original") or perf.get("unit")
    original_value = perf.get("value_original")
    if original_value is None:
        original_value = perf.get("value")
    result = normalize_rate(metric, original_value, original_unit)
    perf["unit_normalization"] = result
    if result.get("status") == "converted":
        perf["value_original"] = original_value
        perf["unit_original"] = original_unit
        perf["value"] = round(float(result["value"]), 12)
        perf["unit"] = result["unit"]
        note = f"unit normalized {original_unit} -> {result['unit']} (factor {result['factor']:g})"
        perf["metric_definition"] = (perf.get("metric_definition") or "") + f" [{note}]"
    elif result.get("status") in ("blocked", "unparsed", "missing_unit"):
        note = f"unit normalization {result.get('status')}: {result.get('reason', result.get('unit', ''))}"
        perf["metric_definition"] = (perf.get("metric_definition") or "") + f" [{note}]"
    return result
