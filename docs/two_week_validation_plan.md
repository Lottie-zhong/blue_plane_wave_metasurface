# Two-Week Validation Plan

## Goal

Freeze the current APCD-inspired dimer-supercell metagrating direction and run physics validation only.

Do not perform:

- large dataset generation;
- DenseNet training;
- cVAE training;
- 3000-5000 structure sweep.

The current validation wavelength is:

```text
lambda = 633 nm
```

The target metagrating behavior is:

```text
LCP_in -> RCP_out, +15 deg
RCP_in -> suppressed in the target output channel
```

## Gate 1: Single APCD Dimer Validation

Purpose:

Validate whether one APCD-inspired dimer can act as a polarization-selective meta-molecule.

Basic unit:

```text
one APCD dimer = two birefringent nanopillars
```

Initial material route:

```text
c-Si / Al2O3 at 633 nm
```

Required checks:

- LCP incidence produces strong RCP output in the desired transmitted channel.
- RCP incidence is suppressed or rejected from the corresponding target-like channel.
- Dimer geometry and gap are physically reasonable.
- The polarization conversion is not a numerical artifact.

Decision gate:

Proceed to Gate 2 only if the single dimer shows a credible polarization-selection / conversion contrast.

## Gate 2: K=6/7 Dimer Metagrating Validation

Purpose:

Build a phase-gradient supercell from APCD dimers and test directional spin-selective diffraction.

Target:

```text
lambda = 633 nm
theta_out = +15 deg
Lambda = lambda / sin(15 deg) ~= 2.45 um
```

Compare first:

- `K = 6` dimers per supercell;
- `K = 7` dimers per supercell.

Notation:

```text
K = number of APCD dimers per supercell
total nanopillars = 2K
```

Required metrics:

- `eta_{RCP <- LCP}^{+1}`
- target leakage from RCP incidence
- opposite-spin redistribution channel
- spin extinction ratio
- all-order polarization-resolved diffraction spectrum

Decision gate:

Proceed to Gate 3 if either `K = 6` or `K = 7` produces convincing `LCP_in -> RCP_out, +15 deg` steering while suppressing the same target channel under RCP incidence.

## Gate 3: TiO2 Feasibility at 633 nm

Purpose:

Test whether the APCD-inspired dimer mechanism can migrate toward blue-light-compatible dielectric materials before returning to 450 nm.

Material candidates:

```text
TiO2 / SiO2
TiO2 / sapphire
```

Required checks:

- Dimer-level polarization selectivity is retained or can be recovered by parameter adjustment.
- `K = 6` or `K = 7` metagrating still supports the target `RCP,+15 deg` channel under LCP incidence.
- RCP input remains suppressed in the target output channel.
- The geometry remains plausible for later 450 nm scaling.

Decision gate:

Only after TiO2 feasibility at 633 nm is understood should the project return to 450 nm blue Micro-LED wavelength scaling.

## Two-Week Success Criteria

Minimum success:

- A documented single-dimer validation result at 633 nm.
- A documented `K = 6` or `K = 7` dimer-supercell result at 633 nm.
- A clear decision on whether TiO2 at 633 nm is promising enough for Stage 2 scaling.

Strong success:

- Both `K = 6` and `K = 7` are compared with all-order polarization-resolved diffraction spectra.
- One candidate route is selected for 450 nm scaling.
- DenseNet and cVAE remain paused until physics validation is complete.
