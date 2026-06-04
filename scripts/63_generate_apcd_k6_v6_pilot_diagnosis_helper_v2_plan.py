from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_helper_v2_plan import (  # noqa: E402
    DIAGNOSIS_FIELDS,
    HELPER_V2_POOL_FIELDS,
    HELPER_V2_SELECTION_FIELDS,
    HELPER_V2_VALIDATION_FIELDS,
    build_helper_v2_candidate_pool,
    build_v6_pilot_failure_diagnosis,
    read_csv_rows,
    select_helper_v2_candidates,
    validate_helper_v2_pool,
    write_csv_rows,
    write_diagnosis_summary,
    write_report,
    write_selection_summary,
)


DEFAULT_PILOT_RESULTS = REPO_ROOT / "outputs/apcd_k6_active_learning/nextgen_phase_knob_pilot_fdtd_results_v6.csv"
DEFAULT_HELPER_V1_VALIDATION = REPO_ROOT / "outputs/apcd_k6_active_learning/weak_helper_candidate_pool_v6_geometry_validation.csv"
DEFAULT_DATASET_V6 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v6.csv"
DEFAULT_DIAGNOSIS = REPO_ROOT / "outputs/apcd_k6_active_learning/v6_pilot_failure_diagnosis.csv"
DEFAULT_DIAGNOSIS_SUMMARY = REPO_ROOT / "outputs/apcd_k6_active_learning/v6_pilot_failure_diagnosis_summary.md"
DEFAULT_POOL = REPO_ROOT / "outputs/apcd_k6_active_learning/weak_helper_v2_candidate_pool_v7.csv"
DEFAULT_VALIDATION = REPO_ROOT / "outputs/apcd_k6_active_learning/weak_helper_v2_candidate_pool_v7_geometry_validation.csv"
DEFAULT_SELECTION = REPO_ROOT / "outputs/apcd_k6_active_learning/weak_helper_v2_fdtd_selection_v7.csv"
DEFAULT_SELECTION_SUMMARY = REPO_ROOT / "outputs/apcd_k6_active_learning/weak_helper_v2_fdtd_selection_v7_summary.md"
DEFAULT_REPORT = REPO_ROOT / "reports/apcd_k6_v6_pilot_diagnosis_and_helper_v2_plan.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate APCD K=6 v6 pilot diagnosis and weak-helper v2 redesign plan.")
    parser.add_argument("--dry-run", action="store_true", help="Print counts only; do not write files.")
    parser.add_argument("--pilot-results", type=Path, default=DEFAULT_PILOT_RESULTS)
    parser.add_argument("--helper-v1-validation", type=Path, default=DEFAULT_HELPER_V1_VALIDATION)
    parser.add_argument("--dataset-v6", type=Path, default=DEFAULT_DATASET_V6)
    parser.add_argument("--diagnosis-csv", type=Path, default=DEFAULT_DIAGNOSIS)
    parser.add_argument("--diagnosis-summary", type=Path, default=DEFAULT_DIAGNOSIS_SUMMARY)
    parser.add_argument("--pool-csv", type=Path, default=DEFAULT_POOL)
    parser.add_argument("--validation-csv", type=Path, default=DEFAULT_VALIDATION)
    parser.add_argument("--selection-csv", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--selection-summary", type=Path, default=DEFAULT_SELECTION_SUMMARY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pilot_rows = read_csv_rows(args.pilot_results)
    helper_v1_validation = read_csv_rows(args.helper_v1_validation)
    dataset_rows = read_csv_rows(args.dataset_v6)
    diagnosis = build_v6_pilot_failure_diagnosis(pilot_rows, helper_v1_validation, dataset_rows)
    pool = build_helper_v2_candidate_pool()
    validation = validate_helper_v2_pool(pool)
    selected = select_helper_v2_candidates(pool, validation)

    print(f"v6_pilot_rows={len(pilot_rows)}")
    print(f"helper_v2_pool_count={len(pool)}")
    print(f"helper_v2_geometry_pass_count={sum(str(row['overall_geometry_pass']) == 'True' for row in validation)}")
    print(f"selected_not_run={[row['candidate_id'] for row in selected]}")
    print("status=diagnosis_and_planning_only_no_fdtd_no_lumapi_no_fsp_no_yaml_no_training_not_steering_result")

    if args.dry_run:
        return 0

    write_csv_rows(diagnosis, args.diagnosis_csv, DIAGNOSIS_FIELDS)
    write_diagnosis_summary(args.diagnosis_summary, diagnosis, helper_v1_validation, dataset_rows)
    write_csv_rows(pool, args.pool_csv, HELPER_V2_POOL_FIELDS)
    write_csv_rows(validation, args.validation_csv, HELPER_V2_VALIDATION_FIELDS)
    write_csv_rows(selected, args.selection_csv, HELPER_V2_SELECTION_FIELDS)
    write_selection_summary(args.selection_summary, selected)
    write_report(args.report, diagnosis, pool, validation, selected, dataset_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
