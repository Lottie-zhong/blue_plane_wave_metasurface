# P186 fixed-height projection results

## Scope

- Single-dimer fixed-height projection only.
- No K=6 supercell run.
- No +15 deg steering claim.
- Mixed-height K=6 remains proof-of-concept only.

## Height-level summary

| fixed h | tested | valid metrics | error/missing | early-pass count | nearest bins seen | early-pass bins seen | best ratio | best candidate |
|---:|---:|---:|---:|---:|---|---|---:|---|
| 232 | 3 | 2 | 1 | 1 | 0 | 0 | 7.672519946 | `p185_fh232_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` |
| 300 | 3 | 2 | 1 | 2 | 60 | 60 | 8.329738838 | `p185_fh300_p060_from_aggr_lhs_retention_dy_05` |
| 425 | 3 | 1 | 2 | 0 | -120 |  | 1.234165146 | `p185_fh425_m180_from_cpk_resphase_scale104_nohelper_01` |

## Candidate results

| h | source bin | status | nearest bin | phase | target | leakage | ratio | early | candidate |
|---:|---:|---|---:|---:|---:|---:|---:|---|---|
| 232 | 0 | ok | 0 | 23.012245007 | 0.808661767 | 0.105397154 | 7.672519946 | True | `p185_fh232_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` |
| 232 | 60 | ok | 0 | 18.239375820 | 0.816379702 | 0.188727037 | 4.325716729 | False | `p185_fh232_p060_from_aggr_lhs_retention_dy_05` |
| 232 | -60 | error |  |  |  |  |  | False | `p185_fh232_m060_from_cpk_060_boundary_h435_aniso_reduce10_01` |
| 300 | 0 | ok | 60 | 76.192984902 | 0.870101298 | 0.109742639 | 7.928561833 | True | `p185_fh300_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` |
| 300 | 60 | ok | 60 | 72.241328096 | 0.857022282 | 0.102887053 | 8.329738838 | True | `p185_fh300_p060_from_aggr_lhs_retention_dy_05` |
| 300 | 120 | error |  |  |  |  |  | False | `p185_fh300_p120_from_cpk_rot_release_02` |
| 425 | -180 | ok | -120 | -106.237564838 | 0.944401730 | 0.765215039 | 1.234165146 | False | `p185_fh425_m180_from_cpk_resphase_scale104_nohelper_01` |
| 425 | -120 | error |  |  |  |  |  | False | `p185_fh425_m120_from_cpk_060_anchor_wh03_h425_scale98_01` |
| 425 | -60 | error |  |  |  |  |  | False | `p185_fh425_m060_from_cpk_060_boundary_h435_aniso_reduce10_01` |

## Preliminary interpretation

- h300 is likely the best next fixed-height branch if it retains two early-pass useful bins.
- h232 remains useful as the zero-bin reference.
- h425 is not preferred unless later recovery improves leakage and failed candidates.

## Next decision

- Use this result to choose the next lateral compensation branch.
- Do not re-enter K=6 until a fixed-height six-bin single-dimer library is available.