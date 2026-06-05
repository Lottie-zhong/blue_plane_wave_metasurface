# 09-P114 0/60 boundary-value FDTD validation plan

Stage: 09-P114 planning and candidate preparation.

Current coverage: early-pass bins [-180, -120, -60, 120]. Remaining missing bins: [0, 60].

Primary anchor: cpk_060_alt_htrans04_h430_aniso_reduce10_01, phase -72.5522 deg, target_conversion 0.8649, opposite_spin_leakage 0.1182, conversion_to_leakage_ratio 7.3176. This is the best P111/P113 early-pass trend toward 0/60.

Boundary reference: cpk_060_alt_htrans04_h430_scale104_01 reached phase -62.8043 deg but failed early-pass due to leakage 0.2087 and ratio 4.5479.

Selected sparse map:

| Rank | Candidate | Family | Rationale |
|---:|---|---|---|
| 1 | cpk_060_boundary_h435_aniso_reduce10_01 | h430_aniso_reduce10_height_continuation | +5 nm height from the best early-pass trend. |
| 2 | cpk_060_boundary_h440_aniso_reduce10_01 | h430_aniso_reduce10_height_continuation | +10 nm height boundary without changing rotations. |
| 3 | cpk_060_boundary_h430_aniso_reduce15_01 | h430_stronger_geometry_trim | Stronger h430 anisotropy reduction. |
| 4 | cpk_060_boundary_h435_aniso_reduce15_01 | h435_stronger_geometry_trim | Combined sparse height and stronger anisotropy trim. |
| 5 | cpk_060_boundary_h430_scale102_aniso_reduce10_01 | scale_boundary_leakage_recovery | Scale102 boundary for leakage recovery. |
| 6 | cpk_060_boundary_h430_scale103_aniso_reduce10_01 | scale_boundary_leakage_recovery | Scale103 middle boundary point. |
| 7 | cpk_060_boundary_h435_scale102_aniso_reduce10_01 | scale_height_boundary_leakage_recovery | Small scale plus h435 phase-motion check. |
| 8 | cpk_060_boundary_h430_scale104_aniso_reduce10_01 | high_risk_crossing_check | High-risk scale104/aniso10 crossing check after min-gap estimate passed. |

The high-risk scale104/aniso10 geometry passed a rotated-rectangle min-gap estimate: p2-helper minimum gap is about 52.36 nm, above the 50 nm guard.

Success definitions:

- opens [0,60]: nearest bin in [0, 60] and early_pass true.
- useful boundary point: phase moves more than 10 deg toward 0/60 while early_pass true.
- failure boundary: phase moves but leakage > 0.2 or ratio < 6.

Scope held:

- Stage 09 only.
- No K=6 phase-ramp supercell.
- No steering claim.
- No stronger common rotation.
- No lower-transition repeat.
- No pure helper-shape sweep.
- No large position-gap change.
- No raw FDTD output is included in this plan.
