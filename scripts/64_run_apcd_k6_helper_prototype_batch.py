from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_helper_prototype import (  # noqa: E402
    HELPER_PROTOTYPE_POOL_FIELDS,
    HELPER_PROTOTYPE_RESULT_FIELDS,
    HELPER_PROTOTYPE_VALIDATION_FIELDS,
    build_dataset_v7,
    build_helper_prototype_candidate_pool,
    read_csv_rows,
    run_helper_prototype_candidates,
    summarize_helper_prototype_results,
    valid_prototype_candidates,
    validate_helper_prototype_configs,
    validate_helper_prototype_pool,
    write_csv_rows,
    write_gap_analysis,
    write_helper_prototype_configs,
    write_readiness,
    write_report,
    write_summary,
)
from metasurface.apcd_phase_lowering_candidates import PHASE_COVERAGE_V4_FIELDS, analyze_phase_coverage_v4  # noqa: E402


DEFAULT_CONFIG_DIR = REPO_ROOT / "configs/apcd_k6_phase_state_candidates"
DEFAULT_RUNTIME = REPO_ROOT / "configs/runtime.yaml"
DEFAULT_DATASET_V6 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v6.csv"
DEFAULT_POOL = REPO_ROOT / "outputs/apcd_k6_active_learning/helper_prototype_candidate_pool_v7.csv"
DEFAULT_VALIDATION = REPO_ROOT / "outputs/apcd_k6_active_learning/helper_prototype_candidate_pool_v7_geometry_validation.csv"
DEFAULT_RESULTS = REPO_ROOT / "outputs/apcd_k6_active_learning/helper_prototype_fdtd_results_v7.csv"
DEFAULT_SUMMARY = REPO_ROOT / "outputs/apcd_k6_active_learning/helper_prototype_fdtd_results_v7_summary.md"
DEFAULT_DATASET_V7 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v7.csv"
DEFAULT_COVERAGE_V7 = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_coverage_v7.csv"
DEFAULT_GAP_V7 = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_gap_analysis_v7.md"
DEFAULT_READINESS_V7 = REPO_ROOT / "outputs/apcd_k6_active_learning/k6_phase_state_readiness_v7.md"
DEFAULT_REPORT = REPO_ROOT / "reports/apcd_k6_helper_prototype_fdtd_v7_note.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare, run, and summarize APCD K=6 helper prototype candidates.")
    parser.add_argument("--prepare", action="store_true", help="Write 4-row candidate pool, validation, and YAML configs for valid candidates.")
    parser.add_argument("--dry-run", action="store_true", help="Config-load validation only; no FDTD/lumapi/.fsp.")
    parser.add_argument("--run-prototypes", action="store_true", help="Run real FDTD for geometry-passing helper prototype candidates.")
    parser.add_argument("--summarize", action="store_true", help="Summarize available results and update dataset/coverage v7.")
    parser.add_argument("--config-dir", type=Path, default=DEFAULT_CONFIG_DIR)
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--dataset-v6", type=Path, default=DEFAULT_DATASET_V6)
    parser.add_argument("--pool-csv", type=Path, default=DEFAULT_POOL)
    parser.add_argument("--validation-csv", type=Path, default=DEFAULT_VALIDATION)
    parser.add_argument("--results-csv", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--summary-md", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--dataset-v7", type=Path, default=DEFAULT_DATASET_V7)
    parser.add_argument("--coverage-v7", type=Path, default=DEFAULT_COVERAGE_V7)
    parser.add_argument("--gap-analysis-v7", type=Path, default=DEFAULT_GAP_V7)
    parser.add_argument("--readiness-v7", type=Path, default=DEFAULT_READINESS_V7)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--python", default=sys.executable)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pool = build_helper_prototype_candidate_pool()
    validation = validate_helper_prototype_pool(pool)
    valid = valid_prototype_candidates(pool, validation)

    print(f"helper_prototype_pool_count={len(pool)}")
    print(f"helper_prototype_geometry_pass_count={sum(str(row['overall_geometry_pass']) == 'True' for row in validation)}")
    print(f"valid_candidate_ids={[row['candidate_id'] for row in valid]}")

    if args.prepare:
        write_csv_rows(pool, args.pool_csv, HELPER_PROTOTYPE_POOL_FIELDS)
        write_csv_rows(validation, args.validation_csv, HELPER_PROTOTYPE_VALIDATION_FIELDS)
        paths = write_helper_prototype_configs(valid, args.config_dir)
        print(f"configs={[str(path) for path in paths]}")

    if args.dry_run:
        paths = [args.config_dir / f"{row['candidate_id']}.yaml" for row in valid]
        dry_rows = validate_helper_prototype_configs(paths)
        print(f"dry_run_validation_pass={all(row['validation_pass'] for row in dry_rows)}")
        for row in dry_rows:
            print(f"{row['candidate_id']}: {row['validation_pass']} {row['notes']}")
        print("status=config_load_validation_only_no_fdtd_no_lumapi_no_fsp")

    if args.run_prototypes:
        run_helper_prototype_candidates(valid, args.config_dir, args.runtime, args.python, REPO_ROOT)

    if args.summarize:
        if args.validation_csv.exists():
            validation_for_summary = read_csv_rows(args.validation_csv)
        else:
            validation_for_summary = validation
        result_rows = summarize_helper_prototype_results(pool, validation_for_summary, REPO_ROOT)
        write_csv_rows(result_rows, args.results_csv, HELPER_PROTOTYPE_RESULT_FIELDS)
        dataset_v6 = read_csv_rows(args.dataset_v6)
        dataset_v7 = build_dataset_v7(dataset_v6, result_rows, pool)
        write_csv_rows(dataset_v7, args.dataset_v7, list(dataset_v7[0].keys()))
        coverage_v7 = analyze_phase_coverage_v4(dataset_v7)
        write_csv_rows(coverage_v7, args.coverage_v7, PHASE_COVERAGE_V4_FIELDS)
        write_summary(args.summary_md, result_rows, validation_for_summary, dataset_v7, coverage_v7)
        write_gap_analysis(args.gap_analysis_v7, coverage_v7, result_rows)
        write_readiness(args.readiness_v7, coverage_v7)
        write_report(args.report, pool, validation_for_summary, result_rows, dataset_v7, coverage_v7)
        print(f"results={args.results_csv}")
        print(f"dataset_v7_rows={len(dataset_v7)}")
        print(f"coverage_v7={[(row['phase_bin_deg'], row['coverage_status']) for row in coverage_v7]}")

    if not any((args.prepare, args.dry_run, args.run_prototypes, args.summarize)):
        print("No action requested.")
    print("status=helper_prototype_only_no_full_helper_v2_pool_no_old_pool_no_k7_no_phase_ramp_no_training_not_steering_result")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
