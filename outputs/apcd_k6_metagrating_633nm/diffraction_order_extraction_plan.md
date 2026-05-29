# APCD K=6 Diffraction-Order Extraction Plan

## Current State

- K=6/K=7 setup-only scaffold has been generated.
- Dimer-level structure-group organization has been completed.
- Phase 2.3A showed that a uniform scaffold is not equivalent to a +15 deg directional metagrating.
- This file is not an optical result and no FDTD run was performed.
- Current structure remains a scaffold only.

## Stage Goal

- Establish a grating-order extraction schema.
- Prepare for later FDTD or RCWA result analysis.
- Verify the diffraction-order sign convention.
- Do not produce real optical efficiency conclusions in this stage.

## Lumerical Basis

- Ansys Lumerical FDTD grating projection commands can report grating-order direction and intensity for periodic structures.
- `grating()` gives the power fraction in each order relative to transmitted power.
- `transmission()` is needed with `grating()` to get source-normalized order efficiency.
- `gratingn()`, `gratingm()`, `gratingu1()`, and `gratingu2()` identify order indices and direction unit-vector components.
- `gratingvector()` and `gratingpolar()` are needed for later vector, polarization, phase, and order-resolved Jones analysis.
- Do not use `grating()` alone to claim polarization-selective extraction.

## Expected Order Mapping

- wavelength_nm: 633.0
- supercell_period_nm: 2445.724192163921
- target_angle_deg: 15.0
- expected +1 theta_deg: 14.999999999999998
- expected -1 theta_deg: -14.999999999999998

Lumerical order sign depends on +x/-x, monitor normal, and the u1/u2 convention. Plus-ramp or minus-ramp correspondence to GUI/FDTD +15 deg must be verified later by real diffraction-order extraction.

## Output Metrics

```text
eta_order_source_norm = grating_fraction * total_transmission
target_order_ER_dB = 10 log10(eta_alpha_to_target_order / eta_beta_to_target_order)
spin_selective_directionality_ratio = eta_alpha_to_target_order / max(eta_alpha_to_other_orders + eta_beta_to_target_order, epsilon)
```

Final APCD metagrating evaluation must use the order-resolved target channel:

```text
t_{alpha*<-alpha}^{(m)}
```

Future real runs need x/y input-basis simulations, order-resolved Jones matrices, and conversion to input alpha/beta and output alpha*/beta* bases.

Future metrics should include:

- eta_alpha_to_target_order
- eta_beta_to_target_order
- target_order_ER_dB
- eta_alpha_to_zero_order
- eta_alpha_to_minus_order
- spin_selective_directionality_ratio

## Later Real-Run Route

Step 1: run one small K=6 or K=7 uniform scaffold case only to validate extraction and order sign convention. Expected m=+/-1 orders should not be strong because the scaffold has no target-channel phase ramp.

Step 2: design a dimer phase-state mechanism.

Step 3: compare plus-ramp and minus-ramp candidates to identify which convention maps to +15 deg.

## Explicit Non-Goals

- Do not treat the current scaffold as the final metagrating.
- Do not claim +15 deg steering.
- Do not use total transmission alone.
- Do not use only `grating()` to claim polarization-selective extraction.
- Do not switch to TiO2 or 450 nm.
- Do not do ML.
- Do not do a large sweep.
