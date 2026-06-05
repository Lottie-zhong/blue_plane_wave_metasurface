# 09-P93 minus60 phase scan plan

Stage: 09-P93 planning only before remote FDTD.

This plan starts a controlled scan for the missing -60 deg bin after the 60 deg recovery branch repeatedly landed in the 60 bin but failed leakage and ratio thresholds. P85 showed that stronger negative common offsets moved phase from 60 toward 0; this plan continues that same branch toward -60 while keeping the scan bounded.

Current early-pass coverage before this plan: [-180, -120, 120].

Remaining missing bins: [-60, 0, 60].

Top selected candidates:

| Rank | Candidate | Family | Purpose |
|---:|---|---|---|
| 1 | cpk_m60scan_common_m80_01 | core_common_rotation_scan | First extension from m75 toward -60. |
| 2 | cpk_m60scan_common_m90_01 | core_common_rotation_scan | Central scan point for locating the -60 branch. |
| 3 | cpk_m60scan_common_m100_01 | core_common_rotation_scan | Upper bounded point before quality collapse risk. |
| 4 | cpk_m60scan_relcomp_m80_diff35_01 | core_relative_angle_compensation | Tests selectivity recovery near m80. |
| 5 | cpk_m60scan_p2geom_m85_90x145_01 | pillar2_mild_geometry_compensation | Tests mild pillar2 compensation at the scan midpoint. |
| 6 | cpk_m60scan_helper_suppress_m85_40x90_01 | weak_leakage_suppression_helper | Tests helper leakage suppression at the scan midpoint. |

Rules held:

- Stage 09 only.
- No K=6 phase-ramp supercell.
- No steering claim.
- No lower-transition/helper-lower repeat.
- No height >= 440 nm.
- No raw FDTD output is included in this plan.
