from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_phase_lowering_candidates import (  # noqa: E402
    PHASE_COVERAGE_V4_FIELDS,
    PHASE_LOWERING_CANDIDATE_FIELDS,
    analyze_phase_coverage_v4,
    build_geometry_lookup,
    build_ml_dataset_v4,
    build_phase_lowering_candidate_pool,
    read_csv_fieldnames,
    read_csv_rows,
    write_csv_rows,
    write_dataset_v4_report,
    write_k6_readiness_v4,
    write_phase_gap_analysis_v4,
    write_phase_lowering_pool_summary,
)


DEFAULT_DATASET_V3 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v3.csv"
DEFAULT_P26_RESULTS = REPO_ROOT / "outputs/apcd_k6_active_learning/focused_next_gap_top2_fdtd_results_v3.csv"
DEFAULT_DATASET_V4 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v4.csv"
DEFAULT_DATASET_REPORT = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v4_collection_report.md"
DEFAULT_COVERAGE = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_coverage_v4.csv"
DEFAULT_GAP_ANALYSIS = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_gap_analysis_v4.md"
DEFAULT_READINESS = REPO_ROOT / "outputs/apcd_k6_active_learning/k6_phase_state_readiness_v4.md"
DEFAULT_POOL = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_lowering_candidate_pool_v4.csv"
DEFAULT_POOL_SUMMARY = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_lowering_candidate_pool_v4_summary.md"
GEOMETRY_POOLS = [
    REPO_ROOT / "outputs/apcd_k6_active_learning/focused_next_gap_candidate_pool_v3.csv",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate APCD K=6 phase-lowering dataset/coverage/candidate pool v4.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--dataset-v3", type=Path, default=DEFAULT_DATASET_V3)
    parser.add_argument("--p26-results", type=Path, default=DEFAULT_P26_RESULTS)
    parser.add_argument("--dataset-v4", type=Path, default=DEFAULT_DATASET_V4)
    parser.add_argument("--dataset-report", type=Path, default=DEFAULT_DATASET_REPORT)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--gap-analysis", type=Path, default=DEFAULT_GAP_ANALYSIS)
    parser.add_argument("--readiness", type=Path, default=DEFAULT_READINESS)
    parser.add_argument("--pool", type=Path, default=DEFAULT_POOL)
    parser.add_argument("--pool-summary", type=Path, default=DEFAULT_POOL_SUMMARY)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset_v4, dataset_columns = build_ml_dataset_v4(
        read_csv_rows(args.dataset_v3),
        read_csv_rows(args.p26_results),
        build_geometry_lookup(GEOMETRY_POOLS),
        read_csv_fieldnames(args.dataset_v3),
    )
    coverage = analyze_phase_coverage_v4(dataset_v4)
    candidates = build_phase_lowering_candidate_pool()
    print(f"dataset_v4_rows={len(dataset_v4)}")
    print(f"candidate_count={len(candidates)}")
    print("status=dataset_coverage_pool_planning_only_no_fdtd_no_lumapi_no_fsp_no_training_not_steering_result")
    if not args.dry_run:
        write_csv_rows(dataset_v4, args.dataset_v4, dataset_columns)
        write_dataset_v4_report(args.dataset_report, dataset_v4)
        write_csv_rows(coverage, args.coverage, PHASE_COVERAGE_V4_FIELDS)
        write_phase_gap_analysis_v4(args.gap_analysis, coverage)
        write_k6_readiness_v4(args.readiness, coverage)
        write_csv_rows(candidates, args.pool, PHASE_LOWERING_CANDIDATE_FIELDS)
        write_phase_lowering_pool_summary(args.pool_summary, candidates)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
