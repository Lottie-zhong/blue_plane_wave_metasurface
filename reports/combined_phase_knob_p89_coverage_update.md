# 09-P89 coverage update after 60deg leakage-recovery top-4

## Scope

This is a stage 09 coverage update after the P88 60 deg leakage-recovery top-4 remote FDTD runs. It is not stage 10, not a K=6 phase-ramp supercell, and not a steering result.

## Coverage decision

All four P88 candidates landed nearest to the 60 deg missing bin, but no candidate reached early-pass. Therefore no missing bin is opened.

Early-pass bins after P89 remain:

```text
[-180, -120, 120]
```

Remaining missing bins after P89 remain:

```text
[-60, 0, 60]
```

## Best tradeoff

`cpk_60rec_counter_m40_relax_01` is the best tradeoff among the P88 candidates:

- phase: `65.46284604437005 deg`
- phase error to 60: `5.462846044370053 deg`
- target_conversion: `0.6590159828254635`
- opposite_spin_leakage: `0.3364428543033098`
- conversion_to_leakage_ratio: `1.9587753890305217`

It still fails the target recovery goal because leakage is above `0.2` and ratio is below `6`.

`cpk_60rec_helper_pos_m45_far_01` is the best phase match at `60.712757284514964 deg`, but its leakage is `0.4586060994189824`, so the helper-position move made selectivity worse.

## Next strategy

Do not generate or run extra candidates in this task. For a later stage 09 plan, the 60 deg phase is reproducible, but leakage remains the bottleneck. The next plan should focus on APCD selectivity recovery around the `m40` and `m42.5/m45 weak-helper` branch without going to stronger negative offsets or lower-transition repeats.

No raw server-side `results.csv`, raw `summary.md`, `.fsp`, pre-run file, `.npy`, or large output is committed.
