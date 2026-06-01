# APCD K=6 Candidate Config Scaffold Report

## Scope

This is 08-P5 for the APCD K=6 dimer phase-state design.

This stage only generates 13 single-dimer candidate config scaffolds. These configs are intended for a future candidate setup-only export workflow and later X/Y Jones evaluation.

No FDTD run was performed. No `.fsp` file was exported. This is not K=7, not a large sweep, not a phase-ramp supercell, and not evidence of `+15 deg` steering.

## Inputs

The 13 variants come from:

`outputs/apcd_k6_metagrating_633nm/phase_state_candidate_route.csv`

Variant IDs:

- baseline
- p1L_m10
- p1L_m5
- p1L_p5
- p1L_p10
- p1W_m5
- p1W_p5
- p2L_m5
- p2L_p5
- p2W_m10
- p2W_m5
- p2W_p5
- p2W_p10

## Baseline Geometry

The baseline is the current alpha-pass dimer:

- pillar 1: `130 x 70 nm`, rotation `67.5 deg`
- pillar 2: `85 x 150 nm`, rotation `112.5 deg`

The original beta-selective pillar 2 geometry `150 x 85 nm` must not be used as the baseline.

## Outputs

Generated config directory:

`configs/apcd_k6_phase_state_candidates/`

Generated index:

`outputs/apcd_k6_metagrating_633nm/phase_state_candidate_config_index.csv`

Each candidate config preserves:

- wavelength `633 nm`
- material `c-Si / Al2O3`
- period `340 x 340 nm`
- height `300 nm`
- `psi_deg = 112.5`
- `chi_deg = 22.5`
- boundary flags marking no FDTD run, no `.fsp` export, not K=7, not a sweep, not a phase-ramp supercell, and not a steering result

## Boundary

These files are config scaffolds only. They do not contain measured `t_{alpha*<-alpha}`, leakage, phase, pass/fail, or order-resolved Jones results.

The future next step is candidate setup-only export workflow, not a solver run in this step.
