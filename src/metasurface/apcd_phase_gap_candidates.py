from __future__ import annotations

import cmath
import csv
import math
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence

from metasurface.apcd_active_learning import DEFAULT_BASELINE, validate_candidate_bounds, wrap_phase_deg
from metasurface.apcd_candidate_validation import validate_candidate_geometry


BASELINE_PHASE_DEG = 111.31665091018952
EARLY_TARGET_CONVERSION_MIN = 0.5
EARLY_OPPOSITE_SPIN_LEAKAGE_MAX = 0.2
EARLY_CONVERSION_TO_LEAKAGE_RATIO_MIN = 6.0

DATASET_NOTES = (
    "09-P13 dataset v1 summary-only row; no new FDTD; no training; not steering result"
)

PHASE_COVERAGE_FIELDS = [
    "phase_bin_deg",
    "nearest_candidate_all",
    "nearest_phase_all",
    "nearest_error_all",
    "nearest_candidate_early_pass",
    "nearest_phase_early_pass",
    "nearest_error_early_pass",
    "bin_status",
    "notes",
]

PHASE_GAP_CANDIDATE_FIELDS = [
    "candidate_id",
    "candidate_family",
    "source_reference",
    "design_intent",
    "p1_length_nm",
    "p1_width_nm",
    "p2_length_nm",
    "p2_width_nm",
    "p1_frac_x",
    "p1_frac_y",
    "p2_frac_x",
    "p2_frac_y",
    "internal_dx_nm",
    "internal_dy_nm",
    "p1_rotation_deg",
    "p2_rotation_deg",
    "period_x_nm",
    "period_y_nm",
    "height_nm",
    "material",
    "substrate",
    "intended_phase_region",
    "expected_risk",
    "requires_geometry_validation",
    "requires_fdtd",
    "status",
    "notes",
]

PHASE_GAP_VALIDATION_FIELDS = [
    "candidate_id",
    "candidate_family",
    "same_cell_min_gap_nm",
    "periodic_image_min_gap_nm",
    "minimum_gap_nm_threshold",
    "bounds_pass",
    "same_cell_gap_pass",
    "periodic_gap_pass",
    "beta_selective_geometry_pass",
    "rotation_policy_pass",
    "duplicate_geometry_pass",
    "overall_geometry_pass",
    "recommended_for_fdtd",
    "notes",
]

PHASE_GAP_SELECTION_FIELDS = [
    "selection_rank",
    "candidate_id",
    "candidate_family",
    "source_reference",
    "selection_reason",
    "expected_risk",
    "intended_phase_region",
    "p1_length_nm",
    "p1_width_nm",
    "p2_length_nm",
    "p2_width_nm",
    "internal_dx_nm",
    "internal_dy_nm",
    "p1_rotation_deg",
    "p2_rotation_deg",
    "geometry_pass",
    "recommended_for_fdtd",
    "requires_fdtd",
    "status",
    "notes",
]

SELECTED_PHASE_GAP_IDS = [
    "gap_bridge_03",
    "gap_lhs_leakred_06",
    "gap_p2w_trim_03",
]

SELECTION_REASONS = {
    "gap_bridge_03": (
        "Conservative bridge from p1w_dx usable anchors: keeps p1/p2 close to the low-leakage region "
        "while adding modest lhs-like dy displacement."
    ),
    "gap_lhs_leakred_06": (
        "Leakage-reduced lhs-like probe: keeps doe_lhs_like_01 as phase-coverage evidence but pulls "
        "lengths, widths, and displacement toward lower-risk geometry."
    ),
    "gap_p2w_trim_03": (
        "Backup p2-width trim around the bridge region; selected_not_run for later leakage-risk comparison."
    ),
}


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_csv_fieldnames(path: str | Path) -> list[str]:
    with Path(path).open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return list(reader.fieldnames or [])


def write_csv_rows(rows: Iterable[dict[str, object]], path: str | Path, fieldnames: Sequence[str]) -> Path:
    row_list = list(rows)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fieldnames} for row in row_list)
    return output_path


def parse_complex_text(value: str) -> complex:
    return complex(str(value).strip())


def overall_early_pass(
    target_conversion: float,
    opposite_spin_leakage: float,
    conversion_to_leakage_ratio: float,
) -> bool:
    return (
        float(target_conversion) >= EARLY_TARGET_CONVERSION_MIN
        and float(opposite_spin_leakage) <= EARLY_OPPOSITE_SPIN_LEAKAGE_MAX
        and float(conversion_to_leakage_ratio) >= EARLY_CONVERSION_TO_LEAKAGE_RATIO_MIN
    )


def build_geometry_lookup(pool_paths: Iterable[str | Path]) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for pool_path in pool_paths:
        path = Path(pool_path)
        if not path.exists():
            continue
        for row in read_csv_rows(path):
            candidate_id = row.get("candidate_id") or row.get("variant_id")
            if candidate_id:
                lookup[str(candidate_id)] = row
    return lookup


def build_ml_dataset_v1(
    v0_rows: Iterable[dict[str, str]],
    summary_paths: Iterable[str | Path],
    geometry_lookup: dict[str, dict[str, str]],
    columns: Sequence[str],
) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = [dict(row) for row in v0_rows]
    existing_ids = {str(row["variant_id"]) for row in rows}
    for summary_path in summary_paths:
        path = Path(summary_path)
        for summary in read_csv_rows(path):
            candidate_id = str(summary["candidate_id"])
            if candidate_id in existing_ids:
                continue
            rows.append(_dataset_row_from_summary(summary, geometry_lookup.get(candidate_id), path, columns))
            existing_ids.add(candidate_id)
    return [{column: row.get(column, "") for column in columns} for row in rows]


def write_ml_dataset_v1_report(path: str | Path, rows: Sequence[dict[str, object]]) -> Path:
    phases = [float(row["phase_deg"]) for row in rows if row.get("phase_deg") not in {"", None}]
    early = [row for row in rows if is_true(row.get("overall_early_pass"))]
    missing_geometry = [str(row["variant_id"]) for row in rows if "missing_geometry" in str(row.get("notes", ""))]
    usable = [str(row["variant_id"]) for row in early]
    lines = [
        "# APCD K=6 ML-Ready Dataset v1 Update Report",
        "",
        "Scope: 09-P13 dataset update only. No new FDTD was run. No lumapi call was made. No model was trained. This is not a steering result.",
        "",
        f"Dataset v1 rows: {len(rows)}",
        f"Phase range deg: {_range_text(phases)}",
        f"Early-pass count: {len(early)}",
        f"Usable candidates by early-pass rule: {', '.join(usable)}",
        f"Missing geometry rows: {', '.join(missing_geometry) if missing_geometry else 'none'}",
        "",
        "New summary-only rows added after v0:",
        "",
        "- `doe_p1w_p2w_02`",
        "- `doe_p1w_dx_01`",
        "- `doe_lhs_like_01`",
        "- `nhood_p1w_dx_05`",
        "- `nhood_p1w_dx_02`",
        "- `fine_p1w_dx_08`",
        "- `fine_p1w_dx_03`",
        "",
        "The dataset still remains small-data plumbing. It is not reliable enough for model training claims.",
    ]
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def analyze_phase_coverage(
    dataset_rows: Sequence[dict[str, object]],
    phase_targets: Sequence[float],
) -> list[dict[str, object]]:
    coverage_rows = []
    for target in phase_targets:
        nearest_all = _nearest_phase_row(dataset_rows, float(target))
        early_rows = [row for row in dataset_rows if is_true(row.get("overall_early_pass"))]
        nearest_early = _nearest_phase_row(early_rows, float(target))
        status = _bin_status(nearest_all, nearest_early)
        coverage_rows.append(
            {
                "phase_bin_deg": float(target),
                "nearest_candidate_all": nearest_all.get("variant_id", ""),
                "nearest_phase_all": nearest_all.get("phase_deg", ""),
                "nearest_error_all": nearest_all.get("phase_error_deg", ""),
                "nearest_candidate_early_pass": nearest_early.get("variant_id", ""),
                "nearest_phase_early_pass": nearest_early.get("phase_deg", ""),
                "nearest_error_early_pass": nearest_early.get("phase_error_deg", ""),
                "bin_status": status,
                "notes": _bin_notes(float(target), status),
            }
        )
    return coverage_rows


def write_phase_gap_analysis(path: str | Path, dataset_rows: Sequence[dict[str, object]], coverage_rows: Sequence[dict[str, object]]) -> Path:
    phases = [float(row["phase_deg"]) for row in dataset_rows]
    early_rows = [row for row in dataset_rows if is_true(row.get("overall_early_pass"))]
    early_phases = [float(row["phase_deg"]) for row in early_rows]
    usable = [str(row["variant_id"]) for row in early_rows]
    missing_bins = [str(row["phase_bin_deg"]) for row in coverage_rows if row["bin_status"] == "missing"]
    lines = [
        "# APCD K=6 Phase Coverage and Gap Analysis v1",
        "",
        "Scope: 09-P14 analysis only. No FDTD was run. No lumapi call was made. No model was trained. This is not a steering result.",
        "",
        f"All sample phase range deg: {_range_text(phases)}",
        f"Early-pass sample phase range deg: {_range_text(early_phases)}",
        f"Early-pass usable candidates: {', '.join(usable)}",
        "",
        "The new fine candidates have pushed usable phase coverage into the 98-99 deg region.",
        "However, the K=6 phase-state library is still incomplete: 0, 60, -60, -120, and -180 deg bins are not covered by early-pass candidates.",
        "The 60 deg bin currently has phase evidence from `doe_lhs_like_01`, but that row has high leakage and cannot be used directly as a phase state.",
        "",
        "Per-bin coverage:",
        "",
        "| bin deg | nearest all | error all | nearest early-pass | error early-pass | status |",
        "|---:|---|---:|---|---:|---|",
        *[
            f"| {row['phase_bin_deg']} | {row['nearest_candidate_all']} | {row['nearest_error_all']} | "
            f"{row['nearest_candidate_early_pass']} | {row['nearest_error_early_pass']} | {row['bin_status']} |"
            for row in coverage_rows
        ],
        "",
        f"Missing bins: {', '.join(missing_bins) if missing_bins else 'none'}",
        "",
        "This is not a +15 deg steering proof and does not justify K=7 or phase-ramp supercell assembly.",
    ]
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def read_phase_targets(path: str | Path) -> list[float]:
    rows = read_csv_rows(path)
    return [float(row.get("phase_target_deg", row.get("phase_bin_deg", 0.0))) for row in rows]


def build_phase_gap_candidate_pool() -> list[dict[str, object]]:
    specs = [
        ("gap_lhs_leakred_01", "gap_60_90_lhs_leakage_reduced", "doe_lhs_like_01", 120, 56, 80, 140, -36, 10, "moderate_leakage_risk"),
        ("gap_lhs_leakred_02", "gap_60_90_lhs_leakage_reduced", "doe_lhs_like_01", 120, 58, 80, 145, -36, 10, "moderate_leakage_risk"),
        ("gap_lhs_leakred_03", "gap_60_90_lhs_leakage_reduced", "doe_lhs_like_01", 125, 56, 80, 140, -38, 10, "moderate_leakage_risk"),
        ("gap_lhs_leakred_04", "gap_60_90_lhs_leakage_reduced", "doe_lhs_like_01", 125, 58, 80, 145, -38, 15, "moderate_to_high_leakage_risk"),
        ("gap_lhs_leakred_05", "gap_60_90_lhs_leakage_reduced", "doe_lhs_like_01", 125, 60, 85, 145, -34, 10, "moderate_leakage_risk"),
        ("gap_lhs_leakred_06", "gap_60_90_lhs_leakage_reduced", "doe_lhs_like_01", 130, 58, 85, 145, -36, 10, "moderate_leakage_risk"),
        ("gap_lhs_leakred_07", "gap_60_90_lhs_leakage_reduced", "doe_lhs_like_01", 130, 60, 85, 140, -34, 15, "moderate_to_high_leakage_risk"),
        ("gap_lhs_leakred_08", "gap_60_90_lhs_leakage_reduced", "doe_lhs_like_01", 120, 60, 85, 150, -34, 20, "moderate_to_high_leakage_risk"),
        ("gap_bridge_01", "gap_60_90_bridge_from_p1w_dx", "fine_p1w_dx_08|doe_lhs_like_01", 130, 56, 85, 150, -36, 5, "low_to_moderate_leakage_risk"),
        ("gap_bridge_02", "gap_60_90_bridge_from_p1w_dx", "fine_p1w_dx_03|doe_lhs_like_01", 130, 57, 85, 150, -36, 5, "low_to_moderate_leakage_risk"),
        ("gap_bridge_03", "gap_60_90_bridge_from_p1w_dx", "fine_p1w_dx_08|doe_lhs_like_01", 130, 56, 85, 145, -36, 5, "low_to_moderate_leakage_risk"),
        ("gap_bridge_04", "gap_60_90_bridge_from_p1w_dx", "fine_p1w_dx_03|doe_lhs_like_01", 125, 56, 85, 145, -36, 5, "moderate_leakage_risk"),
        ("gap_bridge_05", "gap_60_90_bridge_from_p1w_dx", "fine_p1w_dx_08|doe_lhs_like_01", 125, 58, 85, 145, -38, 10, "moderate_leakage_risk"),
        ("gap_bridge_06", "gap_60_90_bridge_from_p1w_dx", "fine_p1w_dx_03|doe_lhs_like_01", 130, 55, 85, 145, -38, 10, "moderate_to_high_leakage_risk"),
        ("gap_p1w_dx_ext_01", "gap_60_90_p1w_dx_extended", "fine_p1w_dx_03", 130, 55, 85, 150, -36, 0, "moderate_leakage_risk"),
        ("gap_p1w_dx_ext_02", "gap_60_90_p1w_dx_extended", "fine_p1w_dx_08", 125, 56, 85, 150, -36, 0, "moderate_leakage_risk"),
        ("gap_p1w_dx_ext_03", "gap_60_90_p1w_dx_extended", "fine_p1w_dx_03", 125, 55, 85, 150, -38, 5, "moderate_to_high_leakage_risk"),
        ("gap_p1w_dx_ext_04", "gap_60_90_p1w_dx_extended", "fine_p1w_dx_08", 120, 56, 85, 150, -36, 5, "moderate_to_high_leakage_risk"),
        ("gap_p2w_trim_01", "gap_60_90_p2w_trim", "fine_p1w_dx_08|p2W_p10", 130, 57, 85, 140, -34, 5, "moderate_leakage_risk"),
        ("gap_p2w_trim_02", "gap_60_90_p2w_trim", "fine_p1w_dx_03|p2W_p10", 130, 56, 85, 140, -34, 5, "moderate_leakage_risk"),
        ("gap_p2w_trim_03", "gap_60_90_p2w_trim", "fine_p1w_dx_08|p2W_p10", 125, 57, 85, 140, -36, 10, "moderate_leakage_risk"),
        ("gap_p2w_trim_04", "gap_60_90_p2w_trim", "fine_p1w_dx_03|p2W_p10", 125, 56, 85, 135, -36, 10, "moderate_to_high_leakage_risk"),
        ("gap_p2w_trim_05", "gap_60_90_p2w_trim", "fine_p1w_dx_08|p2W_p10", 120, 58, 85, 140, -38, 15, "moderate_to_high_leakage_risk"),
        ("gap_p2w_trim_06", "gap_60_90_p2w_trim", "fine_p1w_dx_03|p2W_p10", 120, 56, 85, 135, -38, 15, "moderate_to_high_leakage_risk"),
    ]
    candidates = [
        _candidate_row(
            candidate_id=candidate_id,
            candidate_family=family,
            source_reference=source,
            p1_length_nm=p1_length,
            p1_width_nm=p1_width,
            p2_length_nm=p2_length,
            p2_width_nm=p2_width,
            internal_dx_nm=internal_dx,
            internal_dy_nm=internal_dy,
            expected_risk=risk,
        )
        for candidate_id, family, source, p1_length, p1_width, p2_length, p2_width, internal_dx, internal_dy, risk in specs
    ]
    _validate_phase_gap_candidate_policy(candidates)
    return candidates


def validate_phase_gap_candidate_pool(
    candidates: Iterable[dict[str, object]],
    existing_candidates: Iterable[dict[str, object]] = (),
    minimum_gap_nm: float = 5.0,
) -> list[dict[str, object]]:
    existing_keys = {_geometry_key(row) for row in existing_candidates}
    seen: set[tuple[float, float, float, float, float, float]] = set()
    rows = []
    for candidate in candidates:
        key = _geometry_key(candidate)
        duplicate_pass = key not in existing_keys and key not in seen
        row = validate_candidate_geometry(candidate, minimum_gap_nm=minimum_gap_nm)
        base_notes = [] if row["notes"] == "geometry sanity validation passed; optical response still unknown" else [str(row["notes"])]
        row["duplicate_geometry_pass"] = duplicate_pass
        row["overall_geometry_pass"] = bool(row["overall_geometry_pass"] and duplicate_pass)
        row["recommended_for_fdtd"] = row["overall_geometry_pass"]
        if not duplicate_pass:
            base_notes.append("duplicates an existing geometry")
        if not base_notes:
            base_notes.append("geometry sanity validation passed; duplicate check passed; optical response still unknown")
        row["notes"] = "; ".join(base_notes)
        rows.append(row)
        seen.add(key)
    return rows


def select_phase_gap_fdtd_candidates(
    candidates: Sequence[dict[str, object]],
    validation_rows: Sequence[dict[str, object]],
    selected_ids: Sequence[str] = SELECTED_PHASE_GAP_IDS,
) -> list[dict[str, object]]:
    validation_by_id = {str(row["candidate_id"]): row for row in validation_rows}
    candidate_by_id = {str(row["candidate_id"]): row for row in candidates}
    selected = []
    for rank, candidate_id in enumerate(selected_ids, start=1):
        candidate = candidate_by_id[candidate_id]
        validation = validation_by_id[candidate_id]
        if not is_true(validation["overall_geometry_pass"]) or not is_true(validation["recommended_for_fdtd"]):
            raise ValueError(f"{candidate_id} is not geometry-pass/recommended")
        selected.append(
            {
                "selection_rank": rank,
                "candidate_id": candidate_id,
                "candidate_family": candidate["candidate_family"],
                "source_reference": candidate["source_reference"],
                "selection_reason": SELECTION_REASONS[candidate_id],
                "expected_risk": candidate["expected_risk"],
                "intended_phase_region": candidate["intended_phase_region"],
                "p1_length_nm": candidate["p1_length_nm"],
                "p1_width_nm": candidate["p1_width_nm"],
                "p2_length_nm": candidate["p2_length_nm"],
                "p2_width_nm": candidate["p2_width_nm"],
                "internal_dx_nm": candidate["internal_dx_nm"],
                "internal_dy_nm": candidate["internal_dy_nm"],
                "p1_rotation_deg": candidate["p1_rotation_deg"],
                "p2_rotation_deg": candidate["p2_rotation_deg"],
                "geometry_pass": validation["overall_geometry_pass"],
                "recommended_for_fdtd": validation["recommended_for_fdtd"],
                "requires_fdtd": candidate["requires_fdtd"],
                "status": "selected_not_run",
                "notes": "09-P15 selection only; no config YAML; no FDTD; no surrogate prediction.",
            }
        )
    _validate_phase_gap_selection_policy(selected)
    return selected


def summarize_phase_gap_candidate_pool(candidates: Sequence[dict[str, object]]) -> dict[str, object]:
    return {
        "candidate_count": len(candidates),
        "family_counts": dict(sorted(Counter(str(row["candidate_family"]) for row in candidates).items())),
        "candidate_ids_unique": len({str(row["candidate_id"]) for row in candidates}) == len(candidates),
        "p1_width_range": _range_text([float(row["p1_width_nm"]) for row in candidates]),
        "internal_dx_range": _range_text([float(row["internal_dx_nm"]) for row in candidates]),
    }


def write_phase_gap_candidate_pool_summary(path: str | Path, candidates: Sequence[dict[str, object]]) -> Path:
    summary = summarize_phase_gap_candidate_pool(candidates)
    lines = [
        "# APCD K=6 Phase-Gap Candidate Pool v1 Summary",
        "",
        "Scope: 09-P15 candidate pool only. No FDTD was run. No lumapi call was made. No model was trained. No `.fsp` file was exported. This is not a steering result.",
        "",
        f"Candidate count: {summary['candidate_count']}",
        f"Candidate IDs unique: {summary['candidate_ids_unique']}",
        f"p1_width range nm: {summary['p1_width_range']}",
        f"internal_dx range nm: {summary['internal_dx_range']}",
        "",
        "Family distribution:",
        "",
        *[f"- `{family}`: {count}" for family, count in summary["family_counts"].items()],
        "",
        "Design target: small 60-90 deg leakage-controlled candidate pool based on conservative interpolation between `doe_lhs_like_01` phase evidence and the low-leakage p1w_dx anchors.",
    ]
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def summarize_phase_gap_validation(rows: Sequence[dict[str, object]]) -> dict[str, object]:
    pass_rows = [row for row in rows if is_true(row["overall_geometry_pass"])]
    recommended = [row for row in rows if is_true(row["recommended_for_fdtd"])]
    fail_rows = [row for row in rows if not is_true(row["overall_geometry_pass"])]
    return {
        "total": len(rows),
        "geometry_pass_count": len(pass_rows),
        "fail_count": len(fail_rows),
        "recommended_for_fdtd_count": len(recommended),
        "minimum_same_cell_gap_nm": min(float(row["same_cell_min_gap_nm"]) for row in rows),
        "minimum_periodic_image_gap_nm": min(float(row["periodic_image_min_gap_nm"]) for row in rows),
        "family_counts": dict(sorted(Counter(str(row["candidate_family"]) for row in rows).items())),
        "fail_reasons": dict(sorted(Counter(str(row["notes"]) for row in fail_rows).items())),
    }


def write_phase_gap_selection_summary(
    path: str | Path,
    selection_rows: Sequence[dict[str, object]],
    validation_rows: Sequence[dict[str, object]],
) -> Path:
    validation_summary = summarize_phase_gap_validation(validation_rows)
    lines = [
        "# APCD K=6 Phase-Gap FDTD Selection v1 Summary",
        "",
        "Scope: 09-P15 geometry validation plus selection only. No FDTD was run. No config YAML was generated. No model was trained. This is not a steering result.",
        "",
        f"Pool total: {validation_summary['total']}",
        f"Geometry pass: {validation_summary['geometry_pass_count']}",
        f"Recommended for FDTD: {validation_summary['recommended_for_fdtd_count']}",
        f"Minimum same-cell gap nm: {validation_summary['minimum_same_cell_gap_nm']}",
        f"Minimum periodic-image gap nm: {validation_summary['minimum_periodic_image_gap_nm']}",
        f"Selected count: {len(selection_rows)}",
        "",
        "Selected candidates:",
        "",
        *[
            f"- `{row['candidate_id']}` (`{row['candidate_family']}`): {row['selection_reason']}"
            for row in selection_rows
        ],
        "",
        "These candidates are selected_not_run and are only inputs for a later small real-FDTD batch.",
    ]
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def existing_geometry_rows_from_paths(paths: Iterable[str | Path]) -> list[dict[str, object]]:
    rows = []
    for path in paths:
        candidate_path = Path(path)
        if candidate_path.exists():
            rows.extend(read_csv_rows(candidate_path))
    return rows


def is_true(value: object) -> bool:
    return value is True or str(value) == "True" or str(value).lower() == "true"


def _dataset_row_from_summary(
    summary: dict[str, str],
    geometry: dict[str, str] | None,
    summary_path: Path,
    columns: Sequence[str],
) -> dict[str, object]:
    candidate_id = str(summary["candidate_id"])
    t_alpha = parse_complex_text(summary["t_alpha_star_from_alpha"])
    phase = float(summary.get("phase_deg") or math.degrees(cmath.phase(t_alpha)))
    target = float(summary["target_conversion"])
    leakage = float(summary["opposite_spin_leakage"])
    ratio = float(summary["conversion_to_leakage_ratio"])
    row = {column: "" for column in columns}
    row.update(
        {
            "variant_id": candidate_id,
            "candidate_family": summary.get("candidate_family", geometry.get("candidate_family", "") if geometry else ""),
            "t_alpha_star_from_alpha_real": t_alpha.real,
            "t_alpha_star_from_alpha_imag": t_alpha.imag,
            "t_alpha_star_from_alpha_abs": abs(t_alpha),
            "phase_deg": phase,
            "phase_shift_vs_baseline_deg": wrap_phase_deg(phase - BASELINE_PHASE_DEG),
            "target_conversion": target,
            "opposite_spin_leakage": leakage,
            "conversion_to_leakage_ratio": ratio,
            "PD": float(summary["PD"]),
            "overall_early_pass": overall_early_pass(target, leakage, ratio),
            "source_result_csv": f"summary_only:{summary_path.as_posix()}",
            "notes": DATASET_NOTES,
        }
    )
    if geometry:
        for column in columns:
            if column in geometry and column not in row:
                row[column] = geometry[column]
        for column in (
            "p1_length_nm",
            "p1_width_nm",
            "p2_length_nm",
            "p2_width_nm",
            "p1_frac_x",
            "p1_frac_y",
            "p2_frac_x",
            "p2_frac_y",
            "internal_dx_nm",
            "internal_dy_nm",
            "p1_rotation_deg",
            "p2_rotation_deg",
            "period_x_nm",
            "period_y_nm",
            "height_nm",
            "material",
            "substrate",
        ):
            row[column] = geometry.get(column, row.get(column, ""))
    else:
        row["notes"] = f"{DATASET_NOTES}; missing_geometry"
    return row


def _nearest_phase_row(rows: Sequence[dict[str, object]], target: float) -> dict[str, object]:
    if not rows:
        return {}
    scored = []
    for row in rows:
        phase = float(row["phase_deg"])
        error = abs(wrap_phase_deg(phase - target))
        scored.append({**row, "phase_error_deg": error})
    return min(scored, key=lambda row: (float(row["phase_error_deg"]), str(row["variant_id"])))


def _bin_status(nearest_all: dict[str, object], nearest_early: dict[str, object]) -> str:
    early_error = _optional_float(nearest_early.get("phase_error_deg"))
    all_error = _optional_float(nearest_all.get("phase_error_deg"))
    if early_error is not None and early_error <= 15.0:
        return "covered_candidate"
    if early_error is not None and early_error <= 30.0:
        return "near_candidate"
    if all_error is not None and all_error <= 15.0:
        return "high_leakage_only"
    return "missing"


def _bin_notes(target: float, status: str) -> str:
    if status == "covered_candidate":
        return "early-pass candidate is close to this bin"
    if status == "near_candidate":
        return "early-pass candidate is nearby but still not a clean phase-state"
    if status == "high_leakage_only":
        return "nearest phase evidence fails early leakage/ratio requirements"
    return f"large phase gap remains near {target:g} deg"


def _candidate_row(
    *,
    candidate_id: str,
    candidate_family: str,
    source_reference: str,
    p1_length_nm: float,
    p1_width_nm: float,
    p2_length_nm: float,
    p2_width_nm: float,
    internal_dx_nm: float,
    internal_dy_nm: float,
    expected_risk: str,
) -> dict[str, object]:
    row = dict(DEFAULT_BASELINE)
    row.update(
        {
            "candidate_id": candidate_id,
            "candidate_family": candidate_family,
            "source_reference": source_reference,
            "design_intent": "60-90 deg leakage-controlled phase-gap scaffold; no surrogate prediction",
            "p1_length_nm": p1_length_nm,
            "p1_width_nm": p1_width_nm,
            "p2_length_nm": p2_length_nm,
            "p2_width_nm": p2_width_nm,
            "internal_dx_nm": internal_dx_nm,
            "internal_dy_nm": internal_dy_nm,
            "intended_phase_region": "60_to_90_deg_leakage_controlled_probe",
            "expected_risk": expected_risk,
            "requires_geometry_validation": "true",
            "requires_fdtd": "true",
            "status": "not_evaluated",
            "notes": "Candidate pool only; no FDTD, no training, no steering result, and no predicted phase/leakage.",
        }
    )
    row["p1_rotation_deg"] = 67.5
    row["p2_rotation_deg"] = 112.5
    return row


def _validate_phase_gap_candidate_policy(candidates: Sequence[dict[str, object]]) -> None:
    if not 18 <= len(candidates) <= 30:
        raise ValueError("phase-gap candidate count must be 18-30")
    ids = [str(row["candidate_id"]) for row in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError("candidate_id values must be unique")
    for row in candidates:
        validate_candidate_bounds(row)
        if float(row["p1_rotation_deg"]) != 67.5 or float(row["p2_rotation_deg"]) != 112.5:
            raise ValueError("rotations must remain fixed")
        if float(row["p2_length_nm"]) == 150.0 and float(row["p2_width_nm"]) == 85.0:
            raise ValueError("beta-selective p2 geometry is not allowed")


def _validate_phase_gap_selection_policy(rows: Sequence[dict[str, object]]) -> None:
    if not 2 <= len(rows) <= 4:
        raise ValueError("selected count must be 2-4")
    families = Counter(str(row["candidate_family"]) for row in rows)
    if families.get("gap_60_90_bridge_from_p1w_dx", 0) < 1:
        raise ValueError("selection must include a bridge candidate near low-leakage p1w_dx anchor")
    if families.get("gap_60_90_lhs_leakage_reduced", 0) < 1:
        raise ValueError("selection must include an lhs-like leakage-reduced candidate")
    if any(str(row["status"]) != "selected_not_run" for row in rows):
        raise ValueError("selection status must be selected_not_run")


def _geometry_key(row: dict[str, object]) -> tuple[float, float, float, float, float, float]:
    return (
        float(row["p1_length_nm"]),
        float(row["p1_width_nm"]),
        float(row["p2_length_nm"]),
        float(row["p2_width_nm"]),
        float(row.get("internal_dx_nm", 0.0) or 0.0),
        float(row.get("internal_dy_nm", 0.0) or 0.0),
    )


def _optional_float(value: object) -> float | None:
    if value in {"", None}:
        return None
    return float(value)


def _range_text(values: Sequence[float]) -> str:
    if not values:
        return "none"
    return f"{min(values):.12g} to {max(values):.12g}"
