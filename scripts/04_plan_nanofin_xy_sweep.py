from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.nanofin_sweep import (
    build_xy_sweep_plan_rows,
    load_xy_sweep_config,
    write_xy_case_configs,
    write_xy_sweep_plan,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Plan an x/y rectangular nanofin geometry sweep.")
    parser.add_argument("--config", default="configs/nanofin_xy_sweep.yaml", help="Path to sweep YAML config.")
    parser.add_argument("--output", default=None, help="Optional sweep plan CSV path.")
    parser.add_argument("--write-case-configs", action="store_true", help="Write ignored per-case x/y YAML configs.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_xy_sweep_config(args.config)
    rows = build_xy_sweep_plan_rows(config)
    output_path = Path(args.output) if args.output else config.result_dir / "xy_sweep_plan.csv"
    written_path = write_xy_sweep_plan(rows, output_path)
    if args.write_case_configs:
        write_xy_case_configs(config, rows)
    print(f"cases={len(rows)}")
    print(f"output={written_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
