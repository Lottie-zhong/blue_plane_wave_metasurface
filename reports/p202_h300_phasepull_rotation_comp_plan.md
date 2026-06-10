# P202 h300 phase-pull + rotation compensation plan

## Scope

- Fixed h300 only.
- No helper.
- No K=6 / steering claim.
- Based on P201 phase-pull candidates and p2 negative micro-rotation compensation.

## Candidate plan

| candidate_id | base | variant | selected | gap nm | pass | purpose |
|---|---|---|---|---:|---|---|
| `p202_h300_phasepull_rotcomp_A_m2_p2rot_m2p5` | A_m2 | p2rot_m2p5 | True | 99.302 | True | mild healthy phase-pull point plus p2 -2.5deg selectivity compensation |
| `p202_h300_phasepull_rotcomp_A_m4_p2rot_m2p5` | A_m4 | p2rot_m2p5 | True | 99.326 | True | main recovery candidate: phase-pull m4 plus p2 -2.5deg compensation |
| `p202_h300_phasepull_rotcomp_A_m4_p2rot_m5` | A_m4 | p2rot_m5 | True | 99.326 | True | stronger p2 rotation compensation on m4 phase-pull point |
| `p202_h300_phasepull_rotcomp_A_m6_p2rot_m2p5` | A_m6 | p2rot_m2p5 | True | 99.334 | True | strong phase-pull m6 with mild p2 recovery |
| `p202_h300_phasepull_rotcomp_A_m6_p2rot_m5` | A_m6 | p2rot_m5 | True | 99.334 | True | strong phase-pull m6 with stronger p2 recovery |
| `p202_h300_phasepull_rotcomp_B_Lm4_p2rot_m2p5` | B_Lm4 | p2rot_m2p5 | True | 100.674 | True | common-area phase pull plus p2 -2.5deg recovery |
| `p202_h300_phasepull_rotcomp_A_m4_p1rot_p2p5_p2rot_m2p5` | A_m4 | p1rot_p2p5_p2rot_m2p5 | False | 99.326 | True | relative-angle compensation around m4 phase-pull point |
| `p202_h300_phasepull_rotcomp_A_m6_p1rot_p2p5_p2rot_m2p5` | A_m6 | p1rot_p2p5_p2rot_m2p5 | False | 99.334 | True | relative-angle compensation around m6 phase-pull point |

## First FDTD queue

- `p202_h300_phasepull_rotcomp_A_m2_p2rot_m2p5`
- `p202_h300_phasepull_rotcomp_A_m4_p2rot_m2p5`
- `p202_h300_phasepull_rotcomp_A_m4_p2rot_m5`
- `p202_h300_phasepull_rotcomp_A_m6_p2rot_m2p5`
- `p202_h300_phasepull_rotcomp_A_m6_p2rot_m5`
- `p202_h300_phasepull_rotcomp_B_Lm4_p2rot_m2p5`