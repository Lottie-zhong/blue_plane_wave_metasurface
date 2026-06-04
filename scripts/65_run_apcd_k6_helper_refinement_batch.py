from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_helper_refinement import (  # noqa: E402
    HELPER_REFINEMENT_POOL_FIELDS,
    HELPER_REFINEMENT_RESULT_FIELDS,
    HELPER_REFINEMENT_SELECTION_FIELDS,
    HELPER_REFINEMENT_VALIDATION_FIELDS,
    build_dataset_v8,
    build_helper_refinement_candidate_pool,
    read_csv_rows,
    run_helper_refinement_candidates,
    select_helper_refinement_candidates,
    summarize_helper_refinement_results,
    validate_helper_refinement_configs,
    validate_helper_refinement_pool,
    write_csv_rows,
    write_gap_analysis,
    write_helper_refinement_configs,
    write_pool_summary,
    write_readiness,
    write_report,
    write_result_summary,
    write_validation_summary,
)
from metasurface.apcd_phase_lowering_candidates import PHASE_COVERAGE_V4_FIELDS, analyze_phase_coverage_v4  # noqa: E402


DEFAULT_CONFIG_DIR = REPO_ROOT / "configs/apcd_k6_phase_state_candidates"
DEFAULT_RUNTIME = REPO_ROOT / "configs/runtime.yaml"
DEFAULT_DATASET_V7 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v7.csv"
DEFAULT_POOL = REPO_ROOT / "outputs/apcd_k6_active_learning/helper_refinement_candidate_pool_v8.csv"
DEFAULT_POOL_SUMMARY = REPO_ROOT / "outputs/apcd_k6_active_learning/helper_refinement_candidate_pool_v8_summary.md"
DEFAULT_VALIDATION = REPO_ROOT / "outputs/apcd_k6_active_learning/helper_refinement_candidate_pool_v8_geometry_validation.csv"
DEFAULT_VALIDATION_SUMMARY = REPO_ROOT / "outputs/apcd_k6_active_learning/helper_refinement_candidate_pool_v8_geometry_validation_summary.md"
DEFAULT_SELECTION = REPO_ROOT / "outputs/apcd_k6_active_learning/helper_refinement_fdtd_selection_v8.csv"
DEFAULT_RESULTS = REPO_ROOT / "outputs/apcd_k6_active_learning/helper_refinement_fdtd_results_v8.csv"
DEFAULT_RESULT_SUMMARY = REPO_ROOT / "outputs/apcd_k6_active_learning/helper_refinement_fdtd_results_v8_summary.md"
DEFAULT_DATASET_V8 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v8.csv"
DEFAULT_COVERAGE_V8 = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_coverage_v8.csv"
DEFAULT_GAP_V8 = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_gap_analysis_v8.md"
DEFAULT_READINESS_V8 = REPO_ROOT / "outputs/apcd_k6_active_learning/k6_phase_state_readiness_v8.md"
DEFAULT_REPORT = REPO_ROOT / "reports/apcd_k6_helper_refinement_fdtd_v8_note.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare, run, and summarize APCD K=6 helper refinement candidates.")
    parser.add_argument("--prepare", action="store_true", help="Write pool, validation, selection, and selected YAML configs.")
    parser.add_argument("--dry-run", action="store_true", help="Config-load validation only; no FDTD/lumapi/.fsp.")
    parser.add_argument("--run-selected", action="store_true", help="Run real FDTD for selected top-4 helper refinement candidates.")
    parser.add_argument("--summarize", action="store_true", help="Summarize selected results and update dataset/coverage v8.")
    parser.add_argument("--config-dir", type=Path, default=DEFAULT_CONFIG_DIR)
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--dataset-v7", type=Path, default=DEFAULT_DATASET_V7)
    parser.add_argument("--pool-csv", type=Path, default=DEFAULT_POOL)
    parser.add_argument("--pool-summary", type=Path, default=DEFAULT_POOL_SUMMARY)
    parser.add_argument("--validation-csv", type=Path, default=DEFAULT_VALIDATION)
    parser.add_argument("--validation-summary", type=Path, default=DEFAULT_VALIDATION_SUMMARY)
    parser.add_argument("--selection-csv", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--results-csv", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--result-summary", type=Path, default=DEFAULT_RESULT_SUMMARY)
    parser.add_argument("--dataset-v8", type=Path, default=DEFAULT_DATASET_V8)
    parser.add_argument("--coverage-v8", type=Path, default=DEFAULT_COVERAGE_V8)
    parser.add_argument("--gap-analysis-v8", type=Path, default=DEFAULT_GAP_V8)
    parser.add_argument("--readiness-v8", type=Path, default=DEFAULT_READINESS_V8)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--python", default=sys.executable)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pool = build_helper_refinement_candidate_pool()
    validation = validate_helper_refinement_pool(pool)
    selected = select_helper_refinement_candidates(pool, validation)
    selected_ids = [row["candidate_id"] for row in selected]
    selected_candidates = [row for row in pool if row["candidate_id"] in set(selected_ids)]

    print(f"helper_refinement_pool_count={len(pool)}")
    print(f"helper_refinement_geometry_pass_count={sum(str(row['overall_geometry_pass']) == 'True' for row in validation)}")
    print(f"selected_candidate_ids={selected_ids}")

    if args.prepare:
        write_csv_rows(pool, args.pool_csv, HELPER_REFINEMENT_POOL_FIELDS)
        write_pool_summary(args.pool_summary, pool)
        write_csv_rows(validation, args.validation_csv, HELPER_REFINEMENT_VALIDATION_FIELDS)
        write_validation_summary(args.validation_summary, validation)
        write_csv_rows(selected, args.selection_csv, HELPER_REFINEMENT_SELECTION_FIELDS)
        paths = write_helper_refinement_configs(selected_candidates, args.config_dir)
        print(f"configs={[str(path) for path in paths]}")

    if args.dry_run:
        paths = [args.config_dir / f"{row['candidate_id']}.yaml" for row in selected_candidates]
        dry_rows = validate_helper_refinement_configs(paths)
        print(f"dry_run_validation_pass={all(row['validation_pass'] for row in dry_rows)}")
        for row in dry_rows:
            print(f"{row['candidate_id']}: {row['validation_pass']} {row['notes']}")
        print("status=config_load_validation_only_no_fdtd_no_lumapi_no_fsp")

    if args.run_selected:
        run_helper_refinement_candidates(selected_candidates, args.config_dir, args.runtime, args.python, REPO_ROOT)

    if args.summarize:
        result_rows = summarize_helper_refinement_results(selected_candidates, REPO_ROOT)
        write_csv_rows(result_rows, args.results_csv, HELPER_REFINEMENT_RESULT_FIELDS)
        dataset_v7 = read_csv_rows(args.dataset_v7)
        dataset_v8 = build_dataset_v8(dataset_v7, result_rows, selected_candidates)
        write_csv_rows(dataset_v8, args.dataset_v8, list(dataset_v8[0].keys()))
        coverage_v8 = analyze_phase_coverage_v4(dataset_v8)
        write_csv_rows(coverage_v8, args.coverage_v8, PHASE_COVERAGE_V4_FIELDS)
        write_result_summary(args.result_summary, result_rows, dataset_v8, coverage_v8)
        write_gap_analysis(args.gap_analysis_v8, coverage_v8, result_rows)
        write_readiness(args.readiness_v8, coverage_v8)
        write_report(args.report, validation, selected, result_rows, dataset_v8, coverage_v8)
        print(f"results={args.results_csv}")
        print(f"dataset_v8_rows={len(dataset_v8)}")
        print(f"coverage_v8={[(row['phase_bin_deg'], row['coverage_status']) for row in coverage_v8]}")

    if not any((args.prepare, args.dry_run, args.run_selected, args.summarize)):
        print("No action requested.")
    print("status=helper_refinement_top4_only_no_full_pool_no_old_pool_no_k7_no_phase_ramp_no_training_not_steering_result")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
