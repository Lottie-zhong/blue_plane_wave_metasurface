# APCD K=6 p1w_dx Fine FDTD Selection v1 Summary

Scope: 09-P12 selection output. Only top-2 are marked to run now. No surrogate prediction is included.

Selected count: 3
Run-now count: 2
Run-now candidate IDs: fine_p1w_dx_08, fine_p1w_dx_03
Backup candidate IDs: fine_p1w_dx_p2w_trim_02
Unique candidate IDs: True
Status values: selected_backup_not_run, selected_for_run

Family distribution:

- `p1w_dx_fine_leakage_control`: 2
- `p1w_dx_p2w_leakage_trim`: 1

Selection reasons:

- `fine_p1w_dx_08`: Conservative balance point: p1_width=57 nm with internal_dx=-34 nm, using stronger dx offset to protect leakage while narrowing p1.
- `fine_p1w_dx_03`: Lower-phase risk point: p1_width=56 nm with internal_dx=-33 nm, testing phase reduction without going to the known 55/-30 high-leakage boundary.
- `fine_p1w_dx_p2w_trim_02`: Backup p2W trim point: p1_width=57 nm and internal_dx=-33 nm with a small p2_width trim to test later leakage recovery.
