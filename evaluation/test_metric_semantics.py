"""Metric semantic tests: heat of absorption must not be stored as regeneration heat."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from server.provenance import decide_qc, metric_semantics


def rec(metric, value, unit, definition=""):
    return {
        "recipe": {"additive_flag": 0, "salt_flag": 0, "phase_flag": 0},
        "test": {"test_origin": "literature"},
        "performance": [{"metric_name": metric, "value": value, "unit": unit, "metric_definition": definition}],
    }


CASES = [
    ("heat_of_absorption_mislabeled", rec("regeneration_heat", -85.13, "kJ/mol CO2", "Heat of CO2 absorption"), True),
    ("heat_of_absorption_positive", rec("regeneration_heat", 58.5, "kJ/mol-CO2", "heat of reaction"), True),
    ("correct_regeneration_heat", rec("regeneration_heat", 3.72, "GJ/t_CO2", "total regeneration heat"), False),
    ("correct_kj_per_kg", rec("regeneration_heat", 2400, "kJ/kg", "regeneration heat"), False),
    ("non_heat_metric", rec("equilibrium_loading", 0.5, "mol_CO2/mol_amine", ""), False),
]


def main() -> int:
    failed = 0
    for name, r, should_flag in CASES:
        reasons = metric_semantics(r)
        flagged = bool(reasons)
        ok = flagged == should_flag
        print(("PASS" if ok else "FAIL"), name, reasons)
        failed += 0 if ok else 1
    print(f"{len(CASES)-failed}/{len(CASES)} passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
