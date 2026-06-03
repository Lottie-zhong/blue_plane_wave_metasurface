# APCD K=6 Nextgen Phase-Knob Pilot FDTD v6 Note

## Scope

This is 09-P36/P38. The stage compares released-rotation/dxdy nextgen candidates with one APCD-core plus standalone weak auxiliary phase helper pilot.

No full 60-row nextgen pool, old pool, K=7, phase-ramp supercell, TiO2/450 nm, Micro-LED integration, ML training, +15 deg steering claim, or complete K=6 phase-state library claim was made.

## Helper Audit

Existing nextgen helper family present: False
Weak-helper mini-pool generated: 10 rows
Weak-helper geometry pass: 4/10

The helper role is `weak_auxiliary_phase_helper`. It is a third standalone weak auxiliary phase shifter, not another APCD dimer and not half of another APCD pair.

## Pilot Results

| candidate | family | target | phase | leakage | ratio | early pass | target bin status |
|---|---|---:|---:|---:|---:|---|---|
| `ng_zero_rot_release_07` | `rotation_released_zero_bin` | 0 | 75.89220264939428 | 0.29936680506993796 | 2.8478912664241123 | False | open_gap |
| `ng_neg60_dxdy_release_08` | `rotation_released_neg60_dxdy` | -60 | 154.71643841246305 | 0.4060212164312129 | 1.4369649080489415 | False | open_gap |
| `wh_zero_aux_phase_01` | `apcd_core_plus_weak_helper` | 0 | 78.6430268607827 | 0.26999366921350887 | 3.1617773838687038 | False | open_gap |

## Coverage v6

| bin deg | status |
|---:|---|
| 0.0 | evidence_only |
| 60.0 | early_covered |
| 120.0 | strong_covered |
| -180.0 | evidence_only |
| -120.0 | open_gap |
| -60.0 | open_gap |

Dataset v6 rows: 30

## Next Step

If the weak-helper pilot opens a new usable phase region, design a smaller helper-neighborhood batch. If not, prioritize more radical phase-knob redesign before any phase-ramp supercell work.
