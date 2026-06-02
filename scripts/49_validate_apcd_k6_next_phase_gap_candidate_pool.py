from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_next_phase_gap_candidates import (  # noqa: E402
    NEXT_PHASE_GAP_VALIDATION_FIELDS,
    existing_geometry_rows_from_paths,
    read_csv_rows,
    validate_next_phase_gap_candidate_pool,
    write_csv_rows,
    write_next_validation_summary,
)


DEFAULT_POOL = REPO_ROOT / "outputs/apcd_k6_active_learning/next_phase_gap_candidate_pool_v2.csv"
DEFAULT_VALIDATION = REPO_ROOT / "outputs/apcd_k6_active_learning/next_phase_gap_candidate_pool_v2_geometry_validation.csv"
DEFAULT_SUMMARY = REPO_ROOT / "outputs/apcd_k6_active_learning/next_phase_gap_candidate_pool_v2_geometry_validation_summary.md"
EXISTING_GEOMETRY_INPUTS = [
    REPO_ROOT / "outputs/apcd_k6_active_learning/bounded_candidate_pool_v0.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/neighborhood_candidate_pool_v1.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/p1w_dx_fine_candidate_pool_v1.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/phase_gap_candidate_pool_v1.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/aggressive_phase_gap_candidate_pool_v1.csv",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate APCD K=6 next phase-gap candidate pool v2.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--pool", type=Path, default=DEFAULT_POOL)
    parser.add_argument("--validation", type=Path, default=DEFAULT_VALIDATION)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidates = read_csv_rows(args.pool)
    rows = validate_next_phase_gap_candidate_pool(candidates, existing_geometry_rows_from_paths(EXISTING_GEOMETRY_INPUTS))
    pass_count = sum(str(row["overall_geometry_pass"]) == "True" for row in rows)
    print(f"candidate_count={len(rows)}")
    print(f"geometry_pass_count={pass_count}")
    print(f"recommended_for_fdtd_count={sum(str(row['recommended_for_fdtd']) == 'True' for row in rows)}")
    print("status=geometry_validation_only_no_fdtd_no_lumapi_no_fsp_no_training_not_steering_result")
    if not args.dry_run:
        write_csv_rows(rows, args.validation, NEXT_PHASE_GAP_VALIDATION_FIELDS)
        write_next_validation_summary(args.summary, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
