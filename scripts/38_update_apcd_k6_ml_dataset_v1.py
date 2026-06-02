from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_phase_gap_candidates import (  # noqa: E402
    build_geometry_lookup,
    build_ml_dataset_v1,
    read_csv_fieldnames,
    read_csv_rows,
    write_csv_rows,
    write_ml_dataset_v1_report,
)


DEFAULT_V0 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v0.csv"
DEFAULT_SUMMARIES = [
    REPO_ROOT / "outputs/apcd_k6_active_learning/first_fdtd_batch_v0_results_summary.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/neighborhood_p1w_dx_fdtd_results_v1.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/p1w_dx_fine_fdtd_results_v1.csv",
]
DEFAULT_POOLS = [
    REPO_ROOT / "outputs/apcd_k6_active_learning/bounded_candidate_pool_v0.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/neighborhood_candidate_pool_v1.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/p1w_dx_fine_candidate_pool_v1.csv",
]
DEFAULT_OUTPUT = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v1.csv"
DEFAULT_REPORT = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v1_update_report.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Update APCD K=6 ML-ready dataset v1 from recorded summaries.")
    parser.add_argument("--v0", type=Path, default=DEFAULT_V0)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    columns = read_csv_fieldnames(args.v0)
    rows = build_ml_dataset_v1(
        read_csv_rows(args.v0),
        DEFAULT_SUMMARIES,
        build_geometry_lookup(DEFAULT_POOLS),
        columns,
    )
    write_csv_rows(rows, args.output, columns)
    write_ml_dataset_v1_report(args.report, rows)
    early_count = sum(1 for row in rows if str(row["overall_early_pass"]) == "True")
    print(f"dataset_v1_rows={len(rows)}")
    print(f"early_pass_count={early_count}")
    print(f"output_csv={args.output}")
    print(f"report={args.report}")
    print("status=dataset_update_only_no_new_fdtd_no_lumapi_no_fsp_no_training_not_steering_result")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
