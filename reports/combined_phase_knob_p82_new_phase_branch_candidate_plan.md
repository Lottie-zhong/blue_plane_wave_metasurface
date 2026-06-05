# 09-P82 new phase-branch candidate plan

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

P75-P78 showed both lower-transition candidates were early-pass but nearest to `-180`. P79 then ran six controlled lower/helper variants; all six were early-pass but still nearest to `-180`. That is evidence to stop the lower-height/helper-lower route for now.

## Planning decision

P82 pivots to new phase-branch mechanisms:

- `apcd_core_common_rotation_offset`
- `apcd_core_internal_rotation_release`
- `mild_core_geometry_perturbation`
- `helper_quadrant_swap`
- `explicit_phase_offset_reference`

The plan proposes 10 candidates and selects only 4 for the next FDTD pass. The selected candidates prioritize missing bins `[-60, 0, 60]`, keep period fixed at `340/340`, use `h=300` to avoid reinforcing the observed lower-transition `-180` basin, and avoid any height `>=440`.

## Top-4 next FDTD selection

| rank | candidate_id | family | target bins | height | period | reason |
|---:|---|---|---|---:|---|---|
| 1 | `cpk_branch_core_offset_m30_01` | `apcd_core_common_rotation_offset` | `60/0` | 300 | `340/340` | Common `-30 deg` core rotation offset at plateau height; intended to test a controlled branch away from `-180`. |
| 2 | `cpk_branch_core_offset_p30_01` | `apcd_core_common_rotation_offset` | `-60/0` | 300 | `340/340` | Opposite-sign common offset gives a paired branch comparison without lower-transition geometry. |
| 3 | `cpk_branch_internal_release_01` | `apcd_core_internal_rotation_release` | `0/60` | 300 | `340/340` | Releases the internal APCD core rotations while keeping the period fixed. |
| 4 | `cpk_branch_helper_swap_br_01` | `helper_quadrant_swap` | `-60/0` | 300 | `340/340` | Moves the helper to a different empty quadrant to test a new coupling branch. |

## Guardrails

Do not run more lower-transition/helper-lower repeats. Do not use height `>=440`. Do not treat this plan as a complete phase-state library. If these selected candidates are later prepared as YAMLs, validate geometry before any real FDTD run, especially for helper-quadrant overlap risk.

## Priority and progress judgment

Priority 1: prepare the top-4 YAMLs only if the next task explicitly asks for FDTD preparation.

Priority 2: after real FDTD, update coverage from P80 and stop immediately if a missing bin opens unless the task defines a paired comparison.

Priority 3: keep stage 09 active until `[-60, 0, 60]` are covered by real early-pass evidence.

Project progress judgment: the P75-P79 route is now closed as a useful route to the remaining bins. P82 defines a controlled new-branch plan, but coverage remains incomplete until real FDTD evidence opens at least one missing bin.
