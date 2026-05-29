# APCD K=6 Phase-State Library Pass/Fail Criteria

## Scope

This file defines the Phase 08 initial engineering schema and pass/fail criteria for a future K=6 dimer-level phase-state candidate library.

No FDTD run was performed.

This is schema only, not a steering result.

There is currently no real phase-state candidate library.

The schema prepares later candidate dimer evaluation; it does not prove a true APCD directional metagrating.

## Phase Convention

The dry-run CSV uses the `[-180, 180)` wrapped convention for `phase_target_deg` and `t_alpha_star_from_alpha_phase_deg`.

The plus ramp before wrapping is:

```text
0, 60, 120, 180, 240, 300 deg
```

With `[-180, 180)` wrapping this is stored as:

```text
0, 60, 120, -180, -120, -60 deg
```

The minus ramp is:

```text
0, -60, -120, -180, -240, -300 deg
```

With `[-180, 180)` wrapping this is stored as:

```text
0, -60, -120, -180, 120, 60 deg
```

Phase error is the absolute shortest wrapped difference in degrees.

## Target Channel

The phase target applies to the APCD target channel:

```text
t_{alpha*<-alpha}
```

It is not an ordinary x/y phase target.

All pass/fail checks must be based on the `alpha/beta -> alpha*/beta*` basis.

Do not judge success from total T alone.

Do not judge success from `grating()` power alone.

The uniform scaffold's 0th-order result cannot be reused as six phase states.

## Initial Engineering Thresholds

These are Phase 08 initial engineering thresholds, not final paper metrics.

| Metric | Early acceptable | Strong candidate |
|---|---:|---:|
| `target_conversion` | `>= 0.5` | `>= 0.7` |
| `beta_to_target_leakage` | `<= 0.1` | `<= 0.1` |
| `beta_total_leakage` | `<= 0.2` | `<= 0.2` |
| `target_to_beta_ratio` | `>= 6` | `>= 6` |
| `phase_error_deg` | `<= 20 deg` | `<= 10 deg` |

Definitions:

```text
target_conversion = |t_{alpha*<-alpha}|^2
beta_to_target_leakage = |t_{alpha*<-beta}|^2
beta_total_leakage = |t_{alpha*<-beta}|^2 + |t_{beta*<-beta}|^2
target_to_beta_ratio = target_conversion / max(beta_to_target_leakage, eps)
```

## Physical Boundaries

- Global rotation may change the allowed alpha state and should not be the default phase knob.
- APCD here must not be treated as an ordinary PB half-wave-plate design.
- The original beta-selective pillar 2 geometry `150 x 85 nm` must not enter the candidate library baseline.
- The baseline remains pillar 1 `130 x 70 nm`, rotation `67.5 deg`; pillar 2 `85 x 150 nm`, rotation `112.5 deg`.
- K means dimer count. K=6 means 6 dimers and 12 nanopillars.
- Do not switch to K=7, TiO2/450 nm, ML, large sweeps, or phase-ramp supercell assembly in this schema step.
