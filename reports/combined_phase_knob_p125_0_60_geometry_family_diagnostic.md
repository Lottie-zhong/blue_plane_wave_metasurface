# 09-P125 geometry-family diagnostic

P123 tested rounded rectangle, ellipse, capsule/racetrack, chamfered rectangle, and one weak scalar-resonator bias on an elliptical core. These were real shape-aware FDTD geometries using polygon vertices.

| Candidate | Core shape | Phase (deg) | Nearest bin | Error to best [0,60] bin | Geometry class | Interpretation |
|---|---|---:|---:|---:|---|---|
| cpk_060_geom_round_h420_r12_01 | rounded_rectangle | -135.0904 | -120 | 135.0904 | fail_covered_bin | not near 0/60 and fails early/near pass |
| cpk_060_geom_ellipse_h420_01 | ellipse | 176.3725 | -180 | 116.3725 | fail_covered_bin | not near 0/60 and fails early/near pass |
| cpk_060_geom_capsule_h420_01 | capsule | -162.1028 | -180 | 137.8972 | early_pass_covered_bin | early-pass but in an already-covered bin |
| cpk_060_geom_chamfer_h425_c10_01 | chamfered_rectangle | -131.6039 | -120 | 131.6039 | fail_covered_bin | not near 0/60 and fails early/near pass |
| cpk_060_geom_round_h430_r16_01 | rounded_rectangle | -127.4800 | -120 | 127.4800 | fail_covered_bin | not near 0/60 and fails early/near pass |
| cpk_060_geom_ellipse_h425_scalar55_01 | ellipse_plus_scalar | -173.9952 | -180 | 126.0048 | fail_covered_bin | not near 0/60 and fails early/near pass |

Diagnostic conclusion: the tested smooth/rounded/chamfered core families do not reach the remaining [0, 60] bins. Capsule/racetrack preserves APCD selectivity extremely well, but it is a covered -180 anchor. Rounded and chamfered variants tend to return to -120 with leakage collapse.
