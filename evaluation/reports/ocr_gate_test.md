# OCR quality-gate test

- Result: PASS
- OCR: RapidOCR (`rapidocr_onnxruntime`), page rendering pypdfium2.
- `jece_p6.pdf` is one native-text page copied from the real jece paper; `jece_blur.pdf` is a degraded synthetic scan derived from it.

| Check | Result | Decision | Detail |
|---|---|---|---|
| real_known_scan_auto | PASS | pass | `{"avg_confidence": 0.9679, "critical_conflicts": 0, "reasons": [], "pages": [1], "recognized_chars": 118}` |
| real_text_page_forced_ocr | PASS | pass | `{"avg_confidence": 0.9928, "critical_conflicts": 0, "reasons": [], "critical_ocr": {"temperature": ["286.15K", "313.15K"], "concentration": ["30wt%"], "loading": ["2", "30"], "rate_scale": ["0.35e-46"], "formula": ["AMP", "CO2", "H2O", "MDEA", "MEA"]}}` |
| degraded_scan_auto | PASS | fail | `{"avg_confidence": null, "reasons": ["empty_ocr_text", "missing_confidence"], "recognized_chars": 21}` |
| critical_field_conflict_fixture | PASS | review | `{"conflicts": [{"field": "concentration", "native": ["30wt%"], "ocr": ["80wt%"]}], "reasons": ["critical_field_conflicts_1"]}` |
| low_confidence_fixture | PASS | review | `{"avg_confidence": 0.495, "reasons": ["low_avg_confidence_0.49", "low_confidence_ratio_1.00"]}` |
| summarize_report | PASS | fail | `{"pages": [1]}` |

The degraded scan is a stress fixture, not a genuine scanner corpus.
`pass` means usable as-is; `review` means a human/again-OCR check is required; `fail` means B must stop.
