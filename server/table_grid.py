"""Rebuild table-like pages by word coordinates for LLM extraction.

pdfplumber's plain text loses column boundaries on multi-column/no-border
tables. This module clusters words by y-band and sorts by x, producing a
page-local grid that the extraction prompt can use as a locating aid.
"""
from __future__ import annotations

import re
from pathlib import Path

import pdfplumber

NUM_RE = re.compile(r"\d+(?:\.\d+)?")


def _grid_rows(page) -> list[str]:
    words = page.extract_words(use_text_flow=False, keep_blank_chars=False)
    words.sort(key=lambda w: (round(w["top"] / 4), w["x0"]))
    rows: list[str] = []
    cur_band = None
    cur: list[dict] = []
    for w in words:
        band = round(w["top"] / 4)
        if cur_band is None or band == cur_band:
            cur.append(w)
            cur_band = band
        else:
            rows.append("  ".join(f"{x['text']}@{x['x0']:.0f}" for x in cur))
            cur = [w]
            cur_band = band
    if cur:
        rows.append("  ".join(f"{x['text']}@{x['x0']:.0f}" for x in cur))
    return rows


def build_table_context(
    pdf: Path,
    *,
    max_pages: int = 8,
    max_chars: int = 14000,
    min_numeric_rows: int = 3,
) -> tuple[str, list[int]]:
    if not pdf.exists():
        return "", []
    candidates: list[tuple[float, int, str]] = []
    with pdfplumber.open(pdf) as doc:
        for pno, page in enumerate(doc.pages, 1):
            try:
                text = page.extract_text() or ""
            except Exception:
                continue
            low = text.lower()
            numeric = len(NUM_RE.findall(text))
            if "table" not in low and numeric < 12:
                continue
            rows = _grid_rows(page)
            keep = [r for r in rows if len(NUM_RE.findall(r)) >= 2]
            if len(keep) < min_numeric_rows:
                continue
            block = f"\n--- Page {pno} table grid ---\n" + "\n".join(keep)
            score = (20 if "table" in low else 0) + numeric + len(keep) * 2
            candidates.append((score, pno, block))

    chosen: list[tuple[int, str]] = []
    total = 0
    for _, pno, block in sorted(candidates, key=lambda x: x[0], reverse=True):
        if len(chosen) >= max_pages:
            break
        if total + len(block) > max_chars:
            continue
        chosen.append((pno, block))
        total += len(block)
    chosen.sort(key=lambda x: x[0])
    blocks = [b for _, b in chosen]
    pages = [p for p, _ in chosen]
    header = (
        "\n【辅助表格重建（按 y 带聚类、行内按 x 坐标排序；@ 后是横坐标）】\n"
        "这些行只用于定位表头与列，不要把它们当作改写后的原文；如果与正文冲突，以正文表格/表注为准。\n"
    )
    return (header + "".join(blocks)) if blocks else "", pages
