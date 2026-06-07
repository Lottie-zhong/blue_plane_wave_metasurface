# 09-P119 0/60 anchor discovery plan

Stage: 09-P119 planning and candidate preparation.

Current coverage: early-pass bins [-180, -120, -60, 120]. Remaining missing bins: [0, 60].

P117/P118 decision: stop forcing the alt_htrans04 -60 basin. Stronger height, scale, and anisotropy trims moved phase toward 0/60 but broke APCD selectivity before opening a new bin.

Selected top-6 anchor-discovery candidates:

| Rank | Candidate | Family | Rationale |
|---:|---|---|---|
| 1 | cpk_060_anchor_nohelper_h420_01 | nohelper_fixed_core_height_anchor | Clean fixed-core no-helper height anchor. |
| 2 | cpk_060_anchor_nohelper_h430_scale96_01 | nohelper_fixed_core_size_anchor | No-helper h430 scale96 size resonance. |
| 3 | cpk_060_anchor_wh03_h430_trim_m5_01 | wh03_alternative_geometry_anchor | wh03 high-selectivity trim at h430, not alt_htrans04. |
| 4 | cpk_060_anchor_wh03_h425_scale98_01 | wh03_mild_common_geometry_trim | wh03 mild common geometry trim around a high-selectivity reference. |
| 5 | cpk_060_anchor_htrans04_h410_nohelper_01 | htrans04_alternative_nohelper_anchor | htrans04 reference with helper removed to decouple from the alt_htrans04 route. |
| 6 | cpk_060_anchor_transition02_h380_scale96_01 | transition02_mild_common_geometry_trim | transition_02 high-selectivity reference with mild scale96 trim. |

Success definitions:

- opens [0,60]: nearest bin in [0, 60] and early_pass true.
- useful anchor: phase within 30 deg of [0, 60], leakage <= 0.2, and ratio >= 6.
- phase-hit failed: phase near [0, 60] but leakage > 0.2 or ratio < 6.

Scope held:

- Stage 09 only.
- No K=6 phase-ramp supercell.
- No steering claim.
- No stronger common rotation.
- No continuation of alt_htrans04 stronger h/scale/aniso.
- No lower-transition repeat.
- No pure helper-shape sweep.
- No large position-gap change.
- No raw FDTD output is included in this plan.
