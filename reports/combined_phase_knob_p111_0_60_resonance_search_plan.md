# 09-P111 0/60 resonance search plan

Stage: 09-P111 planning and top-4 FDTD preparation.

Current coverage: early-pass bins [-180, -120, -60, 120]. Remaining missing bins: [0, 60].

Primary anchor: cpk_alt_htrans04_h430_01, phase -88.2507 deg, target_conversion 0.8841, opposite_spin_leakage 0.0506, conversion_to_leakage_ratio 17.4799. This opened -60 while preserving APCD selectivity.

Selected top-4:

| Rank | Candidate | Family | Rationale |
|---:|---|---|---|
| 1 | cpk_060_alt_htrans04_h440_01 | alt_htrans04_continuation_from_h430 | One controlled h440 boundary point from the h430 -60 anchor. |
| 2 | cpk_060_alt_htrans04_h430_aniso_reduce10_01 | h430_geometry_aniso_trim | Stronger h430 anisotropy trim toward less-negative phase. |
| 3 | cpk_060_alt_htrans04_h430_scale104_01 | h430_common_size_scale_trim | H430 common size scale 1.04 resonance trim. |
| 4 | cpk_060_wh03_h430_aniso_reduce10_01 | alternative_core_preserving_resonance_anchor | Alternative weak-helper core-preserving anchor. |

Success definitions:

- early-pass: target >= 0.5, leakage <= 0.2, ratio >= 6.
- opens missing bin: nearest in [0, 60] and early-pass true.
- useful trend: phase moves more than 10 deg from -88.25 toward 0/60 while early-pass.

Scope held:

- Stage 09 only.
- No K=6 phase-ramp supercell.
- No steering claim.
- No stronger common rotation.
- No lower-transition repeat.
- No pure helper-shape sweep.
- No large position-gap change.
- No raw FDTD output is included in this plan.
