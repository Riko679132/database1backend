"""Versioned A -> B paper manifest.

A-stage outputs are currently spread across PDF filenames, Elsevier result JSON,
the triage CSV and per-paper SI manifests. This module gives B one validated
handoff object without moving or rewriting any A artifact.

Status vocabulary:
    present / downloaded  the artifact exists and is usable
    missing               the source itself has no such value/file
    failed                acquisition or integrity check failed
    pending               not verified yet

A missing DOI or SI is not an error. A present PDF/SI with a wrong hash is.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any

from .settings import ROOT

MANIFEST_VERSION = "1.0"
MANIFEST_DIR = ROOT / "data" / "manifests"
PDF_DIR = ROOT / "data" / "raw_pdfs"
SI_DIR = ROOT / "data" / "raw_si"
DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")
STATUS_VALUES = {"present", "missing", "failed", "pending", "downloaded"}


class ManifestError(RuntimeError):
    """Raised when a manifest is unusable; B must not silently continue."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sanitize_doi(doi: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", (doi or "").strip())


def _rel(path: Path, root: Path) -> str | None:
    try:
        return path.resolve().relative_to(root.resolve()).as_posix()
    except (ValueError, OSError):
        return None


def _resolve(path: str | None, root: Path) -> Path | None:
    if not path:
        return None
    p = Path(path)
    if not p.is_absolute():
        p = root / p
    return p


def _inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except (ValueError, OSError):
        return False


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def _read_csv(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def _known_dois(root: Path) -> dict[str, dict]:
    """Map DOI -> Elsevier metadata from the A-stage result files."""
    out: dict[str, dict] = {}
    for name in ("elsevier_results.json", "elsevier_results_broad_20261026.json"):
        data = _read_json(root / "data" / "raw_pdfs" / name)
        if not isinstance(data, dict):
            continue
        for entry in data.get("entries") or []:
            doi = str(entry.get("doi") or "").strip()
            if doi and doi.lower() not in out:
                out[doi.lower()] = entry
    return out


def _triage(root: Path) -> dict[str, dict]:
    rows = _read_csv(root / "data" / "raw_pdfs" / "triage_v2.csv")
    return {str(r.get("doi") or "").strip().lower(): r for r in rows if r.get("doi")}


def _assessment(root: Path) -> dict[str, dict]:
    rows = _read_csv(root / "data" / "raw_pdfs" / "extraction_todo_assessment.csv")
    return {str(r.get("doi") or "").strip().lower(): r for r in rows if r.get("doi")}


def doi_from_stem(stem: str, known: dict[str, dict] | None = None) -> str | None:
    """Prefer a full DOI from A metadata; never split multi-segment DOIs by hand."""
    for doi in (known or {}):
        prefix = sanitize_doi(doi)
        if stem == prefix or stem.startswith(prefix + "_"):
            return doi
    # Legacy filename convention: 10.1021_ie400825u_hash
    m = re.match(r"^(10\.\d{4,9})_([^_]+)(?:_[0-9a-f]{8})?$", stem, re.I)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    return None


def _doi_entry(value: str | None, status: str, source: str | None) -> dict:
    return {"value": value, "status": status, "source": source}


def _title_entry(value: str | None, status: str, source: str | None) -> dict:
    return {"value": value, "status": status, "source": source}


def _si_payload(root: Path, doi: str | None) -> dict:
    if not doi:
        return {"status": "missing", "manifest_path": None, "files": [],
                "note": "no DOI, SI association cannot be established"}
    base = root / "data" / "raw_si" / sanitize_doi(doi)
    path = base / "si_manifest.json"
    if not path.exists():
        return {"status": "missing", "manifest_path": None, "files": [],
                "note": "no SI manifest for this DOI"}
    data = _read_json(path)
    if not isinstance(data, dict):
        return {"status": "failed", "manifest_path": _rel(path, root), "files": [],
                "note": "SI manifest is not valid JSON"}
    files = []
    warnings = []
    for item in data.get("files") or []:
        raw_path = item.get("path")
        p = _resolve(str(raw_path) if raw_path else None, root)
        entry = {
            "path": _rel(p, root) if p else None,
            "type": item.get("type"),
            "sha256": item.get("sha256"),
            "expected_sha256": item.get("sha256"),
            "bytes": item.get("bytes"),
            "status": "missing",
            "parsed": item.get("parsed") or {},
        }
        if p is None or not _inside(p, root):
            entry["status"] = "failed"
            warnings.append(f"SI path outside project: {raw_path}")
        elif not p.exists():
            entry["status"] = "failed"
            warnings.append(f"SI file missing: {entry['path']}")
        else:
            actual = sha256_file(p)
            entry["sha256"] = actual
            if entry.get("expected_sha256") and actual != entry["expected_sha256"]:
                entry["status"] = "failed"
                warnings.append(f"SI hash mismatch: {entry['path']}")
            else:
                entry["status"] = "present"
            parsed = entry.get("parsed") or {}
            pp = _resolve(parsed.get("path"), root) if parsed.get("path") else None
            if pp and pp.exists() and _inside(pp, root):
                parsed = dict(parsed)
                parsed["path"] = _rel(pp, root)
                parsed["sha256"] = sha256_file(pp)
            elif parsed.get("path"):
                parsed = dict(parsed)
                parsed["status"] = "failed"
            entry["parsed"] = parsed
        files.append(entry)
    if not files:
        status = "missing"
    elif any(f["status"] == "failed" for f in files):
        status = "failed"
    elif all(f["status"] == "present" for f in files):
        status = "present"
    else:
        status = "pending"
    if warnings:
        data = dict(data)
        data["integrity_warnings"] = warnings
    return {
        "status": status,
        "manifest_path": _rel(path, root),
        "si_found": bool(data.get("si_found")),
        "files": files,
        "warnings": warnings,
        "human_verified": bool(data.get("human_verified", False)),
    }


def build_manifest(
    pdf: Path,
    *,
    root: Path = ROOT,
    known: dict[str, dict] | None = None,
    triage: dict[str, dict] | None = None,
    assessment: dict[str, dict] | None = None,
) -> dict:
    known = known if known is not None else _known_dois(root)
    triage = triage if triage is not None else _triage(root)
    assessment = assessment if assessment is not None else _assessment(root)
    pdf = pdf.resolve()
    if not pdf.exists():
        raise ManifestError(f"PDF does not exist: {pdf}")
    pdf_hash = sha256_file(pdf)
    doi = doi_from_stem(pdf.stem, known)
    meta = known.get((doi or "").lower(), {})
    tr = triage.get((doi or "").lower(), {})
    assess = assessment.get((doi or "").lower(), {})

    if doi:
        doi_entry = _doi_entry(doi, "present", "elsevier" if meta.get("doi") else "filename")
    elif pdf.stem.startswith("10."):
        doi_entry = _doi_entry(None, "pending", "filename")
    else:
        doi_entry = _doi_entry(None, "missing", None)

    title = meta.get("title") or tr.get("title") or None
    title_status = "present" if title else "missing"
    title_source = "elsevier" if meta.get("title") else ("triage" if tr.get("title") else None)

    in_scope = str(assess.get("in_scope") or "").lower()
    if in_scope == "no":
        verdict = "out_of_scope"
        eligibility_status = "present"
        eligibility_source = "assessment_csv"
    elif in_scope == "yes":
        verdict = "in_scope"
        eligibility_status = "present"
        eligibility_source = "assessment_csv"
    elif tr.get("verdict"):
        verdict = str(tr.get("verdict"))
        eligibility_status = "present"
        eligibility_source = "triage_v2"
    else:
        verdict = "pending"
        eligibility_status = "missing"
        eligibility_source = None
    try:
        priority = int(tr.get("priority")) if tr.get("priority") else None
    except (TypeError, ValueError):
        priority = None

    paper_id = f"doi:{doi.lower()}" if doi else f"pdf:{pdf_hash[:16]}"
    rel_pdf = _rel(pdf, root)
    if not rel_pdf:
        raise ManifestError(f"PDF is outside project root: {pdf}")

    payload = {
        "manifest_version": MANIFEST_VERSION,
        "paper_id": paper_id,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "doi": doi_entry,
        "title": _title_entry(title, title_status, title_source),
        "pdf": {
            "path": rel_pdf,
            "sha256": pdf_hash,
            "bytes": pdf.stat().st_size,
            "status": "present",
        },
        "si": _si_payload(root, doi),
        "eligibility": {
            "verdict": verdict,
            "priority": priority,
            "reason": assess.get("reason") or tr.get("reason") or None,
            "status": eligibility_status,
            "source": eligibility_source,
        },
        "metadata": {
            "source": title_source or ("filename" if doi else "none"),
            "status": "present" if (doi or title) else "missing",
            "year": meta.get("publication_year") or tr.get("publication_year"),
            "journal": meta.get("source_title"),
        },
        "download": {
            "status": "downloaded",
            "source": "local_file",
            "path": rel_pdf,
        },
        "legacy_generated": False,
        "warnings": [],
    }
    if not doi:
        payload["warnings"].append("DOI could not be established from A metadata or filename")
    if payload["si"]["status"] == "failed":
        payload["warnings"].append("SI integrity check failed; B must not use the SI text")
    return payload


def legacy_manifest(pdf: Path, *, root: Path = ROOT) -> dict:
    """Compatibility object for PDFs that pre-date the manifest builder."""
    data = build_manifest(pdf, root=root)
    data["legacy_generated"] = True
    data["warnings"].append("No stored manifest found; generated a legacy manifest for this PDF")
    return data


def validate_manifest(data: Any, *, root: Path = ROOT, check_files: bool = True) -> dict:
    errors: list[str] = []
    warnings: list[str] = []
    if not isinstance(data, dict):
        return {"ok": False, "errors": ["manifest is not an object"], "warnings": []}
    version = data.get("manifest_version")
    if version != MANIFEST_VERSION:
        errors.append(f"unsupported manifest_version: {version!r} (expected {MANIFEST_VERSION})")
    for key in ("paper_id", "doi", "title", "pdf", "si", "eligibility", "metadata", "download"):
        if key not in data:
            errors.append(f"missing field: {key}")
    paper_id = data.get("paper_id")
    if not isinstance(paper_id, str) or not paper_id.startswith(("doi:", "pdf:")):
        errors.append("paper_id must start with doi: or pdf:")

    doi = data.get("doi") or {}
    if not isinstance(doi, dict):
        errors.append("doi must be an object")
    else:
        status = doi.get("status")
        if status not in STATUS_VALUES:
            errors.append(f"doi.status invalid: {status!r}")
        value = doi.get("value")
        if status == "present" and (not value or not DOI_RE.match(str(value))):
            errors.append(f"doi.value invalid for present status: {value!r}")
        if value and status != "present":
            errors.append("doi.value present but status is not present")
        if not value and status == "present":
            errors.append("doi.status present but value is empty")

    title = data.get("title") or {}
    if not isinstance(title, dict) or title.get("status") not in STATUS_VALUES:
        errors.append("title.status invalid")

    pdf = data.get("pdf") or {}
    if not isinstance(pdf, dict):
        errors.append("pdf must be an object")
    else:
        p = _resolve(pdf.get("path"), root)
        if not p or not _inside(p, root):
            errors.append("pdf.path is missing or outside project root")
        elif pdf.get("status") == "present":
            if check_files and not p.exists():
                errors.append(f"pdf.path does not exist: {pdf.get('path')}")
            elif check_files:
                actual = sha256_file(p)
                if actual != pdf.get("sha256"):
                    errors.append(f"pdf.sha256 mismatch: expected {pdf.get('sha256')}, got {actual}")
        elif pdf.get("status") not in STATUS_VALUES:
            errors.append(f"pdf.status invalid: {pdf.get('status')!r}")

    si = data.get("si") or {}
    if not isinstance(si, dict):
        errors.append("si must be an object")
    else:
        if si.get("status") not in STATUS_VALUES:
            errors.append(f"si.status invalid: {si.get('status')!r}")
        files = si.get("files")
        if not isinstance(files, list):
            errors.append("si.files must be a list")
            files = []
        for item in files:
            if not isinstance(item, dict):
                errors.append("si.files item is not an object")
                continue
            status = item.get("status")
            if status not in STATUS_VALUES:
                errors.append(f"si file status invalid: {status!r}")
            p = _resolve(item.get("path"), root)
            if not p or not _inside(p, root):
                errors.append(f"si.path missing or outside project root: {item.get('path')!r}")
                continue
            if status == "present" and check_files:
                if not p.exists():
                    errors.append(f"si file missing: {item.get('path')}")
                else:
                    actual = sha256_file(p)
                    if item.get("sha256") and actual != item.get("sha256"):
                        errors.append(f"si.sha256 mismatch: {item.get('path')}")
            elif status == "failed":
                errors.append(f"si file integrity failed: {item.get('path')}")
        if si.get("status") == "present" and not files:
            errors.append("si.status present but files is empty")

    elig = data.get("eligibility") or {}
    if not isinstance(elig, dict) or elig.get("status") not in STATUS_VALUES:
        errors.append("eligibility.status invalid")
    meta = data.get("metadata") or {}
    if not isinstance(meta, dict) or meta.get("status") not in STATUS_VALUES:
        errors.append("metadata.status invalid")
    download = data.get("download") or {}
    if not isinstance(download, dict) or download.get("status") not in STATUS_VALUES:
        errors.append("download.status invalid")
    warnings.extend(str(x) for x in (data.get("warnings") or []))
    return {"ok": not errors, "errors": errors, "warnings": warnings}


def manifest_path_for(data: dict, outdir: Path = MANIFEST_DIR) -> Path:
    name = sanitize_doi(data["paper_id"])
    return outdir / f"{name}.json"


def write_manifest(data: dict, outdir: Path = MANIFEST_DIR) -> Path:
    outdir.mkdir(parents=True, exist_ok=True)
    path = manifest_path_for(data, outdir)
    text = json.dumps(data, ensure_ascii=False, indent=2)
    path.write_bytes(text.encode("utf-8"))
    return path


def build_all(*, root: Path = ROOT, outdir: Path = MANIFEST_DIR) -> dict:
    known = _known_dois(root)
    triage = _triage(root)
    assessment = _assessment(root)
    entries = []
    errors = []
    for pdf in sorted((root / "data" / "raw_pdfs").glob("*.pdf")):
        try:
            data = build_manifest(pdf, root=root, known=known, triage=triage, assessment=assessment)
        except ManifestError as exc:
            errors.append({"pdf": pdf.name, "error": str(exc)})
            continue
        check = validate_manifest(data, root=root, check_files=False)
        if not check["ok"]:
            if data["si"]["status"] == "failed":
                # Keep the failed manifest on disk so B fails closed instead of
                # silently regenerating a legacy object from the same SI.
                path = write_manifest(data, outdir)
                entries.append({
                    "paper_id": data["paper_id"],
                    "doi": data["doi"]["value"],
                    "pdf": data["pdf"]["path"],
                    "si_status": data["si"]["status"],
                    "manifest": _rel(path, root),
                })
                errors.append({"pdf": pdf.name, "error": "; ".join(check["errors"])})
                continue
            errors.append({"pdf": pdf.name, "error": "; ".join(check["errors"])})
            continue
        path = write_manifest(data, outdir)
        entries.append({
            "paper_id": data["paper_id"],
            "doi": data["doi"]["value"],
            "pdf": data["pdf"]["path"],
            "si_status": data["si"]["status"],
            "manifest": _rel(path, root),
        })
    index = {
        "manifest_version": MANIFEST_VERSION,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "count": len(entries),
        "entries": entries,
        "errors": errors,
    }
    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "index.json").write_bytes(json.dumps(index, ensure_ascii=False, indent=2).encode("utf-8"))
    return index


def _load_stored_manifests(outdir: Path = MANIFEST_DIR) -> list[dict]:
    out = []
    for path in sorted(outdir.glob("*.json")):
        if path.name == "index.json":
            continue
        data = _read_json(path)
        if isinstance(data, dict):
            out.append(data)
    return out


def load_for_pdf(pdf: Path, *, root: Path = ROOT, outdir: Path = MANIFEST_DIR) -> tuple[dict, str]:
    """Return (manifest, source). source is stored or legacy."""
    pdf = pdf.resolve()
    pdf_hash = sha256_file(pdf)
    for data in _load_stored_manifests(outdir):
        stored_pdf = _resolve((data.get("pdf") or {}).get("path"), root)
        if (stored_pdf and stored_pdf.resolve() == pdf) or (data.get("pdf") or {}).get("sha256") == pdf_hash:
            check = validate_manifest(data, root=root)
            if not check["ok"]:
                raise ManifestError("; ".join(check["errors"]))
            return data, "stored"
    data = legacy_manifest(pdf, root=root)
    check = validate_manifest(data, root=root)
    if not check["ok"]:
        raise ManifestError("; ".join(check["errors"]))
    return data, "legacy"


def si_text(manifest: dict, *, root: Path = ROOT, max_chars: int = 30000) -> tuple[str | None, dict]:
    si = manifest.get("si") or {}
    if si.get("status") not in ("present", "pending"):
        return None, {"status": si.get("status") or "missing", "files": si.get("files") or []}
    texts = []
    files = []
    for item in si.get("files") or []:
        parsed = item.get("parsed") or {}
        pp = _resolve(parsed.get("path"), root) if parsed.get("path") else None
        if pp and pp.exists() and _inside(pp, root):
            texts.append(pp.read_text(encoding="utf-8", errors="ignore"))
        files.append({
            "type": item.get("type"),
            "path": item.get("path"),
            "sha256": item.get("sha256"),
            "parsed": parsed,
        })
    body = "\n\n".join(texts)[:max_chars]
    return body or None, {
        "status": "loaded" if body else "no_parsed_text",
        "manifest": si.get("manifest_path"),
        "files": files,
        "chars": len(body),
    }


def manifest_sha256(data: dict) -> str:
    return sha256_bytes(json.dumps(data, ensure_ascii=False, sort_keys=True).encode("utf-8"))
