# MDC-ML recovery record (2026-07-18)

## What was recovered

The working tree contained untracked MDC-ML implementation files dated 2026-07-11 to 2026-07-13. They have been restored as versioned project assets:

- database builder, label-view builder, forward-surrogate trainer, environment/database validators, and semantic audit under `scripts/`;
- label-view regression test under `tests/`;
- the surviving design-space and nominal-semantic audit reports under `reports/mdc_defect_450/`.

The restored workflow keeps the original data boundary: canonical `tmm_nominal_metrics` records are the training universe; tolerance records and FDTD records are not training rows and must not be mixed into the TMM plane-wave targets.

## Recovery boundary

No tracked Git commit, ref, tag, alternate worktree, or local dataset directory containing `datasets/mdc_ml_database_v1/` was found during recovery. Therefore the historical database, prepared label views, model artifacts, and their raw input outputs cannot be recreated or claimed as verified from this workspace.

The recovered scripts intentionally fail with a clear missing-input error until those source results are restored. No solver run, model training, data synthesis, or simulation output generation was performed during this recovery.

## Two repair actions made during recovery

1. Removed the label-view builder's fixed historical `HEAD` gate. Reproducibility remains enforced by SHA-256 checks of all input files, so restoring the workflow on a new commit no longer blocks it.
2. Corrected the forward-surrogate source predicate to use the canonical `tmm_nominal_metrics` fact table rather than `geometry_master.is_nominal_geometry`. The latter is a legacy reference-candidate marker and the surviving semantic audit reports that it would select only two of the historical 2,688 canonical TMM rows.

## Recovery procedure after source data is available

1. Restore the committed lightweight MDC source files and `outputs/mdc_*` result tables required by `scripts/build_mdc_ml_database_v1.py`.
2. Run the database builder, then `python scripts/validate_mdc_ml_database_v1.py`.
3. Build label views and run `python -m unittest tests/test_mdc_ml_label_views_v1.py`.
4. Run the semantic audit before any surrogate training.
5. Train only after the data and label-view checks pass; keep TMM, tolerance, and FDTD roles separated.
