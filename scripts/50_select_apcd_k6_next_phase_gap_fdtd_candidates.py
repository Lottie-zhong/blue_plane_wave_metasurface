from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_next_phase_gap_candidates import (  # noqa: E402
    NEXT_PHASE_GAP_SELECTION_FIELDS,
    read_csv_rows,
    select_next_phase_gap_fdtd_candidates,
    write_csv_rows,
    write_next_selection_summary,
)


DEFAULT_POOL = REPO_ROOT / "outputs/apcd_k6_active_learning/next_phase_gap_candidate_pool_v2.csv"
DEFAULT_VALIDATION = REPO_ROOT / "outputs/apcd_k6_active_learning/next_phase_gap_candidate_pool_v2_geometry_validation.csv"
DEFAULT_SELECTION = REPO_ROOT / "outputs/apcd_k6_active_learning/next_phase_gap_fdtd_selection_v2.csv"
DEFAULT_SUMMARY = REPO_ROOT / "outputs/apcd_k6_active_learning/next_phase_gap_fdtd_selection_v2_summary.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select APCD K=6 next phase-gap FDTD candidates v2.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--pool", type=Path, default=DEFAULT_POOL)
    parser.add_argument("--validation", type=Path, default=DEFAULT_VALIDATION)
    parser.add_argument("--selection", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = select_next_phase_gap_fdtd_candidates(read_csv_rows(args.pool), read_csv_rows(args.validation))
    print(f"selected_count={len(rows)}")
    print(f"selected_candidate_ids={[row['candidate_id'] for row in rows]}")
    print(f"target_bins={[row['target_bin_deg'] for row in rows]}")
    print("status=selection_only_no_yaml_no_fdtd_no_lumapi_no_fsp_no_training_not_steering_result")
    if not args.dry_run:
        write_csv_rows(rows, args.selection, NEXT_PHASE_GAP_SELECTION_FIELDS)
        write_next_selection_summary(args.summary, rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
