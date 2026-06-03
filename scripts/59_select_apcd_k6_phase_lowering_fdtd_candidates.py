from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_phase_lowering_candidates import (  # noqa: E402
    PHASE_LOWERING_SELECTION_FIELDS,
    analyze_phase_coverage_v4,
    read_csv_rows,
    select_phase_lowering_fdtd_candidates,
    write_csv_rows,
    write_phase_lowering_report,
    write_phase_lowering_selection_summary,
)


DEFAULT_DATASET = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v4.csv"
DEFAULT_POOL = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_lowering_candidate_pool_v4.csv"
DEFAULT_VALIDATION = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_lowering_candidate_pool_v4_geometry_validation.csv"
DEFAULT_SELECTION = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_lowering_fdtd_selection_v4.csv"
DEFAULT_SUMMARY = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_lowering_fdtd_selection_v4_summary.md"
DEFAULT_REPORT = REPO_ROOT / "reports/apcd_k6_phase_lowering_redesign_v4_note.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select APCD K=6 phase-lowering FDTD candidates v4.")
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
    coverage = analyze_phase_coverage_v4(dataset)
    candidates = read_csv_rows(args.pool)
    validation = read_csv_rows(args.validation)
    selected = select_phase_lowering_fdtd_candidates(candidates, validation)
    print(f"selected_count={len(selected)}")
    print(f"selected_candidate_ids={[row['candidate_id'] for row in selected]}")
    print("status=selection_report_only_no_yaml_no_fdtd_no_lumapi_no_fsp_no_training_not_steering_result")
    if not args.dry_run:
        write_csv_rows(selected, args.selection, PHASE_LOWERING_SELECTION_FIELDS)
        write_phase_lowering_selection_summary(args.summary, selected)
        write_phase_lowering_report(args.report, coverage, candidates, validation, selected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
