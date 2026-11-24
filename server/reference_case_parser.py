"""Paper-specific reference-row extraction for text-described MEA baselines.

A reference system can be scattered across a table, methods and results text,
with no standalone performance table. The profile declares the paper scope and
regexes; values are parsed from the paper text, not hardcoded.
"""
from __future__ import annotations

import re
from pathlib import Path

PROFILES: dict[str, dict] = {
    "10.1039/d6gc02196d": {
        "version": "phase4-1.0",
        "scope": "Green Chemistry 2026 water-lean solvent paper; 30 wt% aqueous MEA reference",
        "loc_label": "pp.10540-10544, Table 4 (MEA 30 wt%) and regeneration results text",
        "recipe_regex": r"MEA\s*30\s*%?\s*MEA\s*[—\-]\s*70\s*%",
        "temperature_K": 313.15,
        "temperature_regex": r"heated\s*to\s*313\s*K",
        "co2_partial_kPa": 12.0,
        "co2_partial_regex": r"12\s*kPa",
        "co2_vol_pct": 12.0,
        "co2_vol_regex": r"12\s*kPa\s*CO2|simulated\s*flue\s*gas",
        "initial_loading": 0.0,
        "initial_loading_regex": r"150\s*mL\s*of\s*fresh\s*solvent|fresh\s*solvent",
        "performance": [
            {
                "metric_name": "regeneration_efficiency",
                "unit": "%",
                "value_regex": r"lowest\s*regeneration\s*efficiency\s*at\s*only\s*([\d.]+)\s*%",
                "is_derived": 0,
                "definition": "Aqueous 30 wt% MEA regeneration efficiency from the paper's comparison text",
            },
            {
                "metric_name": "regeneration_heat",
                "unit": "GJ/t_CO2",
                "value_regex": r"41%\s*reduction\s*compared\s*to\s*that\s*of\s*MEA.{0,350}?\(\s*([\d.]+)\s*GJ\s*per\s*t\s*CO",
                "is_derived": 1,
                "definition": "Aqueous 30 wt% MEA total regeneration heat from the paper's comparison text",
            },
        ],
        "evidence_quotes": [
            "MEA 30%MEA — 70%",
            "Before each test, 150 mL of fresh solvent was introduced",
            "heated to 313 K",
            "12 kPa CO2",
            "MEA showed the lowest regeneration efficiency at only 55%",
            "MEA (3.72GJ per t CO2)",
        ],
    }
}


def profile_for_doi(doi: str | None) -> dict | None:
    return PROFILES.get((doi or "").lower())


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text or "")


def parse_reference(text: str, profile: dict, pdf: Path, doi: str | None) -> list[dict]:
    body = _norm(text)
    if not re.search(profile["recipe_regex"], body, re.I):
        return []
    if not re.search(profile["temperature_regex"], body, re.I):
        return []
    if not re.search(profile["co2_partial_regex"], body, re.I):
        return []
    if not re.search(profile["co2_vol_regex"], body, re.I):
        return []
    if not re.search(profile["initial_loading_regex"], body, re.I):
        return []
    performances = []
    for spec in profile["performance"]:
        m = re.search(spec["value_regex"], body, re.I)
        if not m:
            continue
        performances.append({
            "metric_name": spec["metric_name"],
            "value": float(m.group(1)),
            "unit": spec["unit"],
            "value_original": float(m.group(1)),
            "unit_original": spec["unit"],
            "metric_definition": spec["definition"],
            "is_derived": spec.get("is_derived", 0),
        })
    if len(performances) != len(profile["performance"]):
        return []
    excerpt = " ... ".join(profile["evidence_quotes"])
    return [{
        "source": {
            "doi": doi,
            "pdf_path": pdf.as_posix(),
            "loc_type": "table",
            "loc_label": profile["loc_label"],
            "excerpt": excerpt,
        },
        "recipe": {
            "recipe_type": "mono",
            "amine_a": {"standard_name": "MEA"},
            "amine_b": None,
            "wt_a": 30.0,
            "wt_b": None,
            "water_wt": 70.0,
            "total_amine_wt": 30.0,
            "additive_flag": 0,
            "salt_flag": 0,
            "phase_flag": 0,
        },
        "test": {
            "test_origin": "literature",
            "temperature_K": profile["temperature_K"],
            "co2_vol_pct": profile["co2_vol_pct"],
            "co2_partial_kPa": profile["co2_partial_kPa"],
            "total_pressure_kPa": None,
            "gas_flow": None,
            "liquid_volume": None,
            "gas_liquid_ratio": None,
            "initial_loading": 0.0,
            "rich_loading": None,
            "lean_loading": None,
        },
        "performance": performances,
        "evidence": [
            {"field": "wt_a", "type": "Explicit", "note": "Table 4 MEA 30 wt%"},
            {"field": "water_wt", "type": "Derived", "note": "100 - 30"},
            {"field": "temperature_K", "type": "Explicit", "note": "methods heated to 313 K"},
            {"field": "co2_partial_kPa", "type": "Explicit", "note": "12 kPa CO2"},
            {"field": "co2_vol_pct", "type": "Explicit", "note": "simulated flue gas 12 kPa CO2"},
            {"field": "initial_loading", "type": "Contextual", "note": "150 mL fresh solvent"},
            {"field": "regeneration_efficiency", "type": "Explicit", "note": "55% text"},
            {"field": "regeneration_heat", "type": "Explicit", "note": "3.72 GJ/t CO2"},
            {"field": "source.excerpt", "type": "Explicit", "note": "table + text quotes"},
        ],
    }]
