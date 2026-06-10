from pathlib import Path
import sys

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

cfg_path = ROOT / "configs/stage10a_h300_hwp_bridge.yaml"
sweep_config = load_xy_sweep_config(cfg_path)
rows = build_xy_sweep_plan_rows(sweep_config)

out_plan = sweep_config.result_dir / "xy_sweep_plan.csv"
write_xy_sweep_plan(rows, out_plan)
write_xy_case_configs(sweep_config, rows)

print(f"plan={out_plan}")
print(f"cases={len(rows)}")
print("headers=" + ",".join(rows[0].keys()))
print("first5:")
for r in rows[:5]:
    print(
        f"{r['case_id']}\tL={r['length_nm']}\tW={r['width_nm']}\t"
        f"x_config={r['x_config']}\ty_config={r['y_config']}"
    )
