from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_phase_states import write_minimal_candidate_route_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Define APCD K=6 minimal phase-state candidate route.")
    parser.add_argument("--dry-run", action="store_true", help="Write route CSV/report without Lumerical.")
    parser.add_argument(
        "--output-dir",
        default="outputs/apcd_k6_metagrating_633nm",
        help="Output directory for K=6 route CSV.",
    )
    parser.add_argument(
        "--report",
        default="reports/apcd_k6_minimal_phase_state_candidate_route.md",
        help="Report path for the route note.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.dry_run:
        raise SystemExit("This route scaffold only supports --dry-run. It does not run FDTD or export .fsp files.")

    csv_path, report_path, rows = write_minimal_candidate_route_outputs(
        output_dir=REPO_ROOT / args.output_dir,
        report_path=REPO_ROOT / args.report,
    )
    variant_ids = [str(row["variant_id"]) for row in rows]

    print("K=6")
    print(f"candidate_count={len(rows)}")
    print(f"variant_ids={','.join(variant_ids)}")
    print("one_factor_at_a_time=True")
    print(f"csv={csv_path}")
    print(f"report={report_path}")
    print("status=dry_run_route_only_no_fdtd_no_fsp_not_steering_result")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
