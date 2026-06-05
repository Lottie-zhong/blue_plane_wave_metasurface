# 09-P88 60deg leakage-recovery results

## Scope

This is a stage 09 report for the P87-selected 60 deg leakage-recovery top-4. The runs used the compact SSH runner on `lumerical-win` with server Python `N:\anaconda_envs\RCP_LCP\python.exe` and server runtime `configs\runtime.yaml`.

This is not stage 10, not a K=6 phase-ramp supercell, and not a steering result.

## Compact metrics

| candidate_id | phase_deg | nearest bin | best missing bin | target_conversion | leakage | ratio | PD | early_pass | near_pass | opens_missing_bin |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|
| `cpk_60rec_offset_m40_01` | 69.20096796626916 | 60 | 60 | 0.6631161664681112 | 0.33870929138709793 | 1.9577737703962284 | 0.32381576305238496 | False | False | False |
| `cpk_60rec_counter_m40_relax_01` | 65.46284604437005 | 60 | 60 | 0.6590159828254635 | 0.3364428543033098 | 1.9587753890305217 | 0.3240446681373942 | False | False | False |
| `cpk_60rec_helper_pos_m45_far_01` | 60.712757284514964 | 60 | 60 | 0.6332027629714944 | 0.4586060994189824 | 1.3807116036470761 | 0.15991504517565358 | False | False | False |
| `cpk_60rec_helper_strength_m42p5_50x100_01` | 57.965867663939264 | 60 | 60 | 0.6583011522494953 | 0.3391108529647767 | 1.9412565138896674 | 0.32001850550798966 | False | False | False |

## Result

All four candidates land nearest to the 60 deg missing bin, but none opens the bin because none reaches early-pass. The target leakage condition is `<=0.2` and ratio condition is `>=6`; all four remain around leakage `0.336` to `0.459` with ratio about `1.38` to `1.96`.

## Best tradeoff

`cpk_60rec_counter_m40_relax_01` is the best P88 tradeoff: phase error `5.463 deg`, lowest leakage in the batch at `0.3364`, and the highest ratio at `1.9588`. It is still far from early-pass.

`cpk_60rec_helper_pos_m45_far_01` is the best phase match at `60.713 deg`, but it worsens leakage to `0.4586`.

No extra candidates were generated or run. No raw server-side `results.csv`, raw `summary.md`, `.fsp`, pre-run file, `.npy`, or large output is committed.
