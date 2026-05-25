# blue_plane_wave_metasurface

P0 code scaffold for a 450 nm blue plane-wave TiO2 metasurface thickness sweep.

Local Windows is used for code edits, dry-run, and tests. Windows server is reserved for `lumapi` / Lumerical runs through `configs/runtime.yaml`, which is intentionally ignored by Git.

## P0 dry-run

```powershell
conda activate plane_wave_local
python scripts\01_run_plane_wave_h_sweep.py --config configs\plane_wave_h_sweep.yaml --dry-run
pytest -q
```

