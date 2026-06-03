from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_focused_next_gap_candidates import (  # noqa: E402
    FOCUSED_NEXT_GAP_CANDIDATE_FIELDS,
    PHASE_COVERAGE_V3_FIELDS,
    analyze_phase_coverage_v3,
    build_focused_next_gap_candidate_pool,
    build_geometry_lookup,
    build_ml_dataset_v3,
    read_csv_fieldnames,
    read_csv_rows,
    write_csv_rows,
    write_dataset_v3_report,
    write_focused_pool_summary,
    write_k6_readiness_v3,
    write_phase_gap_analysis_v3,
)


DEFAULT_DATASET_V2 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v2.csv"
DEFAULT_P23_RESULTS = REPO_ROOT / "outputs/apcd_k6_active_learning/next_phase_gap_top2_fdtd_results_v2.csv"
DEFAULT_DATASET_V3 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v3.csv"
DEFAULT_DATASET_REPORT = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v3_collection_report.md"
DEFAULT_COVERAGE = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_coverage_v3.csv"
DEFAULT_GAP_ANALYSIS = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_gap_analysis_v3.md"
DEFAULT_READINESS = REPO_ROOT / "outputs/apcd_k6_active_learning/k6_phase_state_readiness_v3.md"
DEFAULT_POOL = REPO_ROOT / "outputs/apcd_k6_active_learning/focused_next_gap_candidate_pool_v3.csv"
DEFAULT_POOL_SUMMARY = REPO_ROOT / "outputs/apcd_k6_active_learning/focused_next_gap_candidate_pool_v3_summary.md"
GEOMETRY_POOLS = [
    REPO_ROOT / "outputs/apcd_k6_active_learning/next_phase_gap_candidate_pool_v2.csv",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate APCD K=6 focused next-gap dataset/coverage/pool v3.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--dataset-v2", type=Path, default=DEFAULT_DATASET_V2)
    parser.add_argument("--p23-results", type=Path, default=DEFAULT_P23_RESULTS)
    parser.add_argument("--dataset-v3", type=Path, default=DEFAULT_DATASET_V3)
    parser.add_argument("--dataset-report", type=Path, default=DEFAULT_DATASET_REPORT)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--gap-analysis", type=Path, default=DEFAULT_GAP_ANALYSIS)
    parser.add_argument("--readiness", type=Path, default=DEFAULT_READINESS)
    parser.add_argument("--pool", type=Path, default=DEFAULT_POOL)
    parser.add_argument("--pool-summary", type=Path, default=DEFAULT_POOL_SUMMARY)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset_v3, dataset_columns = build_ml_dataset_v3(
        read_csv_rows(args.dataset_v2),
        read_csv_rows(args.p23_results),
        build_geometry_lookup(GEOMETRY_POOLS),
        read_csv_fieldnames(args.dataset_v2),
    )
    coverage = analyze_phase_coverage_v3(dataset_v3)
    candidates = build_focused_next_gap_candidate_pool()
    print(f"dataset_v3_rows={len(dataset_v3)}")
    print(f"candidate_count={len(candidates)}")
    print("status=dataset_coverage_pool_planning_only_no_fdtd_no_lumapi_no_fsp_no_training_not_steering_result")
    if not args.dry_run:
        write_csv_rows(dataset_v3, args.dataset_v3, dataset_columns)
        write_dataset_v3_report(args.dataset_report, dataset_v3)
        write_csv_rows(coverage, args.coverage, PHASE_COVERAGE_V3_FIELDS)
        write_phase_gap_analysis_v3(args.gap_analysis, coverage)
        write_k6_readiness_v3(args.readiness, coverage)
        write_csv_rows(candidates, args.pool, FOCUSED_NEXT_GAP_CANDIDATE_FIELDS)
        write_focused_pool_summary(args.pool_summary, candidates)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
