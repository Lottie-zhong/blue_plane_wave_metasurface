from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_nextgen_redesign import (  # noqa: E402
    ACCUMULATED_DIAGNOSIS_FIELDS,
    NEXTGEN_CANDIDATE_FIELDS,
    NEXTGEN_SELECTION_FIELDS,
    NEXTGEN_VALIDATION_FIELDS,
    build_accumulated_fdtd_diagnosis,
    build_nextgen_candidate_pool,
    read_csv_rows,
    select_nextgen_fdtd_candidates,
    summarize_phase_span,
    validate_nextgen_candidate_pool,
    write_csv_rows,
    write_nextgen_report,
    write_phase_span_bottleneck_analysis,
)


DEFAULT_DATASET_V5 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v5.csv"
DEFAULT_COVERAGE_V5 = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_coverage_v5.csv"
DEFAULT_DIAGNOSIS = REPO_ROOT / "outputs/apcd_k6_active_learning/accumulated_fdtd_diagnosis_v5.csv"
DEFAULT_BOTTLENECK = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_span_bottleneck_analysis_v5.md"
DEFAULT_POOL = REPO_ROOT / "outputs/apcd_k6_active_learning/nextgen_candidate_pool_v6.csv"
DEFAULT_VALIDATION = REPO_ROOT / "outputs/apcd_k6_active_learning/nextgen_candidate_pool_v6_geometry_validation.csv"
DEFAULT_SELECTION = REPO_ROOT / "outputs/apcd_k6_active_learning/nextgen_fdtd_selection_v6.csv"
DEFAULT_REPORT = REPO_ROOT / "reports/apcd_k6_v5_diagnosis_and_nextgen_redesign_plan.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate APCD K=6 v5 accumulated diagnosis and nextgen candidate planning.")
    parser.add_argument("--dry-run", action="store_true", help="Print planned outputs without writing files.")
    parser.add_argument("--dataset-v5", type=Path, default=DEFAULT_DATASET_V5)
    parser.add_argument("--coverage-v5", type=Path, default=DEFAULT_COVERAGE_V5)
    parser.add_argument("--diagnosis-csv", type=Path, default=DEFAULT_DIAGNOSIS)
    parser.add_argument("--bottleneck-md", type=Path, default=DEFAULT_BOTTLENECK)
    parser.add_argument("--pool-csv", type=Path, default=DEFAULT_POOL)
    parser.add_argument("--validation-csv", type=Path, default=DEFAULT_VALIDATION)
    parser.add_argument("--selection-csv", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset_rows = read_csv_rows(args.dataset_v5)
    coverage_rows = read_csv_rows(args.coverage_v5)
    diagnosis_rows = build_accumulated_fdtd_diagnosis(dataset_rows)
    summary = summarize_phase_span(diagnosis_rows)
    candidates = build_nextgen_candidate_pool()
    validation_rows = validate_nextgen_candidate_pool(candidates)
    selected_rows = select_nextgen_fdtd_candidates(candidates, validation_rows)

    print(f"dataset_v5_rows={len(dataset_rows)}")
    print(f"diagnosis_rows={len(diagnosis_rows)}")
    print(f"nextgen_candidate_count={len(candidates)}")
    print(f"geometry_pass_count={sum(str(row['overall_geometry_pass']) == 'True' for row in validation_rows)}")
    print(f"selected_not_run={[row['candidate_id'] for row in selected_rows]}")
    print("status=planning_only_no_fdtd_no_lumapi_no_fsp_no_yaml_no_training_not_steering_result")

    if args.dry_run:
        print(f"would_write={args.diagnosis_csv}")
        print(f"would_write={args.bottleneck_md}")
        print(f"would_write={args.pool_csv}")
        print(f"would_write={args.validation_csv}")
        print(f"would_write={args.selection_csv}")
        print(f"would_write={args.report}")
        return 0

    write_csv_rows(diagnosis_rows, args.diagnosis_csv, ACCUMULATED_DIAGNOSIS_FIELDS)
    write_phase_span_bottleneck_analysis(args.bottleneck_md, summary, coverage_rows)
    write_csv_rows(candidates, args.pool_csv, NEXTGEN_CANDIDATE_FIELDS)
    write_csv_rows(validation_rows, args.validation_csv, NEXTGEN_VALIDATION_FIELDS)
    write_csv_rows(selected_rows, args.selection_csv, NEXTGEN_SELECTION_FIELDS)
    write_nextgen_report(args.report, summary, candidates, validation_rows, selected_rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
