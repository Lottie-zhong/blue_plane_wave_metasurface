from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_focused_next_gap_candidates import (  # noqa: E402
    FOCUSED_NEXT_GAP_SELECTION_FIELDS,
    analyze_phase_coverage_v3,
    read_csv_rows,
    select_focused_next_gap_fdtd_candidates,
    write_csv_rows,
    write_focused_redesign_report,
    write_focused_selection_summary,
)


DEFAULT_DATASET = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v3.csv"
DEFAULT_POOL = REPO_ROOT / "outputs/apcd_k6_active_learning/focused_next_gap_candidate_pool_v3.csv"
DEFAULT_VALIDATION = REPO_ROOT / "outputs/apcd_k6_active_learning/focused_next_gap_candidate_pool_v3_geometry_validation.csv"
DEFAULT_SELECTION = REPO_ROOT / "outputs/apcd_k6_active_learning/focused_next_gap_fdtd_selection_v3.csv"
DEFAULT_SUMMARY = REPO_ROOT / "outputs/apcd_k6_active_learning/focused_next_gap_fdtd_selection_v3_summary.md"
DEFAULT_REPORT = REPO_ROOT / "reports/apcd_k6_focused_next_gap_redesign_v3_note.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select APCD K=6 focused next-gap FDTD candidates v3.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--pool", type=Path, default=DEFAULT_POOL)
    parser.add_argument("--validation", type=Path, default=DEFAULT_VALIDATION)
    parser.add_argument("--selection", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset = read_csv_rows(args.dataset)
    coverage = analyze_phase_coverage_v3(dataset)
    candidates = read_csv_rows(args.pool)
    validation = read_csv_rows(args.validation)
    selected = select_focused_next_gap_fdtd_candidates(candidates, validation)
    print(f"selected_count={len(selected)}")
    print(f"selected_candidate_ids={[row['candidate_id'] for row in selected]}")
    print("status=selection_report_only_no_yaml_no_fdtd_no_lumapi_no_fsp_no_training_not_steering_result")
    if not args.dry_run:
        write_csv_rows(selected, args.selection, FOCUSED_NEXT_GAP_SELECTION_FIELDS)
        write_focused_selection_summary(args.summary, selected)
        write_focused_redesign_report(args.report, coverage, candidates, validation, selected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
