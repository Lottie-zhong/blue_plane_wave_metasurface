# APCD K=6 Phase-Gap FDTD Selection v1 Summary

Scope: 09-P15 geometry validation plus selection only. No FDTD was run. No config YAML was generated. No model was trained. This is not a steering result.

Pool total: 24
Geometry pass: 24
Recommended for FDTD: 24
Minimum same-cell gap nm: 60.81795173109005
Minimum periodic-image gap nm: 85.7154639635098
Selected count: 3

Selected candidates:

- `gap_bridge_03` (`gap_60_90_bridge_from_p1w_dx`): Conservative bridge from p1w_dx usable anchors: keeps p1/p2 close to the low-leakage region while adding modest lhs-like dy displacement.
- `gap_lhs_leakred_06` (`gap_60_90_lhs_leakage_reduced`): Leakage-reduced lhs-like probe: keeps doe_lhs_like_01 as phase-coverage evidence but pulls lengths, widths, and displacement toward lower-risk geometry.
- `gap_p2w_trim_03` (`gap_60_90_p2w_trim`): Backup p2-width trim around the bridge region; selected_not_run for later leakage-risk comparison.

These candidates are selected_not_run and are only inputs for a later small real-FDTD batch.
