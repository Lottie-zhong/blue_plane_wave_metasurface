from __future__ import annotations

import argparse
import cmath
import csv
import math
import sys
from pathlib import Path
from typing import Iterable


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_active_learning import wrap_phase_deg  # noqa: E402


BASELINE_PHASE_DEG = 111.31665091018952
TOP2_IDS = ["next_zero_rot_anchor_03", "next_rot_anchor_04"]
SKIPPED_IDS = ["next_mixed_bridge_03", "next_pi_mixed_bridge_03"]
DEFAULT_OUTPUT_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/next_phase_gap_top2_fdtd_results_v2.csv"
DEFAULT_SUMMARY = REPO_ROOT / "outputs/apcd_k6_active_learning/next_phase_gap_top2_fdtd_results_v2_summary.md"
DEFAULT_REPORT = REPO_ROOT / "reports/apcd_k6_next_phase_gap_top2_fdtd_result_note.md"

NEXT_PHASE_GAP_TOP2_RESULT_FIELDS = [
    "candidate_id",
    "target_bin_deg",
    "candidate_family",
    "status",
    "phase_deg",
    "phase_error_to_target_deg",
    "target_conversion",
    "opposite_spin_leakage",
    "conversion_to_leakage_ratio",
    "PD",
    "total_transmission",
    "t_alpha_star_from_alpha",
    "phase_shift_vs_baseline_deg",
    "early_target_pass",
    "early_leakage_pass",
    "early_ratio_pass",
    "early_pass",
    "target_bin_pass",
    "target_bin_status",
    "notes",
]

P23_REAL_FDTD_VALUES = [
    {
        "candidate_id": "next_zero_rot_anchor_03",
        "target_bin_deg": 0.0,
        "candidate_family": "zero_bin_probe",
        "status": "ok",
        "target_conversion": 0.5125041298645276,
        "opposite_spin_leakage": 0.45007533270235894,
        "conversion_to_leakage_ratio": 1.1387074399016555,
        "PD": 0.06485573356783089,
        "total_transmission": 0.4812897312834432,
        "t_alpha_star_from_alpha": "0.4861090662723914+0.1845484632767293j",
        "source_result_csv": "outputs/apcd_k6_metagrating_633nm/phase_state_candidates/next_zero_rot_anchor_03/results.csv",
    },
    {
        "candidate_id": "next_rot_anchor_04",
        "target_bin_deg": -60.0,
        "candidate_family": "rotation_assisted_anchor_probe",
        "status": "ok",
        "target_conversion": 0.4526296212631516,
        "opposite_spin_leakage": 0.544645601389285,
        "conversion_to_leakage_ratio": 0.8310534779106825,
        "PD": -0.09226738821536919,
        "total_transmission": 0.4986376113262183,
        "t_alpha_star_from_alpha": "-0.4905872363933683+0.1998671538222805j",
        "source_result_csv": "outputs/apcd_k6_metagrating_633nm/phase_state_candidates/next_rot_anchor_04/results.csv",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize APCD K=6 next phase-gap top-2 real FDTD results.")
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rows = [result_row_from_values(**values) for values in P23_REAL_FDTD_VALUES]
    write_result_csv(rows, args.output_csv)
    write_summary_md(rows, args.summary)
    write_report_md(rows, args.report)
    print(f"result_csv={args.output_csv}")
    print(f"summary={args.summary}")
    print(f"report={args.report}")
    print(f"candidate_ids={[row['candidate_id'] for row in rows]}")
    print("status=summary_only_after_top2_real_fdtd_no_extra_fdtd_no_k7_no_phase_ramp_no_training_not_steering_result")
    return 0


def result_row_from_values(
    *,
    candidate_id: str,
    target_bin_deg: float,
    candidate_family: str,
    status: str,
    target_conversion: float,
    opposite_spin_leakage: float,
    conversion_to_leakage_ratio: float,
    PD: float,
    total_transmission: float,
    t_alpha_star_from_alpha: str,
    source_result_csv: str = "",
) -> dict[str, object]:
    phase = phase_deg_from_complex(t_alpha_star_from_alpha)
    error = angular_distance_deg(phase, target_bin_deg)
    early_target = float(target_conversion) >= 0.5
    early_leakage = float(opposite_spin_leakage) <= 0.2
    early_ratio = float(conversion_to_leakage_ratio) >= 6.0
    early = early_target and early_leakage and early_ratio
    bin_status = target_bin_status(error, early, status)
    target_bin_pass = bin_status in {"strong_covered", "early_covered"}
    return {
        "candidate_id": candidate_id,
        "target_bin_deg": _number(target_bin_deg),
        "candidate_family": candidate_family,
        "status": status,
        "phase_deg": phase,
        "phase_error_to_target_deg": error,
        "target_conversion": target_conversion,
        "opposite_spin_leakage": opposite_spin_leakage,
        "conversion_to_leakage_ratio": conversion_to_leakage_ratio,
        "PD": PD,
        "total_transmission": total_transmission,
        "t_alpha_star_from_alpha": t_alpha_star_from_alpha,
        "phase_shift_vs_baseline_deg": wrap_phase_deg(phase - BASELINE_PHASE_DEG),
        "early_target_pass": early_target,
        "early_leakage_pass": early_leakage,
        "early_ratio_pass": early_ratio,
        "early_pass": early,
        "target_bin_pass": target_bin_pass,
        "target_bin_status": bin_status,
        "notes": _notes(candidate_id, target_bin_deg, bin_status, early, error, source_result_csv),
    }


def phase_deg_from_complex(value: str) -> float:
    return wrap_phase_deg(math.degrees(cmath.phase(complex(value))))


def angular_distance_deg(phase_deg: float, target_deg: float) -> float:
    return abs(wrap_phase_deg(float(phase_deg) - float(target_deg)))


def target_bin_status(phase_error_deg: float, early_pass: bool, status: str = "ok") -> str:
    if status != "ok":
        return "failed"
    if early_pass and phase_error_deg <= 10.0:
        return "strong_covered"
    if early_pass and phase_error_deg <= 20.0:
        return "early_covered"
    if early_pass and phase_error_deg <= 35.0:
        return "near_but_not_covered"
    if phase_error_deg <= 35.0:
        return "evidence_only"
    return "open_gap"


def write_result_csv(rows: Iterable[dict[str, object]], path: str | Path) -> Path:
    row_list = list(rows)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=NEXT_PHASE_GAP_TOP2_RESULT_FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in NEXT_PHASE_GAP_TOP2_RESULT_FIELDS} for row in row_list)
    return output_path


def write_summary_md(rows: Iterable[dict[str, object]], path: str | Path) -> Path:
    row_list = list(rows)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# APCD K=6 Next Phase-Gap Top-2 FDTD Results v2 Summary",
        "",
        "Scope: 09-P23 summary after running only `next_zero_rot_anchor_03` and `next_rot_anchor_04`. No other candidate was run in this stage.",
        "",
        "| candidate_id | target bin deg | phase deg | error deg | leakage | ratio | early pass | target bin status |",
        "|---|---:|---:|---:|---:|---:|---|---|",
        *[
            f"| `{row['candidate_id']}` | {row['target_bin_deg']} | {row['phase_deg']} | {row['phase_error_to_target_deg']} | "
            f"{row['opposite_spin_leakage']} | {row['conversion_to_leakage_ratio']} | {row['early_pass']} | {row['target_bin_status']} |"
            for row in row_list
        ],
        "",
        "No raw `results.csv`, `.fsp`, `pre_run_X.fsp`, or `pre_run_Y.fsp` files are included in this summary output.",
    ]
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def write_report_md(rows: Iterable[dict[str, object]], path: str | Path) -> Path:
    row_list = list(rows)
    by_id = {str(row["candidate_id"]): row for row in row_list}
    zero = by_id["next_zero_rot_anchor_03"]
    neg60 = by_id["next_rot_anchor_04"]
    lines = [
        "# APCD K=6 Next Phase-Gap Top-2 FDTD Result Note",
        "",
        "## Scope",
        "",
        "This is 09-P23. Only two next phase-gap candidates were run with real FDTD:",
        "",
        "- `next_zero_rot_anchor_03`, targeting the 0 deg major gap.",
        "- `next_rot_anchor_04`, targeting the -60 deg major gap.",
        "",
        "The ranks 3-4 selected candidates, `next_mixed_bridge_03` and `next_pi_mixed_bridge_03`, were not run. The full 38-row next candidate pool was not run. No K=7, phase-ramp supercell, TiO2/450 nm, Micro-LED, DenseNet, or cVAE work was done. This is not a +15 deg steering result and does not complete the K=6 phase-state library.",
        "",
        "## Results",
        "",
        "| candidate | target bin | phase deg | error deg | target conversion | leakage | ratio | PD | early pass | target bin status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
        *[
            f"| `{row['candidate_id']}` | {row['target_bin_deg']} | {row['phase_deg']} | {row['phase_error_to_target_deg']} | "
            f"{row['target_conversion']} | {row['opposite_spin_leakage']} | {row['conversion_to_leakage_ratio']} | "
            f"{row['PD']} | {row['early_pass']} | {row['target_bin_status']} |"
            for row in row_list
        ],
        "",
        "## Interpretation",
        "",
        f"`next_zero_rot_anchor_03` reached phase {zero['phase_deg']} deg for target 0 deg, with wrapped error {zero['phase_error_to_target_deg']} deg. It is phase-near evidence, but leakage {zero['opposite_spin_leakage']} and ratio {zero['conversion_to_leakage_ratio']} fail the early-pass criteria, so the 0 deg gap is not filled.",
        "",
        f"`next_rot_anchor_04` reached phase {neg60['phase_deg']} deg for target -60 deg, with wrapped error {neg60['phase_error_to_target_deg']} deg. It is not close to the target and also fails target conversion, leakage, and ratio thresholds, so the -60 deg gap remains open.",
        "",
        "The rotation-assisted hypothesis did not fill either tested major gap in this top-2 run. The 0 deg candidate provides evidence that the phase can be pulled toward 0 deg, but leakage control is currently inadequate.",
        "",
        "## Next Step",
        "",
        "Do not run the full next pool. A reasonable next small step is to use the `next_zero_rot_anchor_03` evidence to design a leakage-controlled 0-deg neighborhood, or run one lower-risk bridge candidate only after explicitly deciding that the high-risk rotation-assisted path is still worth probing.",
    ]
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def _notes(
    candidate_id: str,
    target_bin_deg: float,
    bin_status: str,
    early: bool,
    error: float,
    source_result_csv: str,
) -> str:
    pieces = [
        "09-P23 real FDTD top-2 only",
        f"target bin {target_bin_deg:g} deg",
        f"wrapped phase error {error:.6g} deg",
        f"target_bin_status={bin_status}",
        "early pass" if early else "not early pass",
    ]
    if source_result_csv:
        pieces.append(f"source raw result path not committed: {source_result_csv}")
    if candidate_id in SKIPPED_IDS:
        pieces.append("unexpected skipped candidate")
    pieces.append("not a steering result")
    return "; ".join(pieces)


def _number(value: object) -> int | float:
    number = float(value)
    return int(number) if number.is_integer() else number


if __name__ == "__main__":
    raise SystemExit(main())
