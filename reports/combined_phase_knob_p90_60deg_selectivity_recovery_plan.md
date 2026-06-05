# 09-P90 60deg selectivity-recovery plan

## Scope

This is a stage 09 compact plan for recovering selectivity near the 60 deg phase branch. It does not enter stage 10, does not use a K=6 phase-ramp supercell, and makes no steering claim.

## Evidence base

P88 showed that all selected leakage-recovery candidates land nearest to 60 deg, but none reached early-pass. The best tradeoff was `cpk_60rec_counter_m40_relax_01`, with phase `65.4628 deg`, leakage `0.3364`, and ratio `1.9588`.

The current early-pass bins remain `[-180, -120, 120]`; missing bins remain `[-60, 0, 60]`.

## Plan

P90 stops stronger common-offset sweeps and helper-position sweeps. It proposes 8 candidates across four families:

- `core_relative_angle_restoration`
- `pillar2_mild_geometry_compensation`
- `leakage_channel_suppression_helper`
- `m35_m40_phase_preserving_core_compensation`

All candidates keep period `340/340`, height `300`, and no lower-transition geometry. No candidate uses height `>=440`, and no candidate rolls pillar2 back to `150x85` beta-selective geometry.

## Selected top 4

1. `cpk_60sel_relangle_m40_diff35_01`
2. `cpk_60sel_p2geom_m40_90x145_01`
3. `cpk_60sel_helper_suppress_m40_40x90_01`
4. `cpk_60sel_corecomp_m35_p2_90x145_01`

Success requires nearest bin `60`, `target_conversion >= 0.5`, leakage `<= 0.2`, ratio `>= 6`, and `opens_missing_bin=True`.

No raw `results.csv`, raw `summary.md`, `.fsp`, pre-run file, `.npy`, or large output is created by this plan.
