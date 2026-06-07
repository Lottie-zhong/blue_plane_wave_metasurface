# 09-P137 Positive-Basin 60deg Results

Stage: 09-P137 real FDTD compact summary.

Remote runtime: `lumerical-win`, server root `D:\project\blue_plane_wave_metasurface`, server Python `N:\anaconda_envs\RCP_LCP\python.exe`, runtime `configs\runtime.yaml`.

The selected P136 top-12 candidates were run with the compact remote runner. No raw `results.csv`, raw `summary.md`, `.fsp`, `pre_run`, `.npy`, or large output is included here.

| Candidate | Phase | Nearest | Target | Leakage | Ratio | Early | Opens |
|---|---:|---:|---:|---:|---:|---|---|
| cpk_pos120_hswap_h320_01 | 167.4912 | -180 | 0.9487 | 0.0838 | 11.3154 | True | False |
| cpk_pos120_hswap_h340_01 | -173.8694 | -180 | 0.9044 | 0.2226 | 4.0620 | False | False |
| cpk_pos120_rotrel_h320_01 | 153.9232 | -180 | 0.9164 | 0.0752 | 12.1898 | True | False |
| cpk_pos120_intrel_h320_01 | 164.7841 | -180 | 0.9370 | 0.3037 | 3.0849 | False | False |
| cpk_pos120_hswap_scale96_01 | 119.2776 | 120 | 0.9402 | 0.4121 | 2.2816 | False | False |
| cpk_pos120_hswap_scale104_01 | 153.0735 | -180 | 0.9494 | 0.1497 | 6.3429 | True | False |
| cpk_pos120_rotrel_aspect_reduce5_01 | 128.9572 | 120 | 0.9460 | 0.1744 | 5.4240 | False | False |
| cpk_pos120_intrel_aspect_reduce5_01 | 147.9395 | 120 | 0.8870 | 0.1298 | 6.8313 | True | False |
| cpk_pos120_period430_h320_01 | 151.7780 | -180 | 0.7546 | 0.2221 | 3.3983 | False | False |
| cpk_pos120_period390_h320_01 | 153.0397 | -180 | 0.9164 | 0.0369 | 24.8532 | True | False |
| cpk_pos60_recover_m45weak_notch_p1_01 | 62.9936 | 60 | 0.6083 | 0.3922 | 1.5508 | False | False |
| cpk_pos60_recover_m40counter_notch_p1_01 | 67.9093 | 60 | 0.6318 | 0.3973 | 1.5905 | False | False |

Result: no candidate opens 60 with early-pass selectivity. Two rot60 recovery candidates hit the 60 phase window but fail leakage/ratio.
