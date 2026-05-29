# APCD Fig.2 Alpha-Pass Gate 1 Report

## Scope

This report records the Phase 1 APCD Fig.2-inspired single-dimer result at 633 nm. The model is a periodic c-Si/Al2O3 APCD unit cell with one dimerized metamolecule under normal-incidence plane-wave illumination.

This is not a K=6/K=7 metagrating result, not a TiO2/450 nm scaling result, and not a Micro-LED integration result.

## Reference Model

The reproduction target follows the APCD paper Fig.2 logic: two birefringent nanopillars form a dimerized metamolecule, and the coherent far-field sum can produce an allowed polarization channel and a prevented channel.

For the Fig.2 elliptical basis, the workflow evaluates Jones-matrix response in the APCD paper basis rather than judging the structure only by circular R/L spin metrics.

Target basis:

- wavelength: 633 nm
- material: c-Si nanopillars on Al2O3
- period: 340 nm x 340 nm
- height: 300 nm
- target polarization type: elliptical
- psi: 112.5 deg
- chi: 22.5 deg
- output basis: alpha_beta

## Extraction Workflow

The real-run workflow uses separate x- and y-polarized normal-incidence simulations to build the linear Jones matrix:

```text
J_xy = [[t_xx, t_xy],
        [t_yx, t_yy]]
```

The Lumerical lifecycle is:

1. build setup session
2. save `pre_run_X.fsp` / `pre_run_Y.fsp`
3. close setup session
4. open a new run session
5. load the corresponding pre-run `.fsp`
6. run FDTD
7. do not call `switchtolayout` after `fdtd.run()`
8. extract `T_fields.Ex` / `T_fields.Ey`
9. extract power monitor `T`
10. normalize each Jones column by the corresponding power-monitor transmission
11. transform `J_xy` into the alpha/beta paper basis

The output basis is:

- rows: alpha*, beta* output channels
- columns: alpha, beta input channels

The reported APCD metrics are:

- `t_alpha_star_from_alpha`
- `t_beta_star_from_alpha`
- `t_alpha_star_from_beta`
- `t_beta_star_from_beta`
- `T_alpha`
- `T_beta`
- `PD = (T_alpha - T_beta) / (T_alpha + T_beta)`

## Geometry Comparison

| Case | Geometry change | T_alpha | T_beta | PD | conversion_to_leakage_ratio | Observation |
|---|---:|---:|---:|---:|---:|---|
| Original Fig.2 geometry | pillar 1: 130 x 70 nm, pillar 2: 150 x 85 nm | 0.01883734663909726 | 0.9831710888479276 | -0.9624008222437316 | 0.019159784958843285 | beta-selective under current coordinate/handedness convention |
| Overall rotation -90 deg | rotations changed to 157.5 deg and 22.5 deg | 0.4961477903784082 | 0.5142693968010983 | -0.01793477649886088 | 0.9647624250336957 | selectivity mostly disappears |
| Swap sites | pillar positions/sites exchanged | 0.02595327595264275 | 0.98134244125009 | -0.9484694007730133 | 0.026446706942130763 | still beta-selective |
| Swap pillar 1 length/width | pillar 1: 70 x 130 nm | 0.5145632936340976 | 0.4892898433686501 | 0.025176441985211545 | 1.051653331063228 | selectivity mostly disappears |
| Swap pillar 2 length/width | pillar 2: 85 x 150 nm | 0.9711541351322045 | 0.0401994772579764 | 0.9205036166065964 | 24.158377206667513 | alpha-pass / beta-suppressed |

## Final Alpha-Pass Geometry

The successful alpha-pass dimer is stored in:

`configs/apcd_fig2_elliptical_633nm_alpha_pass.yaml`

Final geometry:

| Pillar | Fractional position | Center position | Length | Width | Rotation |
|---|---:|---:|---:|---:|---:|
| nanopillar_1 | (0.75, 0.75) | (+85 nm, +85 nm) | 130 nm | 70 nm | 67.5 deg |
| nanopillar_2 | (0.25, 0.25) | (-85 nm, -85 nm) | 85 nm | 150 nm | 112.5 deg |

Geometry validation from the successful run:

- same-cell minimum gap: 81.47428823166298 nm
- periodic-image minimum gap: 81.47428823166297 nm
- nearest pair: nanopillar_2 to nanopillar_1 periodic image (-340, -340) nm
- minimum gap threshold: 5 nm
- validation passed: True

## Final Metrics

Evidence files:

- `outputs/apcd_fig2_elliptical_633nm_alpha_pass/summary.md`
- `outputs/apcd_fig2_elliptical_633nm_alpha_pass/results.csv`

Final alpha-pass metrics:

| Metric | Value |
|---|---:|
| status | ok |
| T_alpha | 0.9711541351322045 |
| T_beta | 0.0401994772579764 |
| PD | 0.9205036166065964 |
| conversion_to_leakage_ratio | 24.158377206667513 |
| total_transmission | 0.5056768061950905 |

The complex APCD-basis coefficients are:

| Coefficient | Value |
|---|---:|
| t_alpha_star_from_alpha | -0.35675399032712+0.9142415295978351j |
| t_beta_star_from_alpha | -0.08074170451927708-0.03903752333094723j |
| t_alpha_star_from_beta | 0.05336970750712795-0.1493822403086981j |
| t_beta_star_from_beta | -0.05716854296714084-0.1084797472063268j |

## Gate 1 Decision

Gate 1 early pass criterion:

```text
target_conversion / opposite_channel_leakage > 6
```

The successful alpha-pass case gives:

```text
0.9711541351322045 / 0.0401994772579764 = 24.158377206667513
```

Gate 1 result: pass.

## Interpretation

The original Fig.2 geometry is beta-selective in the current code convention. Overall rotation and site swapping do not recover alpha-pass behavior. Swapping only pillar 2 length/width produces the desired allowed/prevented behavior: alpha input is transmitted into alpha* with high efficiency, while beta input is strongly suppressed.

This supports using the alpha-pass dimer as the basic meta-molecule for the next K=6/K=7 metagrating stage. The present evidence is limited to a 633 nm c-Si/Al2O3 periodic unit-cell plane-wave baseline.

## Next Step

Use `configs/apcd_fig2_elliptical_633nm_alpha_pass.yaml` as the Phase 1 single-dimer baseline. The next design step should build K=6/K=7 metagrating candidates from this alpha-pass dimer, after preserving this Gate 1 result as the fixed reference.

Do not treat this report as evidence for TiO2, 450 nm scaling, Micro-LED coupling, or machine-learning model performance.
