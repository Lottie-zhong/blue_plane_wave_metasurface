# APCD K-Dimer Metagrating Phase 2 Design Plan

## 1. Phase 1 Completed State

Phase 1 has completed the APCD Fig.2-inspired alpha-pass single-dimer Gate 1 validation.

Evidence files:

- Gate 1 report: `reports/apcd_fig2_alpha_pass_gate1_report.md`
- alpha-pass config: `configs/apcd_fig2_elliptical_633nm_alpha_pass.yaml`

Key metrics:

| Metric | Value |
|---|---:|
| T_alpha | 0.9711541351322045 |
| T_beta | 0.0401994772579764 |
| PD | 0.9205036166065964 |
| conversion_to_leakage_ratio | 24.158377206667513 |

Conclusion: the 633 nm c-Si/Al2O3 single APCD dimer periodic unit-cell baseline passed Gate 1.

## 2. Phase 2 Goal

Phase 2 should design an APCD-inspired spin-selective directional metagrating.

The design unit is the APCD dimer, not an isolated nanopillar:

- one APCD dimer is one functional meta-molecule
- one dimer contains two birefringent nanopillars
- K is the number of dimers in one supercell
- total nanopillars per supercell = 2K
- K=6 means 6 dimers and 12 nanopillars
- K=7 means 7 dimers and 14 nanopillars

Target function:

- alpha input is allowed and transmitted/converted
- alpha input is directed mainly into the +15 deg diffraction order
- beta input is suppressed, especially in the +15 deg target output order

## 3. Geometry Scale

Working wavelength:

```text
lambda = 633 nm
```

Target deflection angle:

```text
theta = +15 deg
```

First-order grating-period estimate:

```text
Lambda = lambda / sin(15 deg) ~= 2.45 um
```

Estimated dimer pitch:

| K | Supercell period | Dimer pitch | Pillars per supercell | Comment |
|---:|---:|---:|---:|---|
| 6 | ~2.45 um | ~408 nm | 12 | wider spacing, potentially weaker dimer-to-dimer coupling, coarser phase sampling |
| 7 | ~2.45 um | ~349 nm | 14 | closer to the APCD Fig.2 340 nm period, finer phase sampling |

K=7 is geometrically closer to the validated 340 nm APCD unit-cell period. K=6 gives more spacing margin but samples the supercell phase profile more coarsely. The immediate Phase 2 comparison should focus on K=6 and K=7. K=8 is not the current main line.

## 4. Relation to the Phase 1 Alpha-Pass Dimer

Phase 2 must inherit the alpha-pass switching geometry validated in Phase 1.

Use this dimer as the base meta-molecule:

| Pillar | Length | Width | Fractional position | Rotation |
|---|---:|---:|---:|---:|
| pillar 1 | 130 nm | 70 nm | (0.75, 0.75) | 67.5 deg |
| pillar 2 | 85 nm | 150 nm | (0.25, 0.25) | 112.5 deg |

This is the current-convention alpha-pass geometry. Do not revert to the original Fig.2 geometry, which was beta-selective in the current coordinate and handedness convention.

## 5. Minimal Code Plan

Step A: K=6/K=7 supercell geometry builder.

- Build a supercell containing K APCD dimers.
- Keep the dimer as the functional unit.
- Support dry-run or setup-only export first.
- Do not run a real solver in the first implementation pass.

Step B: far-field / diffraction-order extraction.

At minimum, the later real-run extraction should report:

- `eta_alpha_to_plus1`
- `eta_alpha_to_zero`
- `eta_alpha_to_minus1`
- `eta_beta_to_plus1`
- `target_order_ER_dB`
- `spin_selective_directionality_ratio`

Step C: real K comparison.

- Run one K=6 case.
- Run one K=7 case.
- Compare +15 deg target-order efficiency and beta leakage.
- Use this comparison before considering any local geometry adjustment.

## 6. Phase 2 Risk Points

- A single-dimer alpha-pass result does not automatically guarantee high +15 deg metagrating efficiency.
- Changing dimer pitch inside a supercell can change coupling and the effective response.
- K=7 is close to the APCD 340 nm period, but the discrete phase gradient and coupling still need verification.
- K=6 has a larger dimer pitch, but its phase sampling is coarser.
- Beta suppression must be evaluated in the target diffraction order, not only by total transmission.
- This phase must not be described as a Micro-LED result.
- This phase must not be described as a 450 nm or TiO2 result.

## 7. Explicit Non-Goals

Do not do the following in this stage:

- do not modify the Phase 1 main workflow
- do not rewrite `src/metasurface/apcd_dimer.py`
- do not switch to TiO2 or 450 nm scaling
- do not train DenseNet, cVAE, or active-learning models
- do not run a large geometry sweep
- do not work on Micro-LED integration
- do not treat K as the number of individual nanopillars
- do not directly reuse the PB 8-atom scheme
- do not build the metagrating from the beta-selective original Fig.2 geometry

## 8. Recommended Execution Order

1. Implement a geometry-builder dry run.
2. Export setup-only `.fsp` files for GUI inspection.
3. Implement diffraction/far-field extraction.
4. Run one K=6 case.
5. Run one K=7 case.
6. Compare K=6 vs K=7 target-order efficiency and beta leakage.
7. Only if necessary, make a small local geometry adjustment.

## 9. Current Phase 2 Entry Criterion

The entry criterion for Phase 2 is satisfied because the alpha-pass single-dimer baseline has:

```text
T_alpha = 0.9711541351322045
T_beta = 0.0401994772579764
conversion_to_leakage_ratio = 24.158377206667513
```

The next work item should be a setup-only K=6/K=7 geometry builder, not a solver run, sweep, material change, or ML task.
