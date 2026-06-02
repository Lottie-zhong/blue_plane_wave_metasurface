from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_next_phase_gap_candidates import (  # noqa: E402
    build_geometry_lookup,
    build_ml_dataset_v2,
    read_csv_fieldnames,
    read_csv_rows,
    write_csv_rows,
    write_dataset_v2_report,
)


DEFAULT_V1 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v1.csv"
DEFAULT_P18_RESULTS = REPO_ROOT / "outputs/apcd_k6_active_learning/aggressive_phase_gap_top2_fdtd_results_v1.csv"
DEFAULT_OUTPUT = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v2.csv"
DEFAULT_REPORT = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v2_collection_report.md"
GEOMETRY_POOLS = [
    REPO_ROOT / "outputs/apcd_k6_active_learning/aggressive_phase_gap_candidate_pool_v1.csv",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update APCD K=6 ML-ready dataset v2 from 09-P18 summaries.")
    parser.add_argument("--v1", type=Path, default=DEFAULT_V1)
    parser.add_argument("--p18-results", type=Path, default=DEFAULT_P18_RESULTS)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = build_ml_dataset_v2(
        read_csv_rows(args.v1),
        read_csv_rows(args.p18_results),
        build_geometry_lookup(GEOMETRY_POOLS),
        read_csv_fieldnames(args.v1),
    )
    columns = list(rows[0].keys()) if rows else []
    write_csv_rows(rows, args.output, columns)
    write_dataset_v2_report(args.report, rows)
    early_count = sum(1 for row in rows if str(row["overall_early_pass"]) == "True")
    print(f"dataset_v2_rows={len(rows)}")
    print(f"early_pass_count={early_count}")
    print(f"output_csv={args.output}")
    print(f"report={args.report}")
    print("status=dataset_update_only_no_fdtd_no_lumapi_no_fsp_no_training_not_steering_result")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
