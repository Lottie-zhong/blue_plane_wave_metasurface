# 09-P91 60deg selectivity-recovery results

## Scope

This is a stage 09 report for the P90-selected 60 deg selectivity-recovery top-4. The runs used the compact SSH runner on `lumerical-win` with server Python `N:\anaconda_envs\RCP_LCP\python.exe` and server runtime `configs\runtime.yaml`.

This is not stage 10, not a K=6 phase-ramp supercell, and not a steering result.

## Compact metrics

| candidate_id | phase_deg | nearest bin | target_conversion | leakage | ratio | PD | early_pass | opens_missing_bin |
|---|---:|---:|---:|---:|---:|---:|---|---|
| `cpk_60sel_relangle_m40_diff35_01` | 64.97188647904574 | 60 | 0.6319603455230327 | 0.3609651208445126 | 1.7507518289959705 | 0.272926049192432 | False | False |
| `cpk_60sel_p2geom_m40_90x145_01` | 75.95345859559603 | 60 | 0.6602656651278387 | 0.33787010215019386 | 1.954199738079742 | 0.3229977058697246 | False | False |
| `cpk_60sel_helper_suppress_m40_40x90_01` | 58.7671733210957 | 60 | 0.671383382303259 | 0.33091892059330485 | 2.028845558599388 | 0.33968240991335913 | False | False |
| `cpk_60sel_corecomp_m35_p2_90x145_01` | 81.79618278703117 | 60 | 0.7146487177982361 | 0.30027540443910505 | 2.3799775380596806 | 0.40828009136807275 | False | False |

## Result

No candidate opened the 60 deg missing bin. All four are nearest to 60, but none reaches leakage `<=0.2` or ratio `>=6`.

Best phase/selectivity balance is `cpk_60sel_helper_suppress_m40_40x90_01`, with phase `58.767 deg`, leakage `0.3309`, and ratio `2.0288`.

Best selectivity is `cpk_60sel_corecomp_m35_p2_90x145_01`, with leakage `0.3003`, ratio `2.3800`, and target conversion `0.7146`, but its phase is farther from 60.

No raw server-side `results.csv`, raw `summary.md`, `.fsp`, pre-run file, `.npy`, or large output is committed.
