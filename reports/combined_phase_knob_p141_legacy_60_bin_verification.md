# P141 Legacy 60-bin verification

This is a schema/coverage correction, not a new FDTD run.

Legacy `results.csv` files do not contain `phase_deg`; phase was recomputed from `t_alpha_star_from_alpha`.

## Verified candidates

- `focus_neg60_geom_04`: phase=83.1339 deg, nearest=60, target=0.892944, leakage=0.081133, ratio=11.005968, early_pass=True, opens_60=True
- `aggr_p1w_leakctrl_04`: phase=81.1374 deg, nearest=60, target=0.871890, leakage=0.099119, ratio=8.796387, early_pass=True, opens_60=True
- `aggr_lhs_retention_dy_05`: phase=72.2413 deg, nearest=60, target=0.857022, leakage=0.102887, ratio=8.329739, early_pass=True, opens_60=True

## Decision

The 60 deg bin is accepted as legacy-verified early-pass coverage.
