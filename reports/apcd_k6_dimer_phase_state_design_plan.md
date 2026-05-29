# APCD K=6 Dimer Phase-State Design Plan

## 1. Current Basis

This plan starts Phase 08 for a true APCD-inspired spin-selective directional metagrating. It is a design plan only. It does not run FDTD, export a new `.fsp`, perform a sweep, or claim steering success.

Evidence used:

- Phase 1 Gate 1 report: `reports/apcd_fig2_alpha_pass_gate1_report.md`
- Alpha-pass config: `configs/apcd_fig2_elliptical_633nm_alpha_pass.yaml`
- Phase 2 K-dimer plan: `reports/apcd_k_dimer_metagrating_phase2_design_plan.md`
- K=6 diagnostic extraction note: `reports/k6_diagnostic_gratingvector_jones_extraction_note.md`
- K=6 order-resolved Jones table: `outputs/apcd_k6_metagrating_633nm/diagnostic_uniform_run/order_resolved_jones.csv`

Established basis:

- Phase 1 alpha-pass single dimer Gate 1 passed.
- The validated alpha-pass dimer is:
  - pillar 1: `130 x 70 nm`, rotation `67.5 deg`
  - pillar 2: `85 x 150 nm`, rotation `112.5 deg`
- K=6/K=7 scaffold design has been completed.
- K=6 means 6 dimers and 12 nanopillars.
- K=7 means 7 dimers and 14 nanopillars.
- K=6 uniform diagnostic has been completed.
- `gratingvector` complex extraction has been fixed for the K=6 diagnostic run.
- The order-resolved Jones pipeline is open: X/Y linearly polarized inputs can construct each diffraction order's `J_xy`, then convert into the project `alpha/beta -> alpha*/beta*` basis.

Important limitation:

- The uniform K=6 scaffold has weak `+/-1` target-order response.
- The current uniform result validates extraction and analysis only.
- It is not evidence of successful `+15 deg` steering.

## 2. K=6 Phase-State Target

The true K=6 metagrating needs 6 dimer phase states for the target APCD channel:

```text
t ramp candidates: 0, 60, 120, 180, 240, 300 deg
-t ramp candidates: 0, -60, -120, -180, -240, -300 deg
```

The target channel for each dimer is:

```text
t_{alpha*<-alpha}^{(i)}
```

For each phase state, the dimer should satisfy all of the following:

- high `|t_{alpha*<-alpha}|`
- low beta leakage
- prescribed `arg(t_{alpha*<-alpha})`

The leakage channels that must remain low are:

```text
t_{beta*<-alpha}
t_{alpha*<-beta}
t_{beta*<-beta}
```

The plus/minus phase-ramp sign must be decided only after the order sign convention is checked against the 07 diffraction-order extraction. Do not infer it from total transmission or from `grating()` power alone.

## 3. Optional Phase Knobs

### Small Geometry Variants

Description:

- Perturb pillar length/width around the validated alpha-pass dimer.
- Keep the dimer as the functional unit.
- Use the current alpha-pass convention, especially pillar 2 as `85 x 150 nm`.

Advantages:

- Directly changes the complex local APCD response.
- Can search for phase diversity while monitoring target amplitude and leakage.
- Fits naturally into a dimer-level candidate library.

Risks:

- Geometry changes may weaken the alpha-pass behavior.
- Phase coverage may be incomplete with small perturbations.
- Coupling in the final K=6 supercell may shift the dimer-level response.

Recommended use:

- Use first, but only as a small candidate exploration after the dimer-level evaluation function exists.

### Local Displacement / Detour Phase

Description:

- Move a dimer locally within its K=6 slot to introduce a detour phase.
- The target is to add phase without strongly changing the internal dimer geometry.

Advantages:

- May preserve the validated dimer geometry.
- Can provide a cleaner phase knob if the order mapping is well understood.

Risks:

- Local displacement can modify coupling and near-field environment.
- It may affect supercell periodicity, slot spacing, and order mapping.
- The detour phase sign must be tied to the verified diffraction-order convention.

Recommended use:

- Evaluate after the Jones/order convention is fixed and after defining allowed displacement bounds inside the K=6 scaffold.

### Constrained Rotation

Description:

- Apply limited rotations as a candidate phase knob.

Advantages:

- Rotation may offer a geometric-phase-like control path.
- It can be compact compared with length/width changes.

Risks:

- Global rotation can change the allowed alpha state.
- APCD here is not an ordinary half-wave-plate/PB-phase design.
- Rotating the whole dimer may destroy the current alpha-pass/beta-suppressed condition.

Required guard:

- Global rotation must not be used casually as the phase knob.
- Any constrained rotation must be tested by the same `alpha/beta -> alpha*/beta*` basis metrics, not by visual analogy to PB metasurfaces.

### Hybrid Geometry + Displacement

Description:

- Combine small length/width variants with bounded local displacement.

Advantages:

- Geometry can tune APCD amplitude/leakage.
- Displacement can provide an additional phase correction.
- May reduce how far any single knob needs to move.

Risks:

- More degrees of freedom can hide failures.
- Coupled effects may make interpretation harder.
- It can drift into a sweep if not kept small.

Recommended use:

- Use only after geometry-only and displacement-only responses are understood.
- Keep the candidate count small and evidence-driven.

## 4. Recommended Minimal Route

The minimum verifiable route is:

1. Build a dimer-level phase response analysis.
2. For a given dimer geometry, extract:
   - `|t_{alpha*<-alpha}|`
   - `arg(t_{alpha*<-alpha})`
   - beta leakage
   - `PD`
   - target/leakage ratio
3. Build a small candidate library for 6 target phases:
   - `0, 60, 120, 180, 240, 300 deg`
4. Build the opposite-sign library or map:
   - `0, -60, -120, -180, -240, -300 deg`
5. Select candidate dimers using pass/fail criteria that include amplitude, leakage, and phase error.
6. Only after the candidate library is adequate, assemble a K=6 phase-ramp scaffold.
7. Export setup-only `.fsp` for GUI inspection in a later step.
8. Run diagnostic extraction only after GUI inspection.
9. Compare plus/minus ramp only after order-resolved `J_xy` and `alpha/beta -> alpha*/beta*` outputs are available.

This route keeps Phase 08 tied to order-resolved Jones evidence and avoids claiming steering from a uniform scaffold.

## 5. Inputs And Outputs

Required inputs:

- `configs/apcd_fig2_elliptical_633nm_alpha_pass.yaml`
- `reports/k6_diagnostic_gratingvector_jones_extraction_note.md`
- `outputs/apcd_k6_metagrating_633nm/diagnostic_uniform_run/order_resolved_jones.csv`

Future candidate-library table columns should include:

| Column | Meaning |
|---|---|
| `phase_target_deg` | Desired target-channel phase |
| `geometry_variant_id` | Candidate identifier |
| `pillar_1_length_nm` | Pillar 1 length |
| `pillar_1_width_nm` | Pillar 1 width |
| `pillar_2_length_nm` | Pillar 2 length |
| `pillar_2_width_nm` | Pillar 2 width |
| `t_alpha_star_from_alpha_abs` | Target-channel amplitude |
| `t_alpha_star_from_alpha_phase_deg` | Target-channel phase |
| `target_conversion` | Power-like target-channel metric |
| `beta_leakage` | Suppressed-channel leakage metric |
| `phase_error_deg` | Wrapped phase error versus target |
| `pass_fail` | Candidate decision |

Suggested future target-order metrics after K=6 scaffold assembly:

- `eta_alpha_to_target_order`
- `eta_beta_to_target_order`
- `target_order_ER_dB`
- `eta_alpha_to_zero_order`
- `eta_alpha_to_minus_order`
- `spin_selective_directionality_ratio`

## 6. Explicit Non-Goals

Do not do the following in this Phase 08 planning step:

- Do not do K=7.
- Do not run FDTD.
- Do not export a new `.fsp`.
- Do not perform a large sweep.
- Do not switch to TiO2 or 450 nm.
- Do not start ML, surrogate modeling, DenseNet, Tandem Network, VAE, or inverse design.
- Do not claim `+15 deg` steering has already been achieved.
- Do not judge success from total transmission alone.
- Do not judge success from `grating()` power alone.
- Do not treat `K` as nanopillar count.
- Do not use the original beta-selective pillar 2 geometry `150 x 85 nm`.

## 7. Progress Judgment

Phase 08 can now begin at the planning and dimer-candidate definition level because 07 completed the complex order-resolved Jones extraction pipeline.

However, the project has not yet demonstrated a true spin-selective directional metagrating. The next evidence needed is a small, order-resolved dimer phase-state candidate library that preserves alpha-pass behavior while covering the six K=6 target phases.
