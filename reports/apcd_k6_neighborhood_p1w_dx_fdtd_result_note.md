# APCD K=6 Neighborhood p1w_dx FDTD Result Note

This note records stage 09-P9: first real FDTD validation of selected
`p1w_dx_neighborhood` candidates.

## Scope

Only two neighborhood candidates were run:

- `nhood_p1w_dx_05`
- `nhood_p1w_dx_02`

This round did not run `nhood_lhs_leakred_06`, did not run the 24-row
neighborhood pool, and did not run any other first-batch or bounded-pool
candidates. No model was trained. No K=7, phase-ramp supercell, TiO2 / 450 nm,
or steering claim is involved.

## Early-Pass Rule

The early-pass rule remains:

- `target_conversion >= 0.5`
- `opposite_spin_leakage <= 0.2`
- `conversion_to_leakage_ratio >= 6`

The baseline phase is `111.31665091018952 deg`. The reference
`doe_p1w_dx_01` phase is `100.8199 deg`.

## Result Summary

| candidate | target_conversion | leakage | ratio | PD | total_T | phase_deg | shift_vs_baseline_deg | early pass |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `nhood_p1w_dx_05` | 0.9463 | 0.0869 | 10.8860 | 0.8317 | 0.5166 | 100.9514 | -10.3653 | yes |
| `nhood_p1w_dx_02` | 0.9289 | 0.2153 | 4.3150 | 0.6237 | 0.5721 | 98.3086 | -13.0080 | no |

## Interpretation

`nhood_p1w_dx_05` is a low-leakage conservative reference. It keeps leakage well
below 0.2 and passes the early filters, but its phase does not continue below
`doe_p1w_dx_01`; it also does not enter the 90-100 degree region.

`nhood_p1w_dx_02` enters the 90-100 degree region and has lower phase than
`doe_p1w_dx_01`, but it fails the leakage and ratio filters. It is useful as a
lower-phase / high-leakage boundary point, not as a usable phase state.

The current p1w_dx trend is therefore clear: narrowing `p1_width` can reduce the
target-channel phase, but the leakage boundary becomes tight. At this point
there is still no new phase state that both passes the early filters and falls
inside the 90-100 degree region.

## Next Step

The next step should either build a finer low-leakage neighborhood around
`p1_width = 55-60 nm` and `internal_dx = -30 to -35 nm`, or decide whether to run
`nhood_lhs_leakred_06` as the conservative lhs-like leakage-reduction test.
