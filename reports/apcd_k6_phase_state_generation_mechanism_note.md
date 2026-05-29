# APCD K=6 Phase-State Generation Mechanism Note

## Scope

This is the Phase 08-P2 mechanism note for K=6 dimer phase-state generation.

No FDTD run was performed. No `.fsp` file was exported. This is a mechanism note only, not a steering result.

This note does not create a K=6 phase-ramp supercell, does not generate a large candidate set, does not do K=7, and does not switch to TiO2/450 nm or ML.

## Current Evidence

Inputs:

- `reports/apcd_k6_dimer_phase_state_design_plan.md`
- `reports/k6_diagnostic_gratingvector_jones_extraction_note.md`
- `outputs/apcd_k6_metagrating_633nm/phase_state_library_schema.csv`
- `outputs/apcd_k6_metagrating_633nm/phase_state_pass_fail_criteria.md`
- `outputs/apcd_k6_metagrating_633nm/diagnostic_uniform_run/order_resolved_jones.csv`

Current facts:

- The 07 complex gratingvector extraction and order-resolved Jones pipeline are available.
- The uniform K=6 scaffold has very weak `m = +/-1` target-order response.
- Simply copying six identical alpha-pass dimers is not enough for a directional metagrating.
- The phase target must apply to the APCD target channel `t_{alpha*<-alpha}`, not to ordinary x/y phase.
- Any phase-state candidate must be evaluated with `phase_state_library_schema.csv` and the Phase 08 pass/fail criteria.

## Mechanism Options

### 1. Detour Displacement / Local Displacement

Definition:

- Move the entire dimer group center position.
- Keep the internal pillar length/width and relative dimer geometry unchanged.
- In a simple one-dimensional order convention, use:

```text
phase_deg ~= 360 * order_m * displacement_nm / supercell_period_nm
```

For K=6:

```text
supercell_period_nm = 2445.724192163921
phase_step_deg = 60
displacement_for_60_deg(order_m=+1) = 407.62069869398687 nm
```

Advantages:

- It may introduce a target diffraction-order phase without changing the alpha-pass dimer internals.
- It may be easier to preserve the Phase 1 alpha-pass geometry than changing pillar dimensions.
- It is a good first analytic scaffold for checking sign convention.

Risks:

- The displacement phase is tied to the diffraction-order sign convention.
- The actual plus/minus ramp mapping must be checked against the 07 order-resolved extraction convention.
- Moving dimers by `407.62 nm` is the same scale as the K=6 dimer pitch, so blindly applying this as local displacement may amount to geometry reordering rather than a small phase knob.
- Repositioning dimers can change supercell sampling, nearest-neighbor spacing, and coupling.
- Detour displacement does not automatically change the intrinsic single-dimer `t_{alpha*<-alpha}` phase.

Conclusion:

- Use detour displacement first only as an analytic scaffold and sign-convention note.
- Do not treat the `407.62 nm` step as already feasible.

### 2. Small Geometry Variants

Definition:

- Slightly perturb pillar length/width around the validated alpha-pass dimer:
  - pillar 1: `130 x 70 nm`, rotation `67.5 deg`
  - pillar 2: `85 x 150 nm`, rotation `112.5 deg`

Advantages:

- May tune intrinsic dynamic phase of `t_{alpha*<-alpha}`.
- Can build a true local phase-state library if amplitude and leakage remain acceptable.

Risks:

- Length/width changes can damage alpha-pass behavior.
- Beta suppression can degrade even if the target phase improves.
- It must be evaluated with the existing order-resolved Jones pipeline and `alpha/beta -> alpha*/beta*` basis.
- If done later, it must begin with a very small local candidate set, not a large sweep.

Conclusion:

- Keep as the follow-up route for intrinsic phase library construction.

### 3. Constrained Global Rotation

Definition:

- Rotate the dimer as a whole or rotate both pillars with a constrained rule.

Potential advantage:

- It may introduce a geometric-phase-like response.

Risks:

- APCD is not being treated here as an ordinary PB half-wave-plate design.
- The allowed state alpha is related to the dimer orientation and the `psi/chi` basis.
- Global rotation may change the target alpha/beta basis relationship.
- It may destroy the already validated alpha-pass / beta-suppressed condition.

Conclusion:

- Do not use global rotation as the first-priority default phase knob.

### 4. Hybrid Route

Definition:

- Combine small geometry variation with limited dimer displacement.

Advantages:

- Geometry can tune intrinsic phase and leakage.
- Displacement can provide a smaller phase correction.

Risks:

- More degrees of freedom make failures harder to diagnose.
- It can drift into a large sweep if not tightly bounded.

Conclusion:

- Keep as a later route only. Do not implement it in this step.

## Recommended Minimum Route

Priority A:

- Build only the detour displacement analytic scaffold and sign-convention note.
- Use it to understand the phase-displacement scale for K=6.
- Do not create a phase-ramp supercell yet.

Priority B:

- Preserve small geometry variants as the later intrinsic phase library route.
- Evaluate any future geometry candidate with `t_{alpha*<-alpha}`, beta leakage, phase error, and the Phase 08 pass/fail criteria.

Priority C:

- Do not use global rotation directly as the default phase knob.

Priority D:

- Do not do a large sweep.

Priority E:

- Do not enter K=7.

## Minimal Analytic K=6 Detour Scaffold

Using the simple `order_m=+1` convention:

| phase_target_deg | displacement_nm |
|---:|---:|
| 0 | 0 |
| 60 | 407.62069869398687 |
| 120 | 815.2413973879737 |
| 180 | 1222.8620960819605 |
| 240 | 1630.4827947759475 |
| 300 | 2038.103493469934 |

Using the simple `order_m=+1` convention for the minus ramp:

| phase_target_deg | displacement_nm |
|---:|---:|
| 0 | 0 |
| -60 | -407.62069869398687 |
| -120 | -815.2413973879737 |
| -180 | -1222.8620960819605 |
| -240 | -1630.4827947759475 |
| -300 | -2038.103493469934 |

Warning:

- These numbers are not proposed final coordinates.
- A `60 deg` detour step equals the K=6 dimer pitch scale.
- Directly moving dimers by these values may reorder the scaffold rather than produce a practical local perturbation.
- The sign and order coordinate must be reconciled with the 07 diffraction-order convention before any real design claim.

## Decision

The minimum route for 08-P2 is:

1. Use detour displacement as an analytic scaffold first.
2. Keep small geometry variants as the later intrinsic phase-state library mechanism.
3. Avoid global rotation as the default knob.
4. Continue using `phase_state_library_schema.csv` and the pass/fail criteria for any future candidate.
5. Do not claim `+15 deg` steering until a phase-ramp candidate is run and analyzed through order-resolved Jones metrics.
