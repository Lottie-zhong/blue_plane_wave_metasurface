# 09-P92 coverage update after 60deg selectivity recovery

## Scope

This is a stage 09 coverage update after the P91 60 deg selectivity-recovery top-4 remote FDTD runs. It is not stage 10, not a K=6 phase-ramp supercell, and not a steering result.

## Coverage decision

All four P91 candidates were nearest to the 60 deg missing bin, but no candidate reached early-pass. Therefore the 60 deg bin remains missing.

Early-pass bins after P92 remain:

```text
[-180, -120, 120]
```

Remaining missing bins after P92 remain:

```text
[-60, 0, 60]
```

## Best tradeoff

`cpk_60sel_helper_suppress_m40_40x90_01` gives the best phase/selectivity balance:

- phase: `58.7671733210957 deg`
- leakage: `0.33091892059330485`
- ratio: `2.028845558599388`
- target_conversion: `0.671383382303259`

`cpk_60sel_corecomp_m35_p2_90x145_01` gives the best leakage/ratio:

- phase: `81.79618278703117 deg`
- leakage: `0.30027540443910505`
- ratio: `2.3799775380596806`
- target_conversion: `0.7146487177982361`

The selectivity target `leakage <= 0.2` and `ratio >= 6` is still not met.

No raw server-side `results.csv`, raw `summary.md`, `.fsp`, pre-run file, `.npy`, or large output is committed.
