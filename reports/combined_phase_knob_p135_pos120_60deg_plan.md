# 09-P135 Positive-Basin Iso-Retardance 60deg Plan

Stage: 09-P135 planning and candidate preparation.

Current coverage: early-pass bins [-180, -120, -60, 120]. Remaining missing bins: [0, 60].

Objective: start from existing +120 early-pass anchors and use dynamic, resonance, propagation, and iso-retardance knobs to move toward +60 while preserving APCD selectivity.

Automatically selected +120 anchors from `combined_phase_knob_phase_state_coverage_p134.csv` using nearest bin 120, early_pass true, leakage <= 0.2, and ratio >= 6. Ranking prioritized high ratio, low leakage, high target, and phase closeness to +120.

| Rank | Anchor | Phase | Target | Leakage | Ratio | Error to +120 | Reason |
|---:|---|---:|---:|---:|---:|---:|---|
| 1 | cpk_branch_helper_swap_br_01 | 134.1288 | 0.9525 | 0.0407 | 23.4053 | 14.1288 | highest ratio and target among +120 early-pass anchors |
| 2 | cpk_rot_release_02 | 120.2572 | 0.9365 | 0.0674 | 13.8897 | 0.2572 | closest phase to +120 with early-pass selectivity |
| 3 | cpk_branch_internal_release_01 | 134.1744 | 0.9201 | 0.0786 | 11.6989 | 14.1744 | internal-release +120 anchor for iso-retardance comparison |
| 4 | cpk_period_phase_04 | 122.7820 | 0.7501 | 0.0941 | 7.9710 | 2.7820 | period/dynamic-phase +120 anchor despite lower target |

P136 selected exactly 12 candidates: 4 height scan, 4 size/aspect compensation, 2 mode-order scout, and 2 rot60 leakage-recovery points.

| Slot | Count |
|---|---:|
| height_scan | 4 |
| size_aspect | 4 |
| mode_order | 2 |
| rot60_recovery | 2 |

Rules held: Stage 09 only; no K=6 phase-ramp supercell; no stage 10; no steering claim; no strong common rotation; no -120 basin brute force; no mixed-boundary brute force; no pure scalar-helper phase sweep; no alt_htrans04 forcing; no lower-transition repeat; no large position-gap change.
