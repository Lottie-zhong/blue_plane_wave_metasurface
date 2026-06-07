# 09-P133 Orthogonal Phase-Knob Diagnostic

P131 added real `notched_rectangle` support through addpoly vertices and selected six true FDTD candidates. Hollow/ring-like internal voids were deferred because current single-pillar configs do not support robust internal holes or boolean air regions.

Diagnostic observations:

- Mixed-shape rectangle/capsule, capsule/rectangle, rectangle/rounded, and capsule/chamfer points all remain nearest covered -120 and fail leakage/ratio.
- `cpk_orth_mixed_rect_round_h430_01` reaches the closest covered -120 phase at -123.9242 deg but leakage is 0.3525 and ratio is 2.5510.
- `cpk_orth_notch_p1_right_h425_01` is the best selective new knob: phase -149.2261 deg, leakage 0.0771, ratio 11.2431, early-pass true, but it remains far from [0, 60].
- Weak scalar co-design with mixed rectangle+capsule does not recover selectivity and behaves similarly to the mixed-core failure boundary.

Interpretation: these orthogonal knobs do not create a 0/60 anchor. Mixed boundaries break APCD selectivity before reaching useful phase states; the mild notch preserves selectivity but stays in the covered -120 basin.
