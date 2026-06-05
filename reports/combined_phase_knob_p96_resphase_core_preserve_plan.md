# 09-P96 resphase_core_preserve plan

Stage: 09-P96 planning and top-4 FDTD preparation.

Principle: preserve APCD selection first, then search phase through resonance or propagation geometry. This plan avoids stronger common-rotation phase pulling and does not continue the -80/-90/-100 branch.

Current early-pass bins before this plan: [-180, -120, 120].

Remaining missing bins: [-60, 0, 60].

Selected top-4:

| Rank | Candidate | Family | Reason |
|---:|---|---|---|
| 1 | cpk_resphase_h380_nohelper_01 | resphase_fixed_core_height | Fixed APCD rotations, no helper, h=380 nm resonance/propagation point. |
| 2 | cpk_resphase_scale104_nohelper_01 | resphase_fixed_core_size | Fixed APCD rotations, no helper, common size scale 1.04. |
| 3 | cpk_resphase_anchor_wh03_h410_trim_m5_01 | resphase_anchor_trim | Gentle trim from the high-quality weak-helper anchor. |
| 4 | cpk_resphase_60lock_counter_m40_h320_helper35x85_01 | resphase_60_phase_lock_recovery | Comparison from a failed 60deg phase-hit route with helper weakening and height change. |

Success criteria:

- early-pass: target_conversion >= 0.5, opposite_spin_leakage <= 0.2, conversion_to_leakage_ratio >= 6.
- phase-hit but failed selectivity: phase error to a missing bin <= 15 deg but leakage > 0.2.

Scope held:

- Stage 09 only.
- No K=6 phase-ramp supercell.
- No steering claim.
- No stronger common-rotation phase pulling.
- No raw FDTD outputs are included in this plan.
