# APCD K=6 Weak-Helper v2 FDTD Selection Summary

Scope: selection only. No YAML/FDTD/lumapi/.fsp.

| rank | candidate | target | family | priority |
|---:|---|---:|---|---|
| 1 | `wh2_zero_far_06` | 0 | `helper_v2_weak_far_detour` | top2_next_round |
| 2 | `wh2_neg60_detour_05` | -60 | `helper_v2_neg60_detour` | top2_next_round |
| 3 | `wh2_pi_wrap_04` | -180 | `helper_v2_pi_wrap_probe` | backup_selected_not_run |
| 4 | `wh2_lowleak_trim_03` | 0 | `helper_v2_low_leakage_trim` | backup_selected_not_run |

Next round should run top-2 first: `wh2_zero_far_06` and `wh2_neg60_detour_05`.
