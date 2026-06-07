# 09-P127 Capsule-Core Resonance Branch Plan

Stage: 09-P127 planning and candidate preparation.

Current coverage: early-pass bins [-180, -120, -60, 120]. Remaining missing bins: [0, 60].

P126 anchor: `cpk_060_geom_capsule_h420_01` reached phase -162.1028 deg with target 0.9097, leakage 0.0241, ratio 37.7278, and early_pass=True. It reinforced covered -180, but it is the cleanest new shape-family selectivity anchor from P123-P126.

Selected top-6 capsule validation candidates:

| Rank | Candidate | Family | Rationale |
|---:|---|---|---|
| 1 | cpk_capsule_res_h425_01 | capsule_height_continuation | First height step from h420 while staying below h440. |
| 2 | cpk_capsule_res_h430_01 | capsule_height_continuation | Second height step tests resonance phase motion. |
| 3 | cpk_capsule_res_h435_01 | capsule_height_continuation | Safe height-boundary check below 440 nm. |
| 4 | cpk_capsule_res_aniso_reduce5_01 | capsule_anisotropy_trim | Mild anisotropy release without rotating APCD cores. |
| 5 | cpk_capsule_res_aniso_reduce10_01 | capsule_anisotropy_trim | Stronger anisotropy-release boundary. |
| 6 | cpk_capsule_res_scale98_01 | capsule_common_scale | Small common scale trim around the capsule anchor. |

Backups include scale102, h425+scale98, h425 with one weak scalar resonator, and h430+reduce5. The weak scalar resonator is deliberately backup-only so this does not become a pure helper-shape sweep.

Success definitions:

- Opens [0,60]: nearest bin in [0, 60] and early_pass true.
- Useful trend: phase moves more than 20 deg away from -162 while leakage <= 0.2 and ratio >= 6.
- Fail boundary: phase moves but leakage > 0.2 or ratio < 6.

Scope held:

- Stage 09 only.
- No K=6 phase-ramp supercell.
- No stage 10 or steering claim.
- No stronger common rotation.
- No alt_htrans04 forcing.
- No lower-transition repeat.
- No pure helper-shape sweep.
- No large position-gap change.
- No raw FDTD output is included in this plan.
