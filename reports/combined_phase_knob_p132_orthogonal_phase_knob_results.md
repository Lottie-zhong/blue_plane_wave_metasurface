# 09-P132 Orthogonal Phase-Knob Results

Stage: 09-P132 real FDTD compact summary.

Remote runtime: `lumerical-win`, server root `D:\project\blue_plane_wave_metasurface`, server Python `N:\anaconda_envs\RCP_LCP\python.exe`, runtime `configs\runtime.yaml`.

The selected P131 top-6 orthogonal phase-knob candidates were run with the compact remote runner. No raw `results.csv`, raw `summary.md`, `.fsp`, `pre_run`, `.npy`, or large output is included here.

| Candidate | Phase | Nearest | Target | Leakage | Ratio | PD | Early | Opens |
|---|---:|---:|---:|---:|---:|---:|---|---|
| cpk_orth_mixed_rect_capsule_h425_01 | -147.1610 | -120 | 0.8244 | 0.2810 | 2.9333 | 0.4915 | False | False |
| cpk_orth_mixed_capsule_rect_h425_01 | -138.7198 | -120 | 0.8989 | 0.8605 | 1.0446 | 0.0218 | False | False |
| cpk_orth_mixed_rect_round_h430_01 | -123.9242 | -120 | 0.8992 | 0.3525 | 2.5510 | 0.4368 | False | False |
| cpk_orth_mixed_capsule_chamfer_h430_01 | -135.1359 | -120 | 0.8992 | 0.8676 | 1.0364 | 0.0179 | False | False |
| cpk_orth_notch_p1_right_h425_01 | -149.2261 | -120 | 0.8670 | 0.0771 | 11.2431 | 0.8366 | True | False |
| cpk_orth_scalar_mixed_capsule_35_h425_01 | -146.0955 | -120 | 0.8279 | 0.2811 | 2.9453 | 0.4931 | False | False |

Result: no candidate opens [0, 60]. Only the notch candidate remains early-pass, and it is still a covered -120 result.
