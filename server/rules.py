"""Callable expert rules used by the B-stage reasoning chain.

This is a registry, not a second inference engine. Each rule documents its
scope, inputs, formula/logic, output and source; the executable part remains in
the existing modules (units.py, extract.py, provenance.py, VLE/reference
profiles, OCR gate).
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from .settings import ROOT

RULES: list[dict] = [
    {
        "rule_id": "R-EVD-01",
        "name": "Explicit paper evidence",
        "category": "evidence",
        "scope": "a value stated verbatim in text, table or caption",
        "preconditions": ["loc_label and excerpt recorded"],
        "inputs": ["field", "value", "excerpt"],
        "logic": "keep the paper value; attach loc_type/loc_label/excerpt",
        "outputs": ["evidence_type=Explicit"],
        "knowledge": "validation/evidence_classification.md",
        "exceptions": ["a value only inferred from surrounding text is Contextual, not Explicit"],
    },
    {
        "rule_id": "R-EVD-02",
        "name": "Contextual evidence",
        "category": "evidence",
        "scope": "a value fixed by an explicit method/context sentence without a standalone row",
        "preconditions": ["supporting context sentence quoted"],
        "inputs": ["field", "value", "context"],
        "logic": "accept as Contextual only when the context uniquely fixes the value",
        "outputs": ["evidence_type=Contextual"],
        "knowledge": "validation/evidence_classification.md",
        "exceptions": ["two plausible contexts -> Unknown/null"],
    },
    {
        "rule_id": "R-EVD-03",
        "name": "Derived evidence",
        "category": "evidence",
        "scope": "a value computed by a declared formula from explicit inputs",
        "preconditions": ["all formula inputs have evidence", "formula recorded"],
        "inputs": ["formula", "inputs"],
        "logic": "recompute and compare; store inputs, formula, units and result",
        "outputs": ["evidence_type=Derived"],
        "knowledge": "formulas/concentration_conversion.md",
        "exceptions": ["missing density/concentration blocks mol/L -> wt% conversion"],
    },
    {
        "rule_id": "R-EVD-04",
        "name": "Assumed evidence",
        "category": "evidence",
        "scope": "a professional assumption not stated by the paper",
        "preconditions": ["assumption and reason recorded"],
        "inputs": ["field", "assumption", "reason"],
        "logic": "never upgrade an Assumed required field to L2",
        "outputs": ["evidence_type=Assumed", "qc must remain L3 or lower"],
        "knowledge": "validation/evidence_classification.md",
        "exceptions": ["none for required fields"],
    },
    {
        "rule_id": "R-EVD-05",
        "name": "Unknown evidence",
        "category": "evidence",
        "scope": "the paper does not determine the field",
        "preconditions": [],
        "inputs": ["field"],
        "logic": "keep null; do not fill from convention or external memory",
        "outputs": ["evidence_type=Unknown", "value=null"],
        "knowledge": "validation/evidence_classification.md",
        "exceptions": ["none"],
    },
    {
        "rule_id": "R-DET-01",
        "name": "CO2 partial pressure from gas composition",
        "category": "deterministic",
        "scope": "ideal gas mixture with stated total pressure",
        "preconditions": ["co2_vol_pct is not null", "total_pressure_kPa is not null"],
        "inputs": ["co2_vol_pct", "total_pressure_kPa"],
        "logic": "P_CO2 = co2_vol_pct / 100 * total_pressure_kPa",
        "outputs": ["co2_partial_kPa"],
        "knowledge": "formulas/partial_pressure.md",
        "exceptions": ["do not assume 1 atm when total pressure is absent", "dry/wet basis must be stated"],
    },
    {
        "rule_id": "R-DET-02",
        "name": "Recipe mass balance",
        "category": "deterministic",
        "scope": "aqueous monoamine or two-component amine recipe",
        "preconditions": ["wt_a is not null"],
        "inputs": ["wt_a", "wt_b", "water_wt"],
        "logic": "total_amine = wt_a + wt_b; water = 100 - total_amine; sum must be 100 +/- 0.1",
        "outputs": ["total_amine_wt", "water_wt"],
        "knowledge": "formulas/mass_balance.md",
        "exceptions": ["additive/salt/two-phase systems are out of scope"],
    },
    {
        "rule_id": "R-DET-03",
        "name": "Rate unit normalization",
        "category": "deterministic",
        "scope": "molar rate with convertible amine/solution basis and time unit",
        "preconditions": ["original value and unit recorded"],
        "inputs": ["value_original", "unit_original"],
        "logic": "apply 10^n/mmol/umol scale and time conversion; keep original values",
        "outputs": ["value", "unit", "unit_normalization"],
        "knowledge": "validation/unit_validation.md",
        "exceptions": ["mol solution basis or unknown basis is blocked"],
    },
    {
        "rule_id": "R-DET-04",
        "name": "Blocked unit conversion",
        "category": "deterministic",
        "scope": "rate basis needs density/concentration that the paper does not provide",
        "preconditions": ["basis is mol_solution/unknown/L without density"],
        "inputs": ["unit_original"],
        "logic": "leave the original value; flag conversion blocked",
        "outputs": ["unit_normalization.status=blocked"],
        "knowledge": "formulas/concentration_conversion.md",
        "exceptions": ["never invent a density"],
    },
    {
        "rule_id": "R-DET-05",
        "name": "Pressure consistency",
        "category": "deterministic",
        "scope": "a point with CO2 partial pressure and total pressure",
        "preconditions": ["co2_partial_kPa is not null", "total_pressure_kPa is not null"],
        "inputs": ["co2_partial_kPa", "total_pressure_kPa"],
        "logic": "require 0 <= P_CO2 <= P_total; detailed water-vapour balance is R-DET-06",
        "outputs": ["reasoning check status"],
        "knowledge": "formulas/partial_pressure.md",
        "exceptions": ["a stated total pressure inconsistent with P_CO2 is flagged, not silently adjusted"],
    },
    {
        "rule_id": "R-DET-06",
        "name": "Water vapour and dry/wet gas balance",
        "category": "deterministic",
        "scope": "gas composition with a declared wet/dry basis, P_H2O, or water activity",
        "preconditions": ["gas_basis or P_H2O/y_H2O/water_activity is stated"],
        "inputs": ["gas_basis", "co2_vol_pct", "p_h2o_kPa", "y_h2o", "water_activity",
                   "co2_partial_kPa", "total_pressure_kPa", "temperature_K"],
        "logic": (
            "wet: P_CO2=y_CO2,wet*P_total; dry: P_CO2=y_CO2,dry*(P_total-P_H2O); "
            "dry without P_H2O -> blocked, no P_CO2; P_H2O from pure water only with "
            "water activity or a verified model"
        ),
        "outputs": ["gas-phase status", "water_vapour_check", "derived P_CO2 or blocked"],
        "knowledge": "formulas/water_vapor.md",
        "exceptions": [
            "do not use pure-water saturation pressure for an amine solution without water activity",
            "missing water-vapour data -> not_assessable, not a rejection",
        ],
    },
    {
        "rule_id": "R-EXP-01",
        "name": "Context resolves a condition",
        "category": "expert_judgement",
        "scope": "fresh solvent, pure CO2, atmospheric test, one-column table context",
        "preconditions": ["the context sentence is quoted"],
        "inputs": ["context", "field"],
        "logic": "propose the condition as Contextual; deterministic checks and evidence verification still apply",
        "outputs": ["candidate field value with evidence_type=Contextual"],
        "knowledge": "knowledge/experimental_methods.md",
        "exceptions": ["do not turn a convention into a paper fact"],
    },
    {
        "rule_id": "R-EXP-02",
        "name": "Assumption stays an assumption",
        "category": "expert_judgement",
        "scope": "professional default used to interpret a paper",
        "preconditions": ["assumption is explicit"],
        "inputs": ["assumption", "reason"],
        "logic": "mark Assumed and forbid L2 for required fields",
        "outputs": ["evidence_type=Assumed", "qc<=L3"],
        "knowledge": "validation/evidence_classification.md",
        "exceptions": ["not applicable to non-required descriptive fields"],
    },
    {
        "rule_id": "R-XSEC-01",
        "name": "Cross-section VLE table association",
        "category": "expert_judgement",
        "scope": "multi-column table with repeated t/p/loading groups",
        "preconditions": ["table header coordinates and paper profile available"],
        "inputs": ["header groups", "row coordinates", "paper profile"],
        "logic": "assign each numeric token to its column group, carry temperature down, keep the row excerpt",
        "outputs": ["deterministic VLE records"],
        "knowledge": "knowledge/co2_equilibrium.md",
        "exceptions": ["no profile -> needs_profile, select 0; never apply another paper's apparatus constants"],
    },
    {
        "rule_id": "R-XSEC-02",
        "name": "Scattered reference-row association",
        "category": "expert_judgement",
        "scope": "a baseline recipe/performance split across table, methods and results",
        "preconditions": ["all profile regex evidence found"],
        "inputs": ["recipe regex", "temperature/pressure regex", "performance regex"],
        "logic": "collect the pieces only when every declared evidence anchor matches",
        "outputs": ["reference-row record"],
        "knowledge": "knowledge/experimental_methods.md",
        "exceptions": ["any missing anchor -> no record"],
    },
    {
        "rule_id": "R-XSEC-03",
        "name": "Methods condition profile",
        "category": "expert_judgement",
        "scope": "test conditions stated in methods but absent from a data table",
        "preconditions": ["declared evidence phrases found"],
        "inputs": ["method text", "profile conditions"],
        "logic": "fill only missing condition fields and record the method evidence",
        "outputs": ["condition fields with evidence"],
        "knowledge": "knowledge/experimental_methods.md",
        "exceptions": ["never infer an unstated total pressure"],
    },
    {
        "rule_id": "R-QC-01",
        "name": "Simulation isolation",
        "category": "quality_control",
        "scope": "test_origin=simulation",
        "preconditions": [],
        "inputs": ["test_origin"],
        "logic": "force L3, mark performance is_derived=1, never enter L1/L2",
        "outputs": ["qc_level=L3", "simulation_data tag"],
        "knowledge": "validation/consistency_check.md",
        "exceptions": ["60 wt% simulation is allowed but still L3"],
    },
    {
        "rule_id": "R-QC-02",
        "name": "Metric semantics",
        "category": "quality_control",
        "scope": "metric label contradicts unit, sign or definition",
        "preconditions": ["performance value/unit present"],
        "inputs": ["metric_name", "unit", "value", "metric_definition"],
        "logic": "downgrade to L3 and record the mismatch",
        "outputs": ["qc_level=L3", "metric_semantics_downgrade"],
        "knowledge": "validation/consistency_check.md",
        "exceptions": ["do not silently rename the metric"],
    },
    {
        "rule_id": "R-INF-01",
        "name": "Insufficient evidence",
        "category": "quality_control",
        "scope": "a required field is null after all rules",
        "preconditions": ["required field missing"],
        "inputs": ["temperature_K", "co2_vol_pct", "initial_loading"],
        "logic": "keep null, mark incomplete/L3, list the missing field",
        "outputs": ["qc_level=L3", "incomplete_flag"],
        "knowledge": "validation/consistency_check.md",
        "exceptions": ["information shortage is not a negative label"],
    },
    {
        "rule_id": "R-OCR-01",
        "name": "OCR quality gate",
        "category": "quality_control",
        "scope": "page text obtained by RapidOCR",
        "preconditions": ["page rendered and OCR result recorded"],
        "inputs": ["ocr confidence", "native text", "critical scientific fields"],
        "logic": "pass normal pages; send low-confidence/conflicting pages to review; fail closed when OCR text is unusable",
        "outputs": ["ocr_gate decision per page"],
        "knowledge": "knowledge/experimental_methods.md",
        "exceptions": ["confidence is not a calibrated probability"],
    },
    {
        "rule_id": "R-MAN-01",
        "name": "A->B manifest identity",
        "category": "quality_control",
        "scope": "paper handoff from A to B",
        "preconditions": ["manifest_version supported"],
        "inputs": ["paper_id", "doi", "pdf.sha256", "si.sha256"],
        "logic": "validate schema, path containment and hashes before parsing",
        "outputs": ["manifest validation result"],
        "knowledge": "docs/PHASE5_MANIFEST.md",
        "exceptions": ["missing DOI/SI is allowed; hash mismatch is fatal"],
    },
]

RULES_BY_ID = {r["rule_id"]: r for r in RULES}

MODULE_RULES = {
    "amine_properties": ["R-EVD-01", "R-DET-02"],
    "amine_chemistry": ["R-EVD-02", "R-QC-02"],
    "mixed_amine_systems": ["R-DET-02"],
    "co2_equilibrium": ["R-DET-01", "R-DET-05", "R-XSEC-01"],
    "thermodynamic_models": ["R-QC-01", "R-QC-02"],
    "experimental_methods": ["R-EXP-01", "R-XSEC-02", "R-XSEC-03", "R-OCR-01"],
    "physical_properties": ["R-EVD-03"],
}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else ""


def catalog_manifest() -> dict:
    """Stable version block for the snapshot."""
    skill_root = ROOT / ".qoder" / "skills" / "amine-carbon-capture-literature-reader"
    knowledge = {}
    for rule in RULES:
        rel = rule["knowledge"]
        for candidate in (skill_root / rel, skill_root / rel.rstrip("/"), ROOT / rel):
            if candidate.is_file():
                knowledge[rel] = _sha(candidate)
                break
    payload = {"rule_ids": [r["rule_id"] for r in RULES], "knowledge_sha256": knowledge}
    digest = hashlib.sha256(
        (",".join(payload["rule_ids"]) + "|" + ";".join(
            f"{k}={v}" for k, v in sorted(payload["knowledge_sha256"].items())
        )).encode()
    ).hexdigest()
    return {
        "rule_set_version": "phase5-1.0",
        "rule_count": len(RULES),
        "rule_ids": payload["rule_ids"],
        "knowledge_files": payload["knowledge_sha256"],
        "sha256": digest,
    }


def rules_for_modules(module_ids: list[str]) -> list[str]:
    out = []
    for mid in module_ids:
        for rid in MODULE_RULES.get(mid, []):
            if rid not in out:
                out.append(rid)
    return out
