from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_metagrating import (
    export_apcd_metagrating_setup_only_from_runtime_file,
    read_apcd_metagrating_geometry_csv,
    validate_apcd_metagrating_geometry_rows,
    write_apcd_metagrating_gui_checklist,
    write_apcd_metagrating_setup_summary,
)
from metasurface.config import load_apcd_single_dimer_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export setup-only APCD K-dimer metagrating .fsp files.")
    parser.add_argument(
        "--config",
        default="configs/apcd_fig2_elliptical_633nm_alpha_pass.yaml",
        help="Validated alpha-pass APCD single-dimer config.",
    )
    parser.add_argument("--runtime", default="configs/runtime.yaml", help="Local runtime YAML for lumapi.")
    parser.add_argument("--K", type=int, choices=[6, 7], help="Number of APCD dimers in the supercell.")
    parser.add_argument("--all", action="store_true", help="Export both K=6 and K=7 setup-only .fsp files.")
    parser.add_argument("--setup-only", action="store_true", help="Required; save .fsp without running FDTD.")
    parser.add_argument("--output-root", default="outputs", help="Output root containing geometry.csv files.")
    return parser.parse_args()


def _requested_k_values(args: argparse.Namespace) -> list[int]:
    if args.all:
        return [6, 7]
    if args.K is not None:
        return [args.K]
    raise ValueError("Specify --K 6, --K 7, or --all")


def main() -> int:
    args = parse_args()
    if not args.setup_only:
        raise SystemExit("This exporter is setup-only; pass --setup-only.")

    config = load_apcd_single_dimer_config(REPO_ROOT / args.config)
    runtime_path = REPO_ROOT / args.runtime
    output_root = REPO_ROOT / args.output_root

    for K in _requested_k_values(args):
        output_dir = output_root / f"apcd_k{K}_metagrating_633nm"
        geometry_csv = output_dir / "geometry.csv"
        rows = read_apcd_metagrating_geometry_csv(geometry_csv)
        validate_apcd_metagrating_geometry_rows(rows, K)

        fsp_output = output_dir / f"apcd_k{K}_metagrating_633nm_setup.fsp"
        row = export_apcd_metagrating_setup_only_from_runtime_file(
            config=config,
            geometry_csv=geometry_csv,
            runtime_path=runtime_path,
            fsp_output=fsp_output,
        )
        summary_path = write_apcd_metagrating_setup_summary(row, geometry_csv, output_dir / "setup_summary.md")
        checklist_path = write_apcd_metagrating_gui_checklist(row, output_dir / "gui_inspection_checklist.md")

        print(f"K={K}")
        print(f"status={row['status']}")
        print(f"fdtd_run_called={row['fdtd_run_called']}")
        print(f"nanopillars={row['nanopillar_count']}")
        print(f"fsp={fsp_output}")
        print(f"setup_summary={summary_path}")
        print(f"gui_checklist={checklist_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
