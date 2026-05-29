# APCD K=6 Dimer Metagrating Geometry Dry Run

- status: dry_run_geometry
- K: 6
- dimer_count: 6
- nanopillar_count: 12
- wavelength_nm: 633.0
- target_angle_deg: 15.0
- supercell_period_nm: 2445.724192163921
- dimer_pitch_nm: 407.62069869398687
- K_definition: K is the number of APCD dimers, not the number of individual nanopillars.
- total_nanopillars: 2K

Alpha-pass dimer source geometry:

- nanopillar_1: length_nm=130.0, width_nm=70.0, frac=(0.75, 0.75), rotation_deg=67.5
- nanopillar_2: length_nm=85.0, width_nm=150.0, frac=(0.25, 0.25), rotation_deg=112.5
- pillar_2_switched_length_width: True
- source_config: configs/apcd_fig2_elliptical_633nm_alpha_pass.yaml

Scope note:

- This file is a dry-run geometry definition only.
- This is not an FDTD result.
- This is not an .fsp export.
- This is not a far-field or diffraction-order result.
- No lumapi call is required to generate this file.
