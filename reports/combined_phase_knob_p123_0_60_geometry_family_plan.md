# 09-P123 0/60 geometry-family discovery plan

Stage: 09-P123 planning and candidate preparation.

Current coverage: early-pass bins [-180, -120, -60, 120]. Remaining missing bins: [0, 60].

P122 decision: no-helper, wh03, htrans04, and transition02 anchor discovery reinforced covered -120/-180 basins. P118 decision: do not continue forcing the alt_htrans04 -60 basin.

Implementation note: this stage adds shape-aware APCD core support for real FDTD geometry. Rectangular pillars still use `addrect`; ellipse, rounded rectangle, capsule/racetrack, and chamfered rectangle use `addpoly` polygon cross-sections. This avoids naming a new shape while simulating an old rectangle.

Selected top-6 geometry-family candidates:

| Rank | Candidate | Family | Rationale |
|---:|---|---|---|
| 1 | cpk_060_geom_round_h420_r12_01 | rounded_rectangle_apcd_core | Edge-softened rounded APCD core at h420. |
| 2 | cpk_060_geom_ellipse_h420_01 | elliptical_apcd_core | Smooth anisotropic APCD core at h420. |
| 3 | cpk_060_geom_capsule_h420_01 | capsule_racetrack_apcd_core | Racetrack core with semicircular endcaps. |
| 4 | cpk_060_geom_chamfer_h425_c10_01 | chamfered_rectangle_apcd_core | Corner-removal resonance at h425. |
| 5 | cpk_060_geom_round_h430_r16_01 | rounded_rectangle_apcd_core | Higher rounded-core point without alt_htrans04 scale/aniso forcing. |
| 6 | cpk_060_geom_ellipse_h425_scalar55_01 | ellipse_core_weak_scalar_bias | One weak scalar resonator bias on an elliptical core. |

Success definitions:

- opens [0,60]: nearest bin in [0, 60] and early_pass true.
- useful anchor: phase within 30 deg of [0, 60], leakage <= 0.2, and ratio >= 6.
- phase-hit failed: phase near [0, 60] but leakage > 0.2 or ratio < 6.

Scope held:

- Stage 09 only.
- No K=6 phase-ramp supercell.
- No steering claim.
- No stronger common rotation.
- No forcing alt_htrans04 stronger h/scale/aniso.
- No lower-transition repeat.
- No pure helper-shape sweep.
- No large position-gap change.
- No raw FDTD output is included in this plan.
