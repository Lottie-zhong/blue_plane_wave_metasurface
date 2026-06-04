from __future__ import annotations

import argparse
import cmath
import csv
import math
import re
import sys
from pathlib import Path
from typing import Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_active_learning import wrap_phase_deg  # noqa: E402


TARGET_BINS_DEG = [-180.0, -120.0, -60.0, 0.0, 60.0, 120.0]
REMAINING_MISSING_BINS_DEG = [-60.0, 0.0, 60.0]
ALLOWED_CANDIDATE_IDS = {"cpk_mbin_lower_transition_01", "cpk_mbin_lower_transition_02"}
DEFAULT_COVERAGE_BASE = REPO_ROOT / "outputs/apcd_k6_active_learning/combined_phase_knob_phase_state_coverage_p69.csv"
RESULT_FIELDS = [
    "candidate_id",
    "stage_label",
    "status",
    "phase_deg",
    "nearest_target_bin_deg",
    "phase_error_to_bin_deg",
    "best_remaining_missing_bin_deg",
    "phase_error_to_best_missing_bin_deg",
    "target_conversion",
    "opposite_spin_leakage",
    "conversion_to_leakage_ratio",
    "PD",
    "early_pass",
    "near_pass",
    "opens_missing_bin",
    "source_result_csv",
    "source_coverage_csv",
    "notes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize one APCD lower-transition candidate real FDTD result.")
    parser.add_argument("--candidate-id", required=True, choices=sorted(ALLOWED_CANDIDATE_IDS))
    parser.add_argument("--coverage-base", type=Path, default=DEFAULT_COVERAGE_BASE)
    parser.add_argument("--stage-label", default="09-P73")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result_path = candidate_result_path(args.candidate_id)
    if not result_path.exists():
        print("Real FDTD result missing; run this candidate on the server first.")
        print(f"missing_result_csv={result_path}")
        return 0

    raw_rows = read_csv_rows(result_path)
    if not raw_rows:
        raise ValueError(f"Result CSV contains no rows: {result_path}")

    summary_row = summarize_raw_result(
        candidate_id=args.candidate_id,
        raw=raw_rows[0],
        result_path=result_path,
        coverage_base=args.coverage_base,
        stage_label=args.stage_label,
    )
    summary_csv, report_md = output_paths(args.stage_label, args.candidate_id)
    write_csv_rows([summary_row], summary_csv, RESULT_FIELDS)
    write_report(report_md, summary_row)
    print(f"summary_csv={summary_csv}")
    print(f"report={report_md}")
    print(
        "status=summary_created_stage09_only_no_fdtd_no_lumapi_no_k7_no_phase_ramp_no_steering_no_training"
    )
    return 0


def candidate_result_path(candidate_id: str) -> Path:
    return REPO_ROOT / "outputs/apcd_k6_metagrating_633nm/phase_state_candidates" / candidate_id / "results.csv"


def output_paths(stage_label: str, candidate_id: str) -> tuple[Path, Path]:
    stage = normalize_stage_label(stage_label)
    stem = f"combined_phase_knob_{stage}_{candidate_id}_fdtd_summary"
    return (
        REPO_ROOT / "outputs/apcd_k6_active_learning" / f"{stem}.csv",
        REPO_ROOT / "reports" / f"{stem}.md",
    )


def normalize_stage_label(stage_label: str) -> str:
    normalized = re.sub(r"[^0-9A-Za-z]+", "_", stage_label.strip()).strip("_").lower()
    if not normalized:
        raise ValueError("stage label must contain at least one alphanumeric character")
    return normalized


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def summarize_raw_result(
    *,
    candidate_id: str,
    raw: dict[str, str],
    result_path: Path,
    coverage_base: Path,
    stage_label: str,
) -> dict[str, object]:
    status = raw.get("status", "")
    t_value = raw.get("t_alpha_star_from_alpha", "")
    if not t_value:
        raise ValueError("Result CSV is missing t_alpha_star_from_alpha")
    phase = phase_deg_from_complex(t_value)
    nearest_bin, nearest_error = nearest_phase_bin(phase, TARGET_BINS_DEG)
    missing_bin, missing_error = nearest_phase_bin(phase, REMAINING_MISSING_BINS_DEG)
    target_conversion = required_float(raw, "target_conversion")
    leakage = required_float(raw, "opposite_spin_leakage")
    ratio = required_float(raw, "conversion_to_leakage_ratio")
    pd = required_float(raw, "PD")
    early = early_pass(target_conversion, leakage, ratio)
    near = near_pass(target_conversion, leakage, ratio, early)
    opens = opens_missing_bin(nearest_bin, early)
    return {
        "candidate_id": candidate_id,
        "stage_label": stage_label,
        "status": status,
        "phase_deg": phase,
        "nearest_target_bin_deg": _number(nearest_bin),
        "phase_error_to_bin_deg": nearest_error,
        "best_remaining_missing_bin_deg": _number(missing_bin),
        "phase_error_to_best_missing_bin_deg": missing_error,
        "target_conversion": target_conversion,
        "opposite_spin_leakage": leakage,
        "conversion_to_leakage_ratio": ratio,
        "PD": pd,
        "early_pass": early,
        "near_pass": near,
        "opens_missing_bin": opens,
        "source_result_csv": relative_path(result_path),
        "source_coverage_csv": relative_path(coverage_base),
        "notes": result_notes(candidate_id, status, early, near, opens),
    }


def phase_deg_from_complex(value: str) -> float:
    return wrap_phase_deg(math.degrees(cmath.phase(complex(value))))


def nearest_phase_bin(phase_deg: float, bins: Sequence[float]) -> tuple[float, float]:
    if not bins:
        raise ValueError("bins must not be empty")
    nearest = min((float(item) for item in bins), key=lambda item: (abs(wrap_phase_deg(phase_deg - item)), item))
    return nearest, abs(wrap_phase_deg(phase_deg - nearest))


def early_pass(target_conversion: float, leakage: float, ratio: float) -> bool:
    return target_conversion >= 0.5 and leakage <= 0.2 and ratio >= 6.0


def near_pass(target_conversion: float, leakage: float, ratio: float, early: bool | None = None) -> bool:
    is_early = early_pass(target_conversion, leakage, ratio) if early is None else early
    return (not is_early) and target_conversion >= 0.5 and leakage <= 0.25 and ratio >= 3.0


def opens_missing_bin(nearest_bin: float, early: bool) -> bool:
    return bool(early and float(nearest_bin) in set(REMAINING_MISSING_BINS_DEG))


def required_float(row: dict[str, str], key: str) -> float:
    value = row.get(key, "")
    if value == "":
        raise ValueError(f"Result CSV is missing {key}")
    return float(value)


def write_csv_rows(rows: Iterable[dict[str, object]], path: Path, fieldnames: Sequence[str]) -> Path:
    row_list = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fieldnames} for row in row_list)
    return path


def write_report(path: Path, row: dict[str, object]) -> Path:
    lines = [
        f"# {row['stage_label']} {row['candidate_id']} FDTD summary",
        "",
        "## Scope",
        "",
        "This is a stage 09 single-dimer lower-transition result summary. It does not run FDTD or call lumapi.",
        "",
        "No stage 10, K=6 phase-ramp supercell, steering claim, K=7, 450 nm/TiO2, Micro-LED integration, or ML claim is made.",
        "",
        "## Metrics",
        "",
        "| candidate | phase deg | nearest bin | best missing bin | target conversion | leakage | ratio | PD | early pass | near pass | opens missing bin |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|",
        (
            f"| `{row['candidate_id']}` | {row['phase_deg']} | {row['nearest_target_bin_deg']} | "
            f"{row['best_remaining_missing_bin_deg']} | {row['target_conversion']} | "
            f"{row['opposite_spin_leakage']} | {row['conversion_to_leakage_ratio']} | {row['PD']} | "
            f"{row['early_pass']} | {row['near_pass']} | {row['opens_missing_bin']} |"
        ),
        "",
        "## Source",
        "",
        f"- raw result CSV inspected locally: `{row['source_result_csv']}`",
        f"- coverage base: `{row['source_coverage_csv']}`",
        "",
        "Do not commit the raw candidate `results.csv`, `summary.md`, `.fsp`, `pre_run` files, `.npy`, or large outputs.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def result_notes(candidate_id: str, status: str, early: bool, near: bool, opens: bool) -> str:
    pieces = [
        "09-P73 lower-transition result ingestion",
        f"status={status}",
        "early-pass" if early else "not early-pass",
        "near-pass" if near else "not near-pass",
        "opens remaining missing bin" if opens else "does not open remaining missing bin",
        "not a steering result",
    ]
    if candidate_id == "cpk_mbin_lower_transition_02":
        pieces.append("lower_transition_02 should only be summarized after user-approved server run")
    return "; ".join(pieces)


def relative_path(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _number(value: float) -> int | float:
    return int(value) if float(value).is_integer() else float(value)


if __name__ == "__main__":
    raise SystemExit(main())
