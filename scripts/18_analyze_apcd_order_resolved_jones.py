from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_diffraction import write_order_resolved_jones_dry_run_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare APCD order-resolved Jones analysis schema.")
    parser.add_argument("--K", type=int, choices=[6, 7], help="Number of APCD dimers.")
    parser.add_argument("--all", action="store_true", help="Prepare both K=6 and K=7 schemas.")
    parser.add_argument("--dry-run", action="store_true", help="Write schema and plan without Lumerical.")
    parser.add_argument("--output-root", default="outputs", help="Output root for K-dimer folders.")
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
        raise SystemExit("This scaffold only supports --dry-run.")

    for K in _requested_k_values(args):
        output_dir = REPO_ROOT / args.output_root / f"apcd_k{K}_metagrating_633nm"
        schema_path, plan_path, rows = write_order_resolved_jones_dry_run_outputs(K=K, output_dir=output_dir)
        print(f"K={K}")
        print(f"schema_rows={len(rows)}")
        print(f"schema={schema_path}")
        print(f"plan={plan_path}")
        print("status=dry_run_jones_schema_only")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
