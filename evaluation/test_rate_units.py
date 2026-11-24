"""Rate-unit test cases for server.units.

Run:
  .venv\\Scripts\\python.exe evaluation\\test_rate_units.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from server.units import normalize_rate

CASES = [
    ("initial_absorption_rate", 34.0, "10-5 mol CO2/mol/s", "converted", 0.00034, "mol_CO2/(mol_amine*s)"),
    ("initial_desorption_rate", 13.0, "10-5 mol CO2/mol/s", "converted", 0.00013, "mol_CO2/(mol_amine*s)"),
    ("initial_absorption_rate", 27.0, "1e-5 mol CO2/(mol amine*s)", "converted", 0.00027, "mol_CO2/(mol_amine*s)"),
    ("initial_desorption_rate", 34.8, "10^-5 mol CO2/(mol amine*s)", "converted", 0.000348, "mol_CO2/(mol_amine*s)"),
    ("initial_absorption_rate", 13.7, "10−5 mol CO2/(mol⋅s)", "converted", 0.000137, "mol_CO2/(mol_amine*s)"),
    ("initial_desorption_rate", 32.5, "10-5 mol CO2/mol*s", "converted", 0.000325, "mol_CO2/(mol_amine*s)"),
    ("initial_absorption_rate", 1.0, "mmol CO2/(g amine*min)", "converted", 1.0 / 60.0, "mol_CO2/(kg_amine*s)"),
    ("initial_absorption_rate", 1.0, "umol CO2/(mol amine*min)", "converted", 1e-6 / 60.0, "mol_CO2/(mol_amine*s)"),
    ("initial_absorption_rate", 1.0, "mol CO2/(L solution*h)", "converted", 1.0 / 3600.0, "mol_CO2/(L_solution*s)"),
    ("initial_absorption_rate", 1.0, "mol CO2/(kg solution*s)", "converted", 1.0, "mol_CO2/(kg_solution*s)"),
    ("initial_absorption_rate", 1.0, "mol CO2/(m3 reactor*s)", "converted", 1.0, "mol_CO2/(m3*s)"),
    ("initial_absorption_rate", 1.0, "mol CO2/(mol solution*s)", "blocked", None, None),
    ("initial_absorption_rate", 1.56, "g-CO2/L-soln/min", "unparsed", None, None),
    ("initial_absorption_rate", 1.0, None, "missing_unit", None, None),
    ("equilibrium_loading", 0.5, "mol CO2/mol amine", "not_rate", None, None),
]


def main() -> int:
    failed = 0
    for metric, value, unit, expected_status, expected_value, expected_unit in CASES:
        r = normalize_rate(metric, value, unit)
        ok = r.get("status") == expected_status
        if ok and expected_value is not None:
            ok = math.isclose(float(r.get("value")), float(expected_value), rel_tol=1e-9, abs_tol=1e-15)
        if ok and expected_unit is not None:
            ok = r.get("unit") == expected_unit
        print(("PASS" if ok else "FAIL"), metric, value, repr(unit), "->", r)
        failed += 0 if ok else 1
    print(f"\n{len(CASES) - failed}/{len(CASES)} passed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
