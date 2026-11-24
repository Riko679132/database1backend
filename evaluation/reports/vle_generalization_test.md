# VLE profile generalization test

- Result: PASS

| Paper | Structure | Data points | Selected | Skipped | Duplicates | Wrong association |
|---|---|---:|---:|---:|---:|---:|
| target_multi_column (`10.1021/je00005a025`) | multi-column repeated groups | 181 | 27 | 0 | 0 | 0 |
| vertical_bar_units (`10.1016/j.jece.2024.112664`) | vertical rows, bar units, multi-line cell | 3 | 1 | 2 | 0 | 0 |
| nested_loading_units (`10.1016/j.ijggc.2016.12.018`) | nested loading units, three methods | 2 | 2 | 0 | 0 | 0 |

## Details

```json
[
  {
    "paper": "target_multi_column",
    "doi": "10.1021/je00005a025",
    "structure": "multi-column repeated groups",
    "profile": true,
    "tables": 4,
    "data_points": 181,
    "selected": 27,
    "needs_profile_without_profile": true,
    "selected_without_profile": 0,
    "duplicates": 0,
    "wrong_associations": 0
  },
  {
    "paper": "vertical_bar_units",
    "doi": "10.1016/j.jece.2024.112664",
    "structure": "vertical rows, bar units, multi-line cell",
    "profile": true,
    "tables": 1,
    "data_points": 3,
    "selected": 1,
    "skipped_literature": 2,
    "skipped_other": 0,
    "duplicates": 0,
    "wrong_associations": 0,
    "values": {
      "temperature_K": 313.15,
      "p_CO2_kPa": 15.0,
      "loading": 0.537,
      "recipe": {
        "amine_a": "MEA",
        "wt_a": 30.0
      }
    }
  },
  {
    "paper": "nested_loading_units",
    "doi": "10.1016/j.ijggc.2016.12.018",
    "structure": "nested loading units, three methods",
    "profile": true,
    "tables": 1,
    "data_points": 2,
    "selected": 2,
    "skipped_literature": 0,
    "skipped_other": 0,
    "duplicates": 0,
    "wrong_associations": 0,
    "values": [
      {
        "row_type": "rich",
        "temperature_K": 313.15,
        "p_CO2_kPa": 9.5,
        "loading": 0.52
      },
      {
        "row_type": "lean",
        "temperature_K": 353.15,
        "p_CO2_kPa": 1.0,
        "loading": 0.26
      }
    ]
  }
]
```

Without a profile, the target parser returns `needs_profile=true` and selects 0; the 180 kPa / 40 C / 0.5 L constants are never applied to another paper.
