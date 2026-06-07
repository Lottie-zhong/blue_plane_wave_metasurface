# 09-P129 Capsule Branch Diagnostic

P126 anchor: `cpk_060_geom_capsule_h420_01`, phase -162.1028 deg, target 0.9097, leakage 0.0241, ratio 37.7278.

Diagnostic observations:

- Height continuation from h420 to h435 moves phase slowly from -162.1 to -148.8 deg while preserving early-pass selectivity.
- The largest phase motion is 13.3 deg at h435, below the >20 deg useful-trend threshold.
- Anisotropy reduce10 also moves phase to about -153.2 deg but ratio drops close to the early-pass threshold.
- Scale98 pulls the phase back toward -180 and is not useful for the 0/60 search.
- No candidate opened [0, 60], and no fail-boundary phase crossing occurred in this batch.

Interpretation: capsule/racetrack cores form a robust high-selectivity covered-bin branch, but the tested height, anisotropy, and common-scale knobs are too phase-stiff for 0/60. Continue only if a genuinely orthogonal core-preserving phase knob is introduced; do not turn this into a pure helper-shape sweep.
