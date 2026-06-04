from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_combined_phase_knob_v10_refinement import (  # noqa: E402
    V10_POOL_FIELDS,
    V10_SELECTION_FIELDS,
    V10_VALIDATION_FIELDS,
    build_v10_refinement_pool,
    select_v10_refinement_candidates,
    validate_v10_refinement_pool,
    write_csv_rows,
    write_v10_refinement_report,
)

DEFAULT_POOL = REPO_ROOT / "outputs/apcd_k6_active_learning/combined_phase_knob_v10_refinement_pool.csv"
DEFAULT_VALIDATION = REPO_ROOT / "outputs/apcd_k6_active_learning/combined_phase_knob_v10_refinement_pool_geometry_validation.csv"
DEFAULT_SELECTION = REPO_ROOT / "outputs/apcd_k6_active_learning/combined_phase_knob_v10_refinement_fdtd_selection.csv"
DEFAULT_REPORT = REPO_ROOT / "reports/combined_phase_knob_v10_refinement_plan.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate 09-P54/P56 combined phase-knob v10 refinement planning outputs."
    )
    parser.add_argument("--dry-run", action="store_true", help="Print counts only; do not write files.")
    parser.add_argument("--pool-csv", type=Path, default=DEFAULT_POOL)
    parser.add_argument("--validation-csv", type=Path, default=DEFAULT_VALIDATION)
    parser.add_argument("--selection-csv", type=Path, default=DEFAULT_SELECTION)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    pool = build_v10_refinement_pool()
    validation = validate_v10_refinement_pool(pool)
    selected = select_v10_refinement_candidates(pool, validation)

    print(f"v10_refinement_pool_rows={len(pool)}")
    print(f"v10_refinement_geometry_pass={sum(row['overall_geometry_pass'] for row in validation)}/{len(validation)}")
    print(f"v10_refinement_selected={[row['candidate_id'] for row in selected]}")
    print("status=09_P54_P56_v10_refinement_planning_only_no_fdtd_no_lumapi_no_fsp_no_yaml_no_training_not_steering_result")

    if args.dry_run:
        return 0

    write_csv_rows(pool, args.pool_csv, V10_POOL_FIELDS)
    write_csv_rows(validation, args.validation_csv, V10_VALIDATION_FIELDS)
    write_csv_rows(selected, args.selection_csv, V10_SELECTION_FIELDS)
    write_v10_refinement_report(args.report, pool, validation, selected)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
