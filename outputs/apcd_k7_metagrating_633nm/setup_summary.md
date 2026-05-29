# APCD K=7 Dimer Metagrating Setup-Only Export

- status: setup_only
- K: 7
- nanopillar_count: 14
- supercell_period_nm: 2445.724192163921
- dimer_pitch_nm: 349.3891703091316
- wavelength_nm: 633.0
- target_angle_deg: 15.0
- geometry_source_csv: D:\project\blue_plane_wave_metasurface\outputs\apcd_k7_metagrating_633nm\geometry.csv
- output_fsp_path: D:\project\blue_plane_wave_metasurface\outputs\apcd_k7_metagrating_633nm\apcd_k7_metagrating_633nm_setup.fsp
- fdtd_run_called: False

Alpha-pass switched dimer geometry:

- pillar 1: 130 x 70 nm, rotation 67.5 deg
- pillar 2: 85 x 150 nm, rotation 112.5 deg
- pillar_2_switched_length_width: True

Scope note:

- Current .fsp is setup-only.
- FDTD was not run.
- This is not an FDTD result.
- No far-field or diffraction-order result has been extracted.
- Current structure is only a K-dimer scaffold.
- Future work must inspect or introduce the t_{alpha*<-alpha} phase-gradient design logic.
- Future real runs must evaluate diffraction-order efficiency, not only total T.
