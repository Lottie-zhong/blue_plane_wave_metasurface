# P187 fixed-height platform scan plan

## Scope

- Single-dimer fixed-height platform scan.
- No K=6 supercell.
- No steering claim.
- No Micro-LED claim.

## Heights

240, 260, 280, 320, 350, 375, 400

## Source families

| source bin | source candidate | role |
|---:|---|---|
| -180 | `cpk_resphase_scale104_nohelper_01` | h300 opened 120 with strong selectivity |
| 0 | `cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` | reliable h232 0 anchor |
| 60 | `aggr_lhs_retention_dy_05` | reliable 60 plateau |

generated_candidates: 21

## Queue

| h | source bin | candidate |
|---:|---:|---|
| 240 | -180 | `p187_fh240_m180_from_cpk_resphase_scale104_nohelper_01` |
| 260 | -180 | `p187_fh260_m180_from_cpk_resphase_scale104_nohelper_01` |
| 280 | -180 | `p187_fh280_m180_from_cpk_resphase_scale104_nohelper_01` |
| 320 | -180 | `p187_fh320_m180_from_cpk_resphase_scale104_nohelper_01` |
| 350 | -180 | `p187_fh350_m180_from_cpk_resphase_scale104_nohelper_01` |
| 375 | -180 | `p187_fh375_m180_from_cpk_resphase_scale104_nohelper_01` |
| 400 | -180 | `p187_fh400_m180_from_cpk_resphase_scale104_nohelper_01` |
| 240 | 0 | `p187_fh240_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` |
| 260 | 0 | `p187_fh260_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` |
| 280 | 0 | `p187_fh280_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` |
| 320 | 0 | `p187_fh320_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` |
| 350 | 0 | `p187_fh350_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` |
| 375 | 0 | `p187_fh375_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` |
| 400 | 0 | `p187_fh400_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` |
| 240 | 60 | `p187_fh240_p060_from_aggr_lhs_retention_dy_05` |
| 260 | 60 | `p187_fh260_p060_from_aggr_lhs_retention_dy_05` |
| 280 | 60 | `p187_fh280_p060_from_aggr_lhs_retention_dy_05` |
| 320 | 60 | `p187_fh320_p060_from_aggr_lhs_retention_dy_05` |
| 350 | 60 | `p187_fh350_p060_from_aggr_lhs_retention_dy_05` |
| 375 | 60 | `p187_fh375_p060_from_aggr_lhs_retention_dy_05` |
| 400 | 60 | `p187_fh400_p060_from_aggr_lhs_retention_dy_05` |