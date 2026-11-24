# Water-vapour / dry-wet basis test

- Result: PASS

| Case | Result | QC before→after | P_CO2 | Gas status |
|---|---|---|---|---|
| A_explicit_p_h2o | PASS | L2→L2 | 15.0 | assessed |
| B_wet_basis | PASS | L2→L2 | 15.19875 | derived_wet_basis |
| C_dry_with_p_h2o | PASS | L2→L2 | 14.08875 | derived_dry_basis_with_p_h2o |
| D_dry_without_p_h2o | PASS | L2→L2 | None | blocked_dry_basis_missing_p_h2o |
| E_no_water_info | PASS | L2→L2 | 15.0 | assessed |
| F_unknown_basis_no_partial | PASS | L2→L2 | None | blocked_basis_unknown |
| G_pco2_gt_total | PASS | L2→L3 | 120.0 | anomaly |
| H_component_sum_gt_total | PASS | L2→L3 | 98.0 | anomaly |
| I_wet_fraction_mismatch | PASS | L2→L3 | 30.0 | anomaly |
| A_check | PASS | - | - | - |
| B_check | PASS | - | - | - |
| C_check | PASS | - | - | - |
| D_check | PASS | - | - | - |
| E_check | PASS | - | - | - |
| F_check | PASS | - | - | - |
| G_check | PASS | - | - | - |
| H_check | PASS | - | - | - |
| I_check | PASS | - | - | - |
| pure_water_saturation | PASS | - | - | - |
| solution_requires_activity | PASS | - | - | - |
| real_db_scan | PASS | - | - | - |

Missing water-vapour data is `not_assessable`, not a rejection. Dry-basis composition without P_H2O leaves P_CO2 null. P_CO2 > P_total or component-sum > P_total downgrades L2 to L3.

Full JSON: `evaluation/reports/water_vapor_test.json`
