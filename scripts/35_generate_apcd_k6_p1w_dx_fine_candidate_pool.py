from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_fine_neighborhood_candidates import (  # noqa: E402
    build_fine_candidate_pool,
    export_fine_candidate_pool,
    summarize_fine_candidate_pool,
    write_fine_candidate_pool_summary,
)


DEFAULT_OUTPUT_CSV = "outputs/apcd_k6_active_learning/p1w_dx_fine_candidate_pool_v1.csv"
DEFAULT_SUMMARY_MD = "outputs/apcd_k6_active_learning/p1w_dx_fine_candidate_pool_v1_summary.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate APCD K=6 09-P10 p1w_dx leakage-controlled fine candidate pool."
    )
    parser.add_argument("--dry-run", action="store_true", help="Print summary only; do not write outputs.")
    parser.add_argument("--output-csv", default=DEFAULT_OUTPUT_CSV, help="Output fine candidate pool CSV.")
    parser.add_argument("--summary-md", default=DEFAULT_SUMMARY_MD, help="Output fine candidate pool summary markdown.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_path = _resolve_path(args.output_csv)
    summary_path = _resolve_path(args.summary_md)
    candidates = build_fine_candidate_pool()
    summary = summarize_fine_candidate_pool(candidates)

    print("status=p1w_dx_fine_candidate_pool_only_no_fdtd_no_lumapi_no_fsp_no_training_no_prediction")
    print(f"candidate_count={summary['candidate_count']}")
    print(f"family_counts={summary['family_counts']}")
    print(f"p1_width_range={summary['p1_width_range']}")
    print(f"internal_dx_range={summary['internal_dx_range']}")
    print(f"bounds_ok={summary['bounds_ok']}")
    print(f"deduplicated_against_references={summary['deduplicated_against_references']}")
    print(f"output_csv={output_path}")
    print(f"summary_md={summary_path}")

    if args.dry_run:
        print("dry_run=true; no output files written")
        return 0

    export_fine_candidate_pool(candidates, output_path)
    write_fine_candidate_pool_summary(summary_path, candidates)
    print("dry_run=false; outputs_written=true")
    return 0


def _resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


if __name__ == "__main__":
    raise SystemExit(main())
