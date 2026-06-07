# 09-P121 0/60 anchor diagnostic

P119 tested no-helper fixed-core anchors, wh03 alternatives, htrans04 helper-removed, and transition02 mild trim references. None produced a phase-near [0, 60] anchor.

| Candidate | Phase (deg) | Nearest bin | Error to best [0,60] bin | Anchor class | Interpretation |
|---|---:|---:|---:|---|---|
| cpk_060_anchor_nohelper_h420_01 | -132.4326 | -120 | 132.4326 | fail_covered_bin | not near 0/60 and fails early/near pass |
| cpk_060_anchor_nohelper_h430_scale96_01 | -141.3854 | -120 | 141.3854 | near_pass_covered_bin | near-pass and in an already-covered bin |
| cpk_060_anchor_wh03_h430_trim_m5_01 | -128.1467 | -120 | 128.1467 | early_pass_covered_bin | early-pass but in an already-covered bin |
| cpk_060_anchor_wh03_h425_scale98_01 | -120.0309 | -120 | 120.0309 | early_pass_covered_bin | early-pass but in an already-covered bin |
| cpk_060_anchor_htrans04_h410_nohelper_01 | -151.9099 | -180 | 148.0901 | early_pass_covered_bin | early-pass but in an already-covered bin |
| cpk_060_anchor_transition02_h380_scale96_01 | -157.8044 | -180 | 142.1956 | early_pass_covered_bin | early-pass but in an already-covered bin |

Diagnostic conclusion: these core-preserving anchor families mostly return to covered -120 or -180 basins. The 0/60 search needs a different stage-09 physics knob or geometry family rather than further alt_htrans04 forcing or covered-bin anchor repetition.
