# K=6 Uniform Scaffold Diffraction Diagnostic Summary

## Task Scope

This is a K=6 uniform scaffold diagnostic run.
This is not the final metagrating.
This is not proof of +15 deg steering.
This diagnostic is only for validating the diffraction-order extraction pipeline and order sign convention.

## Setup Source

- input_setup: D:\project\blue_plane_wave_metasurface\outputs\apcd_k6_metagrating_633nm\apcd_k6_metagrating_633nm_setup.fsp
- K: 6
- dimers: 6
- nanopillars: 12
- structure: uniform identical alpha-pass dimer scaffold

## Run Status

- X input run: ok
- Y input run: ok
- grating power extraction: success
- gratingvector or complex field extraction: failed
- order-resolved Jones construction: failed

## Order Sign Convention

| order_n | order_m | u1 | u2 | expected_theta_deg | order_fraction |
|---:|---:|---:|---:|---:|---:|
| -3.0 | 0.0 | -0.7764571353075621 | 0.0 | -50.93732889852323 | 4.6061775629289145e-06 |
| -2.0 | 0 | -0.5176380902050415 | 0.0 | -31.173952196147127 | 2.7052991904859026e-06 |
| -1.0 | 0 | -0.25881904510252074 | 0.0 | -14.999999999999998 | 7.475136421078567e-06 |
| 0.0 | 0 | 0.0 | 0.0 | 0.0 | 0.9999756605682155 |
| 1.0 | 0 | 0.25881904510252074 | 0.0 | 14.999999999999998 | 7.089544294402671e-06 |
| 2.0 | 0 | 0.5176380902050415 | 0.0 | 31.173952196147127 | 9.914537823654958e-07 |
| 3.0 | 0 | 0.7764571353075621 | 0.0 | 50.93732889852323 | 1.4718205332186004e-06 |

If the rows above contain positive and negative u1 values, the sign convention can be inferred from the extracted order table. If not, sign convention remains unresolved.

## Uniform Scaffold Sanity Check

Phase 2.3A showed that uniform identical dimers should not coherently enhance m=+/-1 orders.
Extracted order fractions are m=-1: 7.475136421078567e-06, m=0: 0.9999756605682155, m=+1: 7.089544294402671e-06. This diagnostic does not convert those values into a performance claim.
If m=+/-1 are not weak, do not claim success; first inspect finite aperture effects, monitor normalization, order indexing, geometry uniformity, extraction correctness, source/monitor setup, and boundaries.

## APCD Order-Resolved Metrics

APCD order-resolved Jones metrics are not available in this diagnostic run.

## Next Step

If extraction succeeded, proceed to dimer phase-state mechanism design. If extraction failed, fix extraction only and do not change the physical design yet.

## Run Log Tail

- mode=run_real
- X: setup loaded from D:\project\blue_plane_wave_metasurface\outputs\apcd_k6_metagrating_633nm\apcd_k6_metagrating_633nm_setup.fsp
- X: source set to X-polarized input
- X: pre_run_fsp_saved=D:\project\blue_plane_wave_metasurface\outputs\apcd_k6_metagrating_633nm\diagnostic_uniform_run\pre_run_X.fsp
- X: pre_run_fsp_loaded=D:\project\blue_plane_wave_metasurface\outputs\apcd_k6_metagrating_633nm\diagnostic_uniform_run\pre_run_X.fsp
- X: fdtd.run completed
- X: switchtolayout_after_run=False
- X: grating power extraction success
- X: gratingvector complex extraction failed_or_unavailable
- X: result_fsp_saved=D:\project\blue_plane_wave_metasurface\outputs\apcd_k6_metagrating_633nm\diagnostic_uniform_run\result_X.fsp
- Y: setup loaded from D:\project\blue_plane_wave_metasurface\outputs\apcd_k6_metagrating_633nm\apcd_k6_metagrating_633nm_setup.fsp
- Y: source set to Y-polarized input
- Y: pre_run_fsp_saved=D:\project\blue_plane_wave_metasurface\outputs\apcd_k6_metagrating_633nm\diagnostic_uniform_run\pre_run_Y.fsp
- Y: pre_run_fsp_loaded=D:\project\blue_plane_wave_metasurface\outputs\apcd_k6_metagrating_633nm\diagnostic_uniform_run\pre_run_Y.fsp
- Y: fdtd.run completed
- Y: switchtolayout_after_run=False
- Y: grating power extraction success
- Y: gratingvector complex extraction failed_or_unavailable
- Y: result_fsp_saved=D:\project\blue_plane_wave_metasurface\outputs\apcd_k6_metagrating_633nm\diagnostic_uniform_run\result_Y.fsp
- order-resolved Jones unavailable: complex vector output extraction failed
