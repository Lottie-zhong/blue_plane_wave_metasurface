# APCD K=6 Phase Gap Analysis v8

Scope: helper refinement v8 update. Only selected top-4 FDTD results were added.

| bin deg | status | nearest early-pass | early error | nearest evidence-only | evidence error |
|---:|---|---|---:|---|---:|
| 0.0 | evidence_only | aggr_lhs_retention_dy_05 | 72.24132809604521 | next_zero_rot_anchor_03 | 20.788972844777305 |
| 60.0 | early_covered | aggr_lhs_retention_dy_05 | 12.241328096045208 | doe_lhs_like_01 | 0.6410999999999945 |
| 120.0 | strong_covered | hr_lowleak_control_02 | 0.6917854938060373 | pl_pi_wrap_04 | 43.39711779606267 |
| -180.0 | evidence_only | hr_aniso_push_08 | 48.33501596848589 | pl_pi_wrap_04 | 16.60288220393727 |
| -120.0 | open_gap | hr_aniso_push_08 | 108.33501596848589 | pl_pi_wrap_04 | 76.60288220393733 |
| -60.0 | open_gap | aggr_lhs_retention_dy_05 | 132.2413280960452 | next_zero_rot_anchor_03 | 80.78897284477728 |

Refinement results:
- `hr_aniso_push_05`: phase=128.72874773442857, leakage=0.1200857911932035, ratio=8.045695404886663, early_pass=True, status=usable_but_not_target
- `hr_aniso_push_08`: phase=131.6649840315141, leakage=0.07909108118126469, ratio=12.158022572100036, early_pass=True, status=usable_but_not_target
- `hr_phase_delay_03`: phase=128.72715476002463, leakage=0.056781903980201914, ratio=17.01161162869423, early_pass=True, status=usable_but_not_target
- `hr_lowleak_control_02`: phase=120.69178549380604, leakage=0.04396643352483241, ratio=22.090892311344128, early_pass=True, status=strong_covered
