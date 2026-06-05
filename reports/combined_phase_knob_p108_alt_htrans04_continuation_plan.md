# 09-P108 alt_htrans04 continuation plan

Stage: 09-P108 planning and top-4 FDTD preparation.

Pivot: cpk_resplateau_alt_htrans04_h420_aniso_reduce5_01.

Pivot evidence: phase -99.5115 deg, target_conversion 0.9079, opposite_spin_leakage 0.0380, conversion_to_leakage_ratio 23.8942. It is early-pass and moved toward the missing -60 side, but remained nearest -120.

Selected top-4:

| Rank | Candidate | Family | Rationale |
|---:|---|---|---|
| 1 | cpk_alt_htrans04_h425_01 | alt_htrans04_height_continuation | +5 nm height continuation toward -60. |
| 2 | cpk_alt_htrans04_h430_01 | alt_htrans04_height_continuation | +10 nm continuation below 440 nm. |
| 3 | cpk_alt_htrans04_h420_aniso_reduce10_01 | alt_htrans04_stronger_anisotropy_trim | Stronger geometry/aniso trim at h420. |
| 4 | cpk_alt_htrans04_h420_square_helper50_01 | alt_htrans04_isotropic_helper_phase_bias | One square 50x50 isotropic helper check with weak coupling. |

Success definitions:

- early-pass: target >= 0.5, leakage <= 0.2, ratio >= 6.
- useful trend: phase moves more than 10 deg from -99.5 toward -60 while early-pass.
- missing-bin opening: nearest = -60 and early-pass true.

Scope held:

- Stage 09 only.
- No K=6 phase-ramp supercell.
- No steering claim.
- No stronger common rotation.
- No lower-transition repeat.
- No large position-gap change.
- No pure helper-shape sweep.
- No raw FDTD output is included in this plan.
