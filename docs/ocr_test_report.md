# OCR Test Report

## Tool

- OCR: RapidOCR (`rapidocr-onnxruntime` 1.4.4) on ONNX Runtime 1.32.0.
- Rendering: pypdfium2.
- No system Tesseract is required.
- Integration: `scripts/pdf_to_text.py --ocr auto|always|never` and `--ocr-dpi` (default 200).

## Test 1 — text PDF, auto mode

```powershell
.\.venv\Scripts\python.exe scripts\pdf_to_text.py `
  --pdf data\raw_pdfs\10.1021_acs.iecr.9b00552_6a66ebd9.pdf `
  --outdir .tmp_ocr\text --ocr auto
```

- pages: 10
- chars: 44,876
- OCR pages: 0
- Result: text layer used; no OCR overhead, no regression.

## Test 2 — known-content scan, always mode

A synthetic scan was rendered with known lines:

```
Table 1. CO2 Loading at 40 C
MEA 30 wt%  loading 0.609
AMP 30 wt%  loading 0.875
MDEA 30 wt%  loading 0.520
```

```powershell
.\.venv\Scripts\python.exe scripts\pdf_to_text.py `
  --pdf .tmp_ocr\known_scan.pdf --outdir .tmp_ocr\known --ocr always
```

- pages: 1
- OCR pages: [1]
- average confidence: 0.9679
- low-confidence items: 0
- Recognized text included: `Table 1`, `CO2`, `40`, `MEA`, `AMP`, `MDEA`, `30 wt%`, `0.609`, `0.875`, `0.520`.
- Result: all key chemical names, numbers and units recovered.
- Preserved test artifact: `evaluation/artifacts/ocr/known_scan.pdf`, `known_scan.txt`, `parse_report.json`.

## Test 3 — real rendered PDF page

A page from Barzagli 2019 was rendered at 200 DPI and OCRed.

- items: 103
- average confidence: 0.9724
- recognized: `MEA`, `AMP`, `MDEA`, `EMEA`, `CO2`, table/figure text.
- The page contained an NMR figure; OCR recognized labels but not the fine spectral structure. This is expected: OCR is not a chart digitizer.

## Integration and provenance

`parse_report.json` records:

```json
{
  "ocr": {
    "mode": "always",
    "tool": "rapidocr_onnxruntime",
    "dpi": 200,
    "pages": [1],
    "avg_confidence": 0.9679,
    "low_confidence_items": 0,
    "errors": []
  }
}
```

`server/tasks.py` reads this report and writes `parse_mode` and `ocr` metadata into the extraction snapshot.

## Limitations

- OCR text is approximate; it must not be treated as the exact paper text.
- Chemical subscripts (CO₂, H₂O), merged cells and multi-column tables can be misread.
- Confidence values are useful for triage but are not a calibrated probability of correctness.
- The test used rendered PDF pages and a synthetic known scan, not a large genuine scanner corpus. A real scanned-paper benchmark is still needed.
- OCR output is not automatically human-verified; a low-confidence item should be checked against the page image.

## Commands

```powershell
# only low-text pages
.\.venv\Scripts\python.exe scripts\pdf_to_text.py --pdf <file> --outdir <dir> --ocr auto

# force all pages
.\.venv\Scripts\python.exe scripts\pdf_to_text.py --pdf <file> --outdir <dir> --ocr always --ocr-dpi 300

# disable
.\.venv\Scripts\python.exe scripts\pdf_to_text.py --pdf <file> --outdir <dir> --ocr never
```
