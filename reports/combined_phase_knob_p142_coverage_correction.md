# P142 Coverage correction after legacy 60-bin verification

## Decision

- Accepted 60 deg as an early-pass bin based on verified legacy v5 raw FDTD evidence.
- This is not a new FDTD run.
- Phase was recomputed from the target-channel complex amplitude `t_alpha_star_from_alpha`.

## Updated coverage

- early-pass bins: `[-180, -120, -60, 60, 120]`
- remaining missing bins: `[0]`

## Accepted legacy candidates

- `focus_neg60_geom_04`: phase=83.1339 deg, target=0.892944, leakage=0.081133, ratio=11.005968
- `aggr_p1w_leakctrl_04`: phase=81.1374 deg, target=0.871890, leakage=0.099119, ratio=8.796387
- `aggr_lhs_retention_dy_05`: phase=72.2413 deg, target=0.857022, leakage=0.102887, ratio=8.329739
