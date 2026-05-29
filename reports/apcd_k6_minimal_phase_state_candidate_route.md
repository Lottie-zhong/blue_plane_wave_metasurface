# APCD K=6 Minimal Phase-State Candidate Route

## Scope

This 08-P3 report defines a minimal K=6 phase-state candidate generation route.

No FDTD run was performed. No `.fsp` file was exported. This route is not evaluated and is not a steering result.

This is route only: it does not build a phase-ramp supercell, does not generate a large candidate set, does not do K=7, and does not switch to TiO2/450 nm or ML.

## Current Basis

- Phase 1 alpha-pass dimer Gate 1 passed.
- The 07 order-resolved Jones pipeline has been opened for complex `J_xy` and `alpha/beta -> alpha*/beta*` evaluation.
- 08-P1 phase-state schema and pass/fail criteria have been completed.
- 08-P2 detour mechanism note has been completed.
- There is currently no real phase-state candidate library.

## Why Detour Displacement Is Not Used Directly

- For the simple `order_m=+1` convention, a `60 deg` detour phase requires `407.62069869398687 nm` displacement.
- This is `Lambda/6`, using `Lambda = 2445.724192163921 nm`.
- This equals the K=6 dimer pitch scale.
- Such a large move can reorder dimers rather than act as independent local phase tuning.
- It can also change supercell sampling, nearest-neighbor spacing, and coupling.
- Therefore detour displacement is kept as an analytic/sign-convention reference, not the final K=6 phase-state library.

## Minimal Small-Geometry Variant Route

Baseline alpha-pass dimer:

- pillar 1: length `130 nm`, width `70 nm`, rotation `67.5 deg`
- pillar 2: length `85 nm`, width `150 nm`, rotation `112.5 deg`

Candidate principle:

- Use one-factor-at-a-time length/width perturbations.
- Keep both rotations fixed.
- Do not generate all parameter combinations.
- Do not use the original beta-selective pillar 2 geometry `150 x 85 nm`.
- Future evaluation must use the existing order-resolved Jones pipeline.
- Candidate pass/fail must use `phase_state_library_schema.csv` and `phase_state_pass_fail_criteria.md`.

Candidate count: 13

Variant IDs: `baseline, p1L_m10, p1L_m5, p1L_p5, p1L_p10, p1W_m5, p1W_p5, p2L_m5, p2L_p5, p2W_m10, p2W_m5, p2W_p5, p2W_p10`

The chosen minimal set is baseline plus one-factor changes:

- `pillar_1_length_nm`: baseline +/- 5 nm, +/- 10 nm
- `pillar_1_width_nm`: baseline +/- 5 nm
- `pillar_2_length_nm`: baseline +/- 5 nm
- `pillar_2_width_nm`: baseline +/- 5 nm, +/- 10 nm

## Output CSV

`outputs/apcd_k6_metagrating_633nm/phase_state_candidate_route.csv` records route candidates only.

It deliberately does not include fake `t_alpha_star_from_alpha`, leakage, or phase metrics.

## Next Evidence Needed

- Run no simulation in this step.
- Later, evaluate only a very small selected set through the existing order-resolved Jones pipeline.
- Only after candidates show high `|t_{alpha*<-alpha}|`, low beta leakage, and small target-channel phase error should a K=6 phase-ramp scaffold be considered.
