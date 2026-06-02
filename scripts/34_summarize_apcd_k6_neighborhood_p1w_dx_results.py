from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_CSV = (
    REPO_ROOT
    / "outputs"
    / "apcd_k6_active_learning"
    / "neighborhood_p1w_dx_fdtd_results_v1.csv"
)

RESULT_FIELDS = [
    "candidate_id",
    "candidate_family",
    "target_conversion",
    "opposite_spin_leakage",
    "conversion_to_leakage_ratio",
    "PD",
    "total_transmission",
    "t_alpha_star_from_alpha",
    "phase_deg",
    "phase_shift_vs_baseline_deg",
    "early_target_pass",
    "early_leakage_pass",
    "early_ratio_pass",
    "overall_early_pass",
    "phase_below_doe_p1w_dx_01",
    "inside_90_100_deg_region",
    "priority",
    "notes",
]

TARGET_CONVERSION_THRESHOLD = 0.5
OPPOSITE_SPIN_LEAKAGE_THRESHOLD = 0.2
CONVERSION_TO_LEAKAGE_RATIO_THRESHOLD = 6.0
DOE_P1W_DX_01_PHASE_DEG = 100.8199

EXPLICIT_09_P9_RESULTS = [
    {
        "candidate_id": "nhood_p1w_dx_05",
        "candidate_family": "p1w_dx_neighborhood",
        "target_conversion": 0.9463,
        "opposite_spin_leakage": 0.0869,
        "conversion_to_leakage_ratio": 10.8860,
        "PD": 0.8317,
        "total_transmission": 0.5166,
        "t_alpha_star_from_alpha": "-0.1808305415936028+0.9345255229154362j",
        "phase_deg": 100.9514,
        "phase_shift_vs_baseline_deg": -10.3653,
        "notes": "09-P9 real FDTD row; leakage remains low, but phase does not go below doe_p1w_dx_01 and does not enter 90-100 deg.",
    },
    {
        "candidate_id": "nhood_p1w_dx_02",
        "candidate_family": "p1w_dx_neighborhood",
        "target_conversion": 0.9289,
        "opposite_spin_leakage": 0.2153,
        "conversion_to_leakage_ratio": 4.3150,
        "PD": 0.6237,
        "total_transmission": 0.5721,
        "t_alpha_star_from_alpha": "-0.1347815485360421+0.9229231360105533j",
        "phase_deg": 98.3086,
        "phase_shift_vs_baseline_deg": -13.0080,
        "notes": "09-P9 real FDTD row; phase enters 90-100 deg, but leakage and ratio fail early-pass thresholds.",
    },
]


def classify_priority(candidate_id: str) -> str:
    priorities = {
        "nhood_p1w_dx_05": "low_leakage_conservative_reference",
        "nhood_p1w_dx_02": "lower_phase_high_leakage_boundary",
    }
    return priorities.get(candidate_id, "record_only")


def inside_90_100_deg_region(phase_deg: float) -> bool:
    return 90.0 <= phase_deg <= 100.0


def with_summary_flags(row: dict[str, object]) -> dict[str, object]:
    target_pass = float(row["target_conversion"]) >= TARGET_CONVERSION_THRESHOLD
    leakage_pass = float(row["opposite_spin_leakage"]) <= OPPOSITE_SPIN_LEAKAGE_THRESHOLD
    ratio_pass = float(row["conversion_to_leakage_ratio"]) >= CONVERSION_TO_LEAKAGE_RATIO_THRESHOLD
    phase = float(row["phase_deg"])
    return {
        **row,
        "early_target_pass": target_pass,
        "early_leakage_pass": leakage_pass,
        "early_ratio_pass": ratio_pass,
        "overall_early_pass": target_pass and leakage_pass and ratio_pass,
        "phase_below_doe_p1w_dx_01": phase < DOE_P1W_DX_01_PHASE_DEG,
        "inside_90_100_deg_region": inside_90_100_deg_region(phase),
        "priority": classify_priority(str(row["candidate_id"])),
    }


def build_result_summary_rows(
    rows: Iterable[dict[str, object]] = EXPLICIT_09_P9_RESULTS,
) -> list[dict[str, object]]:
    return [with_summary_flags(row) for row in rows]


def export_result_summary_csv(rows: Iterable[dict[str, object]], output_csv: str | Path) -> Path:
    row_list = list(rows)
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in RESULT_FIELDS} for row in row_list)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize explicit 09-P9 APCD K=6 p1w_dx neighborhood real FDTD results."
    )
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--dry-run", action="store_true", help="Print summary and still write the small CSV.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = build_result_summary_rows()
    output_csv = export_result_summary_csv(rows, args.output_csv)
    print("status=summary_only_no_fdtd_no_lumapi_no_fsp_no_training")
    print("source=explicit_09_p9_real_fdtd_values")
    print(f"output_csv={output_csv}")
    print(f"row_count={len(rows)}")
    for row in rows:
        print(
            f"{row['candidate_id']}: overall_early_pass={row['overall_early_pass']}, "
            f"phase_below_doe_p1w_dx_01={row['phase_below_doe_p1w_dx_01']}, "
            f"inside_90_100_deg_region={row['inside_90_100_deg_region']}, "
            f"priority={row['priority']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
