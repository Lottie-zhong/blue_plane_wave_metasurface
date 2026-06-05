# 09-P105 resonance plateau diagnosis plan

Stage: 09-P105 planning and top-4 FDTD preparation.

Goal: diagnose whether the h420/h430 resonance branch can leave the -120 plateau while preserving APCD selectivity.

Evidence before this plan:

- h420 branch moved from -159 to about -126 while staying early-pass.
- P102-P104 found a stable -120 plateau.
- h430 remains early-pass but ratio is close to the threshold, so this plan does not simply keep increasing height.

Selected top-4:

| Rank | Candidate | Family | Rationale |
|---:|---|---|---|
| 1 | cpk_resplateau_h434_boundary_01 | height_boundary_below_h435 | Height boundary below h435, still below h440. |
| 2 | cpk_resplateau_h420_aniso_reduce10_01 | h420_stronger_anisotropy_trim | Stronger anisotropy trim than reduce5 at h420. |
| 3 | cpk_resplateau_h425_scale102_aniso_reduce5_01 | h425_combined_size_anisotropy_trim | h425 with combined common-size and anisotropy trim. |
| 4 | cpk_resplateau_alt_htrans04_h420_aniso_reduce5_01 | alternative_high_selectivity_anchor_trim | Alternative high-selectivity htrans04 anchor trim, not from common rotation. |

Success definitions:

- early-pass: target >= 0.5, leakage <= 0.2, ratio >= 6.
- useful trend: phase moves more than 15 deg away from -126.7 while still early-pass.
- missing-bin opening: nearest bin in [-60, 0, 60] and early-pass true.

Scope held:

- Stage 09 only.
- No K=6 phase-ramp supercell.
- No steering claim.
- No stronger common rotation.
- No lower-transition repeat.
- No large position-gap change.
- No raw FDTD output is included in this plan.
