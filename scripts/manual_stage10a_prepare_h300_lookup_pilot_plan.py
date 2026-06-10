from pathlib import Path
import sys
import csv

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.nanofin_sweep import (
    load_xy_sweep_config,
    build_xy_sweep_plan_rows,
    write_xy_case_configs,
    write_xy_sweep_plan,
)

cfg_path = ROOT / "configs/stage10a_h300_lookup_pilot.yaml"

sweep_config = load_xy_sweep_config(cfg_path)
rows = build_xy_sweep_plan_rows(sweep_config)

out_plan = sweep_config.result_dir / "xy_sweep_plan.csv"
write_xy_sweep_plan(rows, out_plan)
write_xy_case_configs(sweep_config, rows)

print(f"plan={out_plan}")
print(f"cases={len(rows)}")
print("")

if rows:
    print("headers=" + ",".join(rows[0].keys()))
    print("")
    print("case_id\tlength_nm\twidth_nm\theight_nm\trotation_deg\tx_config\ty_config\tx_summary\ty_summary\tphase_delay_summary")
    for r in rows:
        print(
            f"{r.get('case_id','')}\t"
            f"{r.get('length_nm','')}\t"
            f"{r.get('width_nm','')}\t"
            f"{r.get('height_nm','')}\t"
            f"{r.get('rotation_deg','')}\t"
            f"{r.get('x_config','')}\t"
            f"{r.get('y_config','')}\t"
            f"{r.get('x_summary','')}\t"
            f"{r.get('y_summary','')}\t"
            f"{r.get('phase_delay_summary','')}"
        )
