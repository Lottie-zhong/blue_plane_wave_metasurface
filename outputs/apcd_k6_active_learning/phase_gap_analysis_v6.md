# APCD K=6 Phase Gap Analysis v6

Scope: 09-P36/P38 nextgen phase-knob pilot. At most three pilot candidates were run. No full pool, K=7, phase-ramp supercell, TiO2/450 nm, Micro-LED, or ML training.

| bin deg | status | nearest early-pass | early error | nearest evidence-only | evidence error |
|---:|---|---|---:|---|---:|
| 0.0 | evidence_only | aggr_lhs_retention_dy_05 | 72.24132809604521 | next_zero_rot_anchor_03 | 20.788972844777305 |
| 60.0 | early_covered | aggr_lhs_retention_dy_05 | 12.241328096045208 | doe_lhs_like_01 | 0.6410999999999945 |
| 120.0 | strong_covered | p1W_p5 | 1.9212487281864696 | pl_pi_wrap_04 | 43.39711779606267 |
| -180.0 | evidence_only | p1W_p5 | 61.92124872818647 | pl_pi_wrap_04 | 16.60288220393727 |
| -120.0 | open_gap | p1W_p5 | 121.92124872818647 | pl_pi_wrap_04 | 76.60288220393733 |
| -60.0 | open_gap | aggr_lhs_retention_dy_05 | 132.2413280960452 | next_zero_rot_anchor_03 | 80.78897284477728 |

Pilot results:
- `ng_zero_rot_release_07`: phase=75.89220264939428, leakage=0.29936680506993796, ratio=2.8478912664241123, early_pass=False, status=open_gap
- `ng_neg60_dxdy_release_08`: phase=154.71643841246305, leakage=0.4060212164312129, ratio=1.4369649080489415, early_pass=False, status=open_gap
- `wh_zero_aux_phase_01`: phase=78.6430268607827, leakage=0.26999366921350887, ratio=3.1617773838687038, early_pass=False, status=open_gap

Do not claim a complete K=6 library or +15 deg steering from these results.
