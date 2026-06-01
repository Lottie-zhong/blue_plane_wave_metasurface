from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_candidate_selection import (  # noqa: E402
    export_selected_batch_csv,
    load_candidate_pool,
    load_geometry_validation,
    select_first_fdtd_batch,
    summarize_selected_batch,
    write_selected_batch_summary,
)


DEFAULT_CANDIDATE_POOL = "outputs/apcd_k6_active_learning/bounded_candidate_pool_v0.csv"
DEFAULT_GEOMETRY_VALIDATION = "outputs/apcd_k6_active_learning/bounded_candidate_pool_v0_geometry_validation.csv"
DEFAULT_OUTPUT_CSV = "outputs/apcd_k6_active_learning/first_fdtd_batch_v0.csv"
DEFAULT_SUMMARY_MD = "outputs/apcd_k6_active_learning/first_fdtd_batch_v0_summary.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select APCD K=6 first small FDTD batch.")
    parser.add_argument("--dry-run", action="store_true", help="Write deterministic selection scaffold only.")
    parser.add_argument("--candidate-pool", default=DEFAULT_CANDIDATE_POOL, help="Input candidate pool CSV.")
    parser.add_argument("--geometry-validation", default=DEFAULT_GEOMETRY_VALIDATION, help="Geometry validation CSV.")
    parser.add_argument("--output-csv", default=DEFAULT_OUTPUT_CSV, help="Output selected batch CSV.")
    parser.add_argument("--summary-md", default=DEFAULT_SUMMARY_MD, help="Output selected batch summary Markdown.")
    parser.add_argument("--batch-size", type=int, default=8, help="Selected batch size, expected in 6-10.")
    return parser.parse_args()


def write_first_batch_outputs(
    *,
    candidate_pool: str | Path = DEFAULT_CANDIDATE_POOL,
    geometry_validation: str | Path = DEFAULT_GEOMETRY_VALIDATION,
    output_csv: str | Path = DEFAULT_OUTPUT_CSV,
    summary_md: str | Path = DEFAULT_SUMMARY_MD,
    batch_size: int = 8,
) -> tuple[Path, Path, list[dict[str, object]], dict[str, object]]:
    candidates = load_candidate_pool(_resolve_path(candidate_pool))
    validation = load_geometry_validation(_resolve_path(geometry_validation))
    selected = select_first_fdtd_batch(candidates, validation, batch_size=batch_size)
    csv_path = export_selected_batch_csv(selected, _resolve_path(output_csv))
    summary_path = write_selected_batch_summary(_resolve_path(summary_md), selected)
    return csv_path, summary_path, selected, summarize_selected_batch(selected)


def main() -> int:
    args = parse_args()
    csv_path, summary_path, selected, summary = write_first_batch_outputs(
        candidate_pool=args.candidate_pool,
        geometry_validation=args.geometry_validation,
        output_csv=args.output_csv,
        summary_md=args.summary_md,
        batch_size=args.batch_size,
    )
    print(f"selected_count={len(selected)}")
    print(f"selected_candidate_ids={','.join(summary['selected_candidate_ids'])}")
    print(f"family_counts={summary['family_counts']}")
    print(f"output_csv={csv_path}")
    print(f"summary_md={summary_path}")
    print("status=dry_run_selection_only_no_fdtd_no_lumapi_no_fsp_no_training_no_prediction")
    return 0


def _resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


if __name__ == "__main__":
    raise SystemExit(main())
