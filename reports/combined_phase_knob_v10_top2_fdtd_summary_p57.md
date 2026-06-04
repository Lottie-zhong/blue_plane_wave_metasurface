# 09-P57 v10 top2 FDTD summary

## Scope

This report summarizes the first two real FDTD runs from the 09-P54/P56 v10 refinement pool.

This is still a single-dimer phase-state refinement step. It is not a K=6 phase-ramp supercell, not a K=7 result, not a 450 nm / Micro-LED integration result, not DenseNet/cVAE training, not a +15 degree steering result, and not a complete K=6 phase-state library.

## Compared candidates

| candidate | family | height nm | helper LxW rot | target conversion | leakage | ratio | PD | phase deg | early pass |
|---|---|---:|---|---:|---:|---:|---:|---:|---|
| cpk_height_prop_05 | helper_plus_height_propagation | 420.0 | 70x120, 135.0 deg | 0.927845 | 0.205773 | 4.5091 | 0.636960 | -109.638 | False |
| cpk_refine_htrans_04 | height_transition_sweep | 410.0 | 70x120, 135.0 deg | 0.963606 | 0.019658 | 49.0189 | 0.960015 | -131.308 | True |
| cpk_refine_weak_helper_03 | weak_helper_leakage_recovery | 420.0 | 65x110, 120.0 deg | 0.920946 | 0.100133 | 9.1972 | 0.803868 | -115.182 | True |


## Interpretation

- `cpk_height_prop_05` opened the negative phase region but failed early-pass mainly because leakage was too high.
- `cpk_refine_htrans_04` strongly recovers leakage and ratio while staying in the negative-phase region.
- `cpk_refine_weak_helper_03` also passes early-pass and gives a phase closer to -120 deg, but its leakage and ratio are weaker than `cpk_refine_htrans_04`.
- Best ratio candidate: `cpk_refine_htrans_04`.
- Closest phase-to--120 candidate among the two new runs: `cpk_refine_weak_helper_03`.

## Current conclusion

The v10 refinement direction is supported by real FDTD: height-transition refinement around `cpk_height_prop_05` can recover target-channel amplitude and suppress opposite-spin leakage without losing the useful negative phase.

Recommended next action: keep `cpk_refine_htrans_04` as the current strongest negative-phase early-pass candidate, and use `cpk_refine_weak_helper_03` as a phase-near--120 comparison candidate before deciding whether to run one backup candidate.
