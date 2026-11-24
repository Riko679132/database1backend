#!/usr/bin/env python3
"""Deterministic amine-CO2 concentration / loading / pressure calculations.

The skill must not rely on mental arithmetic for values written into the
database. This script prints a JSON object with inputs, formula, result and
warnings. It uses only the Python standard library.

Examples:
  python calc.py wt-to-mol-fraction --wt 30 --mw 61.08 --water-wt 70
  python calc.py molality-to-wt --molality 7.017 --mw 61.08
  python calc.py molarity-to-wt --molarity 4.90 --mw 61.08 --density 1.00
  python calc.py wt-to-molarity --wt 30 --mw 61.08 --density 1.00
  python calc.py partial-pressure --vol-pct 15 --total-kpa 101.325
  python calc.py loading --co2-mol 0.609 --amine-mol 1.0
  python calc.py loading-from-mass --co2-g 26.8 --amine-g 100 --amine-mw 61.08
  python calc.py cyclic --rich 0.609 --lean 0.200
  python calc.py recipe-check --wt-a 30 --wt-b 5 --water 65
"""
from __future__ import annotations

import argparse
import json
import sys

M_WATER = 18.015


def emit(payload: dict) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def positive(name: str, value: float) -> float:
    if value is None or value <= 0:
        raise ValueError(f"{name} must be positive")
    return float(value)


def wt_to_mol_fraction(wt: float, mw: float, water_wt: float) -> dict:
    positive("wt", wt)
    positive("mw", mw)
    positive("water_wt", water_wt)
    if abs(wt + water_wt - 100.0) > 0.1:
        raise ValueError("wt + water_wt must equal 100 ± 0.1")
    n_amine = (wt / 100.0) / mw
    n_water = (water_wt / 100.0) / M_WATER
    x = n_amine / (n_amine + n_water)
    molality = (wt / 100.0) / (water_wt / 100.0) / mw * 1000.0
    return {
        "calculation": "wt_to_mol_fraction",
        "inputs": {"wt_percent": wt, "mw_g_per_mol": mw, "water_wt_percent": water_wt},
        "formula": "x_i = (w_i/M_i) / sum(w_j/M_j); m = (wt/100)/(water_wt/100)/M * 1000",
        "result": {"mole_fraction": x, "molality_mol_per_kg_solvent": molality},
        "warnings": [],
    }


def molality_to_wt(molality: float, mw: float) -> dict:
    positive("molality", molality)
    positive("mw", mw)
    mass_amine = molality * mw
    wt = mass_amine / (mass_amine + 1000.0) * 100.0
    return {
        "calculation": "molality_to_wt",
        "inputs": {"molality_mol_per_kg_solvent": molality, "mw_g_per_mol": mw},
        "formula": "wt% = m*M/(m*M+1000)*100",
        "result": {"wt_percent": wt},
        "warnings": [],
    }


def molarity_to_wt(molarity: float, mw: float, density: float) -> dict:
    positive("molarity", molarity)
    positive("mw", mw)
    positive("density", density)
    wt = molarity * mw / (density * 1000.0) * 100.0
    return {
        "calculation": "molarity_to_wt",
        "inputs": {
            "molarity_mol_per_L": molarity,
            "mw_g_per_mol": mw,
            "density_g_per_mL": density,
        },
        "formula": "wt% = c*M/(rho*1000)*100",
        "result": {"wt_percent": wt},
        "warnings": [
            "Density must be measured for the same solution composition and temperature. "
            "Do not use water density or a density from a different concentration."
        ],
    }


def wt_to_molarity(wt: float, mw: float, density: float) -> dict:
    positive("wt", wt)
    positive("mw", mw)
    positive("density", density)
    molarity = (wt / 100.0) * density * 1000.0 / mw
    return {
        "calculation": "wt_to_molarity",
        "inputs": {"wt_percent": wt, "mw_g_per_mol": mw, "density_g_per_mL": density},
        "formula": "c = (wt/100)*rho*1000/M",
        "result": {"molarity_mol_per_L": molarity},
        "warnings": [
            "Density must be measured for the same solution composition and temperature."
        ],
    }


def partial_pressure(vol_pct: float | None, y_co2: float | None, total_kpa: float) -> dict:
    positive("total_kpa", total_kpa)
    if y_co2 is None:
        if vol_pct is None:
            raise ValueError("provide --vol-pct or --y-co2")
        y_co2 = vol_pct / 100.0
    if not (0 <= y_co2 <= 1):
        raise ValueError("y_co2 must be between 0 and 1")
    p = y_co2 * total_kpa
    return {
        "calculation": "partial_pressure",
        "inputs": {"y_co2": y_co2, "total_pressure_kPa": total_kpa},
        "formula": "P_CO2 = y_CO2 * P_total",
        "result": {"co2_partial_kPa": p, "co2_vol_percent": y_co2 * 100.0},
        "warnings": [
            "Ideal-gas assumption. If the gas is dry-basis and water vapour is significant, "
            "correct to the same basis before using the result."
        ],
    }


def loading(co2_mol: float, amine_mol: float) -> dict:
    positive("co2_mol", co2_mol)
    positive("amine_mol", amine_mol)
    return {
        "calculation": "loading",
        "inputs": {"co2_mol": co2_mol, "amine_mol": amine_mol},
        "formula": "alpha = n_CO2 / n_amine",
        "result": {"loading_mol_per_mol": co2_mol / amine_mol},
        "warnings": [
            "State whether amine_mol is total amine, one component, or nitrogen sites."
        ],
    }


def loading_from_mass(co2_g: float, amine_g: float, amine_mw: float) -> dict:
    positive("co2_g", co2_g)
    positive("amine_g", amine_g)
    positive("amine_mw", amine_mw)
    n_co2 = co2_g / 44.009
    n_amine = amine_g / amine_mw
    return {
        "calculation": "loading_from_mass",
        "inputs": {"co2_g": co2_g, "amine_g": amine_g, "amine_mw_g_per_mol": amine_mw},
        "formula": "alpha = (m_CO2/44.009)/(m_amine/M_amine)",
        "result": {"loading_mol_per_mol": n_co2 / n_amine, "co2_mol": n_co2, "amine_mol": n_amine},
        "warnings": [
            "Use the amine mass, not the total solution mass. State the amine basis."
        ],
    }


def cyclic(rich: float, lean: float) -> dict:
    if rich < lean:
        raise ValueError("rich loading must be >= lean loading")
    return {
        "calculation": "cyclic_capacity",
        "inputs": {"rich_loading": rich, "lean_loading": lean},
        "formula": "delta_alpha = alpha_rich - alpha_lean",
        "result": {"cyclic_capacity_mol_per_mol": rich - lean},
        "warnings": [],
    }


def recipe_check(wt_a: float, wt_b: float | None, water: float) -> dict:
    positive("wt_a", wt_a)
    positive("water", water)
    wt_b = 0.0 if wt_b is None else wt_b
    total = wt_a + wt_b + water
    ok = abs(total - 100.0) <= 0.1
    return {
        "calculation": "recipe_check",
        "inputs": {"wt_a": wt_a, "wt_b": wt_b, "water_wt": water},
        "formula": "wt_a + wt_b + water_wt = 100 +/- 0.1",
        "result": {"sum_wt_percent": total, "closed": ok, "total_amine_wt": wt_a + wt_b},
        "warnings": [] if ok else ["Recipe does not close to 100 ± 0.1 wt%."],
    }


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)

    q = sub.add_parser("wt-to-mol-fraction")
    q.add_argument("--wt", type=float, required=True)
    q.add_argument("--mw", type=float, required=True)
    q.add_argument("--water-wt", type=float, required=True)

    q = sub.add_parser("molality-to-wt")
    q.add_argument("--molality", type=float, required=True)
    q.add_argument("--mw", type=float, required=True)

    q = sub.add_parser("molarity-to-wt")
    q.add_argument("--molarity", type=float, required=True)
    q.add_argument("--mw", type=float, required=True)
    q.add_argument("--density", type=float, required=True)

    q = sub.add_parser("wt-to-molarity")
    q.add_argument("--wt", type=float, required=True)
    q.add_argument("--mw", type=float, required=True)
    q.add_argument("--density", type=float, required=True)

    q = sub.add_parser("partial-pressure")
    q.add_argument("--vol-pct", type=float)
    q.add_argument("--y-co2", type=float)
    q.add_argument("--total-kpa", type=float, required=True)

    q = sub.add_parser("loading")
    q.add_argument("--co2-mol", type=float, required=True)
    q.add_argument("--amine-mol", type=float, required=True)

    q = sub.add_parser("loading-from-mass")
    q.add_argument("--co2-g", type=float, required=True)
    q.add_argument("--amine-g", type=float, required=True)
    q.add_argument("--amine-mw", type=float, required=True)

    q = sub.add_parser("cyclic")
    q.add_argument("--rich", type=float, required=True)
    q.add_argument("--lean", type=float, required=True)

    q = sub.add_parser("recipe-check")
    q.add_argument("--wt-a", type=float, required=True)
    q.add_argument("--wt-b", type=float)
    q.add_argument("--water", type=float, required=True)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "wt-to-mol-fraction":
            out = wt_to_mol_fraction(args.wt, args.mw, args.water_wt)
        elif args.command == "molality-to-wt":
            out = molality_to_wt(args.molality, args.mw)
        elif args.command == "molarity-to-wt":
            out = molarity_to_wt(args.molarity, args.mw, args.density)
        elif args.command == "wt-to-molarity":
            out = wt_to_molarity(args.wt, args.mw, args.density)
        elif args.command == "partial-pressure":
            out = partial_pressure(args.vol_pct, args.y_co2, args.total_kpa)
        elif args.command == "loading":
            out = loading(args.co2_mol, args.amine_mol)
        elif args.command == "loading-from-mass":
            out = loading_from_mass(args.co2_g, args.amine_g, args.amine_mw)
        elif args.command == "cyclic":
            out = cyclic(args.rich, args.lean)
        elif args.command == "recipe-check":
            out = recipe_check(args.wt_a, args.wt_b, args.water)
        else:
            raise ValueError(f"unknown command: {args.command}")
    except ValueError as exc:
        emit({"error": str(exc)})
        return 2
    emit(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
