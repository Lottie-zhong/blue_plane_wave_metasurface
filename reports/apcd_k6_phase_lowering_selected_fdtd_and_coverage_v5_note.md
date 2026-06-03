# APCD K=6 Phase-Lowering Selected FDTD and Coverage v5 Note

## Scope

This is 09-P29/P32. Four selected phase-lowering YAML configs were generated and dry-run/config validated. Real FDTD was run only for candidates listed as completed below; unrun backups are explicitly marked and not fabricated.

No full 42-row pool, old pool, K=7, phase-ramp supercell, TiO2/450 nm, Micro-LED integration, ML training, +15 deg steering claim, or complete K=6 phase-state library claim was made.

## Completed FDTD Results

| candidate | target bin | phase deg | error deg | leakage | ratio | early pass | target bin status |
|---|---:|---:|---:|---:|---:|---|---|
| `pl_zero_bridge_04` | 0 | 56.62387968893222 | 56.62387968893222 | 0.23236942858441817 | 3.270065259780975 | False | open_gap |
| `pl_neg60_focus_push_05` | -60 | 91.18359149700592 | 151.18359149700592 | 0.0907984852875001 | 9.97754884717948 | True | open_gap |
| `pl_neg120_aspect_03` | -120 | -172.61632817840064 | 52.616328178400636 | 0.5644311449581002 | 0.8235983909960333 | False | open_gap |
| `pl_pi_wrap_04` | -180 | 163.39711779606267 | 16.60288220393727 | 0.4178280655459571 | 1.4731396741955796 | False | evidence_only |

## Not Run

- none

## Coverage v5

| bin deg | status | nearest early-pass | early error |
|---:|---|---|---:|
| 0.0 | evidence_only | aggr_lhs_retention_dy_05 | 72.24132809604521 |
| 60.0 | early_covered | aggr_lhs_retention_dy_05 | 12.241328096045208 |
| 120.0 | strong_covered | p1W_p5 | 1.9212487281864696 |
| -180.0 | evidence_only | p1W_p5 | 61.92124872818647 |
| -120.0 | open_gap | p1W_p5 | 121.92124872818647 |
| -60.0 | open_gap | aggr_lhs_retention_dy_05 | 132.2413280960452 |

Dataset v5 row count: 27

## Next Step

Continue with the still-open phase bins using only small selected batches. Do not assemble a phase-ramp supercell until six usable phase states exist.
