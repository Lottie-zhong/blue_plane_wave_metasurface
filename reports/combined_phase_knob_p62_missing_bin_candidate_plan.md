# 09-P62 missing-bin candidate planning

## Scope

This report plans the next missing-bin candidate pool after P61.

This is a planning report only. It does not include new FDTD results.

The work is still single-dimer phase-state refinement. It is not a K=6 phase-ramp supercell, not a +15 degree steering result, not K=7, not a 450 nm / Micro-LED integration result, not DenseNet/cVAE training, and not a complete K=6 phase-state library.

## P61 input status

- Early-pass bins from P61: [-120, 120]
- Missing bins to target in P62: [-180, -60, 0, 60]

P60 strengthened the -120 deg bin but did not open new bins. Therefore P62 should stop polishing -120 deg and focus on missing bins.

## Candidate plan

| priority | candidate | family | target missing bin | base reference | height | period x/y | helper LxW rot | risk | run recommendation |
|---:|---|---|---:|---|---:|---|---|---|---|
| 1 | cpk_mbin_hprop_01 | missing_bin_height_period_phase | -180 | cpk_refine_htrans_04 | 440 | 340/340 | 70x120, 135 deg | medium_high | top1_if_no_geometry_issue |
| 2 | cpk_mbin_hprop_02 | missing_bin_height_period_phase | -180 | cpk_refine_htrans_04 | 460 | 340/340 | 70x120, 135 deg | high | backup_only |
| 3 | cpk_mbin_period_01 | missing_bin_period_phase | -60 | cpk_refine_weak_helper_04 | 420 | 360/340 | 65x115, 135 deg | medium_high | top2_if_budget_allows |
| 4 | cpk_mbin_rot_01 | missing_bin_helper_rotation_phase | 0 | cpk_rot_release_02 | 300 | 340/340 | 80x110, 90 deg | medium | planning_only |
| 5 | cpk_mbin_global_01 | missing_bin_global_phase_offset_reference | 60 | cpk_rot_release_02 | 320 | 340/340 | 75x110, 135 deg | medium | planning_only |
| 6 | cpk_mbin_nohelper_01 | missing_bin_conservative_reference | 0 | baseline_apcd_dimer | 300 | 340/340 | none | low | planning_only |


## Recommended P63 FDTD order

1. `cpk_mbin_hprop_01`
   - Main goal: test whether the robust negative phase branch can move from -131 deg toward -180 deg.
   - Reason: height_transition_sweep is currently the most selective and lowest-leakage negative-phase route.

2. `cpk_mbin_period_01`
   - Run only if budget allows after `cpk_mbin_hprop_01`.
   - Main goal: test whether a controlled period/position perturbation can escape the crowded -120 deg bin toward -60 deg.
   - Risk: previous pos_gap result showed leakage can worsen, so this should not become the main route unless it improves.

## Do not run yet

- `cpk_mbin_hprop_02`: backup only; higher height may hurt leakage/ratio.
- `cpk_mbin_rot_01`: planning-only probe; previous rotation release was trapped near the 120 deg plateau.
- `cpk_mbin_global_01`: planning-only probe; likely still near 120 deg.
- `cpk_mbin_nohelper_01`: reference only.

## Interpretation

P62 should be treated as a controlled missing-bin planning step, not as a jump to K=6 supercell construction.

The immediate next task should be P63 top-1 FDTD for `cpk_mbin_hprop_01`, with optional top-2 `cpk_mbin_period_01` only if the first run is informative and FDTD budget remains.
