# APCD K=6 Candidate Setup-Only Export Workflow

## Scope

This is 08-P6 for the APCD K=6 dimer phase-state design.

The goal is a single-candidate setup-only `.fsp` export workflow. The default candidate is `baseline`.

This stage does not run FDTD, does not evaluate any real candidate, does not do K=7, does not do a sweep, does not build a phase-ramp supercell, and does not prove `+15 deg` steering.

## Input

Candidate configs are read from:

`configs/apcd_k6_phase_state_candidates/<variant_id>.yaml`

Default:

`configs/apcd_k6_phase_state_candidates/baseline.yaml`

The baseline geometry is:

- pillar 1: `130 x 70 nm`, rotation `67.5 deg`
- pillar 2: `85 x 150 nm`, rotation `112.5 deg`

The original beta-selective pillar 2 geometry `150 x 85 nm` must not be used.

## Command

Dry-run inspection:

```text
python scripts/23_export_apcd_k6_candidate_setup_fsp.py --variant-id baseline --dry-run
```

Setup-only export:

```text
python scripts/23_export_apcd_k6_candidate_setup_fsp.py --variant-id baseline --runtime configs/runtime.yaml --fsp-output outputs/apcd_k6_phase_state_candidates/baseline/baseline_setup.fsp --setup-only
```

The setup-only command should build and save the model, but must not call `fdtd.run()`.

## Output

Recommended `.fsp` output:

`outputs/apcd_k6_phase_state_candidates/<variant_id>/<variant_id>_setup.fsp`

The `.fsp` file is only for GUI inspection and must not enter Git.

The setup should preserve the Phase 1 single-dimer environment:

- wavelength `633 nm`
- material `c-Si / Al2O3`
- period `340 x 340 nm`
- height `300 nm`
- normal incidence
- x/y input capability through the existing single-dimer workflow
- `T` monitor and field monitor
- alpha-pass geometry from the selected candidate config

## Next Step

After GUI inspection passes, the next step can be a baseline X/Y real FDTD evaluation using the existing Jones extraction logic.

That future run is not part of 08-P6.

Future expansion to `p1L`, `p1W`, `p2L`, and `p2W` variants should happen only after the baseline setup-only export is inspected.
