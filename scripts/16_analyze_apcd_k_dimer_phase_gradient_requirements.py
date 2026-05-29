from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_metagrating import normalized_structure_factor, write_phase_gradient_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze APCD K-dimer phase-gradient requirements.")
    parser.add_argument("--K", type=int, choices=[6, 7], help="Number of APCD dimers in the supercell.")
    parser.add_argument("--all", action="store_true", help="Analyze both K=6 and K=7.")
    parser.add_argument("--output-root", default="outputs", help="Output root containing K-dimer geometry files.")
    return parser.parse_args()


def _requested_k_values(args: argparse.Namespace) -> list[int]:
    if args.all:
        return [6, 7]
    if args.K is not None:
        return [args.K]
    raise ValueError("Specify --K 6, --K 7, or --all")


def main() -> int:
    args = parse_args()
    output_root = REPO_ROOT / args.output_root

    for K in _requested_k_values(args):
        output_dir = output_root / f"apcd_k{K}_metagrating_633nm"
        requirements_csv = output_dir / "phase_gradient_requirements.csv"
        sanity_check_md = output_dir / "phase_gradient_sanity_check.md"
        _, _, rows = write_phase_gradient_outputs(
            geometry_csv=output_dir / "geometry.csv",
            requirements_csv=requirements_csv,
            sanity_check_md=sanity_check_md,
        )

        uniform = [float(row["uniform_phase_rad"]) for row in rows]
        plus = [float(row["plus_ramp_phase_rad"]) for row in rows]
        minus = [float(row["minus_ramp_phase_rad"]) for row in rows]
        print(f"K={K}")
        print(f"phase_step_deg={360 / K}")
        print(f"uniform_A_plus1_abs={abs(normalized_structure_factor(uniform, order_m=1))}")
        print(f"uniform_A_minus1_abs={abs(normalized_structure_factor(uniform, order_m=-1))}")
        print(f"plus_ramp_A_plus1_abs={abs(normalized_structure_factor(plus, order_m=1))}")
        print(f"minus_ramp_A_minus1_abs={abs(normalized_structure_factor(minus, order_m=-1))}")
        print(f"requirements_csv={requirements_csv}")
        print(f"sanity_check={sanity_check_md}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
