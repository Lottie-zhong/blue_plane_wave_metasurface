# APCD K=7 Order-Resolved Jones Analysis Plan

## Current State

- K=6/K=7 setup-only scaffold has been completed.
- Dimer-level structure group organization has been completed.
- Phase 2.3A proved that a uniform scaffold is not equivalent to a +15 deg directional metagrating.
- Phase 2.3B established the diffraction-order extraction scaffold.
- There is still no real metagrating optical result.
- This plan is not an optical result and no FDTD run was performed.
- Current structure remains scaffold only.

## Stage Goal

- Establish a Jones-matrix analysis framework for each diffraction order.
- Support future x/y input runs and combine their complex order fields into `J_xy`.
- Transform `J_xy` into the APCD `alpha/beta -> alpha*/beta*` basis.
- Prepare order-resolved APCD metrics.

## APCD Target Channel

The main metric is not total T and not ordinary grating power. The target channel is:

```text
t_{alpha*<-alpha}^{target order}
```

The suppressed channels are:

- `t_{beta*<-alpha}`
- `t_{alpha*<-beta}`
- `t_{beta*<-beta}`

Basis parameters:

- psi_deg: 112.5
- chi_deg: 22.5

Matrix indexing convention:

- `J_ab[0,0] = t_{alpha*<-alpha}`
- `J_ab[1,0] = t_{beta*<-alpha}`
- `J_ab[0,1] = t_{alpha*<-beta}`
- `J_ab[1,1] = t_{beta*<-beta}`

## Lumerical Extraction Relationship

Future real runs need:

1. x-polarized input run
2. y-polarized input run
3. for each run, `gratingvector`, `gratingpolar`, or an equivalent complex vector extraction per diffraction order
4. construction of `J_xy = [[Ex_x, Ex_y], [Ey_x, Ey_y]]` for each order
5. transformation to alpha/beta input and alpha*/beta* output basis

`grating()` power fraction alone is not enough to construct a Jones matrix.

## Later Route

Step 2.3D: run one minimal K=6 uniform scaffold diagnostic only to verify order sign convention, extraction pipeline, and weak m=+/-1 response expected from a uniform scaffold.

Step 2.4: design a dimer phase-state mechanism such that K dimer variants provide high `|t_{alpha*<-alpha}|`, low beta leakage, and prescribed phase `phi_i = +/-2*pi*i/K`.

## Explicit Non-Goals

- Do not claim +15 deg steering.
- Do not treat the uniform scaffold as the final metagrating.
- Do not use total transmission alone.
- Do not use only `grating()` power as a Jones matrix substitute.
- Do not switch to TiO2 or 450 nm.
- Do not do ML.
- Do not do a large sweep.
