# 09-P120 0/60 anchor-discovery FDTD results

Stage: 09-P120 real FDTD compact summary for the P119 top-6 anchor-discovery candidates.

Scope: stage 09 only. These are single-dimer APCD candidates, not K=6 phase-ramp supercells, not steering results, and not a complete phase-state library claim.

Current missing bins are [0, 60]. This report recomputes opens_missing_bin against [0, 60].

| Candidate | Phase (deg) | Nearest bin | Best current missing bin | Target | Leakage | Ratio | PD | Early | Near | Opens [0,60] | Useful anchor | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|---|
| cpk_060_anchor_nohelper_h420_01 | -132.4326 | -120 | 0 | 0.8941 | 0.2877 | 3.1082 | 0.5132 | False | False | False | False | fail_covered_bin |
| cpk_060_anchor_nohelper_h430_scale96_01 | -141.3854 | -120 | 0 | 0.9002 | 0.2087 | 4.3131 | 0.6236 | False | True | False | False | near_pass_covered_bin |
| cpk_060_anchor_wh03_h430_trim_m5_01 | -128.1467 | -120 | 0 | 0.9077 | 0.1474 | 6.1561 | 0.7205 | True | False | False | False | early_pass_covered_bin |
| cpk_060_anchor_wh03_h425_scale98_01 | -120.0309 | -120 | 0 | 0.9142 | 0.0886 | 10.3229 | 0.8234 | True | False | False | False | early_pass_covered_bin |
| cpk_060_anchor_htrans04_h410_nohelper_01 | -151.9099 | -180 | 60 | 0.9028 | 0.1248 | 7.2335 | 0.7571 | True | False | False | False | early_pass_covered_bin |
| cpk_060_anchor_transition02_h380_scale96_01 | -157.8044 | -180 | 60 | 0.8530 | 0.0819 | 10.4112 | 0.8247 | True | False | False | False | early_pass_covered_bin |

Result: no P120 candidate opens [0, 60] or qualifies as a useful 0/60 anchor. The best selectivity anchor is cpk_060_anchor_wh03_h425_scale98_01, but it reinforces the covered -120 bin.
