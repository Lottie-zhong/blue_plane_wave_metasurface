from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_combined_phase_knob_plan import (  # noqa: E402
    COMBINED_POOL_FIELDS,
    COMBINED_SELECTION_FIELDS,
    COMBINED_VALIDATION_FIELDS,
    DIAGNOSIS_FIELDS,
    build_combined_phase_knob_candidate_pool,
    build_helper_plateau_diagnosis,
    read_csv_rows,
    select_combined_phase_knob_candidates,
    validate_combined_candidate_pool,
    write_csv_rows,
    write_diagnosis_summary,
    write_pool_summary,
    write_report,
    write_selection_summary,
    write_validation_summary,
)


DEFAULT_V7_RESULTS = REPO_ROOT / "outputs/apcd_k6_active_learning/helper_prototype_fdtd_results_v7.csv"
DEFAULT_V8_RESULTS = REPO_ROOT / "outputs/apcd_k6_active_learning/helper_refinement_fdtd_results_v8.csv"
DEFAULT_DIAGNOSIS = REPO_ROOT / "outputs/apcd_k6_active_learning/helper_plateau_diagnosis_v8.csv"
DEFAULT_DIAGNOSIS_SUMMARY = REPO_ROOT / "outputs/apcd_k6_active_learning/helper_plateau_diagnosis_v8_summary.md"
DEFAULT_POOL = REPO_ROOT / "outputs/apcd_k6_active_learning/combined_phase_knob_candidate_pool_v9.csv"
DEFAULT_POOL_SUMMARY = REPO_ROOT / "outputs/apcd_k6_active_learning/combined_phase_knob_candidate_pool_v9_summary.md"
DEFAULT_VALIDATION = REPO_ROOT / "outputs/apcd_k6_active_learning/combined_phase_knob_candidate_pool_v9_geometry_validation.csv"
DEFAULT_VALIDATION_SUMMARY = REPO_ROOT / "outputs/apcd_k6_active_learning/combined_phase_knob_candidate_pool_v9_geometry_validation_summary.md"
DEFAULT_SELECTION = REPO_ROOT / "outputs/apcd_k6_active_learning/combined_phase_knob_fdtd_selection_v9.csv"
DEFAULT_SELECTION_SUMMARY = REPO_ROOT / "outputs/apcd_k6_active_learning/combined_phase_knob_fdtd_selection_v9_summary.md"
DEFAULT_REPORT = REPO_ROOT / "reports/apcd_k6_helper_plateau_and_combined_phase_knob_plan.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate APCD K=6 helper plateau diagnosis and combined phase-knob v9 planning.")
    parser.add_argument("--dry-run", action="store_true", help="Print counts only; do not write files.")
    parser.add_argument("--v7-results", type=Path, default=DEFAULT_V7_RESULTS)
    parser.add_argument("--v8-results", type=Path, default=DEFAULT_V8_RESULTS)
    parser.add_argument("--diagnosis-csv", type=Path, default=DEFAULT_DIAGNOSIS)
    parser.add_argument("--diagnosis-summary", type=Path, default=DEFAULT_DIAGNOSIS_SUMMARY)
    parser.add_argument("--pool-csv", type=Path, default=DEFAULT_POOL)
    parser.add_argument("--pool-summary", type=Path, default=DEFAULT_POOL_SUMMARY)
    parser.add_argument("--validation-csv", type=Path, default=DEFAULT_VALIDATION)
    parser.add_argument("--validation-summary", type=Path, default=DEFAULT_VALIDATION_SUMMARY)
    parser.add_argument("--selection-csv", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--selection-summary", type=Path, default=DEFAULT_SELECTION_SUMMARY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    v7_rows = read_csv_rows(args.v7_results)
    v8_rows = read_csv_rows(args.v8_results)
    diagnosis = build_helper_plateau_diagnosis(v7_rows, v8_rows)
    pool = build_combined_phase_knob_candidate_pool()
    validation = validate_combined_candidate_pool(pool)
    selected = select_combined_phase_knob_candidates(pool, validation)

    print(f"helper_plateau_diagnosis_rows={len(diagnosis)}")
    print(f"combined_pool_count={len(pool)}")
    print(f"combined_geometry_pass_count={sum(str(row['overall_geometry_pass']) == 'True' for row in validation)}")
    print(f"selected_not_run={[row['candidate_id'] for row in selected]}")
    print("status=planning_only_no_fdtd_no_lumapi_no_fsp_no_yaml_no_training_not_steering_result")

    if args.dry_run:
        return 0

    write_csv_rows(diagnosis, args.diagnosis_csv, DIAGNOSIS_FIELDS)
    write_diagnosis_summary(args.diagnosis_summary, diagnosis)
    write_csv_rows(pool, args.pool_csv, COMBINED_POOL_FIELDS)
    write_pool_summary(args.pool_summary, pool)
    write_csv_rows(validation, args.validation_csv, COMBINED_VALIDATION_FIELDS)
    write_validation_summary(args.validation_summary, validation)
    write_csv_rows(selected, args.selection_csv, COMBINED_SELECTION_FIELDS)
    write_selection_summary(args.selection_summary, selected)
    write_report(args.report, diagnosis, pool, validation, selected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
