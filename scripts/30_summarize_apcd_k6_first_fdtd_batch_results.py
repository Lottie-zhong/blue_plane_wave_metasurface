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
    / "first_fdtd_batch_v0_results_summary.csv"
)

RESULT_SUMMARY_FIELDS = [
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
    "phase_outside_v0_range",
    "priority",
    "notes",
]

TARGET_CONVERSION_THRESHOLD = 0.5
OPPOSITE_SPIN_LEAKAGE_THRESHOLD = 0.2
CONVERSION_TO_LEAKAGE_RATIO_THRESHOLD = 6.0
V0_PHASE_MIN_DEG = 103.97568470011174
V0_PHASE_MAX_DEG = 124.13005700428602

EXPLICIT_09_P5_RESULTS = [
    {
        "candidate_id": "doe_p1w_p2w_02",
        "candidate_family": "p1w_p2w_combo",
        "target_conversion": 0.9541,
        "opposite_spin_leakage": 0.2038,
        "conversion_to_leakage_ratio": 4.6819,
        "PD": 0.6480,
        "total_transmission": 0.5789,
        "t_alpha_star_from_alpha": "-0.2472161543810461+0.9041036089284182j",
        "phase_deg": 105.2930,
        "phase_shift_vs_baseline_deg": -6.0236,
        "notes": "09-P5 real FDTD row; high target but leakage and ratio fail; no steering claim",
    },
    {
        "candidate_id": "doe_p1w_dx_01",
        "candidate_family": "p1w_internal_dx_combo",
        "target_conversion": 0.9472,
        "opposite_spin_leakage": 0.0915,
        "conversion_to_leakage_ratio": 10.3506,
        "PD": 0.8238,
        "total_transmission": 0.5194,
        "t_alpha_star_from_alpha": "-0.1788038086368039+0.9355529024218128j",
        "phase_deg": 100.8199,
        "phase_shift_vs_baseline_deg": -10.4967,
        "notes": "09-P5 real FDTD row; early pass and expands v0 low-end phase coverage",
    },
    {
        "candidate_id": "doe_lhs_like_01",
        "candidate_family": "lhs_like_mixed_combo",
        "target_conversion": 0.9188,
        "opposite_spin_leakage": 0.6715,
        "conversion_to_leakage_ratio": 1.3684,
        "PD": 0.1555,
        "total_transmission": 0.7951,
        "t_alpha_star_from_alpha": "0.4198863838447232+0.708828036698932j",
        "phase_deg": 59.3589,
        "phase_shift_vs_baseline_deg": -51.9578,
        "notes": "09-P5 real FDTD row; strong phase-coverage evidence but leakage is too high",
    },
]


def classify_priority(candidate_id: str) -> str:
    priorities = {
        "doe_p1w_dx_01": "high_priority_neighborhood",
        "doe_lhs_like_01": "phase_coverage_evidence_high_leakage",
        "doe_p1w_p2w_02": "record_not_priority",
    }
    return priorities.get(candidate_id, "record_only")


def phase_outside_v0_range(phase_deg: float) -> bool:
    return phase_deg < V0_PHASE_MIN_DEG or phase_deg > V0_PHASE_MAX_DEG


def with_early_pass_flags(row: dict[str, object]) -> dict[str, object]:
    target_pass = float(row["target_conversion"]) >= TARGET_CONVERSION_THRESHOLD
    leakage_pass = float(row["opposite_spin_leakage"]) <= OPPOSITE_SPIN_LEAKAGE_THRESHOLD
    ratio_pass = float(row["conversion_to_leakage_ratio"]) >= CONVERSION_TO_LEAKAGE_RATIO_THRESHOLD
    return {
        **row,
        "early_target_pass": target_pass,
        "early_leakage_pass": leakage_pass,
        "early_ratio_pass": ratio_pass,
        "overall_early_pass": target_pass and leakage_pass and ratio_pass,
        "phase_outside_v0_range": phase_outside_v0_range(float(row["phase_deg"])),
        "priority": classify_priority(str(row["candidate_id"])),
    }


def build_result_summary_rows(
    rows: Iterable[dict[str, object]] = EXPLICIT_09_P5_RESULTS,
) -> list[dict[str, object]]:
    return [with_early_pass_flags(row) for row in rows]


def export_result_summary_csv(rows: Iterable[dict[str, object]], output_csv: str | Path) -> Path:
    output_path = Path(output_csv)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    row_list = list(rows)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in RESULT_SUMMARY_FIELDS} for row in row_list)
    return output_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize explicit 09-P5 APCD K=6 first-batch real FDTD results."
    )
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--dry-run", action="store_true", help="Print summary and still write the small CSV.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = build_result_summary_rows()
    output_csv = export_result_summary_csv(rows, args.output_csv)
    print("status=summary_only_no_fdtd_no_lumapi_no_fsp_no_training")
    print(f"source=explicit_09_p5_real_fdtd_values")
    print(f"output_csv={output_csv}")
    print(f"row_count={len(rows)}")
    for row in rows:
        print(
            f"{row['candidate_id']}: overall_early_pass={row['overall_early_pass']}, "
            f"phase_outside_v0_range={row['phase_outside_v0_range']}, priority={row['priority']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
