# APCD K=6 Combined Phase-Knob FDTD Selection v9

Selection only. No YAML/FDTD/lumapi/.fsp in 09-P48/P50.

| rank | candidate | family | target | priority |
|---:|---|---|---:|---|
| 1 | `cpk_rot_release_02` | `helper_plus_released_rotation` | -180 | top2_next_run |
| 2 | `cpk_height_prop_05` | `helper_plus_height_propagation` | -180 | top2_next_run |
| 3 | `cpk_period_phase_04` | `helper_plus_period_phase` | -180 | backup_selected_not_run |
| 4 | `cpk_position_scout_01` | `helper_position_phase_scout` | -180 | backup_selected_not_run |
| 5 | `cpk_strong_delay_07` | `strong_but_safe_phase_delay_helper` | -180 | backup_selected_not_run |

Recommended next run top-2: `cpk_rot_release_02` and `cpk_height_prop_05`.
