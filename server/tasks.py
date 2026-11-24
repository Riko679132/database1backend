"""预设任务注册表：每个任务只调用项目现有脚本，不开放任意命令。"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from collections import Counter
from pathlib import Path

import requests
import yaml

from . import (
    condition_profile,
    excerpt_store,
    extract,
    ocr_gate,
    paper_manifest,
    provenance,
    reasoning,
    reference_case_parser,
    settings,
    vle_table_parser,
)
from .runner import Run, run_script
from .settings import ROOT

EXTRACTIONS = ROOT / "extractions"
PDF_DIR = ROOT / "data" / "raw_pdfs"
CONTROL_DIR = ROOT / "data" / "control"
LEDGER = CONTROL_DIR / "processed_pdfs.json"
TOOLS_PY = ROOT / "tools" / ".venv" / "Scripts" / "python.exe"
CDP = "http://127.0.0.1:9222"

# 检索源：目前仅 Scopus 接入，其余占位（前端置灰）
SEARCH_SOURCES = [
    {"value": "scopus", "label": "Scopus（Elsevier，已接入）"},
    {"value": "sciencedirect", "label": "ScienceDirect 站内检索（未接入）", "disabled": True},
    {"value": "wos", "label": "Web of Science（未接入）", "disabled": True},
    {"value": "pubmed", "label": "PubMed（未接入）", "disabled": True},
    {"value": "scholar", "label": "Google Scholar（未接入）", "disabled": True},
]


def _tools_python() -> str:
    return str(TOOLS_PY) if TOOLS_PY.exists() else "python"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out


def _count_lines(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(encoding="utf-8") as fh:
        return sum(1 for line in fh if line.strip())


# ---------------------------------------------------------------- 处理台账
# 抽取失败的批次不会产生 raw_agent，因此"是否处理过"不能只看 raw_agent；
# 用台账记录每个尝试过的 PDF（含 0 条记录、扫描件、解析失败），避免重复烧 token。


def load_ledger() -> dict:
    if LEDGER.exists():
        try:
            data = json.loads(LEDGER.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except ValueError:
            return {}
    return {}


def mark_processed(pdf: Path, sha: str, status: str, batch_id: str, detail: str | None = None) -> None:
    data = load_ledger()
    data[sha] = {
        "pdf": pdf.name,
        "status": status,
        "batch_id": batch_id,
        "detail": detail,
        "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    CONTROL_DIR.mkdir(parents=True, exist_ok=True)
    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def processed_hashes() -> set[str]:
    hashes: set[str] = set(load_ledger())
    for path in EXTRACTIONS.glob("*/raw_agent.jsonl"):
        for rec in _read_jsonl(path):
            h = (rec.get("source") or {}).get("pdf_hash")
            if h:
                hashes.add(h)
    return hashes


def batch_dir(batch_id: str) -> Path:
    target = (EXTRACTIONS / batch_id).resolve()
    if EXTRACTIONS.resolve() not in target.parents:
        raise ValueError("批次号非法")
    return target


def merged_config_file() -> Path:
    """把 config.yaml 与本地密钥合并成临时配置，供只认 config.yaml 的脚本使用。"""
    path = CONTROL_DIR / "merged_config.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(settings.merged(), allow_unicode=True), encoding="utf-8")
    return path


def _clamp(value, default: int, low: int, high: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(low, min(high, number))


def _pdf_names() -> set[str]:
    return {p.name for p in PDF_DIR.glob("*.pdf")}


def _sanitize_doi(doi: str) -> str:
    return re.sub(r"[^\w.\-]+", "_", doi).strip("_")[:120]


def _record_key(rec: dict) -> tuple:
    r = rec.get("recipe") or {}
    t = rec.get("test") or {}
    a = r.get("amine_a") or {}
    b = r.get("amine_b") or {}
    return (
        (rec.get("source") or {}).get("doi"),
        a.get("standard_name"),
        b.get("standard_name"),
        r.get("wt_a"),
        r.get("wt_b"),
        t.get("temperature_K"),
        t.get("co2_partial_kPa"),
        tuple(sorted(
            (p.get("metric_name"), round(float(p.get("value") or 0), 6))
            for p in rec.get("performance") or []
        )),
    )


def _loading_of(rec: dict) -> float | None:
    for perf in rec.get("performance") or []:
        if perf.get("metric_name") == "equilibrium_loading" and perf.get("value") is not None:
            return float(perf["value"])
    test = rec.get("test") or {}
    for key in ("rich_loading", "lean_loading"):
        if test.get(key) is not None:
            return float(test[key])
    return None


def _same_system(a: dict, b: dict) -> bool:
    ra, rb = a.get("recipe") or {}, b.get("recipe") or {}
    aa, ab = ra.get("amine_a") or {}, rb.get("amine_a") or {}
    if str(aa.get("standard_name") or "").lower() != str(ab.get("standard_name") or "").lower():
        return False
    if ra.get("wt_a") is None or rb.get("wt_a") is None:
        return False
    if abs(float(ra["wt_a"]) - float(rb["wt_a"])) > 0.2:
        return False
    ta, tb = a.get("test") or {}, b.get("test") or {}
    if ta.get("temperature_K") is None or tb.get("temperature_K") is None:
        return False
    return abs(float(ta["temperature_K"]) - float(tb["temperature_K"])) <= 0.1


def _is_vertical_duplicate(candidate: dict, existing: list[tuple]) -> bool:
    for _, rec, _, _ in existing:
        if not _same_system(candidate, rec):
            continue
        pa = (candidate.get("test") or {}).get("co2_partial_kPa")
        pb = (rec.get("test") or {}).get("co2_partial_kPa")
        la, lb = _loading_of(candidate), _loading_of(rec)
        if pa is not None and pb is not None and abs(float(pa) - float(pb)) > 1.0:
            continue
        if la is not None and lb is not None and abs(la - lb) <= 0.02:
            return True
        if pa is not None and pb is not None and abs(float(pa) - float(pb)) <= 1.0 and la is None and lb is None:
            return True
    return False


def _finalize_pair(
    raw: dict,
    rec: dict,
    norm_text: str,
    *,
    context: dict,
    modules: list[dict],
) -> tuple[dict, dict, dict, dict]:
    verification = provenance.verify_record(raw, rec, norm_text)
    level, reason = provenance.decide_qc(rec, verification)
    rec["qc"] = {"qc_level": level, "qc_reason": reason}
    issues = reasoning.consistency_issues(raw, rec)
    if issues:
        reasoning.apply_consistency(rec, issues)
    trace = reasoning.trace_record(
        raw, rec, verification, context=context, modules=modules
    )
    return raw, rec, verification, trace


def _load_si(pdf: Path, manifest: dict | None = None) -> tuple[str | None, dict | None]:
    """Load the A-stage SI handoff through the validated manifest."""
    if manifest is not None:
        return paper_manifest.si_text(manifest)
    doi = extract.doi_from_filename(pdf)
    if not doi:
        return None, None
    base = ROOT / "data" / "raw_si" / _sanitize_doi(doi)
    manifest_path = base / "si_manifest.json"
    if not manifest_path.exists():
        return None, {"status": "not_found"}
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except ValueError:
        return None, {"status": "manifest_invalid", "path": manifest_path.as_posix()}
    texts = []
    files = []
    for f in manifest.get("files") or []:
        parsed = f.get("parsed") or {}
        path = parsed.get("path")
        if path and Path(path).suffix.lower() == ".txt" and Path(path).exists():
            texts.append(Path(path).read_text(encoding="utf-8", errors="ignore"))
        files.append({
            "type": f.get("type"),
            "path": f.get("path"),
            "sha256": f.get("sha256"),
            "parsed": parsed,
        })
    text = "\n\n".join(texts)[:30000]
    return text or None, {
        "status": "loaded" if text else "no_parsed_text",
        "manifest": manifest_path.as_posix(),
        "files": files,
        "chars": len(text),
    }


def cdp_available() -> bool:
    try:
        return requests.get(f"{CDP}/json/version", timeout=2).ok
    except requests.RequestException:
        return False


# ---------------------------------------------------------------- 采集


def task_fetch_elsevier(run: Run) -> dict:
    source = str(run.params.get("source") or "scopus")
    if source != "scopus":
        label = next((s["label"] for s in SEARCH_SOURCES if s["value"] == source), source)
        raise RuntimeError(f"检索源「{label}」尚未接入，当前仅支持 Scopus")
    if not settings.elsevier_key():
        raise RuntimeError("尚未配置 Elsevier API Key")
    cfg = merged_config_file()
    run_script(run, ["scripts/fetch_elsevier.py", "--config", str(cfg)])
    out = PDF_DIR / "elsevier_results.json"
    count = 0
    if out.exists():
        try:
            count = len(json.loads(out.read_text(encoding="utf-8")).get("entries") or [])
        except ValueError:
            count = 0
    return {"source": source, "results_file": out.relative_to(ROOT).as_posix(), "entries": count}


def _prepare_subset(limit: int) -> tuple[Path, list[dict]]:
    src = PDF_DIR / "elsevier_results.json"
    if not src.exists():
        raise RuntimeError("还没有检索结果，请先运行「SciVerse 检索」")
    try:
        entries = json.loads(src.read_text(encoding="utf-8")).get("entries") or []
    except ValueError as exc:
        raise RuntimeError("检索结果文件损坏，请重新检索") from exc
    have = {p.stem.rsplit("_", 1)[0] for p in PDF_DIR.glob("*.pdf") if "_" in p.stem}
    fresh = [e for e in entries if e.get("doi") and _sanitize_doi(e["doi"]) not in have]

    def _oa(entry: dict) -> bool:
        return str(entry.get("openaccess") or "") == "1" or bool(entry.get("openaccessFlag"))

    # 开放获取标记优先，其次按年份新→旧：让「只下载开放获取」尽量有命中
    fresh.sort(
        key=lambda e: (not _oa(e), e.get("publication_year") is None, -(e.get("publication_year") or 0))
    )
    subset = fresh[:limit]
    if not subset:
        raise RuntimeError("检索结果里的文献都已下载过（或没有 DOI）")
    CONTROL_DIR.mkdir(parents=True, exist_ok=True)
    out = CONTROL_DIR / f"elsevier_subset_{time.strftime('%Y%m%d_%H%M%S')}.json"
    out.write_text(json.dumps({"entries": subset}, ensure_ascii=False), encoding="utf-8")
    return out, subset


def _run_fulltext(run: Run, limit: int) -> dict:
    subset_path, subset = _prepare_subset(limit)
    run.log(f"从检索结果中挑出 {len(subset)} 篇待下载（按年份新→旧，跳过已有本地文件）")
    before = _pdf_names()
    run_script(
        run,
        [
            "scripts/fetch_fulltext.py",
            "--results",
            str(subset_path),
            "--outdir",
            "data/raw_pdfs",
            "--config",
            str(merged_config_file()),
        ],
        check=False,
    )
    new_files = sorted(_pdf_names() - before)
    dois = [e["doi"] for e in subset]
    if new_files and dois:
        run.step("校验新下载的 PDF")
        run_script(
            run,
            ["tools/verify_pdfs.py", "--doi", *dois],
            python=_tools_python(),
            check=False,
        )
    return {
        "tried": len(subset),
        "downloaded": len(new_files),
        "files": new_files[:10],
        "manual_csv": "data/raw_pdfs/need_manual_download.csv",
        "note": (
            f"开放获取命中 {len(new_files)} 篇；其余在 need_manual_download.csv，"
            "付费墙文献可用「下载付费墙全文（CDP）」继续"
            if len(new_files) < len(subset)
            else f"全部 {len(new_files)} 篇下载成功"
        ),
    }


def task_fetch_fulltext(run: Run) -> dict:
    limit = _clamp(run.params.get("max_entries"), 5, 1, 20)
    return _run_fulltext(run, limit)


def task_fetch_pipeline(run: Run) -> dict:
    limit = _clamp(run.params.get("max_entries"), 5, 1, 20)
    run.step("第 1 步：SciVerse 检索")
    search = task_fetch_elsevier(run)
    run.step("第 2 步：下载开放获取全文")
    full = _run_fulltext(run, limit)
    return {**full, "entries": search.get("entries")}


def task_download_cdp(run: Run) -> dict:
    if not cdp_available():
        raise RuntimeError(
            "CDP 浏览器未启动。请先运行 tools\\start_cdp_browser.ps1，"
            "并确认校园网/机构权限后重试"
        )
    raw = str(run.params.get("doi") or "").strip()
    limit = _clamp(run.params.get("max_papers"), 3, 1, 10)
    if raw:
        dois = [d.strip() for d in re.split(r"[\s,;]+", raw) if d.strip()]
    else:
        csv_path = PDF_DIR / "need_manual_download.csv"
        if not csv_path.exists():
            raise RuntimeError("没有待下载清单（need_manual_download.csv），请先执行开放获取下载")
        with csv_path.open(encoding="utf-8-sig", newline="") as fh:
            rows = [row["doi"] for row in csv.DictReader(fh) if row.get("doi")]
        have = {p.stem.rsplit("_", 1)[0] for p in PDF_DIR.glob("*.pdf") if "_" in p.stem}
        pending = [d for d in rows if _sanitize_doi(d) not in have]
        dois = pending[:limit]
        if not dois:
            raise RuntimeError(
                "待下载清单里的文献都已下载（或清单为空）。"
                "可直接在 DOI 栏填写目标文献，或先重新执行「检索并下载全文」更新清单"
            )
        run.log(
            f"待下载清单 {len(rows)} 条，已下载 {len(rows) - len(pending)} 条，"
            f"本次取 {len(dois)} 条：{', '.join(dois)}"
        )

    sd = [d for d in dois if d.lower().startswith("10.1016")]
    other = [d for d in dois if d not in sd]
    before = _pdf_names()
    if sd:
        run.step(f"ScienceDirect 下载 {len(sd)} 篇")
        run_script(run, ["tools/fetch_sd_cdp.py", *sd], python=_tools_python(), check=False)
    if other:
        run.step(f"其他出版社下载 {len(other)} 篇")
        run_script(run, ["tools/fetch_pdf_cdp.py", *other], python=_tools_python(), check=False)
    new_files = sorted(_pdf_names() - before)
    if new_files:
        run.step("校验新下载的 PDF")
        run_script(run, ["tools/verify_pdfs.py", "--doi", *dois], python=_tools_python(), check=False)
    return {
        "requested": len(dois),
        "downloaded": len(new_files),
        "files": new_files[:10],
        "note": (
            "全部下载成功" if len(new_files) == len(dois)
            else "部分失败：检查校园网权限或登录状态后重试；失败文献仍在 need_manual_download.csv"
        ),
    }


def task_verify_pdfs(run: Run) -> dict:
    doi = str(run.params.get("doi") or "").strip()
    args = ["tools/verify_pdfs.py"]
    if doi:
        args += ["--doi", doi]
    run_script(run, args, python=_tools_python(), check=False)
    return {"doi": doi or "全部"}


# ---------------------------------------------------------------- 入库预览


def task_ingest_preview(run: Run) -> dict:
    params = run.params
    pdf_dir = (ROOT / (params.get("pdf_dir") or "data/raw_pdfs")).resolve()
    if not pdf_dir.is_dir():
        raise RuntimeError(f"PDF 目录不存在：{pdf_dir}")
    only_new = bool(params.get("only_new", True))
    max_papers = _clamp(params.get("max_papers"), 2, 1, 10)

    all_pdfs = sorted(pdf_dir.glob("*.pdf"))
    candidates = all_pdfs
    if only_new:
        done = processed_hashes()
        candidates = [p for p in all_pdfs if sha256_file(p) not in done]
        run.log(f"PDF 目录共 {len(all_pdfs)} 个；已处理 {len(all_pdfs) - len(candidates)} 个；本次候选 {len(candidates)} 个")
    else:
        run.log(f"PDF 目录共 {len(all_pdfs)} 个；本次不跳过已处理文件")
    pdfs = candidates[:max_papers]
    if not pdfs:
        raise RuntimeError(
            "没有未处理的 PDF。可先把新 PDF 放进 data/raw_pdfs，"
            "或取消勾选「只处理未抽取过的 PDF」重跑"
        )

    batch_id = f"batch_{time.strftime('%Y%m%d_%H%M%S')}"
    bdir = batch_dir(batch_id)
    parsed_dir = bdir / "parsed"
    parsed_dir.mkdir(parents=True, exist_ok=True)
    compounds = extract.load_compounds()
    run.log(f"批次目录：extractions/{batch_id}")
    run.log(f"化合物白名单：{', '.join(c['standard_name'] for c in compounds)}")

    records: list[dict] = []
    skipped: list[dict] = []
    papers: list[dict] = []

    for idx, pdf in enumerate(pdfs, 1):
        sha = sha256_file(pdf)
        try:
            p_manifest, manifest_source = paper_manifest.load_for_pdf(pdf)
        except paper_manifest.ManifestError as exc:
            run.log(f"  [manifest 校验失败] {exc}")
            mark_processed(pdf, sha, "manifest_invalid", batch_id, str(exc))
            skipped.append({"pdf": pdf.name, "reason": f"manifest 校验失败：{exc}"})
            continue
        run.log(
            f"  manifest {p_manifest['paper_id']}（{manifest_source}，"
            f"SI={p_manifest['si']['status']}，A判定={p_manifest['eligibility']['verdict']}）"
        )
        if manifest_source == "legacy":
            run.log("  [兼容] 未找到 A 阶段 manifest，已按文件名/哈希生成；建议先运行 tools/build_manifest.py")
        run.step(f"[{idx}/{len(pdfs)}] 解析 PDF：{pdf.name}")
        try:
            run_script(run, ["scripts/pdf_to_text.py", "--pdf", str(pdf), "--outdir", str(parsed_dir)])
        except Exception as exc:  # noqa: BLE001
            run.log(f"  [解析失败] {exc}")
            mark_processed(pdf, sha, "parse_failed", batch_id, str(exc))
            skipped.append({"pdf": pdf.name, "reason": f"解析失败：{exc}"})
            continue

        txt = parsed_dir / f"{pdf.stem}.txt"
        if not txt.exists():
            mark_processed(pdf, sha, "parse_failed", batch_id, "未生成文本")
            skipped.append({"pdf": pdf.name, "reason": "解析未生成文本"})
            continue
        text = txt.read_text(encoding="utf-8", errors="ignore")
        ocr_meta = None
        ocr_gate_meta = None
        parse_mode = "text"
        report_path = parsed_dir / "parse_report.json"
        if report_path.exists():
            try:
                for item in json.loads(report_path.read_text(encoding="utf-8")):
                    if Path(item.get("pdf", "")).name == pdf.name:
                        ocr_meta = item.get("ocr")
                        ocr_gate_meta = ocr_gate.summarize(ocr_meta)
                        if (ocr_meta or {}).get("pages"):
                            parse_mode = "ocr"
                        break
            except ValueError:
                pass
        if ocr_gate_meta and ocr_gate_meta.get("decision") == "fail":
            reason = "OCR 质量门控未通过：" + ", ".join(ocr_gate_meta.get("reasons") or [])
            if len(text.strip()) < 500:
                run.log(f"  {reason}；可用原生文本不足，转入人工复核")
                mark_processed(pdf, sha, "ocr_review_required", batch_id, reason)
                skipped.append({"pdf": pdf.name, "reason": reason, "ocr_gate": ocr_gate_meta})
                papers.append({
                    "pdf": pdf.name,
                    "paper_id": p_manifest["paper_id"],
                    "records": 0,
                    "status": "ocr_review_required",
                    "ocr_gate": ocr_gate_meta,
                })
                continue
            parse_mode = "ocr_review"
            run.log(f"  {reason}；原生文本仍可用，继续但标记人工复核")
        if ocr_gate_meta and ocr_gate_meta.get("decision") == "review":
            parse_mode = "ocr_review"
            run.log(f"  OCR 复核标记：{', '.join(ocr_gate_meta.get('reasons') or [])}")
        if len(text.strip()) < 500:
            run.log("  文本过短，疑似扫描件，跳过")
            mark_processed(pdf, sha, "scanned_or_short", batch_id)
            skipped.append({"pdf": pdf.name, "reason": "疑似扫描件/文本过短"})
            continue
        si_text, si_meta = _load_si(pdf, p_manifest)
        if p_manifest["si"]["status"] == "failed":
            reason = "SI 完整性校验失败，停止使用该 SI"
            run.log(f"  {reason}")
            mark_processed(pdf, sha, "si_integrity_failed", batch_id, reason)
            skipped.append({"pdf": pdf.name, "reason": reason})
            continue
        if si_text:
            run.log(f"  补充材料：{si_meta.get('chars')} 字符")
        run.log(f"  文本 {len(text)} 字符；解析模式 {parse_mode}")

        run.step(f"[{idx}/{len(pdfs)}] AI 抽取：{pdf.name}")
        try:
            raws, extract_meta = extract.extract_paper(
                text,
                pdf=pdf,
                compounds=compounds,
                log=run.log,
                batch_id=batch_id,
                parsed_text_path=txt,
                parse_mode=parse_mode,
                ocr_meta=ocr_meta,
                si_text=si_text,
                si_meta=si_meta,
            )
        except Exception as exc:  # noqa: BLE001
            run.log(f"  [抽取失败] {exc}")
            fail_payload = provenance.make_snapshot_payload(
                batch_id=batch_id,
                pdf=pdf,
                pdf_hash=sha,
                parsed_text_path=txt,
                parsed_text_hash=provenance.sha256_file(txt),
                raw_records=[],
                normalized_records=[],
                modules=[],
                skill_meta={},
                prompt_meta={},
                model_info={},
                model_params={},
                parse_mode=parse_mode,
                ocr_meta=ocr_meta,
                si_meta=si_meta,
                chart_meta=None,
                raw_output="",
                status="extract_failed",
                error=str(exc),
                manifest=p_manifest,
            )
            fail_path, _ = provenance.write_snapshot(bdir, fail_payload, pdf.stem)
            mark_processed(pdf, sha, "extract_failed", batch_id, str(exc))
            skipped.append({"pdf": pdf.name, "reason": f"抽取失败：{exc}", "snapshot": fail_path.as_posix()})
            papers.append({"pdf": pdf.name, "records": 0, "chars": len(text), "status": "extract_failed", "snapshot": fail_path.relative_to(ROOT).as_posix()})
            continue

        norm_text = provenance.normalize_text(text)
        doi = (p_manifest.get("doi") or {}).get("value") or extract.doi_from_filename(pdf)
        cond_profile = condition_profile.profile_for_doi(doi)
        condition_meta = None
        pairs: list[tuple[dict, dict, dict, dict]] = []
        local_skipped: list[dict] = []
        for raw in raws:
            if cond_profile:
                applied = condition_profile.apply_to_raw(raw, text, cond_profile)
                if applied:
                    condition_meta = {
                        "version": cond_profile.get("version"),
                        "scope": cond_profile.get("scope"),
                        "changed": applied.get("changed"),
                    }
            try:
                rec = extract.normalize(
                    raw,
                    compounds=compounds,
                    pdf=pdf,
                    pdf_hash=sha,
                    batch_id=batch_id,
                )
            except extract.SkipRecord as exc:
                run.log(f"  跳过一条：{exc}")
                skipped.append({"pdf": pdf.name, "reason": str(exc)})
                local_skipped.append({"reason": str(exc), "raw": raw})
                continue
            pairs.append(_finalize_pair(
                raw, rec, norm_text,
                context={"extraction_method": "llm", "condition_profile": condition_meta},
                modules=extract_meta["modules"],
            ))

        # Table-first VLE path: deterministic column-group parsing for the
        # paper-specific low-pressure apparatus. It supplements the LLM and
        # replaces duplicate LLM rows; it does not guess method constants.
        vle_meta = None
        profile = vle_table_parser.profile_for_doi(doi)
        if profile:
            try:
                vle_result = vle_table_parser.parse_vle_tables(pdf, profile)
                vle_raws = vle_table_parser.points_to_raw_records(
                    vle_result,
                    pdf,
                    source_template=(raws[0].get("source") if raws else None),
                    doi=doi,
                    total_pressure_kPa=profile["total_pressure_kPa"],
                    liquid_volume_L=profile["liquid_volume_L"],
                )
                vle_pairs = []
                for raw in vle_raws:
                    rec = extract.normalize(
                        raw,
                        compounds=compounds,
                        pdf=pdf,
                        pdf_hash=sha,
                        batch_id=batch_id,
                        extraction_method="deterministic_vle_table",
                    )
                    vle_pairs.append(_finalize_pair(
                        raw, rec, norm_text,
                        context={"extraction_method": "deterministic_vle_table", "vle_profile": profile},
                        modules=extract_meta["modules"],
                    ))

                parser_keys = {_record_key(rec) for _, rec, _, _ in vle_pairs}
                pairs = [p for p in pairs if _record_key(p[1]) not in parser_keys] + vle_pairs
                vle_meta = {
                    "profile": profile,
                    "counts": vle_result.get("counts"),
                    "tables": [
                        {"number": t.get("number"), "recipe": t.get("recipe"), "points": t.get("points")}
                        for t in vle_result.get("tables") or []
                    ],
                    "selected": len(vle_result.get("selected_40C_lowP") or []),
                }
                run.log(f"  确定性 VLE 表格：{vle_meta['counts']}；合并后 {len(pairs)} 条")
            except Exception as exc:  # noqa: BLE001
                run.log(f"  [VLE 表格解析失败] {exc}")
                vle_meta = {"status": "failed", "error": str(exc)[:300]}

        # Text-described reference-row path: a 30 wt% MEA baseline can be
        # scattered across table/methods/results and have no standalone row.
        reference_meta = None
        ref_profile = reference_case_parser.profile_for_doi(doi)
        if ref_profile:
            try:
                ref_raws = reference_case_parser.parse_reference(text, ref_profile, pdf, doi)
                ref_pairs = []
                for raw in ref_raws:
                    rec = extract.normalize(
                        raw,
                        compounds=compounds,
                        pdf=pdf,
                        pdf_hash=sha,
                        batch_id=batch_id,
                        extraction_method="deterministic_reference_profile",
                    )
                    ref_pairs.append(_finalize_pair(
                        raw, rec, norm_text,
                        context={
                            "extraction_method": "deterministic_reference_profile",
                            "reference_profile": {
                                "version": ref_profile.get("version"),
                                "scope": ref_profile.get("scope"),
                                "loc": ref_profile.get("loc_label"),
                            },
                        },
                        modules=extract_meta["modules"],
                    ))
                ref_keys = {_record_key(rec) for _, rec, _, _ in ref_pairs}
                pairs = [p for p in pairs if _record_key(p[1]) not in ref_keys] + ref_pairs
                reference_meta = {
                    "profile_version": ref_profile.get("version"),
                    "scope": ref_profile.get("scope"),
                    "records": len(ref_pairs),
                    "loc": ref_profile.get("loc_label"),
                }
                run.log(f"  参考行 profile：{len(ref_pairs)} 条；合并后 {len(pairs)} 条")
            except Exception as exc:  # noqa: BLE001
                run.log(f"  [参考行解析失败] {exc}")
                reference_meta = {"status": "failed", "error": str(exc)[:300]}

        # Vertical/nested-unit VLE tables: generic row parser + paper profile.
        # Existing LLM rows are kept; deterministic rows only fill a missing point.
        vertical_meta = None
        vertical_profile = vle_table_parser.vertical_profile_for_doi(doi)
        if vertical_profile:
            try:
                vres = vle_table_parser.parse_vertical_table(pdf, vertical_profile)
                vraws = vle_table_parser.vertical_points_to_raw_records(
                    vres, pdf, doi=doi,
                    source_template=(raws[0].get("source") if raws else None),
                )
                added = 0
                duplicates = 0
                for raw in vraws:
                    rec = extract.normalize(
                        raw,
                        compounds=compounds,
                        pdf=pdf,
                        pdf_hash=sha,
                        batch_id=batch_id,
                        extraction_method="deterministic_vle_vertical",
                    )
                    pair = _finalize_pair(
                        raw, rec, norm_text,
                        context={
                            "extraction_method": "deterministic_vle_vertical",
                            "vle_profile": {
                                "version": vertical_profile.get("version"),
                                "table": vertical_profile.get("table"),
                                "source": vertical_profile.get("source"),
                            },
                        },
                        modules=extract_meta["modules"],
                    )
                    if _is_vertical_duplicate(rec, pairs):
                        duplicates += 1
                        continue
                    pairs.append(pair)
                    added += 1
                vertical_meta = {
                    "profile_version": vertical_profile.get("version"),
                    "table": vertical_profile.get("table"),
                    "counts": vres.get("counts"),
                    "errors": vres.get("errors"),
                    "added": added,
                    "duplicates_skipped": duplicates,
                    "skipped_rows": vres.get("skipped") or [],
                }
                run.log(
                    f"  纵向 VLE 表：解析 {vres.get('counts', {}).get('points', 0)} 点，"
                    f"新增 {added}，与 LLM 重复 {duplicates}"
                )
            except Exception as exc:  # noqa: BLE001
                run.log(f"  [纵向 VLE 表解析失败] {exc}")
                vertical_meta = {"status": "failed", "error": str(exc)[:300]}

        for idx, (_, rec, _, _) in enumerate(pairs):
            rec["record_id"] = excerpt_store.record_id(
                batch_id, p_manifest["paper_id"], rec, idx
            )

        payload = provenance.make_snapshot_payload(            batch_id=batch_id,
            pdf=pdf,
            pdf_hash=sha,
            parsed_text_path=txt,
            parsed_text_hash=provenance.sha256_file(txt),
            raw_records=[p[0] for p in pairs],
            normalized_records=[p[1] for p in pairs],
            modules=extract_meta["modules"],
            skill_meta=extract_meta["skill"],
            prompt_meta=extract_meta["prompt"],
            model_info=extract_meta["model"],
            model_params=extract_meta["model_params"],
            parse_mode=extract_meta["parse_mode"],
            ocr_meta=extract_meta["ocr"],
            si_meta=extract_meta["si"],
            chart_meta=extract_meta["chart"],
            raw_output=extract_meta["raw_output"],
            status="ok" if pairs else "no_records",
            table_meta={
                "pages": extract_meta.get("table_context_pages") or [],
                "chars": extract_meta.get("table_context_chars") or 0,
                "vle_parser": vle_meta,
                "vle_vertical": vertical_meta,
                "reference_parser": reference_meta,
                "condition_profile": condition_meta,
                "ocr_gate": ocr_gate_meta,
            },
            verifications=[p[2] for p in pairs],
            reasonings=[p[3] for p in pairs],
            skipped=local_skipped,
            manifest=p_manifest,
        )
        snap_path, snap_hash = provenance.write_snapshot(bdir, payload, pdf.stem)
        excerpt_entries = excerpt_store.write_records(
            bdir,
            pairs,
            batch_id=batch_id,
            paper_id=p_manifest["paper_id"],
            snapshot_path=snap_path,
            snapshot_hash=snap_hash,
        )
        snap_rel = excerpt_store.rel_path(snap_path)

        kept = 0
        levels = Counter()
        for _, rec, _, _ in pairs:
            rec["test"]["raw_data_path"] = snap_rel
            rec["test"]["raw_data_hash"] = snap_hash
            levels[rec["qc"]["qc_level"]] += 1
            records.append(rec)
            kept += 1
        run.log(f"  抽取 {len(raws)} 条，标准化保留 {kept} 条；QC {dict(levels)}")
        run.log(f"  快照：{snap_path.relative_to(ROOT).as_posix()}")
        mark_processed(pdf, sha, f"extracted:{kept}" if kept else "no_records", batch_id, snap_path.as_posix())
        papers.append(
            {
                "pdf": pdf.name,
                "paper_id": p_manifest["paper_id"],
                "manifest_source": manifest_source,
                "manifest_version": p_manifest["manifest_version"],
                "records": kept,
                "chars": len(text),
                "status": "ok" if kept else "no_records",
                "snapshot": snap_path.relative_to(ROOT).as_posix(),
                "excerpt_index": (bdir / "raw" / "excerpt_index.json").relative_to(ROOT).as_posix(),
                "excerpts": len(excerpt_entries),
                "modules": [m["id"] for m in extract_meta["modules"]],
                "prompt_sha256": extract_meta["prompt"].get("combined_sha256"),
                "model": extract_meta["model"].get("model"),
                "parse_mode": parse_mode,
                "ocr_pages": (ocr_meta or {}).get("pages") or [],
                "ocr_gate": ocr_gate_meta,
                "si": si_meta,
                "vle_parser": vle_meta,
                "vle_vertical": vertical_meta,
                "reference_parser": reference_meta,
                "condition_profile": condition_meta,
                "qc": dict(levels),
            }
        )

    batch_manifest = {
        "batch_id": batch_id,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "manifest_version": paper_manifest.MANIFEST_VERSION,
        "excerpt_version": excerpt_store.EXCERPT_VERSION,
        "excerpt_index": f"{(bdir / 'raw' / 'excerpt_index.json').relative_to(ROOT).as_posix()}" if records else None,
        "papers": papers,
        "records": len(records),
        "note": "One snapshot per paper extraction; see raw/llm_*.json.",
    }
    (bdir / "extraction_manifest.json").write_text(
        json.dumps(batch_manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    raw_path = bdir / "raw_agent.jsonl"
    with raw_path.open("w", encoding="utf-8") as fh:
        for rec in records:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    run.step("校验（不写数据库）")
    run_script(run, ["scripts/validate.py", "--input", str(raw_path), "--outdir", str(bdir)])

    valid = _read_jsonl(bdir / "valid.jsonl")
    incomplete = _read_jsonl(bdir / "valid_incomplete.jsonl")
    rejected = _read_jsonl(bdir / "rejected.jsonl")

    reasons = Counter()
    rejected_rows = []
    for rec in rejected:
        reason = (rec.get("qc") or {}).get("qc_reason") or "unknown"
        for part in str(reason).split(";"):
            if part:
                reasons[part] += 1
        amine = (rec.get("recipe") or {}).get("amine_a") or {}
        rejected_rows.append(
            {
                "amine": amine.get("standard_name"),
                "wt": (rec.get("recipe") or {}).get("total_amine_wt"),
                "reason": reason,
            }
        )

    def brief(rec: dict) -> dict:
        recipe = rec.get("recipe") or {}
        test = rec.get("test") or {}
        return {
            "amine": (recipe.get("amine_a") or {}).get("standard_name"),
            "amine_b": (recipe.get("amine_b") or {}).get("standard_name"),
            "wt_a": recipe.get("wt_a"),
            "wt_b": recipe.get("wt_b"),
            "total_amine_wt": recipe.get("total_amine_wt"),
            "temperature_K": test.get("temperature_K"),
            "co2_vol_pct": test.get("co2_vol_pct"),
            "co2_partial_kPa": test.get("co2_partial_kPa"),
            "initial_loading": test.get("initial_loading"),
            "metrics": len(rec.get("performance") or []),
            "qc_level": (rec.get("qc") or {}).get("qc_level"),
            "loc": (rec.get("source") or {}).get("loc_label"),
        }

    run.step("预览结果")
    run.log(f"valid={len(valid)}  valid_incomplete={len(incomplete)}  rejected={len(rejected)}")
    for key, count in reasons.most_common():
        run.log(f"  拒收原因 {key}: {count}")

    note = None
    if not records:
        note = (
            "本批没有产出可用记录：可能超出研究边界（非水相、含添加剂、胺不在白名单），"
            "或文本中没有可用数据。该 PDF 已记为「已处理」，下次不会重复抽取；"
            "如需重试，可取消勾选「只处理未抽取过的 PDF」。"
        )
        run.log(note)
    elif not valid and not incomplete:
        note = "全部记录被校验拒收，未产生可导入数据。"

    return {
        "batch_id": batch_id,
        "papers": papers,
        "skipped": skipped,
        "counts": {
            "valid": len(valid),
            "incomplete": len(incomplete),
            "rejected": len(rejected),
        },
        "reasons": dict(reasons),
        "records": [brief(r) for r in (valid + incomplete)[:100]],
        "rejected_rows": rejected_rows[:30],
        "ready_to_commit": bool(valid or incomplete),
        "note": note,
    }


# ---------------------------------------------------------------- 确认入库


def task_ingest_commit(run: Run) -> dict:
    batch_id = str(run.params.get("batch_id") or "").strip()
    if not batch_id:
        raise RuntimeError("缺少批次号")
    bdir = batch_dir(batch_id)
    raw_path = bdir / "raw_agent.jsonl"
    if not raw_path.exists():
        raise RuntimeError(f"批次 {batch_id} 没有 raw_agent.jsonl，请先做预览")
    config = "config.yaml"

    run.step("重新校验")
    run_script(run, ["scripts/validate.py", "--input", str(raw_path), "--outdir", str(bdir)])
    valid_path = bdir / "valid.jsonl"
    incomplete_path = bdir / "valid_incomplete.jsonl"
    rejected_path = bdir / "rejected.jsonl"
    n_valid = _count_lines(valid_path)
    n_incomplete = _count_lines(incomplete_path)
    n_rejected = _count_lines(rejected_path)
    if not n_valid and not n_incomplete:
        raise RuntimeError("没有可导入记录（全部被拒收）")

    if n_valid:
        run.step(f"导入 valid（{n_valid} 条）")
        run_script(
            run,
            [
                "scripts/import_jsonl.py",
                "--input",
                str(valid_path),
                "--config",
                config,
                "--batch-id",
                batch_id,
            ],
        )
    if n_incomplete:
        run.step(f"导入 valid_incomplete（{n_incomplete} 条，L3）")
        run_script(
            run,
            [
                "scripts/import_jsonl.py",
                "--input",
                str(incomplete_path),
                "--config",
                config,
                "--batch-id",
                batch_id,
            ],
        )
        run_script(
            run,
            [
                "scripts/audit_log.py",
                "--config",
                config,
                "--action",
                "import_incomplete",
                "--table",
                "test",
                "--detail",
                f"batch={batch_id};n={n_incomplete}",
                "--operator",
                "auto_agent",
            ],
        )

    run.step("入库后核验（postcheck）")
    code = run_script(run, ["tools/postcheck.py", "--batch", batch_id], check=False)

    run.step("更新展示站快照")
    run_script(run, ["tools/build_web_db.py"])

    return {
        "batch_id": batch_id,
        "counts": {"valid": n_valid, "incomplete": n_incomplete, "rejected": n_rejected},
        "postcheck_ok": code == 0,
    }


# ---------------------------------------------------------------- 其它任务


def task_postcheck(run: Run) -> dict:
    code = run_script(run, ["tools/postcheck.py"], check=False)
    return {"ok": code == 0}


def task_export_gold(run: Run) -> dict:
    run_script(run, ["tools/export_gold_standard.py"])
    return {"json": "gold_standard_L2.json", "csv": "gold_standard_L2.csv"}


def task_rebuild_snapshot(run: Run) -> dict:
    run_script(run, ["tools/build_web_db.py"])
    meta_path = ROOT / "web" / "public" / "data" / "meta.json"
    meta = {}
    if meta_path.exists():
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except ValueError:
            meta = {}
    return {
        "tests": meta.get("test_count"),
        "performance": meta.get("performance_count"),
        "sha": (meta.get("source_sha256") or "")[:12],
        "generated_at": meta.get("generated_at"),
    }


TASKS: list[dict] = [
    {
        "id": "ingest_preview",
        "title": "批量入库 · 预览",
        "group": "入库",
        "desc": "选 PDF → 解析 → AI 抽取 → 校验预览。只写 extractions/，不碰数据库。",
        "requires": ["ai"],
        "primary": True,
        "params": [
            {"key": "pdf_dir", "label": "PDF 目录", "type": "text", "default": "data/raw_pdfs"},
            {"key": "only_new", "label": "只处理未抽取过的 PDF", "type": "bool", "default": True},
            {"key": "max_papers", "label": "本次最多处理篇数", "type": "int", "default": 2, "min": 1, "max": 10},
        ],
        "run": task_ingest_preview,
    },
    {
        "id": "ingest_commit",
        "title": "确认入库",
        "group": "入库",
        "desc": "把预览批次写入数据库：校验 → 导入 → 审计 → 体检 → 更新展示站快照。",
        "requires": [],
        "params": [
            {"key": "batch_id", "label": "批次号", "type": "batch", "required": True},
        ],
        "run": task_ingest_commit,
    },
    {
        "id": "fetch_pipeline",
        "title": "检索并下载全文",
        "group": "采集",
        "desc": "Elsevier Scopus API 检索题录 → Unpaywall 下载开放获取 PDF → 存入 data/raw_pdfs → 完整性校验。",
        "requires": ["elsevier", "unpaywall"],
        "primary": True,
        "params": [
            {"key": "source", "label": "检索源", "type": "select", "default": "scopus", "options": SEARCH_SOURCES},
            {"key": "max_entries", "label": "本次最多下载篇数", "type": "int", "default": 5, "min": 1, "max": 20},
        ],
        "run": task_fetch_pipeline,
    },
    {
        "id": "fetch_fulltext",
        "title": "只下载开放获取全文",
        "group": "采集",
        "desc": "用已有检索结果补下载：优先 Scopus 标记开放获取的，再按年份新→旧；不重新检索。",
        "requires": ["unpaywall"],
        "params": [
            {"key": "max_entries", "label": "本次最多下载篇数", "type": "int", "default": 5, "min": 1, "max": 20},
        ],
        "run": task_fetch_fulltext,
    },
    {
        "id": "fetch_elsevier",
        "title": "SciVerse 检索（仅元数据）",
        "group": "采集",
        "desc": "只拉元数据 JSON，不下载 PDF；下载请用上面的任务。",
        "requires": ["elsevier"],
        "params": [
            {"key": "source", "label": "检索源", "type": "select", "default": "scopus", "options": SEARCH_SOURCES},
        ],
        "run": task_fetch_elsevier,
    },
    {
        "id": "download_cdp",
        "title": "下载付费墙全文（CDP）",
        "group": "采集",
        "desc": "需先启动 CDP 浏览器并有校园网/机构权限。不检索：填 DOI 直接下载；留空则用最近一次开放获取下载生成的待下载清单。",
        "requires": [],
        "params": [
            {"key": "doi", "label": "DOI（留空则用待下载清单）", "type": "text", "default": ""},
            {"key": "max_papers", "label": "清单模式下最多篇数", "type": "int", "default": 3, "min": 1, "max": 10},
        ],
        "run": task_download_cdp,
    },
    {
        "id": "verify_pdfs",
        "title": "校验 PDF 完整性",
        "group": "采集",
        "desc": "检查 PDF 首字节、EOF、页数与首页文本；可只校验指定 DOI。",
        "requires": [],
        "params": [
            {"key": "doi", "label": "DOI（留空校验全部）", "type": "text", "default": ""},
        ],
        "run": task_verify_pdfs,
    },
    {
        "id": "postcheck",
        "title": "数据体检",
        "group": "质控",
        "desc": "运行七项硬指标检查（L2 快照、仿真隔离、外键、完整性等）。",
        "requires": [],
        "params": [],
        "run": task_postcheck,
    },
    {
        "id": "export_gold",
        "title": "导出 L2 金标准",
        "group": "质控",
        "desc": "导出 gold_standard_L2.json / .csv 到项目根目录。",
        "requires": [],
        "params": [],
        "run": task_export_gold,
    },
    {
        "id": "rebuild_snapshot",
        "title": "更新展示站快照",
        "group": "展示",
        "desc": "从数据库重建网站只读快照（数据检索页随之更新）。",
        "requires": [],
        "params": [],
        "run": task_rebuild_snapshot,
    },
]


def public_tasks() -> list[dict]:
    ai = settings.ai_config()
    keys = {
        "ai": bool(ai.get("api_key")),
        "elsevier": bool(settings.elsevier_key()),
        "unpaywall": bool(settings.unpaywall_email()),
    }
    out = []
    for task in TASKS:
        item = {k: v for k, v in task.items() if k != "run"}
        item["ready"] = all(keys.get(k) for k in task["requires"])
        item["missing"] = [k for k in task["requires"] if not keys.get(k)]
        out.append(item)
    return out


def get_task(task_id: str) -> dict | None:
    return next((t for t in TASKS if t["id"] == task_id), None)


def list_batches(limit: int = 30) -> list[dict]:
    rows = []
    for path in sorted(EXTRACTIONS.glob("batch_*"), reverse=True)[:limit]:
        raw = path / "raw_agent.jsonl"
        rows.append(
            {
                "batch_id": path.name,
                "records": _count_lines(raw),
                "valid": _count_lines(path / "valid.jsonl"),
                "incomplete": _count_lines(path / "valid_incomplete.jsonl"),
                "rejected": _count_lines(path / "rejected.jsonl"),
                "mtime": time.strftime("%Y-%m-%d %H:%M", time.localtime(path.stat().st_mtime)),
                "has_preview": raw.exists(),
            }
        )
    return rows


def batch_records(batch_id: str) -> dict:
    bdir = batch_dir(batch_id)
    valid = _read_jsonl(bdir / "valid.jsonl")
    incomplete = _read_jsonl(bdir / "valid_incomplete.jsonl")
    rejected = _read_jsonl(bdir / "rejected.jsonl")
    return {
        "batch_id": batch_id,
        "valid": len(valid),
        "incomplete": len(incomplete),
        "rejected": len(rejected),
        "records": (valid + incomplete)[:200],
        "rejected_rows": [
            {
                "amine": ((r.get("recipe") or {}).get("amine_a") or {}).get("standard_name"),
                "reason": (r.get("qc") or {}).get("qc_reason"),
            }
            for r in rejected[:100]
        ],
    }
