from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_active_learning import (  # noqa: E402
    CANDIDATE_PARAMETER_SCHEMA_FIELDS,
    ML_READY_DATASET_SCHEMA_FIELDS,
    build_candidate_parameter_schema,
    build_ml_dataset_schema,
    write_active_learning_scoring_rules,
    write_phase_bin_targets_csv,
    write_rows_csv,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Define APCD K=6 active-learning scaffold files.")
    parser.add_argument("--dry-run", action="store_true", help="Write schema/scoring scaffold only.")
    parser.add_argument(
        "--output-dir",
        default="outputs/apcd_k6_active_learning",
        help="Output directory for scaffold CSV/Markdown files.",
    )
    return parser.parse_args()


def write_active_learning_scaffold(output_dir: str | Path) -> dict[str, Path]:
    root = Path(output_dir)
    if not root.is_absolute():
        root = REPO_ROOT / root
    root.mkdir(parents=True, exist_ok=True)

    dataset_schema = write_rows_csv(
        build_ml_dataset_schema(),
        root / "ml_ready_dataset_schema.csv",
        ML_READY_DATASET_SCHEMA_FIELDS,
    )
    candidate_schema = write_rows_csv(
        build_candidate_parameter_schema(),
        root / "candidate_parameter_schema.csv",
        CANDIDATE_PARAMETER_SCHEMA_FIELDS,
    )
    phase_targets = write_phase_bin_targets_csv(root / "phase_bin_targets.csv", k=6, convention="[-180,180)")
    scoring_rules = write_active_learning_scoring_rules(root / "active_learning_scoring_rules.md")
    return {
        "ml_ready_dataset_schema": dataset_schema,
        "candidate_parameter_schema": candidate_schema,
        "phase_bin_targets": phase_targets,
        "active_learning_scoring_rules": scoring_rules,
    }


def main() -> int:
    args = parse_args()
    if not args.dry_run:
        raise SystemExit("Pass --dry-run for the current scaffold-only workflow.")
    paths = write_active_learning_scaffold(args.output_dir)
    print("status=dry_run_active_learning_scaffold_only_no_training_no_fdtd_no_fsp_not_steering_result")
    for name, path in paths.items():
        print(f"{name}={path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
