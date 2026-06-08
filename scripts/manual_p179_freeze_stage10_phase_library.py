from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path
from typing import Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import manual_p164_build_zero_stage_database as p164  # noqa: E402


ACTIVE_DIR = REPO_ROOT / "outputs/apcd_k6_active_learning"
CONFIG_DIR = REPO_ROOT / "configs/apcd_k6_phase_state_candidates"
RESULT_ROOT = REPO_ROOT / "outputs/apcd_k6_metagrating_633nm/phase_state_candidates"

STAGE09_COVERAGE_CSV = ACTIVE_DIR / "stage09_phase_state_coverage_after_p178.csv"
LATEST_SOURCE_CSV = ACTIVE_DIR / "combined_phase_knob_phase_state_coverage_p139.csv"
PHASE_COVERAGE_CSV = ACTIVE_DIR / "phase_coverage_v8.csv"
P178_REPORT_MD = REPO_ROOT / "reports/p178_zero_bin_opened_final_decision.md"

FROZEN_LIBRARY_CSV = ACTIVE_DIR / "p179_stage10_frozen_phase_library.csv"
SANITY_CSV = ACTIVE_DIR / "p179_stage10_phase_library_sanity.csv"
REPORT_MD = REPO_ROOT / "reports/p179_stage10_phase_library_freeze.md"

REQUIRED_BINS = [-180, -120, -60, 0, 60, 120]
ZERO_ANCHOR = "cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01"

OFFICIAL_ANCHORS = {
    -180: "cpk_resphase_scale104_nohelper_01",
    -120: "cpk_060_anchor_wh03_h425_scale98_01",
    -60: "cpk_060_boundary_h435_aniso_reduce10_01",
    0: ZERO_ANCHOR,
    60: "aggr_lhs_retention_dy_05",
    120: "cpk_rot_release_02",
}

OFFICIAL_SOURCE_FILES = [
    LATEST_SOURCE_CSV,
    ACTIVE_DIR / "aggressive_phase_gap_top2_fdtd_results_v1.csv",
    ACTIVE_DIR / "accumulated_fdtd_diagnosis_v5.csv",
    ACTIVE_DIR / "p177_h232_zero_coupled_results.csv",
]

FROZEN_FIELDS = [
    "bin_deg",
    "candidate_id",
    "phase_deg",
    "phase_error_to_bin",
    "target_conversion",
    "opposite_spin_leakage",
    "conversion_to_leakage_ratio",
    "early_pass",
    "role",
    "config_path",
    "results_csv",
]

SANITY_FIELDS = ["check", "status", "details"]

NO_OVERCLAIM = (
    "This is a Stage 10 input freeze of the Stage 09 single-dimer phase-state library only; "
    "it is not K=6 steering yet, not a K=6 phase-ramp supercell, not a +15 deg beam deflection result, "
    "and not a Micro-LED result."
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Freeze the official six-state APCD phase library for Stage 10 input."
    )
    parser.add_argument("--coverage-csv", type=Path, default=STAGE09_COVERAGE_CSV)
    parser.add_argument("--source-csv", type=Path, default=LATEST_SOURCE_CSV)
    parser.add_argument("--phase-coverage-csv", type=Path, default=PHASE_COVERAGE_CSV)
    parser.add_argument("--p178-report", type=Path, default=P178_REPORT_MD)
    parser.add_argument("--output-csv", type=Path, default=FROZEN_LIBRARY_CSV)
    parser.add_argument("--sanity-csv", type=Path, default=SANITY_CSV)
    parser.add_argument("--report", type=Path, default=REPORT_MD)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    source_paths = unique_existing_sources(
        [args.source_csv, args.phase_coverage_csv, *OFFICIAL_SOURCE_FILES]
    )
    coverage_rows = read_csv_rows(args.coverage_csv)
    source_rows = collect_source_rows(source_paths)
    library_rows = build_frozen_library(source_rows, args.p178_report)
    sanity_rows = build_sanity_rows(library_rows, coverage_rows, source_paths)

    write_csv_rows(library_rows, args.output_csv, FROZEN_FIELDS)
    write_csv_rows(sanity_rows, args.sanity_csv, SANITY_FIELDS)
    write_report(args.report, library_rows, sanity_rows, source_paths, args)

    print(f"frozen_library_csv={args.output_csv}")
    print(f"sanity_csv={args.sanity_csv}")
    print(f"report={args.report}")
    print("status=stage10_phase_library_frozen_no_fdtd_no_lumapi")
    return 0


def unique_existing_sources(paths: Sequence[Path]) -> list[Path]:
    seen: set[Path] = set()
    sources: list[Path] = []
    for path in paths:
        resolved = path.resolve()
        if resolved in seen or not path.exists():
            continue
        seen.add(resolved)
        sources.append(path)
    return sources


def collect_source_rows(source_paths: Sequence[Path]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for path in source_paths:
        for row in read_csv_rows(path):
            row["_source_csv"] = relative_path(path)
            rows.append(row)
    return rows


def build_frozen_library(source_rows: Sequence[dict[str, str]], p178_report: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for bin_deg in REQUIRED_BINS:
        candidate_id = OFFICIAL_ANCHORS[bin_deg]
        if candidate_id == ZERO_ANCHOR:
            rows.append(build_p178_zero_anchor_row(bin_deg, p178_report))
            continue
        source = find_candidate_row(source_rows, candidate_id)
        rows.append(normalize_source_row(bin_deg, source))
    return rows


def find_candidate_row(source_rows: Sequence[dict[str, str]], candidate_id: str) -> dict[str, str]:
    matches = [row for row in source_rows if row.get("candidate_id") == candidate_id]
    if not matches:
        raise ValueError(f"Missing source CSV row for official anchor {candidate_id}")
    early_matches = [row for row in matches if parse_bool(row.get("early_pass")) or parse_bool(row.get("overall_early_pass"))]
    return early_matches[0] if early_matches else matches[0]


def normalize_source_row(bin_deg: int, row: dict[str, str]) -> dict[str, object]:
    candidate_id = required_value(row, "candidate_id")
    phase = float(required_value(row, "phase_deg"))
    phase_error = abs(p164.wrap_phase_deg(phase - bin_deg))
    early = parse_bool(row.get("early_pass")) or parse_bool(row.get("overall_early_pass"))
    return {
        "bin_deg": bin_deg,
        "candidate_id": candidate_id,
        "phase_deg": phase,
        "phase_error_to_bin": phase_error,
        "target_conversion": required_value(row, "target_conversion"),
        "opposite_spin_leakage": required_value(row, "opposite_spin_leakage"),
        "conversion_to_leakage_ratio": required_value(row, "conversion_to_leakage_ratio"),
        "early_pass": early,
        "role": role_from_row(bin_deg, row),
        "config_path": relative_path(CONFIG_DIR / f"{candidate_id}.yaml"),
        "results_csv": source_csv_for_row(row),
    }


def build_p178_zero_anchor_row(bin_deg: int, p178_report: Path) -> dict[str, object]:
    text = p178_report.read_text(encoding="utf-8")
    if ZERO_ANCHOR not in text:
        raise ValueError(f"{ZERO_ANCHOR} is not present in {relative_path(p178_report)}")
    metrics = parse_p178_zero_metrics(text)
    return {
        "bin_deg": bin_deg,
        "candidate_id": ZERO_ANCHOR,
        "phase_deg": metrics["phase_deg"],
        "phase_error_to_bin": abs(p164.wrap_phase_deg(metrics["phase_deg"] - bin_deg)),
        "target_conversion": metrics["target_conversion"],
        "opposite_spin_leakage": metrics["opposite_spin_leakage"],
        "conversion_to_leakage_ratio": metrics["conversion_to_leakage_ratio"],
        "early_pass": True,
        "role": "P178 recommended 0 deg anchor from official zero-bin opening report; local raw results.csv is not committed",
        "config_path": relative_path(CONFIG_DIR / f"{ZERO_ANCHOR}.yaml"),
        "results_csv": relative_path(p178_report),
    }


def parse_p178_zero_metrics(text: str) -> dict[str, float]:
    patterns = {
        "phase_deg": r"phase:\s+about\s+([-+0-9.]+)\s+deg",
        "target_conversion": r"target conversion:\s+about\s+([-+0-9.]+)",
        "opposite_spin_leakage": r"opposite-spin leakage:\s+about\s+([-+0-9.]+)",
        "conversion_to_leakage_ratio": r"conversion-to-leakage ratio:\s+about\s+([-+0-9.]+)",
    }
    metrics: dict[str, float] = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text)
        if not match:
            raise ValueError(f"Could not parse {key} from P178 report")
        metrics[key] = float(match.group(1))
    return metrics


def role_from_row(bin_deg: int, row: dict[str, str]) -> str:
    role = (row.get("role") or row.get("notes") or "").strip()
    if role:
        return role
    source = row.get("_source_csv", "")
    return f"official Stage 09 early-pass anchor for {bin_deg} deg from {source}"


def source_csv_for_row(row: dict[str, str]) -> str:
    source_file = (row.get("source_file") or "").strip()
    if source_file:
        return relative_path(ACTIVE_DIR / source_file)
    return row.get("_source_csv", "")


def build_sanity_rows(
    library_rows: Sequence[dict[str, object]],
    coverage_rows: Sequence[dict[str, str]],
    source_paths: Sequence[Path],
) -> list[dict[str, object]]:
    bins = [int(float(row["bin_deg"])) for row in library_rows]
    coverage_bins = [int(float(row["phase_bin_deg"])) for row in coverage_rows]
    selected = [str(row["candidate_id"]) for row in library_rows]
    missing_bins = [bin_deg for bin_deg in REQUIRED_BINS if bin_deg not in bins]
    duplicate_bins = sorted({bin_deg for bin_deg in bins if bins.count(bin_deg) > 1})
    coverage_missing = [bin_deg for bin_deg in REQUIRED_BINS if bin_deg not in coverage_bins]
    not_covered = [
        int(float(row["phase_bin_deg"]))
        for row in coverage_rows
        if (row.get("coverage_status") or "").lower() != "covered"
    ]
    not_early = [str(row["candidate_id"]) for row in library_rows if not parse_bool(row.get("early_pass"))]

    return [
        sanity_row("exact_six_bins", bins == REQUIRED_BINS, format_list(bins)),
        sanity_row("coverage_csv_exact_bins", coverage_bins == REQUIRED_BINS, format_list(coverage_bins)),
        sanity_row("coverage_csv_all_covered", not not_covered, format_list(not_covered)),
        sanity_row("one_selected_anchor_per_bin", len(selected) == len(set(selected)) == 6 and not duplicate_bins, format_list(selected)),
        sanity_row("selected_anchors_early_pass", not not_early, format_list(not_early)),
        sanity_row("zero_anchor_is_recommended", selected[3] == ZERO_ANCHOR, selected[3]),
        sanity_row("missing_bins", missing_bins == [] and coverage_missing == [], format_list(missing_bins)),
        sanity_row("no_overclaim_wording", "not K=6 steering yet" in NO_OVERCLAIM, NO_OVERCLAIM),
        sanity_row("source_csvs_read", bool(source_paths), format_list(relative_path(path) for path in source_paths)),
    ]


def sanity_row(check: str, ok: bool, details: object) -> dict[str, object]:
    return {"check": check, "status": "pass" if ok else "fail", "details": details}


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


def write_report(
    path: Path,
    library_rows: Sequence[dict[str, object]],
    sanity_rows: Sequence[dict[str, object]],
    source_paths: Sequence[Path],
    args: argparse.Namespace,
) -> Path:
    lines = [
        "# P179 Stage 10 phase-library freeze",
        "",
        "## Scope",
        "",
        NO_OVERCLAIM,
        "",
        "The table freezes one official single-dimer phase-state anchor per bin for Stage 10 input preparation.",
        "This script reads existing CSV/report evidence only and does not run FDTD, call lumapi, or edit `configs/runtime.yaml`.",
        "",
        "## Inputs",
        "",
        f"- compact Stage 09 coverage CSV: `{relative_path(args.coverage_csv)}`",
        f"- latest row-level source CSV: `{relative_path(args.source_csv)}`",
        f"- phase-coverage source CSV: `{relative_path(args.phase_coverage_csv)}`",
        f"- P178 official zero-bin report: `{relative_path(args.p178_report)}`",
    ]
    lines.extend(f"- source read: `{relative_path(path)}`" for path in source_paths)
    lines.extend(
        [
            "",
            "## Frozen Library",
            "",
            "| bin_deg | candidate_id | phase_deg | phase_error_to_bin | target_conversion | leakage | ratio | early_pass |",
            "| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |",
        ]
    )
    for row in library_rows:
        lines.append(
            "| {bin_deg} | `{candidate_id}` | {phase_deg} | {phase_error_to_bin} | {target_conversion} | "
            "{opposite_spin_leakage} | {conversion_to_leakage_ratio} | {early_pass} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Sanity",
            "",
            "| check | status | details |",
            "| --- | --- | --- |",
        ]
    )
    lines.extend(f"| {row['check']} | {row['status']} | {row['details']} |" for row in sanity_rows)
    lines.extend(
        [
            "",
            "## Outputs",
            "",
            f"- frozen library: `{relative_path(args.output_csv)}`",
            f"- sanity CSV: `{relative_path(args.sanity_csv)}`",
            "",
            "## Next Step",
            "",
            "Use this frozen single-dimer table as Stage 10 input only after preserving the no-overclaim boundary above.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def required_value(row: dict[str, str], key: str) -> str:
    value = (row.get(key) or "").strip()
    if not value:
        raise ValueError(f"Missing required {key} for {row.get('candidate_id', '<unknown>')}")
    return value


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"true", "1", "yes", "pass"}


def format_list(values: Iterable[object]) -> str:
    return "[" + ", ".join(str(value) for value in values) + "]"


def relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
