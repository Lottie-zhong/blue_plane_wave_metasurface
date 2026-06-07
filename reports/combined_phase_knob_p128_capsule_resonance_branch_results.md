# 09-P128 Capsule-Core Resonance Branch Results

Stage: 09-P128 real FDTD compact summary.

Remote runtime: `lumerical-win`, server root `D:\project\blue_plane_wave_metasurface`, server Python `N:\anaconda_envs\RCP_LCP\python.exe`, runtime `configs\runtime.yaml`.

The selected P127 top-6 capsule/racetrack candidates were run with the compact remote runner. No raw `results.csv`, raw `summary.md`, `.fsp`, `pre_run`, `.npy`, or large output is included here.

| Candidate | Phase | Nearest | Target | Leakage | Ratio | PD | Early | Opens |
|---|---:|---:|---:|---:|---:|---:|---|---|
| cpk_capsule_res_h425_01 | -157.6913 | -180 | 0.9125 | 0.0149 | 61.1240 | 0.9678 | True | False |
| cpk_capsule_res_h430_01 | -153.2468 | -180 | 0.9152 | 0.0263 | 34.7326 | 0.9440 | True | False |
| cpk_capsule_res_h435_01 | -148.7845 | -120 | 0.9170 | 0.0698 | 13.1346 | 0.8585 | True | False |
| cpk_capsule_res_aniso_reduce5_01 | -156.5074 | -180 | 0.8971 | 0.0393 | 22.8163 | 0.9160 | True | False |
| cpk_capsule_res_aniso_reduce10_01 | -153.1857 | -180 | 0.8619 | 0.1396 | 6.1748 | 0.7212 | True | False |
| cpk_capsule_res_scale98_01 | -169.8469 | -180 | 0.8982 | 0.1101 | 8.1607 | 0.7817 | True | False |

Result: all six candidates are early-pass, but none opens the remaining [0, 60] bins.
