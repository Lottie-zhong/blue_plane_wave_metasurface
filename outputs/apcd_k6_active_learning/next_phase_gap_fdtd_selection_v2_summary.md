# APCD K=6 Next Phase-Gap FDTD Selection v2 Summary

Scope: selected_not_run planning only. No YAML config was generated. No FDTD was run. This is not a steering result.

Selected count: 4

Selected candidates:

- `next_zero_rot_anchor_03` target `0` family `zero_bin_probe`: 0 deg bin candidate using rotation-assisted hypothesis on a usable 60-90 anchor.
- `next_rot_anchor_04` target `-60` family `rotation_assisted_anchor_probe`: -60 deg bin candidate using global rotation-assisted hypothesis; high-risk but targets a major open gap.
- `next_mixed_bridge_03` target `-120` family `mixed_safe_bridge`: -120 deg mixed bridge candidate with moderate risk, included to avoid an all-high-risk next batch.
- `next_pi_mixed_bridge_03` target `-180` family `pi_bin_probe`: -180 deg mixed bridge candidate testing phase wrapping/turning without a full supercell.

Recommended next action: generate YAML and run only the top-2 selected candidates first; do not run the full pool.
