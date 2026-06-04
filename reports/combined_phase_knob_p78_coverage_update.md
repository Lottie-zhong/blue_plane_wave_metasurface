# 09-P78 coverage update after lower_transition_02

## Scope

This is a stage 09 coverage update after the P75/P77 lower-transition top-2 remote FDTD runs. It is not stage 10, not a K=6 phase-ramp supercell, and not a steering result.

## Coverage decision

Both lower-transition candidates are early-pass, but both are nearest to `-180`, which was already covered.

Early-pass bins after P78 remain:

```text
[-180, -120, 120]
```

Remaining missing bins remain:

```text
[-60, 0, 60]
```

## Stop condition

Per the task rule, execution stops after `cpk_mbin_lower_transition_02`. No additional candidates or broader pools were run.

The lower-height transition probes did not open a remaining missing bin. The next planning step should not enter a K=6 phase-ramp supercell; the phase-state library is still incomplete.
