from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_next_phase_gap_candidates import (  # noqa: E402
    PHASE_COVERAGE_V2_FIELDS,
    analyze_phase_coverage_v2,
    read_csv_rows,
    write_csv_rows,
    write_k6_readiness_v2,
    write_phase_gap_analysis_v2,
)


DEFAULT_DATASET = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v2.csv"
DEFAULT_COVERAGE = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_coverage_v2.csv"
DEFAULT_ANALYSIS = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_gap_analysis_v2.md"
DEFAULT_READINESS = REPO_ROOT / "outputs/apcd_k6_active_learning/k6_phase_state_readiness_v2.md"
TARGETS = [0.0, 60.0, 120.0, -180.0, -120.0, -60.0]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze APCD K=6 phase coverage v2.")
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET)
    parser.add_argument("--coverage", type=Path, default=DEFAULT_COVERAGE)
    parser.add_argument("--analysis", type=Path, default=DEFAULT_ANALYSIS)
    parser.add_argument("--readiness", type=Path, default=DEFAULT_READINESS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = read_csv_rows(args.dataset)
    coverage = analyze_phase_coverage_v2(rows, TARGETS)
    write_csv_rows(coverage, args.coverage, PHASE_COVERAGE_V2_FIELDS)
    write_phase_gap_analysis_v2(args.analysis, coverage)
    write_k6_readiness_v2(args.readiness, coverage)
    print(f"dataset_rows={len(rows)}")
    print(f"phase_bins={len(coverage)}")
    print(f"coverage_csv={args.coverage}")
    print(f"analysis={args.analysis}")
    print(f"readiness={args.readiness}")
    print("status=analysis_only_no_fdtd_no_lumapi_no_fsp_no_training_not_steering_result")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
