from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_candidate_pool import (  # noqa: E402
    build_candidate_pool,
    export_candidate_pool_csv,
    summarize_candidate_pool,
    write_candidate_pool_summary,
)


DEFAULT_DATASET_V0 = "outputs/apcd_k6_active_learning/ml_ready_dataset_v0.csv"
DEFAULT_OUTPUT_CSV = "outputs/apcd_k6_active_learning/bounded_candidate_pool_v0.csv"
DEFAULT_SUMMARY_MD = "outputs/apcd_k6_active_learning/bounded_candidate_pool_v0_summary.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate APCD K=6 bounded candidate pool scaffold.")
    parser.add_argument("--dry-run", action="store_true", help="Write deterministic candidate-pool scaffold only.")
    parser.add_argument("--dataset-v0", default=DEFAULT_DATASET_V0, help="Input ML-ready dataset v0 CSV.")
    parser.add_argument("--output-csv", default=DEFAULT_OUTPUT_CSV, help="Output bounded candidate pool CSV.")
    parser.add_argument("--summary-md", default=DEFAULT_SUMMARY_MD, help="Output candidate pool summary Markdown.")
    return parser.parse_args()


def generate_candidate_pool_outputs(
    *,
    dataset_v0: str | Path = DEFAULT_DATASET_V0,
    output_csv: str | Path = DEFAULT_OUTPUT_CSV,
    summary_md: str | Path = DEFAULT_SUMMARY_MD,
) -> tuple[Path, Path, list[dict[str, object]], dict[str, object]]:
    dataset_path = _resolve_path(dataset_v0)
    candidates = build_candidate_pool(dataset_path)
    csv_path = export_candidate_pool_csv(candidates, _resolve_path(output_csv))
    summary_path = write_candidate_pool_summary(_resolve_path(summary_md), candidates)
    return csv_path, summary_path, candidates, summarize_candidate_pool(candidates)


def main() -> int:
    args = parse_args()
    if not args.dry_run:
        raise SystemExit("Pass --dry-run for the current scaffold-only workflow.")
    csv_path, summary_path, candidates, summary = generate_candidate_pool_outputs(
        dataset_v0=args.dataset_v0,
        output_csv=args.output_csv,
        summary_md=args.summary_md,
    )
    print(f"candidate_count={len(candidates)}")
    print(f"family_counts={summary['family_counts']}")
    print(f"anchors_present={','.join(summary['anchors_present'])}")
    print(f"bounds_ok={summary['bounds_ok']}")
    print(f"output_csv={csv_path}")
    print(f"summary_md={summary_path}")
    print("status=dry_run_candidate_pool_only_no_fdtd_no_lumapi_no_fsp_no_training_no_prediction")
    return 0


def _resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


if __name__ == "__main__":
    raise SystemExit(main())
