# P187 fixed-height platform scan results

## Scope

- Single-dimer fixed-height platform scan.
- No K=6 supercell run.
- No +15 deg steering claim.

## Height summary

| h | tested | valid | early | bins seen | early bins | best ratio | best candidate |
|---:|---:|---:|---:|---|---|---:|---|
| 240 | 3 | 3 | 1 | 60 | 60 | 6.778217756 | `p187_fh240_p060_from_aggr_lhs_retention_dy_05` |
| 260 | 3 | 3 | 1 | 60;120 | 60 | 7.861314211 | `p187_fh260_p060_from_aggr_lhs_retention_dy_05` |
| 280 | 3 | 3 | 1 | 60;120 | 60 | 7.591036375 | `p187_fh280_p060_from_aggr_lhs_retention_dy_05` |
| 320 | 3 | 3 | 3 | -180;120 | -180;120 | 20.955565583 | `p187_fh320_m180_from_cpk_resphase_scale104_nohelper_01` |
| 350 | 3 | 3 | 1 | -180;120 | -180 | 7.248964065 | `p187_fh350_m180_from_cpk_resphase_scale104_nohelper_01` |
| 375 | 3 | 3 | 1 | -120;120 | -120 | 9.101455968 | `p187_fh375_m180_from_cpk_resphase_scale104_nohelper_01` |
| 400 | 3 | 3 | 0 | -180;-120 |  | 2.938870617 | `p187_fh400_m180_from_cpk_resphase_scale104_nohelper_01` |

## Candidate results

| h | source bin | status | nearest bin | phase | target | leakage | ratio | early | candidate |
|---:|---:|---|---:|---:|---:|---:|---:|---|---|
| 240 | -180 | ok | 60 | 77.568536157 | 0.785292228 | 0.841298564 | 0.933428703 | False | `p187_fh240_m180_from_cpk_resphase_scale104_nohelper_01` |
| 260 | -180 | ok | 120 | 96.496419828 | 0.860131171 | 0.512508859 | 1.678275714 | False | `p187_fh260_m180_from_cpk_resphase_scale104_nohelper_01` |
| 280 | -180 | ok | 120 | 104.315403322 | 0.930284153 | 0.254086751 | 3.661285557 | False | `p187_fh280_m180_from_cpk_resphase_scale104_nohelper_01` |
| 320 | -180 | ok | -180 | 161.121356078 | 0.952545380 | 0.045455484 | 20.955565583 | True | `p187_fh320_m180_from_cpk_resphase_scale104_nohelper_01` |
| 350 | -180 | ok | -180 | -170.124546579 | 0.901890100 | 0.124416412 | 7.248964065 | True | `p187_fh350_m180_from_cpk_resphase_scale104_nohelper_01` |
| 375 | -180 | ok | -120 | -149.750418755 | 0.902067777 | 0.099112469 | 9.101455968 | True | `p187_fh375_m180_from_cpk_resphase_scale104_nohelper_01` |
| 400 | -180 | ok | -120 | -128.655785743 | 0.916877911 | 0.311983081 | 2.938870617 | False | `p187_fh400_m180_from_cpk_resphase_scale104_nohelper_01` |
| 240 | 0 | ok | 60 | 45.489994214 | 0.825472904 | 0.145942025 | 5.656170012 | False | `p187_fh240_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` |
| 260 | 0 | ok | 60 | 59.471395521 | 0.844889633 | 0.190311122 | 4.439517912 | False | `p187_fh260_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` |
| 280 | 0 | ok | 60 | 60.448614479 | 0.856372802 | 0.174078055 | 4.919475946 | False | `p187_fh280_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` |
| 320 | 0 | ok | 120 | 103.728982119 | 0.901630409 | 0.081163235 | 11.108852586 | True | `p187_fh320_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` |
| 350 | 0 | ok | 120 | 128.486931321 | 0.927845343 | 0.201858430 | 4.596515206 | False | `p187_fh350_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` |
| 375 | 0 | ok | 120 | 148.172448737 | 0.932885199 | 0.311086735 | 2.998794527 | False | `p187_fh375_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` |
| 400 | 0 | ok | -180 | 167.087768715 | 0.923540127 | 0.353629025 | 2.611607256 | False | `p187_fh400_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01` |
| 240 | 60 | ok | 60 | 40.871351639 | 0.813474750 | 0.120013074 | 6.778217756 | True | `p187_fh240_p060_from_aggr_lhs_retention_dy_05` |
| 260 | 60 | ok | 60 | 55.324901637 | 0.826239427 | 0.105101947 | 7.861314211 | True | `p187_fh260_p060_from_aggr_lhs_retention_dy_05` |
| 280 | 60 | ok | 60 | 56.644144952 | 0.841052646 | 0.110795497 | 7.591036375 | True | `p187_fh280_p060_from_aggr_lhs_retention_dy_05` |
| 320 | 60 | ok | 120 | 99.104160987 | 0.891956993 | 0.121936287 | 7.314943046 | True | `p187_fh320_p060_from_aggr_lhs_retention_dy_05` |
| 350 | 60 | ok | 120 | 123.065117432 | 0.923323807 | 0.290263845 | 3.180981101 | False | `p187_fh350_p060_from_aggr_lhs_retention_dy_05` |
| 375 | 60 | ok | 120 | 142.524534731 | 0.933381686 | 0.434427936 | 2.148530534 | False | `p187_fh375_p060_from_aggr_lhs_retention_dy_05` |
| 400 | 60 | ok | -180 | 161.372714815 | 0.927565699 | 0.517582042 | 1.792113372 | False | `p187_fh400_p060_from_aggr_lhs_retention_dy_05` |

## Next decision

- Prefer heights with multiple early-pass bins and low leakage.
- If one height opens 0/60/120, use lateral compensation at that same height for negative bins.
- Do not proceed to K=6 until fixed-height six-bin single-dimer coverage exists.