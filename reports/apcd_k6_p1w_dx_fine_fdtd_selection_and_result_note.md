# APCD K=6 p1w_dx Fine FDTD Selection and Result Note

This note records stage 09-P12: fine candidate selection, top-2 real FDTD, and
result recording for the p1w_dx leakage-controlled neighborhood.

## Scope

This round selected three fine candidates, generated YAML configs only for the
top-2 candidates, and ran real FDTD only for those top-2 candidates:

- `fine_p1w_dx_08`
- `fine_p1w_dx_03`

The backup candidate `fine_p1w_dx_p2w_trim_02` was selected but not run. This
round did not run the 20-row fine pool, did not run `nhood_lhs_leakred_06`, did not train a model,
did not run K=7, did not run a phase-ramp supercell, and does not make a steering claim.

## Why These Candidates

`fine_p1w_dx_08` was selected as the conservative balance point. It uses
`p1_width=57 nm` and `internal_dx=-34 nm`, keeping a stronger negative dx offset
to protect leakage while narrowing p1 enough to test phase reduction.

`fine_p1w_dx_03` was selected as the lower-phase risk point. It uses
`p1_width=56 nm` and `internal_dx=-33 nm`, moving toward lower phase without
going all the way to the known high-leakage `55 / -30` boundary.

`fine_p1w_dx_p2w_trim_02` was kept as a backup p2-width trim candidate and was
not run in this round.

## Result Summary

| candidate | target_conversion | leakage | ratio | PD | total_T | phase_deg | shift_vs_baseline_deg | early pass | inside 90-100 deg |
|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| `fine_p1w_dx_08` | 0.9372 | 0.1285 | 7.2909 | 0.7588 | 0.5328 | 99.1557 | -12.1610 | yes | yes |
| `fine_p1w_dx_03` | 0.9341 | 0.1475 | 6.3336 | 0.7273 | 0.5408 | 98.5502 | -12.7664 | yes | yes |

Both candidates are below the `doe_p1w_dx_01` phase of `100.8199 deg`, both
enter the 90-100 deg region, and both keep `opposite_spin_leakage <= 0.2` and
`conversion_to_leakage_ratio >= 6`.

## Interpretation

This round produced two new usable phase candidates in the p1w_dx fine
neighborhood. The result supports the fine-neighborhood premise: intermediate
`p1_width` and stronger negative `internal_dx` can lower phase into the
90-100 deg region while retaining acceptable leakage and ratio.

This is still not a full K=6 phase-state library. It is one successful local
region within the broader active-learning search.

## Next Step

The next step should record these two rows into the ML-ready dataset, then use
them as anchors for the next candidate choice. A reasonable follow-up is to
either run the backup `fine_p1w_dx_p2w_trim_02` or design a small extension
around `p1_width=56-57 nm` and `internal_dx=-33 to -34 nm`.
