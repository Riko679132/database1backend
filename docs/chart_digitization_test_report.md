# Chart Digitization Test Report

## Tool

`tools/digitize_chart.py` (phase2-1.0):

- `extract`: render a PDF page region to PNG and record PDF/image SHA-256, page, DPI, bbox.
- `digitize`: calibrate linear/log x/y axes from two pixel/value pairs; convert manual points or auto-detected colored markers to CSV.
- Writes CSV + provenance JSON (image/CSV hashes, calibration, points, error estimate, `human_verified:false`).
- WebPlotDigitizer is not integrated: it is an interactive web tool without a stable batch API. This script is the project's equivalent semi-automatic workflow.

## Test 1 — synthetic chart with known truth

Test image: 800×600, x axis 0–100 at pixels 100–700, y axis 0–10 at pixels 500–100. Red markers at known data points:

| Expected x | Expected y | Pixel (x,y) |
|---:|---:|---|
| 20 | 3 | (220, 380) |
| 50 | 6 | (400, 260) |
| 80 | 9 | (580, 140) |

```powershell
python tools\digitize_chart.py digitize `
  --image evaluation\artifacts\chart_digitization\synthetic_chart.png `
  --calibration evaluation\artifacts\chart_digitization\calibration.json `
  --auto-color "#ff0000"
```

Output:

```
auto_3,220.0,380.0,20.0,3.0
auto_2,400.0,260.0,50.0,6.0
auto_1,580.0,140.0,80.0,9.0
```

- 3/3 points recovered exactly.
- Error estimate: x 0.1667 value/px, y 0.025 value/px (pixel scale only).
- Provenance records image SHA-256, CSV SHA-256, calibration, points and `human_verified:false`.

## Test 2 — real PDF figure extraction

```powershell
python tools\digitize_chart.py extract `
  --pdf data\raw_pdfs\10.1021_acs.iecr.9b00552_6a66ebd9.pdf `
  --page 4 --bbox 0 0 2550 3300 --dpi 200 `
  --out evaluation\artifacts\chart_digitization\barzagli_p4.png
```

- image: 2550×3300
- image SHA-256: `b158fbde0741a47c9870cbc2e0528b92664a7b0c6da5442fb74b566a30f22637`
- metadata saved as `.provenance.json`.

## Limitations

- Automatic detection works for **colored markers** after axis calibration; it does not separate overlapping curves or black-only markers.
- Axes, ticks and calibration points must be chosen by a human for each figure; log axes are supported but must be flagged.
- The error estimate is pixel scale only; line width, overlap, image resolution and calibration error are not a full uncertainty.
- For complex figures, use manual points or an external digitizer; do not claim automatic curve extraction.
- Digitized values remain L3 unless a human verifies them and the figure provenance is recorded.

## Commands

```powershell
# extract a figure region
python tools\digitize_chart.py extract --pdf <pdf> --page <n> --bbox X0 Y0 X1 Y1 --dpi 300 --out <png>

# manual points: JSON {"points":[{"label":"MEA","x_px":..,"y_px":..}]}
python tools\digitize_chart.py digitize --image <png> --calibration <json> --points <json>

# colored markers
python tools\digitize_chart.py digitize --image <png> --calibration <json> --auto-color "#ff0000"
```
