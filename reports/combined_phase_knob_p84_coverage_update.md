# 09-P84 coverage update after P83 top-4

## Scope

This is a stage 09 coverage update after the P83 top-4 new phase-branch remote FDTD runs. It is not stage 10, not a K=6 phase-ramp supercell, and not a steering result.

## Coverage decision

The P83 batch completed exactly the four P82-selected candidates:

1. `cpk_branch_core_offset_m30_01`
2. `cpk_branch_core_offset_p30_01`
3. `cpk_branch_internal_release_01`
4. `cpk_branch_helper_swap_br_01`

No candidate opened a remaining missing bin from `[-60, 0, 60]`.

Early-pass bins after P84 remain:

```text
[-180, -120, 120]
```

Remaining missing bins after P84 remain:

```text
[-60, 0, 60]
```

## Interpretation

The new phase-branch batch avoided repeating the lower-transition/helper-lower route, but it still did not open a missing bin. The strongest two candidates, `cpk_branch_internal_release_01` and `cpk_branch_helper_swap_br_01`, were early-pass duplicates around the already covered `120` bin. The `-30 deg` common core offset moved closer to the target `60` bin than prior `-180` duplicates but remained only near-pass and nearest to the covered `120` bin.

## Next strategy

Do not generate or run extra candidates in this task. For a later stage 09 plan, prioritize mechanisms that move phase below `120` without relying on the lower-height/helper-lower route. Candidate planning should explicitly penalize both `-180` and `120` reinforcement and should validate geometry before remote FDTD.

No raw server-side `results.csv`, raw `summary.md`, `.fsp`, pre-run file, `.npy`, or large output is committed.
