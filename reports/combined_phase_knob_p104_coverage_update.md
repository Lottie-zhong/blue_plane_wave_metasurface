# 09-P104 coverage update after h420 resonance continuation

Coverage source: outputs/apcd_k6_active_learning/combined_phase_knob_phase_state_coverage_p101.csv.

No P103 candidate opens a new missing bin. Current early-pass bins remain [-180, -120, 120], and remaining missing bins remain [-60, 0, 60].

Best phase movement: cpk_rescont_h420_aniso_reduce5_01 reaches -126.6809 deg with target_conversion 0.9133, leakage 0.1147, and ratio 7.9642. It is early-pass but still nearest -120 and only 10.8214 deg from the h420 anchor.

Best leakage in the batch: cpk_rescont_h425_h420anchor_01 has leakage 0.0983 and ratio 9.2287, but phase is -132.8836 deg.

Decision: stop the planned top-4 h420 continuation. The branch is now a robust -120 early-pass plateau rather than a route to [-60, 0, 60] within these conservative geometry trims. Do not proceed to K=6 phase-ramp or steering claims from these data.
