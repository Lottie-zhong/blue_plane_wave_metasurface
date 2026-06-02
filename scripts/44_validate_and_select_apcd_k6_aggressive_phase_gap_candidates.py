from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_aggressive_phase_gap_candidates import (  # noqa: E402
    AGGRESSIVE_PHASE_GAP_SELECTION_FIELDS,
    AGGRESSIVE_PHASE_GAP_VALIDATION_FIELDS,
    existing_geometry_rows_from_paths,
    read_csv_rows,
    select_aggressive_phase_gap_fdtd_candidates,
    summarize_aggressive_phase_gap_validation,
    validate_aggressive_phase_gap_candidate_pool,
    write_aggressive_phase_gap_selection_summary,
    write_csv_rows,
)


DEFAULT_POOL = REPO_ROOT / "outputs/apcd_k6_active_learning/aggressive_phase_gap_candidate_pool_v1.csv"
DEFAULT_VALIDATION = REPO_ROOT / "outputs/apcd_k6_active_learning/aggressive_phase_gap_candidate_pool_v1_geometry_validation.csv"
DEFAULT_SELECTION = REPO_ROOT / "outputs/apcd_k6_active_learning/aggressive_phase_gap_fdtd_selection_v1.csv"
DEFAULT_SELECTION_SUMMARY = REPO_ROOT / "outputs/apcd_k6_active_learning/aggressive_phase_gap_fdtd_selection_v1_summary.md"
EXISTING_GEOMETRY_INPUTS = [
    REPO_ROOT / "outputs/apcd_k6_active_learning/bounded_candidate_pool_v0.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/neighborhood_candidate_pool_v1.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/p1w_dx_fine_candidate_pool_v1.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/phase_gap_candidate_pool_v1.csv",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate and select APCD K=6 aggressive phase-gap candidates.")
    parser.add_argument("--dry-run", action="store_true", help="Print summary only; do not write files.")
    parser.add_argument("--pool", type=Path, default=DEFAULT_POOL)
    parser.add_argument("--validation", type=Path, default=DEFAULT_VALIDATION)
    parser.add_argument("--selection", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--selection-summary", type=Path, default=DEFAULT_SELECTION_SUMMARY)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidates = read_csv_rows(args.pool)
    validation_rows = validate_aggressive_phase_gap_candidate_pool(
        candidates,
        existing_geometry_rows_from_paths(EXISTING_GEOMETRY_INPUTS),
    )
    selection_rows = select_aggressive_phase_gap_fdtd_candidates(candidates, validation_rows)
    summary = summarize_aggressive_phase_gap_validation(validation_rows)
    print(f"candidate_count={len(candidates)}")
    print(f"geometry_pass_count={summary['geometry_pass_count']}")
    print(f"recommended_for_fdtd_count={summary['recommended_for_fdtd_count']}")
    print(f"selected_count={len(selection_rows)}")
    print(f"selected_ids={[row['candidate_id'] for row in selection_rows]}")
    print("status=geometry_validation_and_selection_only_no_fdtd_no_lumapi_no_fsp_no_training_not_steering_result")
    if not args.dry_run:
        write_csv_rows(validation_rows, args.validation, AGGRESSIVE_PHASE_GAP_VALIDATION_FIELDS)
        write_csv_rows(selection_rows, args.selection, AGGRESSIVE_PHASE_GAP_SELECTION_FIELDS)
        write_aggressive_phase_gap_selection_summary(args.selection_summary, selection_rows, validation_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
