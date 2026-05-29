from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_phase_states import (
    build_k6_phase_targets,
    write_phase_state_dry_run_outputs,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Define APCD K=6 phase-state library schema.")
    parser.add_argument("--dry-run", action="store_true", help="Write schema and criteria without Lumerical.")
    parser.add_argument(
        "--output-dir",
        default="outputs/apcd_k6_metagrating_633nm",
        help="Output directory for K=6 phase-state schema files.",
    )
    return parser.parse_args()


def _format_targets(values: list[float]) -> str:
    return ", ".join(str(int(value)) if float(value).is_integer() else str(value) for value in values)


def main() -> int:
    args = parse_args()
    if not args.dry_run:
        raise SystemExit("This scaffold only supports --dry-run. It does not run FDTD or export .fsp files.")

    output_dir = REPO_ROOT / args.output_dir
    schema_path, criteria_path, rows = write_phase_state_dry_run_outputs(output_dir)
    plus_targets = build_k6_phase_targets("plus")
    minus_targets = build_k6_phase_targets("minus")

    print("K=6")
    print(f"plus_ramp_phase_targets_deg={_format_targets(plus_targets)}")
    print(f"minus_ramp_phase_targets_deg={_format_targets(minus_targets)}")
    print("phase_convention=minus180_180")
    print(f"schema_rows={len(rows)}")
    print(f"schema={schema_path}")
    print(f"criteria={criteria_path}")
    print("status=dry_run_schema_only_no_fdtd_no_fsp_not_steering_result")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
