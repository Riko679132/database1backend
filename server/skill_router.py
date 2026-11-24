"""Dynamic skill knowledge routing for paper extraction.

The full knowledge base is intentionally not stuffed into every prompt. This
module scores the paper text against a small keyword map, selects up to three
knowledge modules, and returns their content plus hashes for the snapshot.
"""
from __future__ import annotations

import hashlib
from pathlib import Path

from .settings import ROOT

SKILL_ROOT = ROOT / ".qoder" / "skills" / "amine-carbon-capture-literature-reader"
SKILL_FILE = SKILL_ROOT / "SKILL.md"

MODULES: dict[str, dict] = {
    "amine_properties": {
        "path": "knowledge/amine_properties.md",
        "keywords": [
            "monoethanolamine", "mea", "piperazine", "pz", "amp", "mdea", "dea",
            "dga", "tea", "amine", "alkanolamine", "solvent", "cas",
        ],
    },
    "amine_chemistry": {
        "path": "knowledge/amine_chemistry.md",
        "keywords": [
            "carbamate", "bicarbonate", "carbonate", "speciation", "nmr", "ftir",
            "proton", "reaction", "mechanism", "kinetics", "degradation",
        ],
    },
    "mixed_amine_systems": {
        "path": "knowledge/mixed_amine_systems.md",
        "keywords": [
            "blend", "mixed amine", "binary", "ternary", "ratio", "piperazine",
            "promoter", "co-solvent", "cosolvent", "water-lean", "nonaqueous",
        ],
    },
    "co2_equilibrium": {
        "path": "knowledge/co2_equilibrium.md",
        "keywords": [
            "vle", "vapor-liquid", "vapour-liquid", "equilibrium", "solubility",
            "partial pressure", "henry", "loading", "isotherm", "co2 partial",
        ],
    },
    "thermodynamic_models": {
        "path": "knowledge/thermodynamic_models.md",
        "keywords": [
            "kent-eisenberg", "kent eisenberg", "deshmukh", "enrtl", "electrolyte-nrtl",
            "pitzer", "thermodynamic model", "equation of state", "aspen", "simulation",
            "model prediction", "regression",
        ],
    },
    "experimental_methods": {
        "path": "knowledge/experimental_methods.md",
        "keywords": [
            "bubble column", "wetted wall", "stirred cell", "packed column", "pilot",
            "calorimeter", "calorimetry", "mass transfer", "absorption rate",
            "desorption rate", "kinetics", "stopped-flow", "apparatus",
        ],
    },
    "physical_properties": {
        "path": "knowledge/physical_properties.md",
        "keywords": [
            "density", "viscosity", "surface tension", "heat capacity",
            "thermal conductivity", "vapor pressure", "vapour pressure",
            "regeneration energy", "cyclic capacity", "degradation",
        ],
    },
}

DEFAULT_MODULES = ["amine_properties", "amine_chemistry"]
MAX_MODULES = 4
MAX_CHARS_PER_MODULE = 4200
MAX_CONTEXT_CHARS = 15000


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes()) if path.exists() else ""


def _score(text: str, keywords: list[str]) -> int:
    low = text.lower()
    return sum(low.count(k.lower()) for k in keywords)


def select_modules(text: str, title: str = "") -> list[dict]:
    """Select up to three knowledge modules based on keyword scores."""
    hay = f"{title}\n{text}"
    scored: list[tuple[int, str]] = []
    for mid, meta in MODULES.items():
        s = _score(hay, meta["keywords"])
        if s > 0:
            scored.append((s, mid))
    scored.sort(reverse=True)
    chosen = [mid for _, mid in scored[:MAX_MODULES]]
    for mid in DEFAULT_MODULES:
        if len(chosen) >= 2:
            break
        if mid not in chosen:
            chosen.append(mid)
    out = []
    for mid in chosen:
        path = SKILL_ROOT / MODULES[mid]["path"]
        data = path.read_bytes() if path.exists() else b""
        out.append(
            {
                "id": mid,
                "path": MODULES[mid]["path"],
                "sha256": _sha256_bytes(data),
                "chars": len(data.decode("utf-8", errors="ignore")),
                "score": next((s for s, m in scored if m == mid), 0),
                "selection": "keyword" if any(m == mid for _, m in scored) else "default",
            }
        )
    return out


def build_context(modules: list[dict]) -> str:
    """Load and truncate the selected modules for the prompt."""
    parts: list[str] = []
    total = 0
    for m in modules:
        path = SKILL_ROOT / m["path"]
        if not path.exists():
            continue
        body = path.read_text(encoding="utf-8", errors="ignore")
        body = body[:MAX_CHARS_PER_MODULE]
        block = f"\n### 知识模块：{m['id']} (sha256={m['sha256'][:12]})\n{body}\n"
        if total + len(block) > MAX_CONTEXT_CHARS:
            break
        parts.append(block)
        total += len(block)
    return "".join(parts)


def build_rule_context(modules: list[dict]) -> str:
    """Compact callable-rule list for the modules selected for this paper."""
    from . import rules

    ids = rules.rules_for_modules([m["id"] for m in modules if m.get("id")])
    if not ids:
        return ""
    lines = [f"- {rid}: {rules.RULES_BY_ID[rid]['name']}" for rid in ids]
    return (
        "【本次可用推理规则】（仅用于检查证据、单位、边界和常见陷阱；"
        "不得用规则补造论文没有的数值）\n" + "\n".join(lines)
    )


def skill_manifest() -> dict:
    """Version information for the Skill and its selected knowledge files."""
    return {
        "skill_path": SKILL_FILE.relative_to(ROOT).as_posix() if SKILL_FILE.exists() else "",
        "skill_sha256": _sha256_file(SKILL_FILE),
        "skill_version": "phase2",
    }


def prompt_fingerprint(system: str, user: str) -> dict:
    return {
        "system_sha256": _sha256_bytes(system.encode("utf-8")),
        "user_sha256": _sha256_bytes(user.encode("utf-8")),
        "combined_sha256": _sha256_bytes((system + "\n" + user).encode("utf-8")),
    }
