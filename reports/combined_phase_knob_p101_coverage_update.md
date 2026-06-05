# 09-P101 coverage update after resonance continuation

Coverage source: outputs/apcd_k6_active_learning/combined_phase_knob_phase_state_coverage_p98.csv.

No P100 candidate opens a new missing bin. Current early-pass bins remain [-180, -120, 120], and remaining missing bins remain [-60, 0, 60].

Useful trend: cpk_rescont_h420_anchor_wh03_01 moved phase by 21.5053 deg from the high-selectivity anchor while preserving early-pass selectivity. This supports continuing height/resonance continuation from h420 within Stage 09, but it is not a coverage success.

Best selectivity: cpk_rescont_aniso_reduce5_anchor_wh03_01 has leakage 0.0114 and ratio 80.5428, but phase shift is only 10.6508 deg.

Decision: stop after the planned top-4 and record h420 as the next local continuation anchor if more Stage 09 budget is assigned. Do not proceed to K=6 phase-ramp or steering claims from these data.
