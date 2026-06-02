from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_neighborhood_candidates import (
    build_neighborhood_candidate_pool,
    export_neighborhood_candidate_pool,
    load_reference_candidate_config,
    summarize_neighborhood_candidate_pool,
    write_neighborhood_candidate_pool_summary,
)


DEFAULT_P1W_DX_CONFIG = (
    REPO_ROOT / "configs" / "apcd_k6_phase_state_candidates" / "doe_p1w_dx_01.yaml"
)
DEFAULT_LHS_CONFIG = (
    REPO_ROOT / "configs" / "apcd_k6_phase_state_candidates" / "doe_lhs_like_01.yaml"
)
DEFAULT_OUTPUT_CSV = (
    REPO_ROOT / "outputs" / "apcd_k6_active_learning" / "neighborhood_candidate_pool_v1.csv"
)
DEFAULT_SUMMARY_MD = (
    REPO_ROOT / "outputs" / "apcd_k6_active_learning" / "neighborhood_candidate_pool_v1_summary.md"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate APCD K=6 09-P6 neighborhood candidate pool scaffold."
    )
    parser.add_argument("--p1w-dx-config", type=Path, default=DEFAULT_P1W_DX_CONFIG)
    parser.add_argument("--lhs-config", type=Path, default=DEFAULT_LHS_CONFIG)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--summary-md", type=Path, default=DEFAULT_SUMMARY_MD)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print reference candidates and pool summary without writing outputs.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    p1w_dx_reference = load_reference_candidate_config(args.p1w_dx_config)
    lhs_reference = load_reference_candidate_config(args.lhs_config)
    candidates = build_neighborhood_candidate_pool(p1w_dx_reference, lhs_reference)
    summary = summarize_neighborhood_candidate_pool(candidates)

    print("status=neighborhood_candidate_pool_only_no_fdtd_no_lumapi_no_fsp_no_training_no_prediction")
    print(f"reference_candidates={p1w_dx_reference['candidate_id']},{lhs_reference['candidate_id']}")
    print(f"candidate_count={summary['candidate_count']}")
    print(f"family_counts={summary['family_counts']}")
    print(f"bounds_ok={summary['bounds_ok']}")
    print(f"output_csv={args.output_csv}")
    print(f"summary_md={args.summary_md}")

    if args.dry_run:
        print("dry_run=true; no output files written")
        return 0

    export_neighborhood_candidate_pool(candidates, args.output_csv)
    write_neighborhood_candidate_pool_summary(args.summary_md, candidates)
    print("dry_run=false; outputs_written=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
