# APCD K=6 Baseline Candidate Real FDTD Validation Note

## Scope

This is the 08-P7 note for the K=6 dimer phase-state design.

It records the baseline candidate real x/y FDTD validation reported for:

```text
C:\Users\DELL\anaconda3\python.exe scripts\13_run_apcd_single_dimer.py --config configs\apcd_k6_phase_state_candidates\baseline.yaml --runtime configs\runtime.yaml
```

This note does not commit `.fsp`, `pre_run_X.fsp`, `pre_run_Y.fsp`, or large simulation output files.

## Evidence Status

User-provided result paths:

```text
outputs\apcd_k6_metagrating_633nm\phase_state_candidates\baseline\results.csv
outputs\apcd_k6_metagrating_633nm\phase_state_candidates\baseline\summary.md
```

Current local workspace check: these two files were not present in this checkout when this note was written. Therefore, this report records the user-provided run record and compares it against the committed Phase 1 Gate 1 evidence.

Committed comparison evidence:

- `configs/apcd_k6_phase_state_candidates/baseline.yaml`
- `reports/apcd_fig2_alpha_pass_gate1_report.md`
- `reports/apcd_k6_candidate_config_scaffold_report.md`

## Baseline Geometry

The baseline candidate remains the alpha-pass geometry:

| Pillar | Length | Width | Rotation |
|---|---:|---:|---:|
| pillar 1 | 130 nm | 70 nm | 67.5 deg |
| pillar 2 | 85 nm | 150 nm | 112.5 deg |

The original beta-selective pillar 2 geometry `150 x 85 nm` was not used as the baseline.

## Reported Real-Run Metrics

The user-provided baseline candidate run reports:

| Metric | Value |
|---|---:|
| status | ok |
| target_conversion | 0.9711541351322045 |
| opposite_spin_leakage | 0.0401994772579764 |
| conversion_to_leakage_ratio | 24.158377206667513 |
| PD | 0.9205036166065964 |
| total_transmission | 0.5056768061950905 |

These values match the committed Phase 1 alpha-pass Gate 1 metrics in `reports/apcd_fig2_alpha_pass_gate1_report.md`.

## Interpretation

The baseline candidate config, setup-only export path, real x/y FDTD run, and single-dimer Jones extraction workflow are reported as validated for the baseline candidate.

This result is consistent with the Phase 1 alpha-pass Gate 1 result. It supports using the baseline candidate as the first reference for later small-subset candidate evaluation.

## Boundaries

This is not evidence of `+15 deg` steering.

This is not a K=6 phase-ramp supercell result.

This is not a K=7 result.

This is not a large sweep.

This is not a TiO2/450 nm or ML result.

Do not infer directional metagrating performance from this single-dimer validation.

## Next Step

Evaluate a very small subset of one-factor geometry variants through the same x/y real FDTD and Jones extraction workflow. Do not immediately run all 13 candidates as a large batch. A reasonable next subset is:

- `baseline` as the reference
- one mild pillar-1 perturbation such as `p1L_m5`
- one mild pillar-2 perturbation such as `p2W_m5`

Each future candidate should be judged by the Phase 08 schema and pass/fail criteria before any K=6 phase-ramp supercell is assembled.
