# APCD K=6 Aggressive Phase-Gap FDTD Selection v1 Summary

Scope: 09-P17 geometry validation plus selection only. No FDTD was run. No config YAML was generated. No model was trained. This is not a steering result.

Pool total: 32
Geometry pass: 32
Recommended for FDTD: 32
Minimum same-cell gap nm: 88.26958309667273
Minimum periodic-image gap nm: 75.72476807342596
Selected count: 3

Selected candidates:

- `aggr_lhs_retention_dy_05` (`lhs_like_retention_high_dy`): Most aggressive selected row: retains short lhs-like p1/p2 geometry and high internal_dy to keep the 60 deg phase-shift ingredients.
- `aggr_p1w_leakctrl_04` (`lhs_like_leakage_control_p1w`): Leakage-control row: keeps high internal_dy but relaxes p1_width and p2_width away from the most aggressive lhs-like geometry.
- `aggr_bridge_lhs_fine_05` (`lhs_to_fine_bridge_aggressive`): Bridge row: interpolates between doe_lhs_like_01 and the low-leakage fine p1w_dx anchors without collapsing back to the 96 deg conservative geometry.

These candidates are selected_not_run. They are only inputs for a later small real-FDTD batch.
