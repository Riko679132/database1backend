"""Layered gas-phase / water-vapour consistency checks.

It never invents P_H2O for an amine solution. Pure-water saturation pressure is
available only with the documented NIST Antoine constants and temperature
range; a solution requires an explicit water activity (or a future verified
model), otherwise the check stays not assessable.
"""
from __future__ import annotations

import re

# NIST Chemistry WebBook, Antoine equation for water, 1-100 °C, mmHg:
# log10(P/mmHg) = 8.07131 - 1730.63 / (233.426 + T/°C)
# Converted to kPa with 1 mmHg = 0.133322387415 kPa.
ANTOINE = {
    "A": 8.07131,
    "B": 1730.63,
    "C": 233.426,
    "t_min_C": 1.0,
    "t_max_C": 100.0,
    "source": "NIST Chemistry WebBook, Antoine equation for water (1-100 C), https://webbook.nist.gov/cgi/cbook.cgi?ID=C7732185&Mask=4&Type=ANTOINE",
    "version": "nist-antoine-water-1-100c",
    "mmhg_to_kpa": 0.133322387415,
}


def _num(value) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    m = re.search(r"-?\d+(?:\.\d+)?", str(value))
    return float(m.group(0)) if m else None


def normalize_basis(value) -> str:
    text = str(value or "").strip().lower()
    if text in ("wet", "wet_basis", "wet-basis", "湿基"):
        return "wet"
    if text in ("dry", "dry_basis", "dry-basis", "干基"):
        return "dry"
    return "unknown"


def water_saturation_pressure_kpa(temperature_K: float | None) -> dict:
    """Pure-water saturation pressure with an explicit source and validity range."""
    if temperature_K is None:
        return {"status": "missing_temperature"}
    t_c = float(temperature_K) - 273.15
    if not (ANTOINE["t_min_C"] <= t_c <= ANTOINE["t_max_C"]):
        return {
            "status": "out_of_range",
            "temperature_C": t_c,
            "range_C": [ANTOINE["t_min_C"], ANTOINE["t_max_C"]],
            "source": ANTOINE["source"],
            "version": ANTOINE["version"],
        }
    log10_mmhg = ANTOINE["A"] - ANTOINE["B"] / (ANTOINE["C"] + t_c)
    p_kpa = (10.0 ** log10_mmhg) * ANTOINE["mmhg_to_kpa"]
    return {
        "status": "ok",
        "p_kPa": round(p_kpa, 6),
        "temperature_C": round(t_c, 4),
        "range_C": [ANTOINE["t_min_C"], ANTOINE["t_max_C"]],
        "source": ANTOINE["source"],
        "version": ANTOINE["version"],
        "note": "pure water only; not the water vapour pressure of an amine solution",
    }


def _check(name: str, status: str, detail: str = "") -> dict:
    return {"name": name, "status": status, "detail": detail}


def assess(
    test: dict,
    *,
    p_h2o_kPa: float | None = None,
    gas_basis: str | None = None,
    y_h2o: float | None = None,
    water_activity: float | None = None,
    other_partial_kPa: float | None = None,
) -> dict:
    """Assess gas-phase consistency and, only when justified, derive P_CO2."""
    p_total = _num(test.get("total_pressure_kPa"))
    p_co2 = _num(test.get("co2_partial_kPa"))
    y_co2 = _num(test.get("co2_vol_pct"))
    y_co2 = y_co2 / 100.0 if y_co2 is not None else None
    p_h2o = _num(p_h2o_kPa if p_h2o_kPa is not None else test.get("p_h2o_kPa"))
    y_h2o = _num(y_h2o if y_h2o is not None else test.get("y_h2o"))
    aw = _num(water_activity if water_activity is not None else test.get("water_activity"))
    other = _num(other_partial_kPa if other_partial_kPa is not None else test.get("other_partial_kPa"))
    basis = normalize_basis(gas_basis if gas_basis is not None else test.get("gas_basis"))
    temperature = _num(test.get("temperature_K"))

    notes: list[str] = []
    checks: list[dict] = []
    anomalies: list[dict] = []
    water_source = "missing"
    saturation = None

    if p_h2o is not None:
        water_source = "explicit_paper_value"
    elif y_h2o is not None and p_total is not None and basis == "wet":
        p_h2o = y_h2o * p_total
        water_source = "y_h2o_wet_times_total_pressure"
        notes.append("P_H2O derived from wet-basis water mole fraction and total pressure")
    elif aw is not None and temperature is not None:
        saturation = water_saturation_pressure_kpa(temperature)
        if saturation.get("status") == "ok" and 0.0 < aw <= 1.0:
            p_h2o = aw * saturation["p_kPa"]
            water_source = "water_activity_times_pure_water_saturation"
            notes.append("P_H2O = water_activity * pure-water saturation pressure")
        elif saturation.get("status") != "ok":
            notes.append(f"P_H2O not calculated: {saturation.get('status')}")
        else:
            notes.append("P_H2O not calculated: water_activity outside (0,1]")
    elif basis == "dry":
        notes.append("dry-basis gas composition without P_H2O; total pressure is not dry-gas pressure")
    else:
        notes.append("no water-vapour information; water check not assessable")

    derived = None
    derivation = "none"
    if p_co2 is None:
        if basis == "wet" and y_co2 is not None and p_total is not None:
            derived = y_co2 * p_total
            derivation = "wet_basis"
            notes.append("P_CO2 = y_CO2,wet * P_total")
        elif basis == "dry" and y_co2 is not None and p_total is not None and p_h2o is not None:
            dry_total = p_total - p_h2o
            derived = y_co2 * dry_total
            derivation = "dry_basis_with_p_h2o"
            notes.append("P_CO2 = y_CO2,dry * (P_total - P_H2O)")
        elif basis == "dry" and y_co2 is not None and p_total is not None:
            derivation = "blocked_dry_basis_missing_p_h2o"
            notes.append("P_CO2 not derived: dry basis but P_H2O is unknown")
        elif basis == "unknown" and y_co2 is not None and p_total is not None:
            derivation = "blocked_basis_unknown"
            notes.append("P_CO2 not derived: gas basis is unknown; total pressure cannot be assumed wet")
        else:
            derivation = "not_assessable_missing_inputs"
    else:
        derivation = "explicit_p_co2"

    p_co2_final = p_co2 if p_co2 is not None else derived
    if p_total is not None:
        checks.append(_check(
            "co2_le_total",
            "pass" if p_co2_final is not None and p_co2_final <= p_total + 1e-9 else
            ("not_assessable" if p_co2_final is None else "fail"),
            f"P_CO2={p_co2_final}, P_total={p_total}",
        ))
        if p_co2_final is not None and p_co2_final > p_total + 1e-9:
            anomalies.append({"code": "p_co2_exceeds_total", "detail": f"P_CO2={p_co2_final} > P_total={p_total}"})
    else:
        checks.append(_check("co2_le_total", "not_assessable", "P_total missing"))

    if p_h2o is not None and p_total is not None:
        water_ok = p_h2o <= p_total + 1e-9
        component_ok = p_co2_final is None or (p_co2_final + p_h2o <= p_total + 1e-9)
        checks.append(_check(
            "water_vapour_le_total",
            "pass" if water_ok else "fail",
            f"P_H2O={p_h2o}, P_total={p_total}",
        ))
        checks.append(_check(
            "component_sum_le_total",
            "pass" if component_ok else "fail",
            f"P_CO2+P_H2O={None if p_co2_final is None else round(p_co2_final + p_h2o, 6)}, P_total={p_total}",
        ))
        if not water_ok:
            anomalies.append({"code": "p_h2o_exceeds_total", "detail": f"P_H2O={p_h2o} > P_total={p_total}"})
        if not component_ok:
            anomalies.append({"code": "component_sum_exceeds_total",
                              "detail": f"P_CO2+P_H2O={p_co2_final + p_h2o} > P_total={p_total}"})
        water_check = "pass" if water_ok and component_ok else "fail"
    else:
        checks.append(_check("water_vapour_le_total", "not_assessable", "P_H2O or P_total missing"))
        checks.append(_check("component_sum_le_total", "not_assessable", "P_H2O or P_total missing"))
        water_check = "not_assessable"
        if derivation in ("blocked_dry_basis_missing_p_h2o", "blocked_basis_unknown"):
            water_check = "blocked"

    if y_co2 is not None and y_h2o is not None:
        checks.append(_check(
            "gas_fraction_sum",
            "pass" if y_co2 + y_h2o <= 1.01 else "fail",
            f"y_CO2+y_H2O={round(y_co2 + y_h2o, 6)}",
        ))
        if y_co2 + y_h2o > 1.01:
            anomalies.append({"code": "gas_fraction_sum_exceeds_one",
                              "detail": f"y_CO2+y_H2O={y_co2 + y_h2o}"})

    tol = 0.5
    if basis == "wet" and y_co2 is not None and p_total is not None and p_co2 is not None:
        expected = y_co2 * p_total
        if abs(p_co2 - expected) > max(tol, abs(expected) * 0.01):
            anomalies.append({"code": "partial_pressure_inconsistent_with_wet_fraction",
                              "detail": f"recorded={p_co2}, y_wet*P_total={round(expected, 6)}"})
    if basis == "dry" and y_co2 is not None and p_total is not None and p_h2o is not None and p_co2 is not None:
        expected = y_co2 * (p_total - p_h2o)
        if abs(p_co2 - expected) > max(tol, abs(expected) * 0.01):
            anomalies.append({"code": "partial_pressure_inconsistent_with_dry_fraction",
                              "detail": f"recorded={p_co2}, y_dry*(P_total-P_H2O)={round(expected, 6)}"})

    if anomalies:
        status = "anomaly"
    elif derivation in ("blocked_dry_basis_missing_p_h2o", "blocked_basis_unknown"):
        status = derivation
    elif p_co2_final is None:
        status = "not_assessable"
    elif derivation in ("wet_basis", "dry_basis_with_p_h2o"):
        status = f"derived_{derivation}"
    else:
        status = "assessed"

    return {
        "status": status,
        "derivation": derivation,
        "basis": basis,
        "inputs": {
            "total_pressure_kPa": p_total,
            "co2_vol_pct": _num(test.get("co2_vol_pct")),
            "p_co2_kPa": p_co2,
            "p_h2o_kPa": p_h2o,
            "y_h2o": y_h2o,
            "water_activity": aw,
            "other_partial_kPa": other,
            "temperature_K": temperature,
        },
        "p_co2_kPa": p_co2_final,
        "derived_co2_partial_kPa": derived,
        "p_h2o_kPa": p_h2o,
        "p_h2o_source": water_source,
        "saturation": saturation,
        "water_vapour_check": water_check,
        "checks": checks,
        "anomalies": anomalies,
        "notes": notes,
    }


def apply_to_test(test: dict) -> dict:
    """Fill a missing P_CO2 only when the declared basis justifies it."""
    result = assess(test)
    derived = result.get("derived_co2_partial_kPa")
    if test.get("co2_partial_kPa") is None and derived is not None:
        test["co2_partial_kPa"] = round(float(derived), 6)
        result["applied_to_test"] = True
    else:
        result["applied_to_test"] = False
    return result
