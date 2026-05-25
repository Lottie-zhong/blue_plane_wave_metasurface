from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.config import load_sweep_config
from metasurface.h_sweep import write_h_sweep_summary
from metasurface.lumapi_runner import SweepRunner


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run blue plane-wave TiO2 h-sweep.")
    parser.add_argument("--config", required=True, help="Path to public sweep YAML config.")
    parser.add_argument("--runtime", default="configs/runtime.yaml", help="Path to local runtime YAML.")
    parser.add_argument("--dry-run", action="store_true", help="Generate planned sweep CSV without lumapi.")
    parser.add_argument("--output", default=None, help="Optional output CSV path.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = load_sweep_config(args.config)

    runner = SweepRunner.from_runtime_file(
        config=config,
        runtime_path=args.runtime,
        dry_run=args.dry_run,
    )
    rows = runner.run()

    output_path = Path(args.output) if args.output else config.output.result_dir / "h_sweep_summary.csv"
    written_path = write_h_sweep_summary(rows, output_path)

    print(f"status={'dry_run' if args.dry_run else 'lumerical'}")
    print(f"rows={len(rows)}")
    print(f"output={written_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

