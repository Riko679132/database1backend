"""LLM 结构化抽取：论文文本 → raw_agent 记录（与 validate.py 的字段完全对齐）。"""
from __future__ import annotations

import csv
import json
import re
from pathlib import Path

from . import gas_phase, llm, provenance, skill_router, table_grid, units
from .settings import ROOT

MAX_CHARS = 110_000
WHITELIST = ROOT / "data" / "compound_whitelist.csv"

METRIC_ENUM = [
    "equilibrium_loading",
    "cyclic_capacity",
    "cyclic_capacity_volumetric",
    "regeneration_energy",
    "regeneration_heat",
    "regeneration_efficiency",
    "initial_absorption_rate",
    "initial_desorption_rate",
    "absorption_rate_volumetric",
    "absorption_amount_volumetric",
    "co2_removal_efficiency",
    "cost_per_tonne_co2",
    "iron_solubility",
    "pka",
    "model_prediction_deviation",
    "annual_energy_consumption_reduction",
    "aard_equilibrium_co2_partial_pressure",
]

BASE_SYSTEM_PROMPT = f"""你是水相胺 CO2 捕集文献的结构化数据抽取器。
只依据给定的论文文本抽取，禁止使用外部知识补全数值、结构或文献信息。

研究边界（不满足则不输出该配方）：
1) 水相单胺或双组分复配胺，总胺 20–50 wt%；
2) 无添加剂、无盐、无两相、无浆料。

输出必须是 JSON 对象，形如 {{"records": [...]}}，不要任何解释文字。
每条记录结构：
{{
  "source": {{"doi": null, "title": null, "authors": null, "year": null, "journal": null,
              "loc_type": "table|text|figure", "loc_label": "页码/表号/章节", "excerpt": "支撑本条的原文片段，<=400字"}},
  "recipe": {{"recipe_type": "mono|binary",
              "amine_a": {{"standard_name": "...", "cas_no": "..."}},
              "amine_b": null 或 {{"standard_name": "...", "cas_no": "..."}},
              "wt_a": null, "wt_b": null, "water_wt": null, "total_amine_wt": null,
              "additive_flag": 0, "salt_flag": 0, "phase_flag": 0}},
  "test": {{"temperature_K": null, "co2_vol_pct": null, "co2_partial_kPa": null,
            "total_pressure_kPa": null, "gas_basis": "wet|dry|unknown",
            "p_h2o_kPa": null, "y_h2o": null, "water_activity": null,
            "other_partial_kPa": null,
            "gas_flow": null, "liquid_volume": null,
            "gas_liquid_ratio": null, "initial_loading": null, "rich_loading": null, "lean_loading": null}},
  "performance": [{{"metric_name": "...", "value": null, "unit": null, "value_original": null,
                    "unit_original": null, "metric_definition": null, "is_derived": 0}}],
  "evidence": [{{"field": "temperature_K", "type": "Explicit|Contextual|Derived|External|Assumed|Unknown", "note": "依据"}}]
}}

规则：
- 单位统一：温度 K；CO2 体积分数 vol%；压力 kPa；负载 mol CO2/mol amine；同时把原文数值写入 value_original。
- 缺失一律 null，不得猜测，不得从其他文献补。
- 胺只能取自给定白名单（按 CAS 或名称匹配）；白名单外的胺，整条不输出。
- 原文只给 molality（mol/kg 溶剂）且给出分子量时可换算 wt%；只给 mol/L 且未给溶液密度时，该配方不输出。
- 同一论文中每个「配方 × 工况」组合输出一条记录；不要输出重复记录。
- metric_name 只能取以下枚举之一：{", ".join(METRIC_ENUM)}。
- excerpt 必须逐字来自论文（保留原文语言），至少 30 个字符，并包含表号/行标签或条件句；不得改写或概括。
- loc_label 必须写页码/表号/章节；loc_type 只能是 table/text/figure。
- evidence 必须覆盖 temperature_K、co2_vol_pct、initial_loading、recipe 的 wt_a/wt_b/water_wt 和每个 performance 指标。Explicit=论文直接写；Contextual=论文上下文明确确定；Derived=由明确数据按公式算出；External=外部可靠来源；Assumed=专业假设；Unknown=无法确定。note 控制在 20 字以内；同一表格内重复字段可复用同一 note。
- 关键字段如果只能靠 Assumed 或 Unknown 得到，保留 null，不要为了凑 L2 强行填值。
- evidence 与值必须一致：Explicit/Contextual 必须有值；值为 null 时 evidence 必须是 Unknown。
- 若方法明确使用 pure CO2（如 "pure CO2"），co2_vol_pct=100.0；若明确使用 15% CO2 in N2，co2_vol_pct=15.0。不要因为没写数字就留空。
- 若方法明确使用 fresh solution / unloaded sorbent 开始批次吸收，initial_loading=0.0，evidence=Contextual；若是循环实验的 lean/rich loading，按论文报告值，不要默认 0。
- 若论文报告的是 rich loading / maximum capacity / equilibrium loading，把同一数值同步写入 test.rich_loading；若论文明确报告 lean loading，填入 test.lean_loading；不要为同一个数值编造第二个性能指标。
- VLE 表必须逐行输出：每一行 (T, P_CO2, loading) 都是一条独立记录，即使配方相同、温度相同也不能合并、平均或只取第一行。表格有 N 行就输出 N 条；跨页续表要合并，不要漏行。
- VLE 表只给 CO2 分压时，co2_partial_kPa 填表值；total_pressure_kPa 若未给则 null；co2_vol_pct 不能由未给出的总压/气相组成确定时留 null，不要猜。
- 气相组成必须标明 gas_basis：wet=湿基，dry=干基，unknown=论文未说明。不要默认干基或湿基。
- 若干基且论文给出 y_CO2,dry 和 P_total，但没有 P_H2O，不得用 P_total 直接派生 P_CO2；co2_partial_kPa 保持 null，gas_basis 写 dry。
- 若论文给出 P_H2O 或水蒸气摩尔分数，原样写入 p_h2o_kPa / y_h2o，并保留原文证据；不要用纯水饱和蒸气压替代胺溶液上方的水蒸气分压。
- 只有论文明确给出水活度或适用模型参数时，才允许计算溶液 P_H2O；否则保持 null。
- VLE 平衡点若方法明确使用 fresh/unloaded 溶液，initial_loading=0.0（Contextual）；若没有说明，留 null。
- 速率类指标必须保留论文原始数值和原始单位：value_original 写原值，unit_original 写原单位（包括 10^-5、mmol、min 等前缀/时间单位）；不要自行把前缀乘进 value 后又不记录。标准化由程序完成。
- 先扫描全文所有表格和数据段，再判断是否为空；不要只看标题、摘要或主要体系。
- 论文可能以非水体系、非白名单胺或 3.0 mol/L 体系为主，但同一表格中可能含有一行 30 wt% MEA（或其他白名单胺）的水相参比数据。只要该行满足边界，就必须输出该行，不能因为论文其他部分超边界而整篇返回空。
- 同一表格中，只输出 wt% 且配方闭合的行；mol/L 且无密度的行不输出，但不要因此丢掉同表的 wt% 行。
- 若本文确实没有任何符合边界的实验数据，才输出 {{"records": []}}。"""


def build_system_prompt(knowledge_context: str, rule_context: str = "") -> str:
    if not knowledge_context.strip() and not rule_context.strip():
        return BASE_SYSTEM_PROMPT
    return (
        BASE_SYSTEM_PROMPT
        + "\n\n【本次动态加载的领域知识】\n"
        + knowledge_context
        + ("\n" + rule_context if rule_context else "")
        + "\n【知识使用规则】\n"
        + "- 知识模块只用于判断单位、机理、边界和常见陷阱，不得把知识库中的数值当作本论文数据。\n"
        + "- 如果论文需要知识库未覆盖的判断，保留 null 并在 evidence 中标记 Unknown，不要凭模型记忆编造。\n"
    )


class SkipRecord(Exception):
    """该条记录不进 raw_agent（例如未知化合物），需在预览中提示。"""


def load_compounds() -> list[dict]:
    rows: list[dict] = []
    if WHITELIST.exists():
        with WHITELIST.open(encoding="utf-8-sig", newline="") as fh:
            for row in csv.DictReader(fh):
                if not row.get("standard_name"):
                    continue
                rows.append(
                    {
                        "standard_name": row["standard_name"].strip(),
                        "cas_no": (row.get("cas_no") or "").strip(),
                        "smiles": (row.get("smiles") or "").strip(),
                        "inchikey": (row.get("inchikey") or "").strip(),
                        "amine_class": (row.get("amine_class") or "").strip(),
                    }
                )
    return rows


def _index(compounds: list[dict]) -> tuple[dict, dict]:
    by_cas, by_name = {}, {}
    for c in compounds:
        if c["cas_no"]:
            by_cas[c["cas_no"]] = c
        by_name[c["standard_name"].upper()] = c
    return by_cas, by_name


def resolve(compounds: list[dict], obj: dict | None) -> dict | None:
    if not obj:
        return None
    by_cas, by_name = _index(compounds)
    for raw in (obj.get("cas_no"), obj.get("standard_name"), obj.get("name")):
        if not raw:
            continue
        key = str(raw).strip()
        hit = by_cas.get(key) or by_name.get(key.upper())
        if hit:
            return hit
    return None


def _num(value) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    match = re.search(r"-?\d+(?:\.\d+)?", text)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def doi_from_filename(pdf: Path) -> str | None:
    stem = pdf.stem
    if not stem.startswith("10."):
        return None
    parts = stem.split("_")
    if len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    return None


def _truncate(text: str) -> tuple[str, bool]:
    if len(text) <= MAX_CHARS:
        return text, False
    head = text[: int(MAX_CHARS * 0.25)]
    tail = text[-int(MAX_CHARS * 0.75) :]
    return head + "\n\n[... 中间部分因长度限制省略 ...]\n\n" + tail, True


def extract_paper(
    text: str,
    *,
    pdf: Path,
    compounds: list[dict],
    log=lambda _msg: None,
    batch_id: str | None = None,
    parsed_text_path: Path | None = None,
    parse_mode: str = "text",
    ocr_meta: dict | None = None,
    si_meta: dict | None = None,
    si_text: str | None = None,
    chart_meta: dict | None = None,
    table_context: str | None = None,
) -> tuple[list[dict], dict]:
    body, truncated = _truncate(text)
    if truncated:
        log(f"  文本长度 {len(text)} 字符，超限已截断至 {MAX_CHARS}")

    modules = skill_router.select_modules(text, pdf.stem)
    knowledge_context = skill_router.build_context(modules)
    rule_context = skill_router.build_rule_context(modules)
    system_prompt = build_system_prompt(knowledge_context, rule_context)
    log("  知识路由：" + ", ".join(f"{m['id']}({m['selection']})" for m in modules))

    meta = {
        "file": pdf.name,
        "doi_guess": doi_from_filename(pdf),
    }
    if table_context is None:
        table_context, table_pages = table_grid.build_table_context(pdf)
    else:
        table_pages = []
    if table_context:
        log(f"  表格坐标重建：{table_pages or 'provided'}，{len(table_context)} 字符")
    whitelist = [
        {"standard_name": c["standard_name"], "cas_no": c["cas_no"], "amine_class": c["amine_class"]}
        for c in compounds
    ]
    si_block = f"【补充材料（SI）】\n{si_text}\n" if si_text else ""
    user = (
        f"【文献元信息】文件名：{meta['file']}；文件名推测 DOI：{meta['doi_guess'] or '未知'}\n"
        f"【化合物白名单】{json.dumps(whitelist, ensure_ascii=False)}\n"
        f"{table_context}"
        f"{si_block}"
        f"【论文文本】\n{body}"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user},
    ]
    content = llm.chat(messages, json_mode=True, max_tokens=8192)
    records = _parse_records(content)
    if records is None:
        log("  模型输出不是合法 JSON，重试一次")
        messages.append({"role": "assistant", "content": content[:2000]})
        messages.append({"role": "user", "content": "上面的输出不是合法 JSON。请只输出 {\"records\": [...]} 形式的 JSON。"})
        content = llm.chat(messages, json_mode=True, max_tokens=8192)
        records = _parse_records(content)
    if records is None:
        raise llm.LLMError("模型两次输出均无法解析为 JSON")

    return records, {
        "truncated": truncated,
        "modules": modules,
        "skill": skill_router.skill_manifest(),
        "prompt": skill_router.prompt_fingerprint(system_prompt, user),
        "model": llm.config_snapshot(),
        "model_params": {"temperature": 0.1, "max_tokens": 8192, "json_mode": True},
        "parse_mode": parse_mode,
        "ocr": ocr_meta,
        "si": si_meta,
        "chart": chart_meta,
        "raw_output": content,
        "batch_id": batch_id,
        "parsed_text_path": parsed_text_path.as_posix() if parsed_text_path else None,
        "table_context_pages": table_pages,
        "table_context_chars": len(table_context or ""),
    }


def _salvage_records(text: str) -> list[dict]:
    """Recover complete record objects from a truncated JSON array."""
    marker = text.find('"records"')
    start = text.find("[", marker if marker >= 0 else 0)
    if start < 0:
        return []
    records: list[dict] = []
    depth = 0
    in_str = False
    escape = False
    obj_start = None
    for i in range(start + 1, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue
        if ch == '"':
            in_str = True
        elif ch == "{":
            if depth == 0:
                obj_start = i
            depth += 1
        elif ch == "}":
            if depth > 0:
                depth -= 1
                if depth == 0 and obj_start is not None:
                    try:
                        records.append(json.loads(text[obj_start : i + 1]))
                    except ValueError:
                        pass
                    obj_start = None
    return records


def _parse_records(content: str) -> list[dict] | None:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    try:
        data = json.loads(text)
    except ValueError:
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            try:
                data = json.loads(text[start : end + 1])
            except ValueError:
                data = None
        else:
            data = None
        if data is None:
            salvaged = _salvage_records(text)
            return salvaged or None
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        records = data.get("records")
        if isinstance(records, list):
            return records
    return None


def normalize(
    raw: dict,
    *,
    compounds: list[dict],
    pdf: Path,
    pdf_hash: str,
    batch_id: str,
    qc_level: str | None = None,
    qc_reason: str | None = None,
    snapshot_path: Path | None = None,
    snapshot_hash: str | None = None,
    extraction_method: str = "llm",
) -> dict:
    recipe_raw = raw.get("recipe") or {}
    amine_a = resolve(compounds, recipe_raw.get("amine_a"))
    if not amine_a:
        raise SkipRecord(f"胺 A 不在白名单：{(recipe_raw.get('amine_a') or {}).get('standard_name')}")
    amine_b_raw = recipe_raw.get("amine_b")
    amine_b = resolve(compounds, amine_b_raw) if amine_b_raw else None
    if amine_b_raw and not amine_b:
        raise SkipRecord(f"胺 B 不在白名单：{(amine_b_raw or {}).get('standard_name')}")

    notes: list[str] = []
    wt_a = _num(recipe_raw.get("wt_a"))
    wt_b = _num(recipe_raw.get("wt_b")) if amine_b else None
    total = _num(recipe_raw.get("total_amine_wt"))
    water = _num(recipe_raw.get("water_wt"))
    if total is None and wt_a is not None:
        total = round(wt_a + (wt_b or 0), 4)
        notes.append("total_amine_wt_derived")
    if water is None and total is not None:
        water = round(100 - total, 4)
        notes.append("water_wt_derived_by_mass_balance")

    test_raw = raw.get("test") or {}
    test = {
        "test_origin": "literature",
        "batch_id": batch_id,
        "temperature_K": _num(test_raw.get("temperature_K")),
        "co2_vol_pct": _num(test_raw.get("co2_vol_pct")),
        "co2_partial_kPa": _num(test_raw.get("co2_partial_kPa")),
        "total_pressure_kPa": _num(test_raw.get("total_pressure_kPa")),
        "gas_basis": gas_phase.normalize_basis(test_raw.get("gas_basis")),
        "p_h2o_kPa": _num(test_raw.get("p_h2o_kPa")),
        "y_h2o": _num(test_raw.get("y_h2o")),
        "water_activity": _num(test_raw.get("water_activity")),
        "other_partial_kPa": _num(test_raw.get("other_partial_kPa")),
        "gas_flow": _num(test_raw.get("gas_flow")),
        "liquid_volume": _num(test_raw.get("liquid_volume")),
        "gas_liquid_ratio": _num(test_raw.get("gas_liquid_ratio")),
        "initial_loading": _num(test_raw.get("initial_loading")),
        "rich_loading": _num(test_raw.get("rich_loading")),
        "lean_loading": _num(test_raw.get("lean_loading")),
    }
    gas_result = gas_phase.apply_to_test(test)
    if gas_result.get("applied_to_test"):
        notes.append(f"co2_partial_derived_{gas_result.get('derivation')}")
    elif gas_result.get("status") == "blocked_dry_basis_missing_p_h2o":
        notes.append("co2_partial_not_derived_dry_basis_missing_p_h2o")
    elif gas_result.get("status") == "blocked_basis_unknown":
        notes.append("co2_partial_not_derived_basis_unknown")
    elif gas_result.get("status") == "anomaly":
        notes.append("gas_phase_anomaly")

    performance = []
    for item in raw.get("performance") or []:
        if not isinstance(item, dict):
            continue
        metric = str(item.get("metric_name") or "").strip()
        value = _num(item.get("value"))
        if not metric or value is None:
            continue
        performance.append(
            {
                "metric_name": metric,
                "value": value,
                "unit": item.get("unit"),
                "value_original": _num(item.get("value_original")),
                "unit_original": item.get("unit_original"),
                "error_value": _num(item.get("error_value")),
                "repeat_count": _num(item.get("repeat_count")),
                "metric_definition": item.get("metric_definition"),
                "is_derived": int(item.get("is_derived") or 0),
            }
        )

    for perf in performance:
        res = units.apply_to_performance(perf)
        if res.get("status") == "converted":
            notes.append("rate_unit_normalized")
        elif res.get("status") in ("blocked", "unparsed", "missing_unit"):
            notes.append("rate_unit_conversion_blocked")

    source_raw = raw.get("source") or {}
    try:
        pdf_path = pdf.relative_to(ROOT).as_posix()
    except ValueError:
        pdf_path = pdf.as_posix()
    source = {
        "doi": source_raw.get("doi") or doi_from_filename(pdf),
        "title": source_raw.get("title"),
        "authors": source_raw.get("authors"),
        "year": int(_num(source_raw.get("year")) or 0) or None,
        "journal": source_raw.get("journal"),
        "pdf_path": pdf_path,
        "pdf_hash": pdf_hash,
        "loc_type": source_raw.get("loc_type") or "text",
        "loc_label": source_raw.get("loc_label"),
        "excerpt": source_raw.get("excerpt"),
        "extraction_method": extraction_method,
    }

    if snapshot_path is not None and snapshot_hash:
        test["raw_data_path"] = snapshot_path.as_posix()
        test["raw_data_hash"] = snapshot_hash

    level = qc_level if qc_level in ("L1", "L2", "L3", "L4") else "L3"
    if level == "L2" and not (snapshot_path and snapshot_hash):
        level = "L3"
        qc_reason = ";".join(filter(None, [qc_reason, "L2_without_snapshot_downgraded"]))
    reason = qc_reason or "llm_extraction_no_snapshot"
    if notes:
        reason = ";".join([reason, *notes])

    return {
        "source": source,
        "recipe": {
            "recipe_type": "binary" if amine_b else "mono",
            "amine_a": amine_a,
            "amine_b": amine_b,
            "wt_a": wt_a,
            "wt_b": wt_b,
            "water_wt": water,
            "total_amine_wt": total,
            "additive_flag": int(recipe_raw.get("additive_flag") or 0),
            "salt_flag": int(recipe_raw.get("salt_flag") or 0),
            "phase_flag": int(recipe_raw.get("phase_flag") or 0),
        },
        "test": test,
        "performance": performance,
        "gas_phase": gas_result,
        "qc": {"qc_level": level, "qc_reason": reason},
    }
