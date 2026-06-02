from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_neighborhood_selection import (  # noqa: E402
    export_neighborhood_fdtd_selection_csv,
    load_neighborhood_candidate_pool,
    load_neighborhood_geometry_validation,
    select_neighborhood_fdtd_candidates,
    summarize_neighborhood_fdtd_selection,
    write_neighborhood_fdtd_selection_summary,
)


DEFAULT_CANDIDATE_POOL = "outputs/apcd_k6_active_learning/neighborhood_candidate_pool_v1.csv"
DEFAULT_GEOMETRY_VALIDATION = (
    "outputs/apcd_k6_active_learning/neighborhood_candidate_pool_v1_geometry_validation.csv"
)
DEFAULT_OUTPUT_CSV = "outputs/apcd_k6_active_learning/neighborhood_fdtd_selection_v1.csv"
DEFAULT_SUMMARY_MD = "outputs/apcd_k6_active_learning/neighborhood_fdtd_selection_v1_summary.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Select APCD K=6 09-P8 neighborhood candidates for the next real FDTD batch."
    )
    parser.add_argument("--dry-run", action="store_true", help="Print selection only; do not write outputs.")
    parser.add_argument("--candidate-pool", default=DEFAULT_CANDIDATE_POOL, help="Input neighborhood pool CSV.")
    parser.add_argument("--geometry-validation", default=DEFAULT_GEOMETRY_VALIDATION, help="Input geometry validation CSV.")
    parser.add_argument("--output-csv", default=DEFAULT_OUTPUT_CSV, help="Output selection CSV.")
    parser.add_argument("--summary-md", default=DEFAULT_SUMMARY_MD, help="Output selection summary markdown.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pool_path = _resolve_path(args.candidate_pool)
    validation_path = _resolve_path(args.geometry_validation)
    output_path = _resolve_path(args.output_csv)
    summary_path = _resolve_path(args.summary_md)
    candidates = load_neighborhood_candidate_pool(pool_path)
    validation = load_neighborhood_geometry_validation(validation_path)
    selected = select_neighborhood_fdtd_candidates(candidates, validation)
    summary = summarize_neighborhood_fdtd_selection(selected)

    print("status=neighborhood_fdtd_selection_only_no_fdtd_no_lumapi_no_fsp_no_training_no_prediction")
    print(f"candidate_pool={pool_path}")
    print(f"geometry_validation={validation_path}")
    print(f"selected_count={summary['selected_count']}")
    print(f"selected_candidate_ids={summary['selected_candidate_ids']}")
    print(f"family_counts={summary['family_counts']}")
    print(f"output_csv={output_path}")
    print(f"summary_md={summary_path}")

    if args.dry_run:
        print("dry_run=true; no output files written")
        return 0

    export_neighborhood_fdtd_selection_csv(selected, output_path)
    write_neighborhood_fdtd_selection_summary(summary_path, selected)
    print("dry_run=false; outputs_written=true")
    return 0


def _resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


if __name__ == "__main__":
    raise SystemExit(main())
