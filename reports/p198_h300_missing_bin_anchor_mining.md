# P198 h300 missing-bin anchor mining

## Purpose

- Mine existing h300 real FDTD results for missing early bins: -120, -60, 0.
- No new FDTD run.
- Goal: identify phase-hit candidates suitable for leakage/selectivity recovery.

## Top candidates by missing bin

| target_missing_bin | candidate_id | family | phase | phase_error | target | leakage | ratio | early | score |
|---:|---|---|---:|---:|---:|---:|---:|---|---:|
| -120 | `cpk_m60scan_common_m100_01` | other | -100.660805135 | 19.339194865 | 0.500707505 | 0.634988906 | 0.788529533 | False | 3.497882 |
| -60 | `cpk_m60scan_relcomp_m80_diff35_01` | other | -62.940823949 | 2.940823949 | 0.552396445 | 0.597564541 | 0.924413026 | False | 5.090350 |
| -60 | `cpk_m60scan_common_m80_01` | other | -64.361484308 | 4.361484308 | 0.474027919 | 0.673805662 | 0.703508364 | False | 4.114266 |
| -60 | `cpk_m60scan_helper_suppress_m85_40x90_01` | other | -73.479805480 | 13.479805480 | 0.463215213 | 0.574762033 | 0.805925211 | False | 4.108598 |
| -60 | `cpk_m60scan_common_m90_01` | other | -74.121352694 | 14.121352694 | 0.440076873 | 0.633543110 | 0.694628142 | False | 3.564939 |
| -60 | `cpk_m60scan_p2geom_m85_90x145_01` | other | -67.201146469 | 7.201146469 | 0.388346255 | 0.709055507 | 0.547695140 | False | 3.347156 |
| 0 | `next_zero_rot_anchor_03` | zero_family | 20.788972845 | 20.788972845 | 0.512504130 | 0.450075333 | 1.138707440 | False | 4.732987 |
| 0 | `cpk_branch_core_offset_m75_01` | other | -28.272420020 | 28.272420020 | 0.444177679 | 0.766065355 | 0.579816952 | False | 2.181791 |