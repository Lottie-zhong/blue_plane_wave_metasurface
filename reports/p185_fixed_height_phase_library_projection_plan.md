# P185 fixed-height phase-library projection plan

## Scope

- Mainline changed to fabrication-aware same-height / fixed-height single-dimer phase library.
- Current mixed-height P179/P181/P183 K=6 result is archived as numerical proof-of-concept only.
- This P185 step does not run K=6, does not claim +15 deg steering, and does not use Micro-LED.

## Fixed heights

- h232: zero-bin priority height.
- h300: legacy-60-friendly middle height.
- h425: negative-bin reference height.

## Generation rule

- For each frozen six-state source dimer, set every pillar height to the selected fixed height.
- Preserve lateral geometry in this first diagnostic pass.
- Enforce integer nm height and same-height within each candidate.
- No sub-nm height, no multi-height candidate, no K=6 supercell.

- generated_candidates: 18
- selected_for_fdtd: 9

## Selected FDTD queue

| fixed h | source bin | new candidate | source | approx min gap nm |
|---:|---:|---|---|---:|
| 232 | 0 | `p185_fh232_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` | `cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` | 999.000000 |
| 232 | 60 | `p185_fh232_p060_from_aggr_lhs_retention_dy_05` | `aggr_lhs_retention_dy_05` | 999.000000 |
| 232 | -60 | `p185_fh232_m060_from_cpk_060_boundary_h435_aniso_reduce10_01` | `cpk_060_boundary_h435_aniso_reduce10_01` | 999.000000 |
| 300 | 0 | `p185_fh300_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` | `cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` | 999.000000 |
| 300 | 60 | `p185_fh300_p060_from_aggr_lhs_retention_dy_05` | `aggr_lhs_retention_dy_05` | 999.000000 |
| 300 | 120 | `p185_fh300_p120_from_cpk_rot_release_02` | `cpk_rot_release_02` | 999.000000 |
| 425 | -180 | `p185_fh425_m180_from_cpk_resphase_scale104_nohelper_01` | `cpk_resphase_scale104_nohelper_01` | 999.000000 |
| 425 | -120 | `p185_fh425_m120_from_cpk_060_anchor_wh03_h425_scale98_01` | `cpk_060_anchor_wh03_h425_scale98_01` | 999.000000 |
| 425 | -60 | `p185_fh425_m060_from_cpk_060_boundary_h435_aniso_reduce10_01` | `cpk_060_boundary_h435_aniso_reduce10_01` | 999.000000 |

## Decision after FDTD

- Compare which fixed height keeps the most useful APCD selectivity and phase diversity.
- Do not pick final height before seeing projection results.
- If one height shows phase diversity but leakage failure, use lateral compensation next.