# blue_plane_wave_metasurface

Code and planning workspace for an APCD-inspired spin-selective directional metagrating project.

## Current Direction

The current frozen direction is:

```text
APCD-inspired dimer-supercell metagrating
633 nm physics validation first
LCP_in -> RCP_out, +15 deg
RCP_in -> suppressed / redistributed away from the target output channel
```

The basic unit is no longer an individual nanofin meta-atom. The basic unit is an APCD-inspired dimer meta-molecule:

```text
1 APCD dimer = 2 birefringent nanopillars
K = number of APCD dimers per supercell
total nanopillars per supercell = 2K
```

For Stage 0 / Stage 1:

```text
lambda = 633 nm
theta_out = +15 deg
Lambda = lambda / sin(15 deg) ~= 2.45 um
```

Compare first:

- `K = 6`: dimer pitch ~= 408 nm, phase step = 60 deg, 12 nanopillars total.
- `K = 7`: dimer pitch ~= 349 nm, phase step ~= 51.4 deg, 14 nanopillars total.

Keep `K = 8` only for later comparison because inter-dimer coupling risk is higher.

## Material Route

Stage 1A:

```text
c-Si / Al2O3 at 633 nm
Purpose: reproduce APCD-like dimer behavior.
```

Stage 1B:

```text
TiO2 / SiO2 or TiO2 / sapphire at 633 nm
Purpose: test migration toward blue-light-compatible materials.
```

Stage 2:

```text
TiO2 or GaN at 450 nm
Purpose: scale verified dimer-metagrating mechanism to blue Micro-LED wavelengths.
```

Stage 3:

```text
Micro-LED migration
unpolarized MQW emission -> high-purity RCP output in the +15 deg target direction.
```

## Current Two-Week Rule

Do physics validation only:

1. Single APCD dimer at 633 nm.
2. `K = 6` and `K = 7` dimer supercells at 633 nm.
3. TiO2 material feasibility at 633 nm.

Do not do:

- large dataset generation;
- DenseNet training;
- cVAE training;
- 3000-5000 structure sweep.

## Legacy Baseline

The earlier 450 nm TiO2 PB nanofin metagrating scripts and configs remain in the repository as automation and extraction baselines:

- Lumerical run orchestration;
- grating order extraction;
- RCP/LCP handedness spectrum;
- spin extinction ratio summaries.

They are no longer the main research direction.

## Runtime Notes

Local Windows is used for code edits, dry-runs, and tests. The Windows server is reserved for `lumapi` / Lumerical runs through `configs/runtime.yaml`, which is intentionally ignored by Git.

Outputs remain on the server under:

```text
D:\project\blue_plane_wave_metasurface\outputs
```

Do not commit or sync simulation outputs, `.fsp`, `.csv`, large data files, or model weights to GitHub.
