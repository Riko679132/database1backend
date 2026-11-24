"""Paper-specific condition profiles.

Only fills a condition when the paper text contains the declared evidence and
the value is otherwise missing. It never guesses a pressure from convention.
"""
from __future__ import annotations

import re

PROFILES: dict[str, dict] = {
    "10.1021/ie400825u": {
        "version": "phase4-1.0",
        "scope": "Chowdhury et al. 2013 gas scrubbing test",
        "total_pressure_kPa": 101.325,
        "co2_vol_pct": 20.0,
        "temperature_K": 313.15,
        "temperature_regex": r"40\s*°?C",
        "initial_loading": 0.0,
        "initial_loading_regex": r"50\s*mL.*aqueous|gas\s*scrubbing\s*bottle\s*was\s*filled",
        "evidence": [
            r"atmospheric\s*pressure",
            r"20%\s*CO",
        ],
    }
}


def profile_for_doi(doi: str | None) -> dict | None:
    return PROFILES.get((doi or "").lower())


def apply_to_raw(raw: dict, text: str, profile: dict) -> dict | None:
    body = re.sub(r"\s+", " ", text or "")
    for phrase in profile["evidence"]:
        if not re.search(phrase, body, re.I):
            return None
    for field, regex_key in (
        ("temperature_K", "temperature_regex"),
        ("initial_loading", "initial_loading_regex"),
    ):
        if profile.get(regex_key) and not re.search(profile[regex_key], body, re.I):
            return None
    test = raw.setdefault("test", {})
    changed = []
    evidence = raw.setdefault("evidence", [])
    for field, value, etype, note in (
        ("total_pressure_kPa", profile["total_pressure_kPa"], "Explicit", "method: atmospheric pressure"),
        ("co2_vol_pct", profile["co2_vol_pct"], "Explicit", "method: 20% CO2 / 80% N2"),
        ("temperature_K", profile.get("temperature_K"), "Explicit", "method: 40 C water bath"),
        ("initial_loading", profile.get("initial_loading"), "Contextual", "fresh 50 mL solution at start"),
    ):
        if value is None:
            continue
        if test.get(field) is None:
            test[field] = value
            changed.append(field)
        if isinstance(evidence, list):
            evidence.append({"field": field, "type": etype, "note": note})
    return {"changed": changed, "profile": profile}
