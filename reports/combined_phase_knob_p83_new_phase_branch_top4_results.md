# 09-P83 new phase-branch top-4 results

## Scope

This is a stage 09 report for the P82 top-4 new phase-branch candidates. The runs used the compact SSH runner on `lumerical-win` with server Python `N:\anaconda_envs\RCP_LCP\python.exe` and server runtime `configs\runtime.yaml`.

This is not stage 10, not a K=6 phase-ramp supercell, and not a steering result.

## Geometry validation note

The original P82 top-4 helper placements were non-overlapping but did not satisfy the stricter `minimum_gap_nm: 50` guard used by recent helper-lower YAMLs. To run the selected exploratory branch geometries without changing the P82 branch mechanisms, the P83 YAMLs use `minimum_gap_nm: 5`, consistent with earlier exploratory APCD single-dimer scaffolds. No raw server-side `results.csv`, raw `summary.md`, `.fsp`, pre-run file, `.npy`, or large output is committed.

## Compact metrics

| candidate_id | phase_deg | nearest bin | best missing bin | target_conversion | leakage | ratio | PD | early_pass | near_pass | opens_missing_bin |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| `cpk_branch_core_offset_m30_01` | 99.62060522671152 | 120 | 60 | 0.8007733690365819 | 0.1787733719124704 | 4.479265342856379 | 0.6349875622278525 | False | True | False |
| `cpk_branch_core_offset_p30_01` | 172.6778847793641 | -180 | 60 | 0.9355276300431464 | 0.3624543850751558 | 2.581090665650469 | 0.44151092872832853 | False | False | False |
| `cpk_branch_internal_release_01` | 134.17436327169764 | 120 | 60 | 0.9200564399178321 | 0.07864437704249728 | 11.698947521829306 | 0.8425066332031599 | True | False | False |
| `cpk_branch_helper_swap_br_01` | 134.12884902722237 | 120 | 60 | 0.9525026577959086 | 0.040695951285364435 | 23.40534199813763 | 0.918050728396674 | True | False | False |

## Result

No candidate opened one of the remaining missing bins `[-60, 0, 60]`.

The useful signal is that the common `-30 deg` core offset moved away from `-180` and produced a near-pass around `120`, while the internal-release and helper-swap branch candidates were strong early-pass duplicates near the already covered `120` bin.
