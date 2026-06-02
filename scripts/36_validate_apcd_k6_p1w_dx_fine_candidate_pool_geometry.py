from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_candidate_validation import (  # noqa: E402
    export_fine_candidate_validation_csv,
    read_candidate_pool_csv,
    summarize_fine_validation,
    validate_fine_candidate_pool,
)


DEFAULT_CANDIDATE_POOL = "outputs/apcd_k6_active_learning/p1w_dx_fine_candidate_pool_v1.csv"
DEFAULT_OUTPUT_CSV = "outputs/apcd_k6_active_learning/p1w_dx_fine_candidate_pool_v1_geometry_validation.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate APCD K=6 09-P10 p1w_dx fine candidate-pool geometry/gap sanity."
    )
    parser.add_argument("--dry-run", action="store_true", help="Print input/output/count only; do not write files.")
    parser.add_argument("--candidate-pool", default=DEFAULT_CANDIDATE_POOL, help="Input fine candidate pool CSV.")
    parser.add_argument("--output-csv", default=DEFAULT_OUTPUT_CSV, help="Output fine geometry validation CSV.")
    parser.add_argument("--minimum-gap-nm", type=float, default=5.0, help="Minimum allowed gap in nm.")
    return parser.parse_args()


def validate_fine_candidate_pool_file(
    *,
    candidate_pool: str | Path = DEFAULT_CANDIDATE_POOL,
    output_csv: str | Path = DEFAULT_OUTPUT_CSV,
    minimum_gap_nm: float = 5.0,
) -> tuple[Path, list[dict[str, object]], dict[str, object]]:
    pool_path = _resolve_path(candidate_pool)
    output_path = _resolve_path(output_csv)
    candidates = read_candidate_pool_csv(pool_path)
    rows = validate_fine_candidate_pool(candidates, minimum_gap_nm=minimum_gap_nm)
    export_fine_candidate_validation_csv(rows, output_path)
    return output_path, rows, summarize_fine_validation(rows)


def main() -> int:
    args = parse_args()
    pool_path = _resolve_path(args.candidate_pool)
    output_path = _resolve_path(args.output_csv)
    candidates = read_candidate_pool_csv(pool_path)
    if args.dry_run:
        print(f"input_csv={pool_path}")
        print(f"output_csv={output_path}")
        print(f"candidate_count={len(candidates)}")
        print(f"minimum_gap_nm={args.minimum_gap_nm}")
        print("status=dry_run_p1w_dx_fine_geometry_validation_only_no_fdtd_no_lumapi_no_fsp_no_training")
        return 0

    written, rows, summary = validate_fine_candidate_pool_file(
        candidate_pool=pool_path,
        output_csv=output_path,
        minimum_gap_nm=args.minimum_gap_nm,
    )
    print(f"input_csv={pool_path}")
    print(f"output_csv={written}")
    print(f"candidate_count={summary['total']}")
    print(f"geometry_pass_count={summary['geometry_pass_count']}")
    print(f"fail_count={summary['fail_count']}")
    print(f"recommended_for_fdtd_count={summary['recommended_for_fdtd_count']}")
    print(f"minimum_same_cell_gap_nm={summary['minimum_same_cell_gap_nm']}")
    print(f"minimum_periodic_image_gap_nm={summary['minimum_periodic_image_gap_nm']}")
    print(f"duplicate_geometry_fail_count={summary['duplicate_geometry_fail_count']}")
    print(f"family_counts={summary['family_counts']}")
    print(f"fail_reason_counts={summary['fail_reason_counts']}")
    print("status=p1w_dx_fine_geometry_validation_only_no_fdtd_no_lumapi_no_fsp_no_training")
    return 0


def _resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


if __name__ == "__main__":
    raise SystemExit(main())
