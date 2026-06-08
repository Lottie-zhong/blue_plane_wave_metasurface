# P179 Stage 10 phase-library freeze

## Scope

This is a Stage 10 input freeze of the Stage 09 single-dimer phase-state library only; it is not K=6 steering yet, not a K=6 phase-ramp supercell, not a +15 deg beam deflection result, and not a Micro-LED result.

The table freezes one official single-dimer phase-state anchor per bin for Stage 10 input preparation.
This script reads existing CSV/report evidence only and does not run FDTD, call lumapi, or edit `configs/runtime.yaml`.

## Inputs

- compact Stage 09 coverage CSV: `outputs/apcd_k6_active_learning/stage09_phase_state_coverage_after_p178.csv`
- latest row-level source CSV: `outputs/apcd_k6_active_learning/combined_phase_knob_phase_state_coverage_p139.csv`
- phase-coverage source CSV: `outputs/apcd_k6_active_learning/phase_coverage_v8.csv`
- P178 official zero-bin report: `reports/p178_zero_bin_opened_final_decision.md`
- source read: `outputs/apcd_k6_active_learning/combined_phase_knob_phase_state_coverage_p139.csv`
- source read: `outputs/apcd_k6_active_learning/phase_coverage_v8.csv`
- source read: `outputs/apcd_k6_active_learning/aggressive_phase_gap_top2_fdtd_results_v1.csv`
- source read: `outputs/apcd_k6_active_learning/accumulated_fdtd_diagnosis_v5.csv`
- source read: `outputs/apcd_k6_active_learning/p177_h232_zero_coupled_results.csv`

## Frozen Library

| bin_deg | candidate_id | phase_deg | phase_error_to_bin | target_conversion | leakage | ratio | early_pass |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |
| -180 | `cpk_resphase_scale104_nohelper_01` | -179.81204497638768 | 0.18795502361231797 | 0.9173492195087667 | 0.09002136925293662 | 10.190349548250746 | True |
| -120 | `cpk_060_anchor_wh03_h425_scale98_01` | -120.03085152462465 | 0.03085152462466567 | 0.914178722486521 | 0.08855793276990336 | 10.322945600508461 | True |
| -60 | `cpk_060_boundary_h435_aniso_reduce10_01` | -66.33411515401983 | 6.334115154019827 | 0.8588550425801951 | 0.13843098639575319 | 6.20421095692878 | True |
| 0 | `cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` | 23.01 | 23.00999999999999 | 0.809 | 0.105 | 7.67 | True |
| 60 | `aggr_lhs_retention_dy_05` | 72.24132809604521 | 12.241328096045208 | 0.8570222822237621 | 0.1028870531101224 | 8.329738837977422 | True |
| 120 | `cpk_rot_release_02` | 120.25715682505454 | 0.25715682505455106 | 0.9364983370134424 | 0.06742385860976192 | 13.88971732426127 | True |

## Sanity

| check | status | details |
| --- | --- | --- |
| exact_six_bins | pass | [-180, -120, -60, 0, 60, 120] |
| coverage_csv_exact_bins | pass | [-180, -120, -60, 0, 60, 120] |
| coverage_csv_all_covered | pass | [] |
| one_selected_anchor_per_bin | pass | [cpk_resphase_scale104_nohelper_01, cpk_060_anchor_wh03_h425_scale98_01, cpk_060_boundary_h435_aniso_reduce10_01, cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01, aggr_lhs_retention_dy_05, cpk_rot_release_02] |
| selected_anchors_early_pass | pass | [] |
| zero_anchor_is_recommended | pass | cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01 |
| missing_bins | pass | [] |
| no_overclaim_wording | pass | This is a Stage 10 input freeze of the Stage 09 single-dimer phase-state library only; it is not K=6 steering yet, not a K=6 phase-ramp supercell, not a +15 deg beam deflection result, and not a Micro-LED result. |
| source_csvs_read | pass | [outputs/apcd_k6_active_learning/combined_phase_knob_phase_state_coverage_p139.csv, outputs/apcd_k6_active_learning/phase_coverage_v8.csv, outputs/apcd_k6_active_learning/aggressive_phase_gap_top2_fdtd_results_v1.csv, outputs/apcd_k6_active_learning/accumulated_fdtd_diagnosis_v5.csv, outputs/apcd_k6_active_learning/p177_h232_zero_coupled_results.csv] |

## Outputs

- frozen library: `outputs/apcd_k6_active_learning/p179_stage10_frozen_phase_library.csv`
- sanity CSV: `outputs/apcd_k6_active_learning/p179_stage10_phase_library_sanity.csv`

## Next Step

Use this frozen single-dimer table as Stage 10 input only after preserving the no-overclaim boundary above.
