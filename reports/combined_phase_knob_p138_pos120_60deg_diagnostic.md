# 09-P138 Positive-Basin 60deg Diagnostic

P135 selected four +120 early-pass anchors from coverage_p134: `cpk_branch_helper_swap_br_01`, `cpk_rot_release_02`, `cpk_branch_internal_release_01`, and `cpk_period_phase_04`.

Diagnostic observations:

- Height scans from the +120 anchors did not move into the useful 75-105 deg early-pass window; several wrapped toward covered -180.
- Size/aspect compensation either stayed near covered +120, wrapped toward -180, or lost ratio.
- Mode-order scouts preserved selectivity best at `cpk_pos120_period390_h320_01` but still landed near wrapped -180.
- Rot60 notch recovery produced actual 60deg phase hits at 62.9936 and 67.9093 deg, but both remain leakage-limited with ratio near 1.6.

Interpretation: positive-basin dynamic/resonance knobs preserve selectivity but do not reach 60; the 60 phase branch remains accessible but selectivity-limited. Recovery should focus only around the two phase-hit failed anchors, not around +120 height/period continuation.
