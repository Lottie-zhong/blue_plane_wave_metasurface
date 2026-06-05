# 09-P87 60deg leakage-recovery candidate plan

## Scope

This is a stage 09 planning artifact only. No FDTD was run, no lumapi call was made, and no `.fsp`, raw `results.csv`, raw `summary.md`, pre-run file, `.npy`, or large output is created.

This plan does not enter stage 10, does not use a K=6 phase-ramp supercell, and makes no steering claim.

## Evidence base

Current early-pass bins are:

```text
[-180, -120, 120]
```

Remaining missing bins are:

```text
[-60, 0, 60]
```

P85 separated the phase-placement problem from the leakage problem:

- `cpk_branch_core_offset_m30_01`: `99.6206 deg`, near-pass, leakage `0.1788`, ratio `4.4793`.
- `cpk_branch_core_offset_m45_01`: `81.9563 deg`, leakage `0.3830`, ratio `1.6766`.
- `cpk_branch_core_offset_m45_weak_01`: `59.5382 deg`, leakage `0.3571`, ratio `1.8147`.
- `m60` and `m75` moved phase but collapsed optical quality.

The next useful plan should stop stronger negative offsets and focus leakage recovery around `m35` to `m45`, especially the `m45_weak` phase anchor.

## Candidate families

The P87 plan proposes 10 candidates across five families:

- `core_offset_interpolation`
- `core_offset_with_internal_counter_release`
- `helper_position_leakage_recovery`
- `helper_strength_leakage_recovery`
- `core_geometry_mild_recovery`

All candidates keep period `340/340`, height `300`, stage 09 scope, and no lower-transition repeats. None uses height `>=440`. None reverts pillar2 to `150x85` beta-selective geometry.

## Top-4 next FDTD selection

| rank | candidate_id | family | reason |
|---:|---|---|---|
| 1 | `cpk_60rec_offset_m40_01` | `core_offset_interpolation` | Best balance between the low-leakage `m30` branch and the near-60 `m45_weak` branch. |
| 2 | `cpk_60rec_counter_m40_relax_01` | `core_offset_with_internal_counter_release` | Tests whether restoring a little APCD relative angle recovers selectivity while keeping the phase shifted. |
| 3 | `cpk_60rec_helper_pos_m45_far_01` | `helper_position_leakage_recovery` | Uses the `m45_weak` phase anchor and moves the helper farther away to reduce leakage. |
| 4 | `cpk_60rec_helper_strength_m42p5_50x100_01` | `helper_strength_leakage_recovery` | Compares moderate helper weakening with an offset just below m45 to retain phase while improving leakage. |

## Guardrails

Do not continue `m60` or `m75` in the next batch. Do not return to lower-transition/helper-lower repeats. Do not enter a K=6 phase-ramp supercell. If the top-4 are later prepared as YAMLs, validate geometry before any remote FDTD run.

## Progress judgment

The phase target for 60 deg is now reachable, but the phase-state library remains incomplete because no 60 deg candidate has early-pass selectivity. P87 defines a compact leakage-recovery path around the most promising branch without expanding into random or out-of-scope designs.
