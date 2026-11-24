# Phase-4 Lessons

## Reference rows can be scattered across table + methods + results

- A 30 wt% MEA baseline may appear as Table 4 composition, methods conditions and results text, with no standalone performance table.
- The LLM can correctly return 0 for a paper whose main system is out of scope, even when a reference row exists.
- Use a paper-specific reference profile when needed:
  - DOI/scope/version and evidence location;
  - regexes to parse values from the paper text;
  - no hardcoded final values;
  - profile applied only to that DOI.
- d6gc 2026: Table 4 MEA 30/70, 12 kPa, 313 K, fresh 150 mL, 55%, 3.72 GJ/t.

## Conditions must be evidence-backed

- Derive CO2 partial pressure only when both gas composition and total pressure are explicit:
  `P_CO2 = vol% / 100 × P_total`.
- Do not assume 1 atm for jece 2024.
- A paper-specific condition profile may fill atmospheric pressure/20% CO2 only when the text says so (ie400825).
- Leave null when the total pressure is not stated.

## Metric labels can be semantically wrong even when values are correct

- `regeneration_heat` in kJ/mol with a negative sign is heat of absorption/reaction, not regeneration heat.
- Keep the value and original unit, but downgrade L2 to L3 and flag `metric_definition_mismatch_regeneration_heat_is_heat_of_absorption`.
- Do not silently rename to a new enum value; propose an extension.

## Negative set must distinguish labels

- `Valid L3`: real data outside the L2 target, not negative.
- `Insufficient Evidence`: L3 reference acceptable; L2 is a false accept.
- `Out of Scope`/`Duplicate`/`Negative`: no accepted record.
- `Model-derived`: L3 only.
- High pressure alone is not a negative label.

## VLE profiles

- Generic algorithm detects repeated t/p/loading column groups; paper profile selects temperature/pressure/volume.
- With no profile, select 0 points and report `needs_profile=true`; never apply another paper's constants.
- Cross-paper test: only the target paper is currently parseable; three other layouts need profiles. Do not claim universal VLE parsing.

## Human gold standard

- A review packet is not a human gold standard. Keep `human_verified=false` and `review_status=pending` until a person checks evidence.
- Historical-label agreement (97.25%) is not human accuracy.
