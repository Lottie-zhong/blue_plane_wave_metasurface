# 09-P102 resonance continuation from h420 anchor

Stage: 09-P102 planning and top-4 FDTD preparation.

Anchor: cpk_rescont_h420_anchor_wh03_01.

Anchor evidence: phase -137.5023 deg, target_conversion 0.9063, opposite_spin_leakage 0.0591, conversion_to_leakage_ratio 15.3323. This was the first useful trend from the high-selectivity resonance branch, moving more than 20 deg from the -159 anchor while staying early-pass.

Selected top-4:

| Rank | Candidate | Family | Rationale |
|---:|---|---|---|
| 1 | cpk_rescont_h425_h420anchor_01 | h425_continuation | Small +5 nm height continuation from the useful h420 trend. |
| 2 | cpk_rescont_h430_h420anchor_01 | h430_continuation | Bounded +10 nm continuation below 440 nm. |
| 3 | cpk_rescont_h420_scale102_01 | h420_common_size_trim | Combine h420 with a small common size trim. |
| 4 | cpk_rescont_h420_aniso_reduce5_01 | h420_anisotropy_trim | Combine h420 with anisotropy reduction. |

Success definitions:

- early-pass: target >= 0.5, leakage <= 0.2, ratio >= 6.
- useful trend: phase moves more than 15 deg from -137.5 while still early-pass.
- missing-bin opening: nearest bin in [-60, 0, 60] and early-pass true.

Scope held:

- Stage 09 only.
- No K=6 phase-ramp supercell.
- No steering claim.
- No stronger common rotation.
- No lower-transition repeat.
- No height >= 440 nm.
- No raw FDTD output is included in this plan.
