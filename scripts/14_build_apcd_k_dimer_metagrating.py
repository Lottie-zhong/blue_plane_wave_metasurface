from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_metagrating import write_apcd_metagrating_dry_run_outputs
from metasurface.config import load_apcd_single_dimer_config


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build APCD K-dimer metagrating dry-run geometry.")
    parser.add_argument(
        "--config",
        default="configs/apcd_fig2_elliptical_633nm_alpha_pass.yaml",
        help="Validated alpha-pass APCD single-dimer config.",
    )
    parser.add_argument("--K", type=int, choices=[6, 7], help="Number of APCD dimers in the supercell.")
    parser.add_argument("--all", action="store_true", help="Build both K=6 and K=7 dry-run geometries.")
    parser.add_argument("--dry-run", action="store_true", help="Required; writes geometry files without lumapi.")
    parser.add_argument("--target-angle-deg", type=float, default=15.0, help="Target diffraction angle in degrees.")
    parser.add_argument("--output-root", default="outputs", help="Output root for dry-run geometry files.")
    return parser.parse_args()


def _requested_k_values(args: argparse.Namespace) -> list[int]:
    if args.all:
        return [6, 7]
    if args.K is not None:
        return [args.K]
    raise ValueError("Specify --K 6, --K 7, or --all")


def main() -> int:
    args = parse_args()
    if not args.dry_run:
        raise SystemExit("This script currently supports geometry dry-run only; pass --dry-run.")

    config = load_apcd_single_dimer_config(REPO_ROOT / args.config)
    output_root = REPO_ROOT / args.output_root

    for K in _requested_k_values(args):
        output_dir = output_root / f"apcd_k{K}_metagrating_633nm"
        csv_path, summary_path, rows = write_apcd_metagrating_dry_run_outputs(
            config=config,
            K=K,
            output_dir=output_dir,
            target_angle_deg=args.target_angle_deg,
        )
        print(f"K={K}")
        print(f"nanopillars={len(rows)}")
        print(f"dimer_pitch_nm={rows[0]['dimer_pitch_nm']}")
        print(f"supercell_period_nm={rows[0]['supercell_period_nm']}")
        print(f"geometry_csv={csv_path}")
        print(f"geometry_summary={summary_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
