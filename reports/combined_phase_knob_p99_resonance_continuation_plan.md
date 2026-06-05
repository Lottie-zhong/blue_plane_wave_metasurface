# 09-P99 resonance continuation plan

Stage: 09-P99 planning and top-4 FDTD preparation.

Anchor: cpk_resphase_anchor_wh03_h410_trim_m5_01.

Anchor evidence: phase -159.0076 deg, target_conversion 0.9191, opposite_spin_leakage 0.0088, conversion_to_leakage_ratio 104.8964. This preserves APCD selectivity but is still nearest the already-covered -180 bin.

Goal: move phase by more than 20 deg from -159 while preserving leakage <= 0.2 and ratio >= 6. A missing-bin opening requires nearest bin in [-60, 0, 60] and early_pass true.

Selected top-4:

| Rank | Candidate | Family | Rationale |
|---:|---|---|---|
| 1 | cpk_rescont_h420_anchor_wh03_01 | anchor_height_continuation | +10 nm height continuation from the high-selectivity anchor. |
| 2 | cpk_rescont_scale102_anchor_wh03_01 | anchor_common_size_trim | Small scale-up toward the original weak-helper anchor geometry. |
| 3 | cpk_rescont_aniso_reduce5_anchor_wh03_01 | anchor_anisotropy_trim | Long-axis -5 nm and short-axis +5 nm trim to soften resonance. |
| 4 | cpk_rescont_ultraweak_helper35x85_anchor_wh03_01 | ultraweak_helper_phase_bias | Ultraweak helper bias at <=35x85 nm to reduce helper coupling. |

Scope held:

- Stage 09 only.
- No K=6 phase-ramp supercell.
- No steering claim.
- No stronger common-rotation phase pulling.
- No -80/-90/-100 common offset continuation.
- No lower-transition repeat.
- No raw FDTD output is included in this plan.
