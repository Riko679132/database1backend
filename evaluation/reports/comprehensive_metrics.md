# Comprehensive precision / recall / F1

- Preliminary: 38 L2 positive samples and 28 negative/boundary samples; labels are not human-verified.
- Positive samples: 38 (38 L2 reference)
- Negative/boundary samples: 28; with candidate: 18

## Acceptance level (record kept at L2)

| TP | FN | FP | TN | Precision | Recall | F1 | FAR (all negatives) | FAR (with candidate) |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 38 | 0 | 0 | 28 | 100.0% | 100.0% | 1.000 | 0.0% | 0.0% |

FP = extra L2 candidates not matched to a positive + negative false accepts. TN counts all negative samples, including those with no candidate record.

## Strict field level (all expected fields present and within tolerance)

| TP | FN | FP | Precision | Recall | F1 |
|---:|---:|---:|---:|---:|---:|
| 33 | 5 | 0 | 100.0% | 86.8% | 0.930 |

Strict failures:
- `24`: conditions.co2_partial_kPa:missing
- `25`: conditions.co2_partial_kPa:missing
- `26`: conditions.co2_partial_kPa:missing
- `58`: conditions.total_pressure_kPa:missing,loadings.lean:missing,performance.cyclic_capacity:missing,performance.regeneration_efficiency:missing
- `59`: performance.absorption_rate_volumetric:missing,performance.absorption_amount_volumetric:missing,performance.cyclic_capacity_volumetric:missing,performance.pka:missing

## Scope limits

- The positive set covers 7 papers; it is not a random sample of the literature.
- Negative labels are machine-derived and include 10 samples with no candidate record.
- Boundary samples are valid VLE points outside the current profile range; they are excluded from FAR and checked for false reject.
- No human verification has been performed; these metrics are preliminary.
