# P178 zero-bin opened final decision

## Scope

Stage 09 single-dimer phase-state library coverage only. This report does not run FDTD, call lumapi, edit `configs/runtime.yaml`, claim a K=6 phase-ramp supercell, claim +15 steering, or claim Micro-LED results.

## Physical Logic

P176 starts from the fixed-height h232 zero-bin phase-hit and uses coupled p2 width/size-up compensation to recover APCD selectivity. The h232 baseline already sits in the 0-bin phase window, but its selectivity ratio is below the early-pass threshold. The P176 coupled route uses the remaining phase budget to increase p2 size and recover leakage/ratio without leaving the 0-bin.

## Opened 0-Bin Candidates

The current P178 decision context reports `opens_0_count = 4` and `final_decision = 0_bin_opened`. The four P176 candidates recorded as 0-bin openings are:

- `cpk_zero_l60_h232_p1geom120x58_p2geom75x136_01`
- `cpk_zero_l60_h232_p1geom120x58_p2geom76x136_01`
- `cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01`
- `cpk_zero_l60_h232_p1geom120x58_p2geom77x137_01`

## Recommended 0 Deg Anchor

Recommended anchor: `cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01`.

Current P178 context for this anchor:

- phase: about 23.01 deg
- nearest bin: 0 deg
- target conversion: about 0.809
- opposite-spin leakage: about 0.105
- conversion-to-leakage ratio: about 7.67

## Coverage Update

Official Stage 09 phase-state bin coverage is now complete for the K=6 dimer phase-state library bins:

- before P178: covered `[-180, -120, -60, 60, 120]`, missing `[0]`
- after P178: covered `[-180, -120, -60, 0, 60, 120]`, missing `[]`

The compact coverage CSV is `outputs/apcd_k6_active_learning/stage09_phase_state_coverage_after_p178.csv`.

## No-Overclaim Statement

This is a Stage 09 single-dimer phase-state library coverage update only. It is not a K=6 phase-ramp supercell, not a steering result, not a +15 steering result, not a Stage 10 result, and not a Micro-LED result. Raw `results.csv`, raw `summary.md`, `.fsp`, `pre_run`, `.npy`, and large simulation outputs are not part of this finalization commit.
