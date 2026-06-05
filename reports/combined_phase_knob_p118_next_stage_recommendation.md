# 09-P118 next-stage recommendation

Evidence base: P114-P115 sparse boundary FDTD validation around the alt_htrans04 branch.

Recommendation: stop the alt_htrans04 stronger scale/aniso boundary route for opening 0/60. It is useful for a robust -60 early-pass state, but the boundary map shows phase motion toward 0/60 only when leakage rises or ratio drops below the early-pass limit.

Highest-confidence retained point: cpk_060_boundary_h435_aniso_reduce10_01. It is early-pass at phase -66.3341 deg with target_conversion 0.8589, leakage 0.1384, and ratio 6.2042, but it does not open a remaining missing bin.

Next stage-09 direction: pivot to a different core-preserving resonance anchor or a leakage-suppressed geometry family that does not simply increase scale, strengthen anisotropy reduction, use stronger common rotation, repeat lower-transition routes, or sweep helper shape. The goal remains [0, 60] with target >= 0.5, leakage <= 0.2, and ratio >= 6.

Do not proceed to K=6 phase-ramp supercell, stage 10, steering claims, K7, 450 nm, Micro-LED, ML, or large sweeps from the current evidence.
