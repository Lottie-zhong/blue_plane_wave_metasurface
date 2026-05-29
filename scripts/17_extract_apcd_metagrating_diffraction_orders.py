from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_diffraction import write_diffraction_dry_run_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare APCD metagrating diffraction-order extraction schema.")
    parser.add_argument("--K", type=int, choices=[6, 7], required=True, help="Number of APCD dimers.")
    parser.add_argument("--dry-run", action="store_true", help="Write schema and extraction plan without Lumerical.")
    parser.add_argument("--fsp", default=None, help="Future solved .fsp path for real extraction.")
    parser.add_argument("--output-root", default="outputs", help="Output root for K-dimer folders.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.dry_run and args.fsp:
        raise SystemExit("Use either --dry-run or --fsp, not both.")
    if args.fsp:
        fsp_path = REPO_ROOT / args.fsp
        if not fsp_path.exists():
            raise SystemExit(f"FSP file does not exist: {fsp_path}")
        raise SystemExit(
            "Real solved-FDTD extraction is not implemented in this scaffold. "
            "If this is a setup-only .fsp or has no run results, do not fabricate diffraction data."
        )
    if not args.dry_run:
        raise SystemExit("Pass --dry-run for the current scaffold workflow.")

    output_dir = REPO_ROOT / args.output_root / f"apcd_k{args.K}_metagrating_633nm"
    schema_path, plan_path, rows = write_diffraction_dry_run_outputs(K=args.K, output_dir=output_dir)
    plus = next(row for row in rows if int(row["order_n"]) == 1)
    minus = next(row for row in rows if int(row["order_n"]) == -1)

    print(f"K={args.K}")
    print(f"expected_plus1_theta_deg={round(float(plus['expected_theta_deg']), 12)}")
    print(f"expected_minus1_theta_deg={round(float(minus['expected_theta_deg']), 12)}")
    print(f"schema={schema_path}")
    print(f"plan={plan_path}")
    print("status=dry_run_schema_only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
