"""Discover, download and parse Supporting Information (SI) via the CDP browser.

The script reuses the project's authorized Chrome session on 127.0.0.1:9222.
It does not bypass access control: if a file is paywalled or login-gated, the
failure is recorded and the original URL is kept.

Output: data/raw_si/<sanitized doi>/si_manifest.json plus downloaded files and
optional parsed text/tables.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import re
import time
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
CDP = "http://127.0.0.1:9222"
SI_WORDS = re.compile(r"support|supplement|supplementary|additional data|appendix|esi", re.I)
FILE_EXT = {".pdf", ".csv", ".xlsx", ".xls", ".docx", ".doc", ".zip", ".txt"}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sanitize(doi: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", doi)


def guess_type(url: str, content_type: str) -> str:
    ct = (content_type or "").lower()
    if "pdf" in ct:
        return "pdf"
    if "csv" in ct or "text/plain" in ct:
        return "csv" if url.lower().endswith(".csv") or "csv" in ct else "text"
    if "spreadsheet" in ct or "excel" in ct or url.lower().endswith((".xlsx", ".xls")):
        return "xlsx"
    if "word" in ct or url.lower().endswith((".docx", ".doc")):
        return "docx"
    if "zip" in ct or url.lower().endswith(".zip"):
        return "zip"
    ext = Path(urlparse(url).path).suffix.lower()
    return {".pdf": "pdf", ".csv": "csv", ".xlsx": "xlsx", ".xls": "xlsx", ".docx": "docx", ".doc": "docx", ".zip": "zip"}.get(ext, "other")


async def discover_and_download(doi: str | None, url: str | None, outdir: Path, max_files: int) -> dict:
    from playwright.async_api import async_playwright

    target = url or (f"https://doi.org/{doi}" if doi else None)
    if not target:
        raise ValueError("provide --doi or --url")
    outdir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "tool": "fetch_si.py",
        "version": "phase2-1.0",
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "doi": doi,
        "requested_url": target,
        "si_found": False,
        "links": [],
        "files": [],
        "errors": [],
        "human_verified": False,
    }
    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(CDP)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                f"CDP not reachable at {CDP}: {exc}. Start tools/start_cdp_browser.ps1 first."
            ) from exc
        ctx = browser.contexts[0] if browser.contexts else await browser.new_context()
        page = await ctx.new_page()
        try:
            await page.goto(target, wait_until="domcontentloaded", timeout=60000)
            await page.wait_for_timeout(2500)
            links = await page.eval_on_selector_all(
                "a",
                "els => els.map(e => ({t:(e.innerText||'').trim(), h:e.href})).filter(x => x.h)",
            )
            relevant = []
            seen = set()
            bad_domains = ("acs.service-now.com", "scholar.google.com", "wolsupport", "hub.wiley.com")
            for link in links:
                text = link.get("t") or ""
                href = link.get("h") or ""
                if not (SI_WORDS.search(text) or SI_WORDS.search(href)):
                    continue
                if href.startswith("javascript:") or any(d in href for d in bad_domains):
                    continue
                if href.endswith("#supplementary-data") or "goto=supporting-info" in href:
                    continue
                if href in seen:
                    continue
                seen.add(href)
                relevant.append({"text": text[:160], "url": href})
            file_like = [
                x for x in relevant
                if any(ext in x["url"].lower() for ext in FILE_EXT)
                or "article-supplement" in x["url"].lower()
                or "/suppl" in x["url"].lower()
            ]
            candidates = file_like or relevant
            manifest["all_links"] = relevant[:30]
            manifest["links"] = candidates[:30]
            manifest["si_found"] = bool(candidates)
            req = ctx.request
            for i, link in enumerate(candidates[:max_files], 1):
                href = link["url"]
                try:
                    resp = await req.get(href, timeout=45000)
                    body = await resp.body()
                    ctype = resp.headers.get("content-type", "")
                    status = resp.status
                    ftype = guess_type(href, ctype)
                    entry = {
                        "url": href,
                        "text": link["text"],
                        "http_status": status,
                        "content_type": ctype,
                        "type": ftype,
                        "bytes": len(body),
                    }
                    if status >= 400 or not body:
                        entry["status"] = "failed"
                        entry["error"] = f"HTTP {status} or empty body"
                        manifest["files"].append(entry)
                        continue
                    if ftype in ("other", "text") and "html" in ctype.lower():
                        entry["status"] = "not_a_file"
                        entry["error"] = "link returns HTML (landing/redirect), not a SI file"
                        manifest["files"].append(entry)
                        continue
                    ext = {"pdf": ".pdf", "csv": ".csv", "xlsx": ".xlsx", "docx": ".docx", "zip": ".zip", "text": ".txt"}.get(ftype, ".bin")
                    path = outdir / f"si_{i:02d}{ext}"
                    path.write_bytes(body)
                    entry.update({
                        "status": "downloaded",
                        "path": path.as_posix(),
                        "sha256": sha256_bytes(body),
                    })
                    manifest["files"].append(entry)
                except Exception as exc:  # noqa: BLE001
                    manifest["files"].append({"url": href, "text": link["text"], "status": "failed", "error": str(exc)[:300]})
        finally:
            await page.close()
    return manifest


def parse_downloaded(manifest: dict, outdir: Path) -> None:
    parsed_dir = outdir / "parsed"
    parsed_dir.mkdir(parents=True, exist_ok=True)
    for f in manifest.get("files") or []:
        if f.get("status") != "downloaded" or not f.get("path"):
            continue
        path = Path(f["path"])
        ftype = f.get("type")
        try:
            if ftype == "pdf":
                import pdfplumber
                with pdfplumber.open(path) as pdf:
                    text = "\n\n".join(f"--- Page {i} ---\n{p.extract_text() or ''}" for i, p in enumerate(pdf.pages, 1))
                txt = parsed_dir / (path.stem + ".txt")
                txt.write_text(text, encoding="utf-8")
                f["parsed"] = {"kind": "pdf_text", "path": txt.as_posix(), "chars": len(text), "pages": len(pdf.pages)}
            elif ftype == "csv":
                import csv
                rows = list(csv.reader(path.open(encoding="utf-8-sig", errors="ignore")))
                f["parsed"] = {"kind": "csv", "rows": len(rows), "header": rows[0][:20] if rows else [], "preview": rows[1:6]}
            elif ftype == "xlsx":
                import openpyxl
                wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
                sheets = []
                for ws in wb.worksheets:
                    sheets.append({"name": ws.title, "rows": ws.max_row, "cols": ws.max_column})
                f["parsed"] = {"kind": "xlsx", "sheets": sheets}
            elif ftype == "docx":
                import docx
                doc = docx.Document(path)
                f["parsed"] = {
                    "kind": "docx",
                    "paragraphs": len(doc.paragraphs),
                    "tables": len(doc.tables),
                    "preview": [p.text[:200] for p in doc.paragraphs[:8] if p.text.strip()],
                }
            elif ftype == "zip":
                import zipfile
                with zipfile.ZipFile(path) as z:
                    f["parsed"] = {"kind": "zip", "members": z.namelist()[:50], "count": len(z.namelist())}
            else:
                f["parsed"] = {"kind": "unsupported", "note": "file type not parsed"}
        except Exception as exc:  # noqa: BLE001
            f["parse_error"] = str(exc)[:300]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--doi")
    ap.add_argument("--url")
    ap.add_argument("--outdir", default=str(ROOT / "data" / "raw_si"))
    ap.add_argument("--max-files", type=int, default=6)
    ap.add_argument("--no-parse", action="store_true")
    args = ap.parse_args()
    key = sanitize(args.doi or urlparse(args.url or "").netloc or "si")
    outdir = Path(args.outdir) / key
    manifest = asyncio.run(discover_and_download(args.doi, args.url, outdir, args.max_files))
    if not args.no_parse:
        parse_downloaded(manifest, outdir)
    manifest_path = outdir / "si_manifest.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "manifest": manifest_path.as_posix(),
        "si_found": manifest["si_found"],
        "links": len(manifest["links"]),
        "files": [
            {"type": f.get("type"), "status": f.get("status"), "path": f.get("path"), "parsed": f.get("parsed")}
            for f in manifest["files"]
        ],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
