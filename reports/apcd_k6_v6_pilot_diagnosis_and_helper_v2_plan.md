# APCD K=6 v6 Pilot Diagnosis and Weak-Helper v2 Plan

## Scope

This is 09-P39/P41. It diagnoses the failed v6 pilot and designs a weak-helper / triatomic meta-molecule v2 candidate scaffold.

No FDTD, lumapi, `.fsp`, YAML generation, old-pool run, full nextgen pool run, K=7, phase-ramp supercell, TiO2/450 nm, Micro-LED integration, ML training, +15 deg steering claim, or complete K=6 phase-state library claim was made.

## v6 Diagnosis

Current usable phase span remains 72.24132809604521 to 118.07875127181353 deg, concentrated in 60-120 deg.

- Released rotation did not fill 0 deg: it landed near 75.9 deg and failed leakage/ratio.
- Released dx/dy did not fill -60 deg: it moved to positive 154.7 deg and failed leakage/ratio.
- Weak-helper v1 did not early-pass: phase stayed near 78.6 deg and leakage/ratio failed.
- Helper v1 geometry pass was low because center/near-core helper placements overlapped or violated same-cell gap.

## Helper v2 Strategy

APCD core remains responsible for spin-selective conversion. The helper is a standalone weak auxiliary phase shifter that provides additional target-channel phase freedom; it is not another APCD dimer and not half of another APCD pair.

Helper v2 pool rows: 48
Geometry pass: 37/48

Family counts:
- `helper_v2_low_leakage_trim`: 8
- `helper_v2_medium_phase_delay`: 8
- `helper_v2_neg60_detour`: 8
- `helper_v2_pi_wrap_probe`: 8
- `helper_v2_weak_far_detour`: 8
- `helper_v2_zero_bridge`: 8

## Selected Not Run

| rank | candidate | target | family | priority |
|---:|---|---:|---|---|
| 1 | `wh2_zero_far_06` | 0 | `helper_v2_weak_far_detour` | top2_next_round |
| 2 | `wh2_neg60_detour_05` | -60 | `helper_v2_neg60_detour` | top2_next_round |
| 3 | `wh2_pi_wrap_04` | -180 | `helper_v2_pi_wrap_probe` | backup_selected_not_run |
| 4 | `wh2_lowleak_trim_03` | 0 | `helper_v2_low_leakage_trim` | backup_selected_not_run |

Next round: run only top-2 first, `wh2_zero_far_06` and `wh2_neg60_detour_05`.
