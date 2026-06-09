from __future__ import annotations

import argparse
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_p196_h320_zero_scout import (
    build_p196_candidate_specs,
    export_p196_outputs,
    validate_p196_pool,
)


CONFIG_DIR = REPO_ROOT / "configs/apcd_k6_phase_state_candidates"
ACTIVE_DIR = REPO_ROOT / "outputs/apcd_k6_active_learning"
SUMMARY_CSV = ACTIVE_DIR / "p196_h320_zero_bin_mechanism_scout_candidates.csv"
VALIDATION_CSV = ACTIVE_DIR / "p196_h320_zero_bin_mechanism_scout_geometry_validation.csv"
REPORT_MD = REPO_ROOT / "reports/p196_h320_zero_bin_mechanism_scout.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate P196 fixed-height h320 zero-bin mechanism scout configs and summaries only."
    )
    parser.add_argument("--dry-run", action="store_true", help="Print plan without writing files.")
    parser.add_argument("--config-dir", type=Path, default=CONFIG_DIR)
    parser.add_argument("--summary-csv", type=Path, default=SUMMARY_CSV)
    parser.add_argument("--validation-csv", type=Path, default=VALIDATION_CSV)
    parser.add_argument("--report", type=Path, default=REPORT_MD)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    specs = build_p196_candidate_specs()
    validation = validate_p196_pool(specs)
    pass_count = sum(row["overall_geometry_pass"] is True for row in validation)
    print("stage=09_p196_h320_zero_bin_mechanism_scout")
    print(f"candidate_count={len(specs)}")
    print(f"geometry_pass={pass_count}/{len(validation)}")
    print("height_nm=320")
    print("target_bin_deg=0")
    print("no_fdtd_no_lumapi_no_fsp_no_k6_phase_ramp")
    if args.dry_run:
        for spec in specs:
            print(f"candidate={spec.candidate_id} group={spec.group}")
        return 0
    export_p196_outputs(
        specs,
        config_dir=args.config_dir,
        summary_csv=args.summary_csv,
        validation_csv=args.validation_csv,
        report_md=args.report,
    )
    print(f"summary_csv={args.summary_csv}")
    print(f"validation_csv={args.validation_csv}")
    print(f"report={args.report}")
    print(f"config_dir={args.config_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
