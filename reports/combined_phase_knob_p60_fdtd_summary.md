# 09-P60 priority FDTD summary

## Scope

This report summarizes the two P60 single-dimer FDTD runs selected after the P59 phase-state coverage report.

This is still single-dimer phase-state refinement. It is not a K=6 phase-ramp supercell, not a +15 degree steering result, not K=7, not a 450 nm / Micro-LED integration result, not DenseNet/cVAE training, and not a complete K=6 phase-state library.

## Compared candidates

| candidate | family | height nm | helper LxW rot | target | leakage | ratio | PD | phase deg | early pass | role |
|---|---|---:|---|---:|---:|---:|---:|---:|---|---|
| cpk_refine_htrans_04 | height_transition_sweep | 410.0 | 70x120, 135.0 deg | 0.963606 | 0.019658 | 49.0189 | 0.960015 | -131.308 | True | P57 reference; current strongest negative-phase candidate by leakage and ratio |
| cpk_refine_weak_helper_03 | weak_helper_leakage_recovery | 420.0 | 65x110, 120.0 deg | 0.920946 | 0.100133 | 9.1972 | 0.803868 | -115.182 | True | P57 reference; phase-near--120 early-pass comparison |
| cpk_refine_htrans_03 | height_transition_sweep | 400.0 | 70x120, 135.0 deg | 0.952936 | 0.085589 | 11.1339 | 0.835172 | -128.330 | True | P60 priority-1; lower-height transition check around htrans_04 |
| cpk_refine_weak_helper_04 | weak_helper_leakage_recovery | 420.0 | 65x115, 135.0 deg | 0.932750 | 0.083423 | 11.1810 | 0.835810 | -113.644 | True | P60 priority-2; weak-helper local tuning around weak_helper_03 |


## Interpretation

- `cpk_refine_htrans_03` passes early-pass and confirms that the height-transition route is robust around 400-410 nm.
- `cpk_refine_htrans_04` remains the strongest negative-phase candidate by leakage suppression and ratio.
- `cpk_refine_weak_helper_04` also passes early-pass and improves leakage/ratio relative to `cpk_refine_weak_helper_03`, but its phase moves slightly farther from -120 deg.
- Neither P60 candidate opens a new missing phase bin. Both remain in the -120 deg bin.

## Current conclusion

P60 supports the priority rule from P59: keep height_transition_sweep as priority 1 and weak_helper_leakage_recovery as priority 2, while continuing to pause pos_gap. However, current coverage is still insufficient for K=6 phase-ramp supercell construction because -180, -60, 0, and 60 deg bins are missing.

Recommended next action: stop P60 after these two FDTD runs, commit the small summary files, then perform P61 coverage update before deciding whether another targeted candidate is worth running.
