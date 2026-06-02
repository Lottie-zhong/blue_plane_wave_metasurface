from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_phase_gap_candidates import (  # noqa: E402
    PHASE_GAP_CANDIDATE_FIELDS,
    build_phase_gap_candidate_pool,
    summarize_phase_gap_candidate_pool,
    write_csv_rows,
    write_phase_gap_candidate_pool_summary,
)


DEFAULT_OUTPUT = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_gap_candidate_pool_v1.csv"
DEFAULT_SUMMARY = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_gap_candidate_pool_v1_summary.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate APCD K=6 60-90 deg phase-gap candidate pool v1.")
    parser.add_argument("--dry-run", action="store_true", help="Print summary only; do not write files.")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidates = build_phase_gap_candidate_pool()
    summary = summarize_phase_gap_candidate_pool(candidates)
    print(f"candidate_count={summary['candidate_count']}")
    print(f"family_counts={summary['family_counts']}")
    print(f"output_csv={args.output}")
    print(f"summary={args.summary}")
    print("status=candidate_pool_only_no_fdtd_no_lumapi_no_fsp_no_training_not_steering_result")
    if not args.dry_run:
        write_csv_rows(candidates, args.output, PHASE_GAP_CANDIDATE_FIELDS)
        write_phase_gap_candidate_pool_summary(args.summary, candidates)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
