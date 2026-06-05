# 09-P85 core-offset continuation results

## Scope

This is a stage 09 controlled continuation of the promising P83 common negative APCD-core rotation branch. The runs used the compact SSH runner on `lumerical-win` with server Python `N:\anaconda_envs\RCP_LCP\python.exe` and server runtime `configs\runtime.yaml`.

This is not stage 10, not a K=6 phase-ramp supercell, and not a steering result.

## Compact metrics

| candidate_id | offset | phase_deg | nearest bin | best missing bin | target_conversion | leakage | ratio | PD | early_pass | near_pass | opens_missing_bin |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| `cpk_branch_core_offset_m45_01` | -45 | 81.95631354619724 | 60 | 60 | 0.6420595961718223 | 0.3829537353537556 | 1.6765983378593752 | 0.25278291788866186 | False | False | False |
| `cpk_branch_core_offset_m60_01` | -60 | 33.607340186280425 | 60 | 60 | 0.48345956612499263 | 0.6270617955126208 | 0.7709919015716707 | -0.1293106412430806 | False | False | False |
| `cpk_branch_core_offset_m75_01` | -75 | -28.27242002005036 | 0 | 0 | 0.4441776786864729 | 0.7660653546367946 | 0.5798169516457061 | -0.26596945166143043 | False | False | False |
| `cpk_branch_core_offset_m45_weak_01` | -45 | 59.53824659138192 | 60 | 60 | 0.6479998963734737 | 0.3570751587304602 | 1.8147437045930284 | 0.2894557338433195 | False | False | False |

## Result

No candidate opened a remaining missing bin because none reached early-pass.

The branch is phase-promising: `cpk_branch_core_offset_m45_weak_01` lands at `59.538 deg`, only `0.462 deg` from the 60 deg missing bin. The limiting issue is leakage/ratio, not phase placement.

## Stop condition

The task-defined maximum of four candidates was reached. No extra candidates were generated or run.

No raw server-side `results.csv`, raw `summary.md`, `.fsp`, pre-run file, `.npy`, or large output is committed.
