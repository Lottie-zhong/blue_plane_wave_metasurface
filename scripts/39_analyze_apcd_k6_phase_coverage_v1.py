from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_phase_gap_candidates import (  # noqa: E402
    PHASE_COVERAGE_FIELDS,
    analyze_phase_coverage,
    read_csv_rows,
    read_phase_targets,
    write_csv_rows,
    write_phase_gap_analysis,
)


DEFAULT_DATASET = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v1.csv"
DEFAULT_TARGETS = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_bin_targets.csv"
DEFAULT_COVERAGE = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_coverage_v1.csv"
DEFAULT_REPORT = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_gap_analysis_v1.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze APCD K=6 phase coverage from ML-ready dataset v1.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--targets", type=Path, default=DEFAULT_TARGETS)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    dataset_rows = read_csv_rows(args.dataset)
    targets = read_phase_targets(args.targets)
    coverage_rows = analyze_phase_coverage(dataset_rows, targets)
    write_csv_rows(coverage_rows, args.coverage, PHASE_COVERAGE_FIELDS)
    write_phase_gap_analysis(args.report, dataset_rows, coverage_rows)
    print(f"dataset_rows={len(dataset_rows)}")
    print(f"phase_bins={len(targets)}")
    print(f"coverage_csv={args.coverage}")
    print(f"report={args.report}")
    print("status=analysis_only_no_fdtd_no_lumapi_no_fsp_no_training_not_steering_result")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
