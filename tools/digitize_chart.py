"""Semi-automatic chart digitization with provenance.

This is not a replacement for WebPlotDigitizer's interactive curve tracing.
It provides a scriptable, traceable workflow for:
- extracting a chart region from a PDF page to PNG;
- calibrating linear/log axes from two pixel/value pairs;
- converting manually supplied pixel points, or auto-detecting colored markers,
  to data values;
- writing CSV + provenance JSON with hashes and an error estimate.

For overlapping curves or black-only markers, use manual points or an external
digitizer; do not claim automatic separation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import time
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
VERSION = "phase2-1.0"


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extract_chart(pdf: Path, page: int, bbox: tuple[int, int, int, int], dpi: int, out: Path) -> dict:
    import pypdfium2 as pdfium

    doc = pdfium.PdfDocument(str(pdf))
    img = doc[page - 1].render(scale=dpi / 72.0).to_pil().convert("RGB")
    x0, y0, x1, y1 = bbox
    crop = img.crop((x0, y0, x1, y1))
    out.parent.mkdir(parents=True, exist_ok=True)
    crop.save(out)
    meta = {
        "tool": "pypdfium2+Pillow",
        "version": VERSION,
        "pdf": str(pdf),
        "pdf_sha256": sha256_file(pdf),
        "page": page,
        "dpi": dpi,
        "bbox_px": list(bbox),
        "image_path": str(out),
        "image_sha256": sha256_file(out),
        "image_size": crop.size,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "human_verified": False,
    }
    meta_path = out.with_suffix(".provenance.json")
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def _map_axis(px: float, axis: dict) -> float:
    p1, v1 = axis["p1"]
    p2, v2 = axis["p2"]
    if axis.get("log"):
        lv1, lv2 = math.log10(v1), math.log10(v2)
        lv = lv1 + (px - p1) / (p2 - p1) * (lv2 - lv1)
        return 10 ** lv
    return v1 + (px - p1) / (p2 - p1) * (v2 - v1)


def detect_colored_markers(image_path: Path, color: str, min_area: int = 8, max_area: int = 2000) -> list[dict]:
    import cv2

    img = cv2.imread(str(image_path))
    if img is None:
        raise ValueError(f"cannot read image: {image_path}")
    hex_color = color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    target = np.array([b, g, r], dtype=np.int16)
    diff = np.abs(img.astype(np.int16) - target).sum(axis=2)
    mask = (diff < 90).astype(np.uint8) * 255
    n, labels, stats, centroids = cv2.connectedComponentsWithStats(mask, 8)
    points = []
    for i in range(1, n):
        area = int(stats[i, cv2.CC_STAT_AREA])
        if min_area <= area <= max_area:
            x, y = centroids[i]
            points.append({"label": f"auto_{len(points)+1}", "x_px": float(x), "y_px": float(y), "area_px": area})
    points.sort(key=lambda p: p["x_px"])
    return points


def digitize(
    image_path: Path,
    calibration: dict,
    points: list[dict],
    outdir: Path,
    source_meta: dict | None = None,
) -> dict:
    x_axis, y_axis = calibration["x"], calibration["y"]
    rows = []
    for p in points:
        xv = _map_axis(float(p["x_px"]), x_axis)
        yv = _map_axis(float(p["y_px"]), y_axis)
        rows.append({
            "label": p.get("label") or f"p{len(rows)+1}",
            "x_px": round(float(p["x_px"]), 2),
            "y_px": round(float(p["y_px"]), 2),
            "x_value": round(xv, 6),
            "y_value": round(yv, 6),
        })
    outdir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    csv_path = outdir / f"digitized_{stamp}.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["label", "x_px", "y_px", "x_value", "y_value"])
        w.writeheader()
        w.writerows(rows)
    x_scale = abs((x_axis["p2"][1] - x_axis["p1"][1]) / (x_axis["p2"][0] - x_axis["p1"][0])) if x_axis["p2"][0] != x_axis["p1"][0] else None
    y_scale = abs((y_axis["p2"][1] - y_axis["p1"][1]) / (y_axis["p2"][0] - y_axis["p1"][0])) if y_axis["p2"][0] != y_axis["p1"][0] else None
    provenance = {
        "tool": "digitize_chart.py",
        "version": VERSION,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "image_path": str(image_path),
        "image_sha256": sha256_file(image_path),
        "calibration": calibration,
        "points": rows,
        "csv_path": str(csv_path),
        "csv_sha256": sha256_file(csv_path),
        "error_estimate": {
            "x_value_per_px": x_scale,
            "y_value_per_px": y_scale,
            "note": "Pixel scale only; not a full uncertainty. Overlapping curves, line width and axis calibration add error.",
        },
        "source": source_meta or {},
        "human_verified": False,
    }
    prov_path = outdir / f"digitized_{stamp}.provenance.json"
    prov_path.write_text(json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"csv": str(csv_path), "provenance": str(prov_path), "rows": len(rows)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("extract", help="extract a page region to PNG")
    p.add_argument("--pdf", required=True)
    p.add_argument("--page", type=int, required=True)
    p.add_argument("--bbox", type=int, nargs=4, required=True, metavar=("X0", "Y0", "X1", "Y1"))
    p.add_argument("--dpi", type=int, default=300)
    p.add_argument("--out", required=True)

    p = sub.add_parser("digitize", help="calibrate and convert pixels to values")
    p.add_argument("--image", required=True)
    p.add_argument("--calibration", required=True, help="JSON with x/y p1,p2 and optional log flags")
    p.add_argument("--points", help="JSON with points[{label,x_px,y_px}]")
    p.add_argument("--auto-color", help="hex color for auto marker detection, e.g. #ff0000")
    p.add_argument("--outdir", default=str(ROOT / "evaluation" / "artifacts" / "chart_digitization"))

    args = ap.parse_args()
    if args.cmd == "extract":
        meta = extract_chart(Path(args.pdf), args.page, tuple(args.bbox), args.dpi, Path(args.out))
        print(json.dumps(meta, ensure_ascii=False, indent=2))
        return

    image = Path(args.image)
    calibration = json.loads(Path(args.calibration).read_text(encoding="utf-8"))
    if args.points:
        points = json.loads(Path(args.points).read_text(encoding="utf-8")).get("points") or []
    elif args.auto_color:
        points = detect_colored_markers(image, args.auto_color)
    else:
        raise SystemExit("provide --points or --auto-color")
    source_meta = {}
    prov = image.with_suffix(".provenance.json")
    if prov.exists():
        try:
            source_meta = json.loads(prov.read_text(encoding="utf-8"))
        except ValueError:
            pass
    result = digitize(image, calibration, points, Path(args.outdir), source_meta)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
