# Phase 4 — Human Review Progress

## Status

**Human-verified gold standard: 0/38.** No claim of human accuracy is made.

A review-ready packet exists:

- `evaluation/human_review_packet_v1.json`
- `evaluation/human_review_packet_v1.csv`

Each sample contains:

- sample ID, DOI, PDF path, final snapshot path;
- historical recipe/conditions/performance;
- final extracted metrics and QC;
- priority and agent precheck;
- blank human fields: `human_verified`, `review_status`, `human_verdict`, `reviewer`, `review_time`, `disputed_fields`, `notes`.

All 38 records are `review_status=pending`, `human_verified=false`.

## Priority distribution

| Priority | Count | Meaning |
|---|---:|---|
| 1 | 28 | 27 VLE points + d6gc reference-row case |
| 2 | 3 | jece rate-unit cases (plus complex blends as assigned) |
| 3 | 1 | unit-sensitive sample |
| 4 | 6 | remaining normal L2 samples |

## Metrics that are / are not available

Available:

- agreement with historical L2 labels: **97.25% field-level** (38/38 coverage, 97.25% fields within tolerance);
- positive recall: 38/38;
- negative false-accept: 0/18 (limited negative set).

Not available:

- human-verified field-level agreement;
- human-verified sample-level exact agreement;
- human-confirmed precision/recall.

The historical-label agreement is **not** a human gold-standard accuracy. It must not be reported as one.

## Recommended review order

1. d6gc reference-row record (new profile path).
2. 27 VLE points (table/group/temperature/pressure/loading).
3. jece rate records (1e-5 unit, original value/unit).
4. Binary-blend recipe records.
5. Remaining L2 samples.

## What a reviewer must check per sample

- amine identity/recipe and mass closure;
- temperature;
- total pressure and CO2 partial pressure (or null reason);
- initial/rich/lean loading;
- performance metric definition and unit;
- evidence location and classification;
- snapshot path/hash;
- disputed fields.

Human review is a required next step before any claim of production-grade accuracy.
