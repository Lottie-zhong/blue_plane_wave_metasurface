# Future Machine-Learning Data Schema

## Scope

This document defines the future data schema for APCD-inspired dimer-supercell metagratings.

Current rule:

```text
Do not train DenseNet.
Do not train cVAE.
Do not generate a large dataset.
```

This is documentation only. It prepares a future schema for forward surrogate modeling and inverse-design loops after physics validation is complete.

## Future Input

The future ML input should represent the full dimer-supercell, not only a small list of scalar parameters.

### Required input

```text
full dimer-supercell mask
```

The mask should encode the complete 2D layout of all APCD dimers in the supercell.

Recommended base channel:

```text
binary geometry mask: solid dielectric / background
```

### Optional input channels

Optional channels may be added if they improve learning stability or generalization:

- signed distance map;
- material / channel map;
- geometry parameter vector.

The geometry parameter vector may include:

- `K`, the number of APCD dimers per supercell;
- supercell period;
- dimer pitch;
- nanopillar lengths and widths;
- nanopillar rotations;
- relative dimer displacement;
- material identifiers;
- wavelength;
- substrate / environment identifier.

## Future Output

The future ML target is the polarization-resolved diffraction matrix:

```text
S_m^{q <- p}
```

where:

- `m` is the diffraction order;
- `p` is the incident polarization state;
- `q` is the output polarization state.

The initial polarization basis should include:

```text
p, q in {L, R}
```

The key diffraction orders should include:

```text
m in {-1, 0, +1}
```

## Required Labels

The dataset should include at least the following labels.

### Target order labels

```text
S_{+1}^{R <- L}
S_{+1}^{R <- R}
S_{+1}^{L <- R}
S_{+1}^{L <- L}
```

### Zero-order labels

All `S_0` circular-polarization channels:

```text
S_0^{R <- L}
S_0^{L <- L}
S_0^{R <- R}
S_0^{L <- R}
```

### Minus-one-order labels

All `S_{-1}` circular-polarization channels:

```text
S_{-1}^{R <- L}
S_{-1}^{L <- L}
S_{-1}^{R <- R}
S_{-1}^{L <- R}
```

### Energy-balance labels

Include these when available:

- total transmission;
- total reflection;
- loss.

### Derived metrics

Include:

```text
DCP_plus15
directionality
spin_ER_dB
```

Definitions:

```text
DCP_plus15 = [I_R(+15 deg) - I_L(+15 deg)] / [I_R(+15 deg) + I_L(+15 deg)]
```

```text
directionality = P(target cone around +15 deg) / P(all transmitted angles)
```

```text
spin_ER_dB = 10 log10((target efficiency + eps) / (target leakage + eps))
```

The project-specific target efficiency is:

```text
target efficiency = S_{+1}^{R <- L}
```

The project-specific target leakage should include the target output channel under wrong-spin input and other same-order leakage terms as needed by the physics question.

## DenseNet Role

DenseNet is a future forward surrogate:

```text
structure -> optical response
```

DenseNet should predict the polarization-resolved diffraction matrix and derived metrics from the full dimer-supercell representation.

DenseNet is not the inverse design itself.

## Future Inverse-Design Loop

The future inverse-design workflow should be:

```text
candidate generation
-> DenseNet prediction
-> BO / NSGA-II selection
-> RCWA / FDTD validation
-> active learning update
```

The role of each step:

- candidate generation proposes APCD dimer-supercell structures;
- DenseNet predicts optical response quickly;
- BO / NSGA-II selects promising structures under multi-objective constraints;
- RCWA / FDTD validates selected structures;
- active learning adds validated labels back into the training set.

## cVAE Role

cVAE is optional later.

It should only be introduced after enough labeled data exist.

Future cVAE role:

```text
target response -> candidate structures
```

The cVAE should generate candidate dimer-supercell structures from a desired response vector.

The generated structures must still be filtered and validated:

```text
cVAE candidate generation
-> DenseNet filtering
-> RCWA / FDTD validation
```

cVAE is not a current priority.

## Current Non-Goals

Do not implement this schema yet.

Do not train DenseNet.

Do not train cVAE.

Do not generate a 3000-5000 structure dataset.

Do not start large-scale active learning until Gate 1, Gate 2, and material feasibility are complete.
