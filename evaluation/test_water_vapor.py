"""Water-vapour / dry-wet basis checks on the real B normalization path."""
from __future__ import annotations

import json
import sqlite3
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from server import extract, gas_phase, reasoning  # noqa: E402

REPORT = ROOT / "evaluation" / "reports" / "water_vapor_test.md"
PDF = ROOT / "data/raw_pdfs/10.1021_je00005a025_0770ae31.pdf"


def raw_record(test_overrides: dict) -> dict:
    test = {
        "test_origin": "literature",
        "temperature_K": 313.15,
        "co2_vol_pct": 15.0,
        "co2_partial_kPa": 15.0,
        "total_pressure_kPa": 101.325,
        "gas_basis": "wet",
        "initial_loading": 0.0,
        **test_overrides,
    }
    return {
        "source": {
            "doi": "10.1021/je00005a025",
            "loc_type": "table",
            "loc_label": "test fixture",
            "excerpt": "Table fixture row for gas-phase validation",
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
        "test": test,
        "performance": [{
            "metric_name": "equilibrium_loading",
            "value": 0.5,
            "unit": "mol CO2/mol amine",
            "value_original": 0.5,
            "unit_original": "mol CO2/mol amine",
            "is_derived": 0,
        }],
        "evidence": [
            {"field": "temperature_K", "type": "Explicit", "note": "fixture"},
            {"field": "co2_vol_pct", "type": "Explicit", "note": "fixture"},
            {"field": "co2_partial_kPa", "type": "Explicit", "note": "fixture"},
            {"field": "total_pressure_kPa", "type": "Explicit", "note": "fixture"},
            {"field": "initial_loading", "type": "Explicit", "note": "fixture"},
            {"field": "wt_a", "type": "Explicit", "note": "fixture"},
            {"field": "water_wt", "type": "Derived", "note": "100-30"},
            {"field": "equilibrium_loading", "type": "Explicit", "note": "fixture"},
        ],
    }


def normalize_case(test_overrides: dict, compounds: list[dict]) -> tuple[dict, dict]:
    raw = raw_record(test_overrides)
    rec = extract.normalize(
        raw,
        compounds=compounds,
        pdf=PDF,
        pdf_hash="fixture",
        batch_id="water_vapor_test",
        qc_level="L2",
        snapshot_path=ROOT / "dummy_snapshot.json",
        snapshot_hash="dummy",
    )
    issues = reasoning.consistency_issues(raw, rec)
    before = rec["qc"]["qc_level"]
    reasoning.apply_consistency(rec, issues)
    return rec, {
        "issues": issues,
        "qc_before": before,
        "qc_after": rec["qc"]["qc_level"],
        "gas_phase": rec.get("gas_phase") or {},
        "co2_partial_kPa": rec["test"].get("co2_partial_kPa"),
        "notes": rec["qc"].get("qc_reason"),
    }


def main() -> None:
    compounds = extract.load_compounds()
    checks = []

    cases = [
        ("A_explicit_p_h2o", {"p_h2o_kPa": 7.4, "gas_basis": "wet"}),
        ("B_wet_basis", {"co2_partial_kPa": None, "gas_basis": "wet"}),
        ("C_dry_with_p_h2o", {"co2_partial_kPa": None, "gas_basis": "dry", "p_h2o_kPa": 7.4}),
        ("D_dry_without_p_h2o", {"co2_partial_kPa": None, "gas_basis": "dry"}),
        ("E_no_water_info", {"gas_basis": "unknown"}),
        ("F_unknown_basis_no_partial", {"co2_partial_kPa": None, "gas_basis": "unknown"}),
        ("G_pco2_gt_total", {"co2_partial_kPa": 120.0, "p_h2o_kPa": 7.4, "gas_basis": "wet"}),
        ("H_component_sum_gt_total", {"co2_partial_kPa": 98.0, "p_h2o_kPa": 7.4, "gas_basis": "wet"}),
        ("I_wet_fraction_mismatch", {"co2_partial_kPa": 30.0, "gas_basis": "wet"}),
    ]
    for name, overrides in cases:
        rec, out = normalize_case(overrides, compounds)
        checks.append({"case": name, **out})

    by = {c["case"]: c for c in checks}
    checks.append({
        "case": "A_check", "ok": by["A_explicit_p_h2o"]["gas_phase"].get("water_vapour_check") == "pass"
        and by["A_explicit_p_h2o"]["qc_after"] == "L2",
    })
    checks.append({
        "case": "B_check", "ok": abs(by["B_wet_basis"]["co2_partial_kPa"] - 15.19875) < 1e-6
        and by["B_wet_basis"]["gas_phase"].get("derivation") == "wet_basis",
    })
    checks.append({
        "case": "C_check", "ok": abs(by["C_dry_with_p_h2o"]["co2_partial_kPa"] - 14.08875) < 1e-6
        and by["C_dry_with_p_h2o"]["gas_phase"].get("derivation") == "dry_basis_with_p_h2o",
    })
    checks.append({
        "case": "D_check", "ok": by["D_dry_without_p_h2o"]["co2_partial_kPa"] is None
        and by["D_dry_without_p_h2o"]["gas_phase"].get("status") == "blocked_dry_basis_missing_p_h2o",
    })
    checks.append({
        "case": "E_check", "ok": by["E_no_water_info"]["gas_phase"].get("water_vapour_check") == "not_assessable"
        and by["E_no_water_info"]["qc_after"] == "L2",
    })
    checks.append({
        "case": "F_check", "ok": by["F_unknown_basis_no_partial"]["co2_partial_kPa"] is None
        and by["F_unknown_basis_no_partial"]["gas_phase"].get("status") == "blocked_basis_unknown",
    })
    checks.append({
        "case": "G_check", "ok": by["G_pco2_gt_total"]["qc_before"] == "L2"
        and by["G_pco2_gt_total"]["qc_after"] == "L3"
        and any(i["reason"] == "co2_partial_exceeds_total_pressure" for i in by["G_pco2_gt_total"]["issues"]),
    })
    checks.append({
        "case": "H_check", "ok": by["H_component_sum_gt_total"]["qc_after"] == "L3"
        and any(i["reason"] == "component_sum_exceeds_total" for i in by["H_component_sum_gt_total"]["issues"]),
    })
    checks.append({
        "case": "I_check", "ok": by["I_wet_fraction_mismatch"]["qc_after"] == "L3"
        and any(i["reason"] == "partial_pressure_inconsistent_with_wet_fraction"
                for i in by["I_wet_fraction_mismatch"]["issues"]),
    })

    sat100 = gas_phase.water_saturation_pressure_kpa(373.15)
    sat25 = gas_phase.water_saturation_pressure_kpa(298.15)
    sat_out = gas_phase.water_saturation_pressure_kpa(400.0)
    aw = gas_phase.assess({
        "temperature_K": 313.15, "total_pressure_kPa": 101.325,
        "co2_partial_kPa": 15.0, "water_activity": 0.9,
    })
    no_aw = gas_phase.assess({
        "temperature_K": 313.15, "total_pressure_kPa": 101.325,
        "co2_partial_kPa": 15.0,
    })
    checks.append({
        "case": "pure_water_saturation",
        "ok": sat100["status"] == "ok" and abs(sat100["p_kPa"] - 101.325) < 0.2
        and sat25["status"] == "ok" and abs(sat25["p_kPa"] - 3.17) < 0.1
        and sat_out["status"] == "out_of_range",
        "sat100": sat100, "sat25": sat25, "sat400": sat_out,
    })
    checks.append({
        "case": "solution_requires_activity",
        "ok": no_aw["p_h2o_kPa"] is None and aw["p_h2o_kPa"] is not None
        and aw["p_h2o_source"] == "water_activity_times_pure_water_saturation",
        "no_activity": {"p_h2o": no_aw["p_h2o_kPa"], "source": no_aw["p_h2o_source"]},
        "with_activity": {"p_h2o": aw["p_h2o_kPa"], "source": aw["p_h2o_source"]},
    })

    # Real database scan: no water data should not create anomalies or rejections.
    conn = sqlite3.connect(f"file:{ROOT / 'data/ccus.sqlite'}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    db_rows = conn.execute("SELECT test_id,qc_level,temperature_K,co2_vol_pct,co2_partial_kPa,total_pressure_kPa FROM test").fetchall()
    conn.close()
    status_counts = {}
    anomaly_rows = []
    for r in db_rows:
        result = gas_phase.assess(dict(r))
        status_counts[result["status"]] = status_counts.get(result["status"], 0) + 1
        if result["anomalies"]:
            anomaly_rows.append({"test_id": r["test_id"], "anomalies": result["anomalies"]})
    checks.append({
        "case": "real_db_scan",
        "ok": not anomaly_rows,
        "tests": len(db_rows),
        "status_counts": status_counts,
        "anomalies": anomaly_rows,
        "note": "existing rows have no gas_basis/P_H2O, so water checks are not_assessable; no row is rejected",
    })

    ok = all(c.get("ok") for c in checks if "ok" in c)
    payload = {
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "ok": ok,
        "cases": checks,
    }
    (ROOT / "evaluation" / "reports" / "water_vapor_test.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        "# Water-vapour / dry-wet basis test",
        "",
        f"- Result: {'PASS' if ok else 'FAIL'}",
        "",
        "| Case | Result | QC before→after | P_CO2 | Gas status |",
        "|---|---|---|---|---|",
    ]
    for c in checks:
        if "case" not in c:
            continue
        if "qc_before" in c:
            lines.append(
                f"| {c['case']} | {'PASS' if c.get('ok', True) else 'FAIL'} | "
                f"{c['qc_before']}→{c['qc_after']} | {c.get('co2_partial_kPa')} | "
                f"{c.get('gas_phase', {}).get('status')} |"
            )
        else:
            lines.append(f"| {c['case']} | {'PASS' if c.get('ok') else 'FAIL'} | - | - | - |")
    lines += [
        "",
        "Missing water-vapour data is `not_assessable`, not a rejection. "
        "Dry-basis composition without P_H2O leaves P_CO2 null. "
        "P_CO2 > P_total or component-sum > P_total downgrades L2 to L3.",
    ]
    lines.append("")
    lines.append("Full JSON: `evaluation/reports/water_vapor_test.json`")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
