# APCD-inspired spin-selective directional metagrating for Micro-LED circularly polarized emission

## Core Target

The current target is a spin-selective directional metagrating:

```text
LCP_in -> RCP_out, +15 deg
RCP_in -> suppressed in the target output channel
```

The target output channel is the `RCP, +15 deg` diffraction channel under LCP incidence. RCP incidence should be rejected, suppressed, or redistributed into non-target channels.

## Current Priority

The current priority is:

```text
633 nm physics proof-of-concept before returning to 450 nm blue Micro-LED.
```

The project should not immediately optimize the previous 450 nm TiO2 nanofin gradient metasurface route. The immediate focus is to validate the APCD-inspired dimer mechanism at 633 nm, then migrate the verified mechanism toward blue-light-compatible materials and finally to 450 nm Micro-LED operation.

## Basic Unit

The basic unit is one APCD dimer:

```text
one APCD dimer = two birefringent nanopillars
```

The APCD dimer is responsible for polarization selection and conversion:

```text
LCP_in -> RCP_out
RCP_in -> suppressed / rejected from the target output channel
```

## Supercell

The phase-gradient supercell is built from multiple APCD dimers:

```text
K APCD dimers per supercell
total nanopillars = 2K
```

Use `K` to denote the number of APCD dimers per supercell. Do not use `N` as the number of individual nanopillars in the new scheme.

For Stage 0 / Stage 1:

```text
lambda = 633 nm
theta_out = +15 deg
Lambda = lambda / sin(15 deg) ~= 2.45 um
```

## First Comparison

Compare first:

- `K = 6`
- `K = 7`

Interpretation:

| K | Dimer pitch | Phase step | Total nanopillars | Role |
| --- | --- | --- | --- | --- |
| 6 | ~408 nm | 60 deg | 12 | Lower inter-dimer coupling risk |
| 7 | ~349 nm | ~51.4 deg | 14 | Close to APCD paper's ~340 nm unit period |

Keep `K = 8` only as a later comparison:

| K | Dimer pitch | Phase step | Total nanopillars | Role |
| --- | --- | --- | --- | --- |
| 8 | ~306 nm | 45 deg | 16 | Later comparison only; higher inter-dimer coupling risk |

The reason for `K = 7` is not that odd numbers have special physics. `K = 7` is only a geometry-matching option because `633 nm` and `+15 deg` give `Lambda ~= 2.45 um`, and `Lambda / 7 ~= 349 nm`, close to APCD's reported period scale.

## Machine Learning Status

Machine learning is paused for the current stage.

Do not train DenseNet yet.

Do not train cVAE yet.

DenseNet is not the inverse design itself. DenseNet may later be used as a forward surrogate:

```text
full dimer-supercell mask -> polarization-resolved diffraction matrix S_m^{q <- p}
```

Later inverse design means:

```text
DenseNet forward prediction
+ BO / NSGA-II / active learning search
+ RCWA / FDTD validation
```

cVAE is optional later, not a current priority. It may be introduced only after enough labeled data are accumulated, as a candidate-structure generator:

```text
target response -> possible dimer-supercell candidates
```

Candidate structures still need DenseNet filtering and RCWA / FDTD validation.
