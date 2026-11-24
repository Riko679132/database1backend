# Phase 4 — VLE Method Profile Specification and Cross-Paper Test

## Separation of layers

### Generic algorithm (`server/vle_table_parser.py`)

- Reads PDF words with coordinates.
- Finds repeated `t/…`, `p/kPa`, `loading` column groups.
- Assigns numeric tokens to the nearest column.
- Carries temperature down a group, skips interleaved footnotes.
- Parses table caption/recipe.
- Reports tables, groups, data rows and points.

### Paper method profile

A profile declares only paper-specific facts:

- DOI and profile version;
- source/evidence location;
- target temperature group;
- maximum CO2 partial pressure for the selected apparatus;
- total pressure and liquid volume from the methods;
- columns/units mapping;
- scope and applicability.

The target profile:

```json
{
  "doi": "10.1021/je00005a025",
  "version": "phase4-1.0",
  "source": "Shen & Li 1992, methods p.97 (180 kPa, 0.5 L) and Tables II-V (40 C group)",
  "target_temperature_C": 40,
  "max_p_CO2_kPa": 180,
  "total_pressure_kPa": 180,
  "liquid_volume_L": 0.5
}
```

These constants are **not** applied when no profile exists. `parse_vle_tables(pdf, None)` returns `needs_profile=true` and selects 0 points.

## Cross-paper test

Command: `evaluation/test_vle_profiles.py`

| Paper | Structure | Profile | Tables detected | All points | Selected 27? |
|---|---|---|---:|---:|---:|
| `10.1021/je00005a025` | multi-column, 4 tables, cross-page | yes | 4 | 181 | **27** |
| `10.1021/ie400825u` | single MDEA table / different layout | no | 0 | 0 | 0 |
| `10.1016/j.ijggc.2016.12.018` | MEA VLE, different layout | no | 0 | 0 | 0 |
| `10.1016/j.apenergy.2016.03.043` | amine screening, different layout | no | 0 | 0 | 0 |

Result: **PASS** for the separation test:

- the target paper uses its profile and selects 27;
- the other three papers have `needs_profile=true` and select 0;
- no target temperature/pressure/volume is applied to another paper.

## Conclusion and limitation

The parser is **not** a universal VLE extractor. It has a reusable column-group algorithm plus paper-specific profiles. Three other VLE papers need their own header mappings/profiles before extraction. No false application was observed in this test.

This is the correct architecture: generic structure detection must not silently inherit another paper's apparatus constants.
