# 09-P79 remaining-bin batch results

## Scope

This report summarizes the controlled stage 09 remaining-bin batch for `[-60, 0, 60]`. The runs used the compact SSH runner on `lumerical-win` with the server Python `N:\anaconda_envs\RCP_LCP\python.exe` and server runtime `configs\runtime.yaml`.

This is not stage 10, not a K=6 phase-ramp supercell, and not a steering result.

## Candidates run

Six candidates were run, which reaches the task maximum. No random extra candidates were run.

| candidate_id | phase_deg | nearest bin | best missing bin | target_conversion | leakage | ratio | PD | early_pass | near_pass | opens_missing_bin |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| `cpk_mbin_helper_rot_lower_01` | -177.98742797597288 | -180 | -60 | 0.9604897595164789 | 0.10519332330974679 | 9.130710289284615 | 0.8025804763060103 | True | False | False |
| `cpk_mbin_helper_rot_lower_02` | -165.3676397913848 | -180 | -60 | 0.9678788573908697 | 0.0671018360033864 | 14.424029430857898 | 0.8703321976301631 | True | False | False |
| `cpk_mbin_helper_weak_lower_01` | 176.11240019533437 | -180 | 60 | 0.9211921388626363 | 0.1294701491589224 | 7.115092898562845 | 0.7535456432854425 | True | False | False |
| `cpk_mbin_helper_weak_lower_02` | 171.78237328107832 | -180 | 60 | 0.9452889841394692 | 0.07354094406220983 | 12.853914185925806 | 0.8556364668390853 | True | False | False |
| `cpk_mbin_nohelper_lower_01` | 160.88957106662167 | -180 | 60 | 0.9673388261871968 | 0.04620006385450978 | 20.938040891318654 | 0.908834156619164 | True | False | False |
| `cpk_mbin_period_guarded_lower_01` | 174.42038394013554 | -180 | 60 | 0.9394440611522423 | 0.0915220395034957 | 10.264675768147576 | 0.8224538334564152 | True | False | False |

## Stop-rule evidence

No candidate opened a remaining missing bin. No pair of consecutive candidates failed with leakage above `0.4`; all leakage values were below `0.13`.

The run stopped after the sixth candidate because the max-6 task limit was reached.

## Interpretation

All six candidates are early-pass by conversion/leakage/ratio, but every one is nearest to the already covered `-180` bin. The controlled helper-rotation, weak-helper, no-helper, and guarded-period probes did not open `-60`, `0`, or `60`.

Raw server-side `results.csv`, `summary.md`, `.fsp`, pre-run files, `.npy`, and large outputs are not included in this report or committed.
