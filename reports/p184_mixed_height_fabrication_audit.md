# P184 mixed-height fabrication audit

## Conclusion

- library_is_single_height: False
- unique_library_heights_nm: [232.0, 300.0, 340.0, 425.0, 435.0]
- fabrication_decision: current P179/P181 mixed-height K=6 library is numerical proof-of-concept only.
- fabrication_target: False
- reason: a single-step etched metasurface normally requires one global pillar height, while this K=6 assembly uses multiple heights.
- next_step: restart same-height / fixed-height single-dimer phase-state search.

## Dimer-level height audit

| index | bin | candidate | pillar_count | height_nm | same-height within dimer |
|---:|---:|---|---:|---:|---|
| 0 | 0 | `cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` | 2 | 232.0 | True |
| 1 | 60 | `aggr_lhs_retention_dy_05` | 2 | 300.0 | True |
| 2 | 120 | `cpk_rot_release_02` | 3 | 300.0 | True |
| 3 | -180 | `cpk_resphase_scale104_nohelper_01` | 2 | 340.0 | True |
| 4 | -120 | `cpk_060_anchor_wh03_h425_scale98_01` | 3 | 425.0 | True |
| 5 | -60 | `cpk_060_boundary_h435_aniso_reduce10_01` | 3 | 435.0 | True |

## Important boundary

- Do not claim this mixed-height K=6 as a fabrication-ready design.
- Do not use this as the final manufacturable metasurface.
- It can be kept as a physics-first phase-library integration proof.
- The next official mainline should enforce fixed height globally.