from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
ACTIVE_DIR = REPO_ROOT / "outputs/apcd_k6_active_learning"

P179_LIBRARY_CSV = ACTIVE_DIR / "p179_stage10_frozen_phase_library.csv"
PLAN_CSV = ACTIVE_DIR / "p180_k6_phase_ramp_supercell_plan.csv"
SANITY_CSV = ACTIVE_DIR / "p180_k6_phase_ramp_sanity.csv"
REPORT_MD = REPO_ROOT / "reports/p180_k6_phase_ramp_supercell_plan.md"

WAVELENGTH_NM = 633.0
TARGET_ANGLE_DEG = 15.0
K = 6
EXPECTED_PHASE_STEP_DEG = 360.0 / K
REQUIRED_BINS = [-180, -120, -60, 0, 60, 120]
PHASE_RAMP_ORDER = [0, 60, 120, -180, -120, -60]

PLAN_FIELDS = [
    "supercell_index",
    "target_bin_deg",
    "candidate_id",
    "phase_deg",
    "phase_error_to_bin",
    "target_conversion",
    "opposite_spin_leakage",
    "conversion_to_leakage_ratio",
    "dimer_center_x_nm",
    "dimer_pitch_nm",
    "cumulative_target_phase_deg",
    "config_path",
]

SANITY_FIELDS = [
    "K",
    "wavelength_nm",
    "target_angle_deg",
    "supercell_period_nm",
    "dimer_pitch_nm",
    "expected_phase_step_deg",
    "phase_bins_complete",
    "all_anchors_early_pass",
    "max_phase_error_deg",
    "no_steering_claim",
]

NO_OVERCLAIM = (
    "This is a Stage 10 K=6 design plan only. No K=6 FDTD has been run. "
    "No +15 deg steering has been verified yet. The result is a supercell assembly input for later FDTD. "
    "It is not a Micro-LED result."
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate the P180 K=6 phase-ramp supercell assembly plan from the P179 frozen phase library."
    )
    parser.add_argument("--library-csv", type=Path, default=P179_LIBRARY_CSV)
    parser.add_argument("--plan-csv", type=Path, default=PLAN_CSV)
    parser.add_argument("--sanity-csv", type=Path, default=SANITY_CSV)
    parser.add_argument("--report", type=Path, default=REPORT_MD)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    library_rows = read_phase_library(args.library_csv)
    plan_rows = build_phase_ramp_plan(library_rows)
    sanity_rows = [build_sanity_row(library_rows, plan_rows)]

    write_csv_rows(plan_rows, args.plan_csv, PLAN_FIELDS)
    write_csv_rows(sanity_rows, args.sanity_csv, SANITY_FIELDS)
    write_report(args.report, args.library_csv, args.plan_csv, args.sanity_csv, plan_rows, sanity_rows[0])

    print(f"plan_csv={args.plan_csv}")
    print(f"sanity_csv={args.sanity_csv}")
    print(f"report={args.report}")
    print("status=stage10_k6_phase_ramp_plan_built_no_fdtd_no_lumapi")
    return 0


def read_phase_library(path: Path) -> list[dict[str, str]]:
    rows = read_csv_rows(path)
    bins = sorted(int(float(row["bin_deg"])) for row in rows)
    if bins != REQUIRED_BINS:
        raise ValueError(f"P179 library must contain exactly {REQUIRED_BINS}; got {bins}")
    return rows


def build_phase_ramp_plan(library_rows: Sequence[dict[str, str]]) -> list[dict[str, object]]:
    rows_by_bin = {int(float(row["bin_deg"])): row for row in library_rows}
    supercell_period = supercell_period_nm()
    dimer_pitch = supercell_period / K
    plan_rows: list[dict[str, object]] = []

    for index, target_bin in enumerate(PHASE_RAMP_ORDER):
        anchor = rows_by_bin[target_bin]
        cumulative_phase = index * EXPECTED_PHASE_STEP_DEG
        plan_rows.append(
            {
                "supercell_index": index,
                "target_bin_deg": target_bin,
                "candidate_id": anchor["candidate_id"],
                "phase_deg": anchor["phase_deg"],
                "phase_error_to_bin": anchor["phase_error_to_bin"],
                "target_conversion": anchor["target_conversion"],
                "opposite_spin_leakage": anchor["opposite_spin_leakage"],
                "conversion_to_leakage_ratio": anchor["conversion_to_leakage_ratio"],
                "dimer_center_x_nm": (index + 0.5) * dimer_pitch,
                "dimer_pitch_nm": dimer_pitch,
                "cumulative_target_phase_deg": cumulative_phase,
                "config_path": anchor["config_path"],
            }
        )
    return plan_rows


def build_sanity_row(library_rows: Sequence[dict[str, str]], plan_rows: Sequence[dict[str, object]]) -> dict[str, object]:
    bins = sorted(int(float(row["bin_deg"])) for row in library_rows)
    phase_bins_complete = bins == REQUIRED_BINS and len(plan_rows) == K
    all_anchors_early_pass = all(parse_bool(row.get("early_pass")) for row in library_rows)
    max_phase_error = max(float(row["phase_error_to_bin"]) for row in plan_rows)
    return {
        "K": K,
        "wavelength_nm": WAVELENGTH_NM,
        "target_angle_deg": TARGET_ANGLE_DEG,
        "supercell_period_nm": supercell_period_nm(),
        "dimer_pitch_nm": supercell_period_nm() / K,
        "expected_phase_step_deg": EXPECTED_PHASE_STEP_DEG,
        "phase_bins_complete": phase_bins_complete,
        "all_anchors_early_pass": all_anchors_early_pass,
        "max_phase_error_deg": max_phase_error,
        "no_steering_claim": True,
    }


def supercell_period_nm() -> float:
    return WAVELENGTH_NM / math.sin(math.radians(TARGET_ANGLE_DEG))


def write_report(
    path: Path,
    library_csv: Path,
    plan_csv: Path,
    sanity_csv: Path,
    plan_rows: Sequence[dict[str, object]],
    sanity: dict[str, object],
) -> Path:
    lines = [
        "# P180 K=6 phase-ramp supercell plan",
        "",
        "## Scope",
        "",
        NO_OVERCLAIM,
        "",
        "`K` means six dimers in the supercell. The target angle is used only to size the design-period input.",
        "",
        "## Inputs",
        "",
        f"- frozen P179 single-dimer phase library: `{relative_path(library_csv)}`",
        f"- wavelength: {WAVELENGTH_NM:g} nm",
        f"- target design angle: +{TARGET_ANGLE_DEG:g} deg",
        f"- K: {K} dimers",
        f"- supercell period target Lambda = wavelength / sin(15 deg) = {sanity['supercell_period_nm']} nm",
        f"- dimer pitch = Lambda / K = {sanity['dimer_pitch_nm']} nm",
        "",
        "## Phase Ramp",
        "",
        "The selected wrapped phase-bin order is `0, 60, 120, -180, -120, -60`, representing a 60 deg step ramp.",
        "",
        "| index | target_bin_deg | candidate_id | center_x_nm | cumulative_target_phase_deg |",
        "| ---: | ---: | --- | ---: | ---: |",
    ]
    for row in plan_rows:
        lines.append(
            "| {supercell_index} | {target_bin_deg} | `{candidate_id}` | {dimer_center_x_nm} | "
            "{cumulative_target_phase_deg} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Sanity",
            "",
            f"- K: {sanity['K']}",
            f"- phase bins complete: {sanity['phase_bins_complete']}",
            f"- all anchors early-pass: {sanity['all_anchors_early_pass']}",
            f"- expected phase step: {sanity['expected_phase_step_deg']} deg",
            f"- max phase error: {sanity['max_phase_error_deg']} deg",
            f"- no steering claim: {sanity['no_steering_claim']}",
            "",
            "## Outputs",
            "",
            f"- plan CSV: `{relative_path(plan_csv)}`",
            f"- sanity CSV: `{relative_path(sanity_csv)}`",
            "",
            "## Boundary",
            "",
            "This plan should be treated as an assembly input for a later K=6 FDTD run, not as optical validation.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv_rows(rows: Iterable[dict[str, object]], path: Path, fieldnames: Sequence[str]) -> Path:
    row_list = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fieldnames} for row in row_list)
    return path


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"true", "1", "yes", "pass"}


def relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
