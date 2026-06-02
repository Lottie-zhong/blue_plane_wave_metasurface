from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_fine_candidate_selection import (  # noqa: E402
    export_candidate_configs,
    export_fine_fdtd_selection_csv,
    load_fine_candidate_pool,
    load_fine_geometry_validation,
    select_fine_fdtd_candidates,
    summarize_fine_fdtd_selection,
    write_fine_fdtd_selection_summary,
)


DEFAULT_CANDIDATE_POOL = "outputs/apcd_k6_active_learning/p1w_dx_fine_candidate_pool_v1.csv"
DEFAULT_GEOMETRY_VALIDATION = (
    "outputs/apcd_k6_active_learning/p1w_dx_fine_candidate_pool_v1_geometry_validation.csv"
)
DEFAULT_SELECTION_CSV = "outputs/apcd_k6_active_learning/p1w_dx_fine_fdtd_selection_v1.csv"
DEFAULT_SELECTION_SUMMARY = "outputs/apcd_k6_active_learning/p1w_dx_fine_fdtd_selection_v1_summary.md"
DEFAULT_CONFIG_DIR = "configs/apcd_k6_phase_state_candidates"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Select APCD K=6 p1w_dx fine candidates and prepare top-2 configs.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--select-only", action="store_true", help="Write selection CSV/summary only.")
    mode.add_argument("--run-top", type=int, choices=[2], help="Write selection CSV/summary and top-2 configs.")
    parser.add_argument("--candidate-pool", default=DEFAULT_CANDIDATE_POOL)
    parser.add_argument("--geometry-validation", default=DEFAULT_GEOMETRY_VALIDATION)
    parser.add_argument("--selection-csv", default=DEFAULT_SELECTION_CSV)
    parser.add_argument("--selection-summary", default=DEFAULT_SELECTION_SUMMARY)
    parser.add_argument("--config-dir", default=DEFAULT_CONFIG_DIR)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidates = load_fine_candidate_pool(_resolve_path(args.candidate_pool))
    validation = load_fine_geometry_validation(_resolve_path(args.geometry_validation))
    selected = select_fine_fdtd_candidates(candidates, validation)
    summary = summarize_fine_fdtd_selection(selected)

    selection_csv = export_fine_fdtd_selection_csv(selected, _resolve_path(args.selection_csv))
    selection_summary = write_fine_fdtd_selection_summary(_resolve_path(args.selection_summary), selected)

    print("status=p1w_dx_fine_selection_only_no_fdtd_no_lumapi_no_fsp_no_training_no_prediction")
    print(f"selection_csv={selection_csv}")
    print(f"selection_summary={selection_summary}")
    print(f"selected_count={summary['selected_count']}")
    print(f"run_now_candidate_ids={summary['run_now_candidate_ids']}")
    print(f"backup_candidate_ids={summary['backup_candidate_ids']}")
    print(f"family_counts={summary['family_counts']}")

    if args.select_only:
        print("mode=select_only; no configs written")
        return 0

    written_configs = export_candidate_configs(selected, _resolve_path(args.config_dir))
    print("mode=run_top_2_config_prepare_only")
    print("config_files=" + ",".join(str(path) for path in written_configs))
    print("dry_run_required_before_real_fdtd=True")
    print("no_fdtd_run_from_this_script=True")
    return 0


def _resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


if __name__ == "__main__":
    raise SystemExit(main())
