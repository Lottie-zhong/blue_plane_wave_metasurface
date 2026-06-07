# 09-P131 Orthogonal Core-Preserving Phase-Knob Plan

Stage: 09-P131 planning and candidate preparation.

Current coverage: early-pass bins [-180, -120, -60, 120]. Remaining missing bins: [0, 60].

Recent evidence:

- P126 showed simple rounded, ellipse, chamfer, and capsule replacements did not open [0, 60].
- P130 showed the capsule/racetrack branch preserves selectivity but is phase-stiff around covered -180/-120 bins.
- The alt_htrans04 route is a stable -60 basin and should not be forced further.

Implementation note: this stage adds real `notched_rectangle` support through `addpoly` polygon vertices. Hollow/ring-like internal voids are not selected because the current single-pillar config does not robustly support internal holes or boolean air regions.

Selected top-6 candidates:

| Rank | Candidate | Family | Rationale |
|---:|---|---|---|
| 1 | cpk_orth_mixed_rect_capsule_h425_01 | mixed_shape_apcd_dimer | Rectangle plus capsule, breaking the symmetric capsule branch. |
| 2 | cpk_orth_mixed_capsule_rect_h425_01 | mixed_shape_apcd_dimer | Opposite ordering of the rectangle/capsule mix. |
| 3 | cpk_orth_mixed_rect_round_h430_01 | mixed_shape_apcd_dimer | Rectangle plus rounded pillar2 at h430. |
| 4 | cpk_orth_mixed_capsule_chamfer_h430_01 | mixed_shape_apcd_dimer | Capsule plus chamfered pillar2. |
| 5 | cpk_orth_notch_p1_right_h425_01 | mild_notch_slot_perturbation | Real mild notch on pillar1, co-tested with capsule pillar2. |
| 6 | cpk_orth_scalar_mixed_capsule_35_h425_01 | weak_scalar_resonator_codesign | One weak scalar resonator with mixed rectangle+capsule core. |

Success definitions:

- Opens [0,60]: nearest bin in [0, 60] and early_pass true.
- Useful anchor: phase within 30 deg of [0, 60], leakage <= 0.2, and ratio >= 6.
- Phase-hit failed: phase near [0, 60] but leakage > 0.2 or ratio < 6.

Scope held:

- Stage 09 only.
- No K=6 phase-ramp supercell.
- No stage 10 or steering claim.
- No strong common rotation.
- No beta-selective pillar2 rollback.
- No alt_htrans04 forcing.
- No capsule simple height/scale/aniso continuation.
- No lower-transition repeat.
- No pure helper-shape sweep.
- No large position-gap change.
- No raw FDTD output is included in this plan.
