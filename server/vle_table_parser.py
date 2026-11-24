"""Deterministic parser for multi-column VLE tables with repeated t/p/loading groups.

It reconstructs column groups from the header row's word coordinates, carries
the temperature down a group, and returns every point plus diagnostics. It is
used as a table-first extraction path before the LLM, not as a replacement for
the paper's original values.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import pdfplumber

NUM = re.compile(r"^-?\d+(?:\.\d+)?$")
TABLE_RE = re.compile(r"Table\s+([IVX]+)", re.I)
# Method constants must be paper-specific; do not apply 180 kPa / 40 C to other papers.
PROFILES: dict[str, dict] = {
    "10.1021/je00005a025": {
        "version": "phase4-1.0",
        "source": "Shen & Li 1992, methods p.97 (180 kPa, 0.5 L) and Tables II-V (40 C group)",
        "target_temperature_C": 40.0,
        "max_p_CO2_kPa": 180.0,
        "total_pressure_kPa": 180.0,
        "liquid_volume_L": 0.5,
        "note": "Shen & Li 1992 low-pressure apparatus; methods state ~180 kPa and ~0.5 L",
    }
}

# Vertical row tables and nested-unit tables use a different layout from the
# repeated column groups above. The profile declares header/layout/units and
# selection rules; the parser below stays generic.
VERTICAL_PROFILES: dict[str, dict] = {
    "10.1016/j.jece.2024.112664": {
        "version": "phase5-1.0",
        "source": "Kim et al. 2024, Table 2, p.6; comparison rows 30wt% MEA at 313.15 K",
        "page": 6,
        "table": "2",
        "header_tokens": ["Absorbent", "Temperature", "PCO2", "loading", "Source"],
        "x_max": 300.0,
        "y_end": 165.0,
        "columns": {
            "recipe": 44.0,
            "temperature": 88.0,
            "pressure": 142.0,
            "loading": 186.0,
            "source": 259.0,
        },
        "temperature_unit": "K",
        "pressure_unit": "bar",
        "loading_unit": "mol CO2/mol amine",
        "row_filter": {"source_contains": "This"},
        "recipe_regex": r"(?P<wt>\d+(?:\.\d+)?)\s*wt\s*%?\s*(?P<amine>MEA|MDEA|AMP|PZ|DEA|TEA|DGA)",
        "loc_label": "Table 2, p.6, this-work row",
    },
    "10.1016/j.ijggc.2016.12.018": {
        "version": "phase5-1.0",
        "source": "Hartono et al. 2017, Table A1, p.210; 30 mass% MEA screening reference",
        "page": 10,
        "table": "A1",
        "header_tokens": ["Sample", "PCO2", "T", "Loading"],
        "x_max": 600.0,
        "y_end": 120.0,
        "columns": {
            "sample": 80.0,
            "pressure": 136.0,
            "temperature": 187.0,
            # VLE mol/mol sub-column; the table also has mol/kg columns.
            "loading": 493.0,
        },
        "temperature_unit": "C",
        "pressure_unit": "kPa",
        "loading_unit": "mol CO2/mol MEA",
        "row_filter": {"sample_in": ["Absorption", "Desorption"]},
        "fixed_recipe": {"amine_a": "MEA", "wt_a": 30.0},
        "recipe_evidence_regex": r"30\s*mass\s*%\s*MEA",
        "recipe_source": "abstract/methods: 30 mass% MEA reference",
        "loc_label": "Table A1, p.210, VLE mol/mol column",
    },
}


def vertical_profile_for_doi(doi: str | None) -> dict | None:
    return VERTICAL_PROFILES.get((doi or "").lower())



def profile_for_doi(doi: str | None) -> dict | None:
    return PROFILES.get((doi or "").lower())


@dataclass
class Group:
    t_x: float
    p_x: float
    load_x: float
    t: float | None = None


@dataclass
class Table:
    number: str
    recipe: dict
    page: int
    header_top: float
    groups: list[Group] = field(default_factory=list)
    points: list[dict] = field(default_factory=list)
    data_rows: int = 0
    unparsed_rows: list[str] = field(default_factory=list)


def _rows(page) -> list[dict]:
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
    words.sort(key=lambda w: (round(w["top"] / 4), w["x0"]))
    rows: list[dict] = []
    cur_band = None
    cur: list[dict] = []
    for w in words:
        band = round(w["top"] / 4)
        if cur_band is None or band == cur_band:
            cur.append(w)
            cur_band = band
        else:
            rows.append({"top": cur[0]["top"], "words": cur, "text": " ".join(x["text"] for x in cur)})
            cur = [w]
            cur_band = band
    if cur:
        rows.append({"top": cur[0]["top"], "words": cur, "text": " ".join(x["text"] for x in cur)})
    return rows


def _is_header(text: str) -> bool:
    low = re.sub(r"\s+", "", text.lower())
    return ("p/kpa" in low or "p/kPa" in text) and "loading" in low and ("t/" in low or low.startswith("o"))


def _groups_from_header(row: dict) -> list[Group]:
    words = row["words"]
    groups: list[Group] = []
    seen = set()
    for i, w in enumerate(words):
        if not re.search(r"p\s*/\s*kpa", w["text"], re.I):
            continue
        p_x = w["x0"]
        if p_x in seen:
            continue
        seen.add(p_x)
        left = [
            x for x in words
            if x["x0"] < p_x and p_x - x["x0"] < 55
            and not re.search(r"p\s*/|loading|^a$", x["text"], re.I)
        ]
        right = [
            x for x in words
            if x["x0"] > p_x and x["x0"] - p_x < 85 and re.search(r"loading", x["text"], re.I)
        ]
        if left and right:
            groups.append(Group(t_x=left[-1]["x0"], p_x=p_x, load_x=right[0]["x0"]))
    return groups


def _caption(rows: list[dict], header_idx: int) -> tuple[str, dict]:
    text = " ".join(r["text"] for r in rows[max(0, header_idx - 6):header_idx])
    text = re.sub(r"\s+", " ", text)
    m = TABLE_RE.search(text)
    number = m.group(1) if m else "?"
    amines = re.findall(r"\b(MEA|MDEA|PZ|AMP|DEA|TEA|DGA)\b", text.upper())
    values = re.findall(r"(\d+(?:\.\d+)?)\s*(?:wt\s*)?%", text, re.I)
    recipe = {"raw": text}
    if amines and values:
        recipe["amine_a"] = amines[0]
        recipe["wt_a"] = float(values[0])
    if len(amines) >= 2 and len(values) >= 2:
        recipe["amine_b"] = amines[1]
        recipe["wt_b"] = float(values[1])
    return number, recipe


def _assign_row(row: dict, groups: list[Group], tol: float = 25.0) -> list[dict]:
    """Assign each numeric token to its nearest t/p/loading column."""
    columns = []
    for gi, g in enumerate(groups):
        columns.extend([
            (gi, "t", g.t_x),
            (gi, "p", g.p_x),
            (gi, "load", g.load_x),
        ])
    assigned = [{"t": None, "p": None, "load": None} for _ in groups]
    for w in row["words"]:
        if not NUM.fullmatch(w["text"]):
            continue
        gi, kind, _ = min(columns, key=lambda c: abs(w["x0"] - c[2]))
        if abs(w["x0"] - next(c[2] for c in columns if c[0] == gi and c[1] == kind)) > tol:
            continue
        if assigned[gi][kind] is None:
            assigned[gi][kind] = float(w["text"])
    return assigned


def parse_vle_tables(pdf_path: Path | str, profile: dict | None = None) -> dict:
    pdf_path = Path(pdf_path)
    target = profile
    needs_profile = target is None
    tables: list[Table] = []
    with pdfplumber.open(pdf_path) as pdf:
        for pno, page in enumerate(pdf.pages, 1):
            rows = _rows(page)
            header_idxs = [i for i, r in enumerate(rows) if _is_header(r["text"])]
            for hi, idx in enumerate(header_idxs):
                header = rows[idx]
                groups = _groups_from_header(header)
                if not groups:
                    continue
                number, recipe = _caption(rows, idx)
                end = header_idxs[hi + 1] if hi + 1 < len(header_idxs) else len(rows)
                table = Table(number=number, recipe=recipe, page=pno, header_top=header["top"], groups=groups)
                for raw in rows[idx + 1:end]:
                    # Two-column PDFs can interleave a footnote into the middle
                    # of a table; rows without p/loading are simply skipped.
                    assigned = _assign_row(raw, table.groups)
                    if not any(v["p"] is not None for v in assigned):
                        continue
                    if not any(v["load"] is not None for v in assigned):
                        continue
                    table.data_rows += 1
                    for gi, g in enumerate(table.groups):
                        if assigned[gi]["t"] is not None:
                            g.t = assigned[gi]["t"]
                        if g.t is None or assigned[gi]["p"] is None or assigned[gi]["load"] is None:
                            continue
                        table.points.append({
                            "table": number,
                            "group": gi + 1,
                            "temperature_C": g.t,
                            "p_CO2_kPa": assigned[gi]["p"],
                            "loading": assigned[gi]["load"],
                            "page": pno,
                            "raw_row": raw["text"],
                        })
                tables.append(table)
    # Deduplicate by table/group/t/p/loading and select the target 40 C low-pressure points.
    seen = set()
    all_points = []
    for t in tables:
        for p in t.points:
            key = (p["table"], p["temperature_C"], p["p_CO2_kPa"], p["loading"])
            if key in seen:
                continue
            seen.add(key)
            all_points.append(p)
    selected = []
    if target is not None:
        selected = [
            p for p in all_points
            if abs(float(p["temperature_C"]) - float(target["target_temperature_C"])) <= 0.5
            and float(p["p_CO2_kPa"]) <= float(target["max_p_CO2_kPa"])
        ]
    return {
        "pdf": pdf_path.as_posix(),
        "profile": target,
        "needs_profile": needs_profile,
        "tables": [
            {
                "number": t.number,
                "recipe": t.recipe,
                "page": t.page,
                "groups": [
                    {"t_x": g.t_x, "p_x": g.p_x, "load_x": g.load_x, "last_temperature_C": g.t}
                    for g in t.groups
                ],
                "data_rows": t.data_rows,
                "points": len([p for p in t.points if (p["table"], p["temperature_C"], p["p_CO2_kPa"], p["loading"]) in seen]),
            }
            for t in tables
        ],
        "all_points": all_points,
        "selected_40C_lowP": selected,
        "counts": {
            "tables": len(tables),
            "all_points": len(all_points),
            "selected_40C_lowP": len(selected),
        },
    }


def _assign_cells(row: dict, columns: dict[str, float], x_max: float, tol: float = 30.0) -> dict[str, str]:
    cells = {key: "" for key in columns}
    for word in row["words"]:
        if word["x0"] > x_max:
            continue
        key = min(columns, key=lambda k: abs(word["x0"] - columns[k]))
        if abs(word["x0"] - columns[key]) <= tol:
            cells[key] = (cells[key] + " " + word["text"]).strip()
    return cells


def _cell_num(text: str | None) -> float | None:
    m = re.search(r"-?\d+(?:\.\d+)?", str(text or ""))
    return float(m.group(0)) if m else None


def _paper_text(pdf_path: Path) -> str:
    with pdfplumber.open(pdf_path) as pdf:
        return "\n".join((page.extract_text() or "") for page in pdf.pages)


def parse_vertical_table(pdf_path: Path | str, profile: dict) -> dict:
    """Parse a vertical row table or a nested-unit table declared by a profile.

    The layout (page/header/columns/x limits) is in the profile. This function
    does not contain any paper-specific temperature, pressure or recipe values.
    """
    pdf_path = Path(pdf_path)
    page_no = int(profile["page"])
    rows_out: list[dict] = []
    skipped: list[dict] = []
    errors: list[str] = []
    body = _paper_text(pdf_path)
    if profile.get("recipe_evidence_regex") and not re.search(profile["recipe_evidence_regex"], body, re.I):
        return {
            "pdf": pdf_path.as_posix(),
            "profile": profile,
            "points": [],
            "skipped": [],
            "errors": ["recipe_evidence_not_found"],
            "counts": {"data_rows": 0, "points": 0, "skipped": 0},
        }

    with pdfplumber.open(pdf_path) as pdf:
        if page_no < 1 or page_no > len(pdf.pages):
            raise ValueError(f"profile page {page_no} outside PDF")
        page = pdf.pages[page_no - 1]
        rows = _rows(page)
        header = None
        for row in rows:
            low = row["text"].lower()
            if all(tok.lower() in low for tok in profile["header_tokens"]):
                header = row
                break
        if header is None:
            return {
                "pdf": pdf_path.as_posix(),
                "profile": profile,
                "points": [],
                "skipped": [],
                "errors": ["header_not_found"],
                "counts": {"data_rows": 0, "points": 0, "skipped": 0},
            }
        columns = dict(profile["columns"])
        y_end = float(profile.get("y_end") or 1e9)
        x_max = float(profile.get("x_max") or 1e9)
        current = None
        for row in rows:
            if row["top"] <= header["top"] or row["top"] > y_end:
                continue
            cells = _assign_cells(row, columns, x_max)
            if not any(cells.values()):
                continue
            if _cell_num(cells.get("temperature")) is not None:
                if current:
                    rows_out.append(current)
                current = {
                    "top": row["top"],
                    "cells": cells,
                    "text": " ".join(v for v in cells.values() if v).strip(),
                }
            elif current:
                for key, value in cells.items():
                    if value:
                        current["cells"][key] = (current["cells"].get(key, "") + " " + value).strip()
                current["text"] = " ".join(v for v in current["cells"].values() if v).strip()
        if current:
            rows_out.append(current)

    points = []
    for row in rows_out:
        cells = row["cells"]
        filter_rule = profile.get("row_filter") or {}
        if "source_contains" in filter_rule:
            if filter_rule["source_contains"].lower() not in str(cells.get("source") or "").lower():
                skipped.append({"row": row["text"], "reason": "source_filter"})
                continue
        if "sample_in" in filter_rule:
            sample = str(cells.get("sample") or "").strip().lower()
            allowed = [x.lower() for x in filter_rule["sample_in"]]
            if sample not in allowed:
                skipped.append({"row": row["text"], "reason": "sample_filter"})
                continue
        if profile.get("fixed_recipe"):
            recipe = dict(profile["fixed_recipe"])
            recipe_evidence = "Explicit" if profile.get("recipe_evidence_regex") else "Contextual"
        else:
            recipe_text = str(cells.get("recipe") or row["text"])
            m = re.search(profile["recipe_regex"], recipe_text, re.I)
            if not m:
                skipped.append({"row": row["text"], "reason": "recipe_not_parsed"})
                continue
            recipe = {"amine_a": m.group("amine").upper(), "wt_a": float(m.group("wt"))}
            recipe_evidence = "Explicit"
        if not recipe.get("amine_a") or recipe.get("wt_a") is None:
            skipped.append({"row": row["text"], "reason": "recipe_incomplete"})
            continue
        temp = _cell_num(cells.get("temperature"))
        pressure = _cell_num(cells.get("pressure"))
        loading = _cell_num(cells.get("loading"))
        if temp is None or pressure is None or loading is None:
            skipped.append({"row": row["text"], "reason": "numeric_missing"})
            continue
        if str(profile.get("temperature_unit") or "K").upper() == "C":
            temp += 273.15
        unit = str(profile.get("pressure_unit") or "kPa").lower()
        if unit == "bar":
            pressure *= 100.0
        elif unit == "mpa":
            pressure *= 1000.0
        elif unit == "atm":
            pressure *= 101.325
        sample = str(cells.get("sample") or "").strip()
        row_type = {"absorption": "rich", "desorption": "lean"}.get(sample.lower(), None)
        points.append({
            "table": profile.get("table"),
            "page": page_no,
            "temperature_K": round(temp, 4),
            "p_CO2_kPa": round(pressure, 4),
            "loading": round(loading, 6),
            "loading_unit": profile.get("loading_unit"),
            "row_type": row_type,
            "recipe": recipe,
            "recipe_evidence": recipe_evidence,
            "raw_row": row["text"],
            "source_excerpt": str(cells.get("source") or row["text"])[:400],
        })
    return {
        "pdf": pdf_path.as_posix(),
        "profile": profile,
        "points": points,
        "skipped": skipped,
        "errors": errors,
        "counts": {
            "data_rows": len(rows_out),
            "points": len(points),
            "skipped": len(skipped),
        },
    }


def vertical_points_to_raw_records(
    result: dict,
    pdf_path: Path | str,
    *,
    doi: str | None,
    source_template: dict | None = None,
) -> list[dict]:
    import hashlib

    pdf_path = Path(pdf_path)
    pdf_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    src = dict(source_template or {})
    src.update({
        "doi": doi,
        "pdf_path": pdf_path.as_posix(),
        "pdf_hash": pdf_hash,
        "loc_type": "table",
    })
    profile = result.get("profile") or {}
    records = []
    for point in result.get("points") or []:
        recipe = point["recipe"]
        amine = recipe["amine_a"]
        wt_a = float(recipe["wt_a"])
        if not (20.0 <= wt_a <= 50.0):
            continue
        water = round(100.0 - wt_a, 4)
        rich = point["loading"] if point.get("row_type") == "rich" else None
        lean = point["loading"] if point.get("row_type") == "lean" else None
        record = {
            "source": {
                **src,
                "loc_label": profile.get("loc_label"),
                "excerpt": point["raw_row"],
            },
            "recipe": {
                "recipe_type": "mono",
                "amine_a": {"standard_name": amine},
                "amine_b": None,
                "wt_a": wt_a,
                "wt_b": None,
                "water_wt": water,
                "total_amine_wt": wt_a,
                "additive_flag": 0,
                "salt_flag": 0,
                "phase_flag": 0,
            },
            "test": {
                "test_origin": "literature",
                "temperature_K": point["temperature_K"],
                "co2_vol_pct": None,
                "co2_partial_kPa": point["p_CO2_kPa"],
                "total_pressure_kPa": None,
                "gas_flow": None,
                "liquid_volume": None,
                "gas_liquid_ratio": None,
                "initial_loading": None,
                "rich_loading": rich,
                "lean_loading": lean,
            },
            "performance": [{
                "metric_name": "equilibrium_loading",
                "value": point["loading"],
                "unit": point["loading_unit"] or "mol CO2/mol amine",
                "value_original": point["loading"],
                "unit_original": point["loading_unit"] or "mol CO2/mol amine",
                "metric_definition": (
                    f"{profile.get('loc_label')}; P_CO2={point['p_CO2_kPa']} kPa; "
                    "total pressure and initial loading are not stated in the row"
                ),
                "is_derived": 0,
            }],
            "evidence": [
                {"field": "wt_a", "type": point.get("recipe_evidence") or "Explicit",
                 "note": profile.get("recipe_source") or "table row"},
                {"field": "water_wt", "type": "Derived", "note": "100 - wt_a"},
                {"field": "temperature_K", "type": "Explicit", "note": "temperature column"},
                {"field": "co2_partial_kPa", "type": "Explicit", "note": "PCO2 column"},
                {"field": "initial_loading", "type": "Unknown", "note": "not stated in table/methods"},
                {"field": "equilibrium_loading", "type": "Explicit", "note": "loading column"},
                {"field": "source.excerpt", "type": "Explicit", "note": "raw table row"},
            ],
        }
        records.append(record)
    return records


def points_to_raw_records(
    result: dict,
    pdf_path: Path | str,
    *,
    source_template: dict | None = None,
    doi: str | None = None,
    total_pressure_kPa: float = 180.0,
    liquid_volume_L: float = 0.5,
) -> list[dict]:
    """Convert selected table points into the raw_agent record shape."""
    import hashlib

    pdf_path = Path(pdf_path)
    pdf_hash = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    src = dict(source_template or {})
    src.setdefault("doi", doi)
    records = []
    tmap = {t["number"]: t for t in result.get("tables") or []}
    for p in result.get("selected_40C_lowP") or []:
        table = tmap[p["table"]]
        recipe = table["recipe"]
        amine_a = recipe.get("amine_a")
        amine_b = recipe.get("amine_b")
        wt_a = recipe.get("wt_a")
        wt_b = recipe.get("wt_b")
        if not amine_a or wt_a is None:
            continue
        total = float(wt_a) + float(wt_b or 0)
        if not (20.0 <= total <= 50.0):
            continue
        water = round(100.0 - total, 4)
        pco2 = float(p["p_CO2_kPa"])
        co2_vol = round(pco2 / total_pressure_kPa * 100.0, 4)
        loc_label = f"Table {p['table']}, p.{p['page']}, 40 C column group"
        record = {
            "source": {
                **src,
                "pdf_path": pdf_path.as_posix(),
                "pdf_hash": pdf_hash,
                "loc_type": "table",
                "loc_label": loc_label,
                "excerpt": p["raw_row"],
            },
            "recipe": {
                "recipe_type": "binary" if amine_b else "mono",
                "amine_a": {"standard_name": amine_a},
                "amine_b": {"standard_name": amine_b} if amine_b else None,
                "wt_a": float(wt_a),
                "wt_b": float(wt_b) if wt_b is not None else None,
                "water_wt": water,
                "total_amine_wt": total,
                "additive_flag": 0,
                "salt_flag": 0,
                "phase_flag": 0,
            },
            "test": {
                "test_origin": "literature",
                "temperature_K": 313.15,
                "co2_vol_pct": co2_vol,
                "co2_partial_kPa": pco2,
                "total_pressure_kPa": total_pressure_kPa,
                "gas_flow": None,
                "liquid_volume": liquid_volume_L,
                "gas_liquid_ratio": None,
                "initial_loading": 0.0,
                "rich_loading": float(p["loading"]),
                "lean_loading": None,
            },
            "performance": [{
                "metric_name": "equilibrium_loading",
                "value": float(p["loading"]),
                "unit": "mol_CO2/mol_amine",
                "value_original": float(p["loading"]),
                "unit_original": "mol CO2/mol amine",
                "metric_definition": (
                    f"Table {p['table']} 40 C column group; P_CO2={pco2} kPa; "
                    f"total pressure {total_pressure_kPa} kPa (methods); fresh solution"
                ),
                "is_derived": 0,
            }],
            "evidence": [
                {"field": "temperature_K", "type": "Explicit", "note": "table 40 C header"},
                {"field": "co2_partial_kPa", "type": "Explicit", "note": "p/kPa column"},
                {"field": "total_pressure_kPa", "type": "Explicit", "note": "methods ~180 kPa"},
                {"field": "co2_vol_pct", "type": "Derived", "note": "P_CO2/180*100"},
                {"field": "initial_loading", "type": "Contextual", "note": "fresh solution"},
                {"field": "wt_a", "type": "Explicit", "note": "table caption"},
                {"field": "water_wt", "type": "Derived", "note": "100 - total amine"},
                {"field": "equilibrium_loading", "type": "Explicit", "note": "loading column"},
                {"field": "source.excerpt", "type": "Explicit", "note": "raw table row"},
            ],
        }
        records.append(record)
    return records


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    result = parse_vle_tables(args.pdf)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("counts:", result["counts"])
        for t in result["tables"]:
            print(t["number"], t["recipe"], "groups=", len(t["groups"]), "rows=", t["data_rows"], "points=", t["points"])
        for p in result["selected_40C_lowP"][:40]:
            print(p["table"], p["group"], p["temperature_C"], p["p_CO2_kPa"], p["loading"])


if __name__ == "__main__":
    main()
