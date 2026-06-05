# 09-P86 coverage update after core-offset continuation

## Scope

This is a stage 09 coverage update after the P85 controlled common negative APCD-core rotation continuation. It is not stage 10, not a K=6 phase-ramp supercell, and not a steering result.

## Coverage decision

No P85 candidate opened a remaining missing bin because none reached early-pass.

Early-pass bins after P86 remain:

```text
[-180, -120, 120]
```

Remaining missing bins after P86 remain:

```text
[-60, 0, 60]
```

## Key evidence

The continuation is still useful because it separates the phase and leakage problems:

- `cpk_branch_core_offset_m45_weak_01` lands at `59.538 deg`, within `0.462 deg` of the 60 deg missing bin.
- `cpk_branch_core_offset_m75_01` moves toward the 0 deg missing bin.
- All four P85 candidates fail early-pass due to leakage/ratio, so no coverage update is allowed.

## Next strategy

Do not generate or run extra candidates in this task. A later stage 09 plan should treat `cpk_branch_core_offset_m45_weak_01` as a phase anchor for 60 deg and focus on leakage recovery around that geometry. The next plan should not return to lower-transition/helper-lower repeats and should not enter a K=6 phase-ramp supercell.

No raw server-side `results.csv`, raw `summary.md`, `.fsp`, pre-run file, `.npy`, or large output is committed.
