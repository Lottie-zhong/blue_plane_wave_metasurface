# 09-P107 coverage update after resonance plateau diagnosis

Coverage source: outputs/apcd_k6_active_learning/combined_phase_knob_phase_state_coverage_p104.csv.

No P106 candidate opens a new missing bin. Current early-pass bins remain [-180, -120, 120], and remaining missing bins remain [-60, 0, 60].

Diagnosis: the h420/h430 resonance branch is a -120 plateau under the tested conservative geometry trims. Pushing height to h434 and combining h425 size/anisotropy trims both stay nearest -120 and lose early-pass ratio.

Pivot evidence: cpk_resplateau_alt_htrans04_h420_aniso_reduce5_01 reaches phase -99.5115 deg while staying early-pass with leakage 0.0380 and ratio 23.8942. This is not coverage success, but it is the best new core-preserving resonance anchor candidate for future Stage 09 work.

Decision: mark the h420/h430 branch as a -120 plateau and pivot to a new core-preserving resonance anchor. Do not proceed to K=6 phase-ramp or steering claims from these data.
