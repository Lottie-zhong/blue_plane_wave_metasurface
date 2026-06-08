# P168 fabrication-aware zero recovery note

## Scope

Stage 09 only. This note updates the zero-bin recovery workflow policy and does not run FDTD, call lumapi, edit `configs/runtime.yaml`, or claim K=6 phase-ramp steering.

## Fabrication Rule

- The h232.49 to h232.48 cliff scan is diagnostic history only.
- Sub-nm height tuning is not manufacturable enough for the main zero-bin recovery route.
- Stop further sub-nm cliff scans as official candidate generation.
- The next official route fixes `height_nm = 232` and recovers leakage using integer-nm geometry changes.

## Next Official Route

Use `aggr_lhs_retention_dy_05` as the anchor, keep Stage 09 APCD selectivity metrics, and generate only integer-nm candidate geometry for server-side FDTD review.

Do not commit raw candidate `results.csv`, raw `summary.md`, `.fsp`, `pre_run` files, `.npy`, or large outputs.
