# P186B fixed-height projection all-18 results

## Scope

- Single-dimer fixed-height projection only.
- All 18 candidates from P185 are summarized.
- No K=6 supercell run.
- No +15 deg steering claim.
- Mixed-height K=6 remains proof-of-concept only.

## Height-level summary

| fixed h | tested | valid metrics | error/missing | early-pass count | nearest bins seen | early-pass bins seen | best ratio | best candidate |
|---:|---:|---:|---:|---:|---|---|---:|---|
| 232 | 6 | 3 | 3 | 1 | 0;60 | 0 | 7.672519946 | `p185_fh232_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` |
| 300 | 6 | 3 | 3 | 3 | 60;120 | 60;120 | 11.662619208 | `p185_fh300_m180_from_cpk_resphase_scale104_nohelper_01` |
| 425 | 6 | 3 | 3 | 0 | -180;-120 |  | 3.269681553 | `p185_fh425_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` |

## Candidate results

| h | source bin | status | nearest bin | phase | target | leakage | ratio | early | candidate |
|---:|---:|---|---:|---:|---:|---:|---:|---|---|
| 232 | -180 | ok | 60 | 54.804466470 | 0.771191807 | 0.935617409 | 0.824259788 | False | `p185_fh232_m180_from_cpk_resphase_scale104_nohelper_01` |
| 300 | -180 | ok | 120 | 128.119704139 | 0.956633045 | 0.082025575 | 11.662619208 | True | `p185_fh300_m180_from_cpk_resphase_scale104_nohelper_01` |
| 425 | -180 | ok | -120 | -106.237564838 | 0.944401730 | 0.765215039 | 1.234165146 | False | `p185_fh425_m180_from_cpk_resphase_scale104_nohelper_01` |
| 232 | -120 | error |  |  |  |  |  | False | `p185_fh232_m120_from_cpk_060_anchor_wh03_h425_scale98_01` |
| 300 | -120 | error |  |  |  |  |  | False | `p185_fh300_m120_from_cpk_060_anchor_wh03_h425_scale98_01` |
| 425 | -120 | error |  |  |  |  |  | False | `p185_fh425_m120_from_cpk_060_anchor_wh03_h425_scale98_01` |
| 232 | -60 | error |  |  |  |  |  | False | `p185_fh232_m060_from_cpk_060_boundary_h435_aniso_reduce10_01` |
| 300 | -60 | error |  |  |  |  |  | False | `p185_fh300_m060_from_cpk_060_boundary_h435_aniso_reduce10_01` |
| 425 | -60 | error |  |  |  |  |  | False | `p185_fh425_m060_from_cpk_060_boundary_h435_aniso_reduce10_01` |
| 232 | 0 | ok | 0 | 23.012245007 | 0.808661767 | 0.105397154 | 7.672519946 | True | `p185_fh232_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` |
| 300 | 0 | ok | 60 | 76.192984902 | 0.870101298 | 0.109742639 | 7.928561833 | True | `p185_fh300_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` |
| 425 | 0 | ok | -180 | -174.789511484 | 0.912280276 | 0.279011965 | 3.269681553 | False | `p185_fh425_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` |
| 232 | 60 | ok | 0 | 18.239375820 | 0.816379702 | 0.188727037 | 4.325716729 | False | `p185_fh232_p060_from_aggr_lhs_retention_dy_05` |
| 300 | 60 | ok | 60 | 72.241328096 | 0.857022282 | 0.102887053 | 8.329738838 | True | `p185_fh300_p060_from_aggr_lhs_retention_dy_05` |
| 425 | 60 | ok | -180 | 179.528953189 | 0.914728038 | 0.529490388 | 1.727563065 | False | `p185_fh425_p060_from_aggr_lhs_retention_dy_05` |
| 232 | 120 | error |  |  |  |  |  | False | `p185_fh232_p120_from_cpk_rot_release_02` |
| 300 | 120 | error |  |  |  |  |  | False | `p185_fh300_p120_from_cpk_rot_release_02` |
| 425 | 120 | error |  |  |  |  |  | False | `p185_fh425_p120_from_cpk_rot_release_02` |

## Decision rule

- Choose the fixed-height platform with the best combination of phase diversity and APCD selectivity.
- If h300 remains phase-stiff around 60, use lateral geometry compensation rather than K=6.
- If h232 only keeps 0, keep it as zero-bin reference but do not treat it as full-library height yet.
- Do not re-enter K=6 until a same-height six-bin single-dimer library exists.