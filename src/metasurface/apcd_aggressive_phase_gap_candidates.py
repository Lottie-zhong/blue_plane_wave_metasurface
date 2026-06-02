from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence

from metasurface.apcd_active_learning import DEFAULT_BASELINE, validate_candidate_bounds
from metasurface.apcd_candidate_validation import validate_candidate_geometry


AGGRESSIVE_PHASE_GAP_CANDIDATE_FIELDS = [
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

AGGRESSIVE_PHASE_GAP_VALIDATION_FIELDS = [
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

AGGRESSIVE_PHASE_GAP_SELECTION_FIELDS = [
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

SELECTED_AGGRESSIVE_PHASE_GAP_IDS = [
    "aggr_lhs_retention_dy_05",
    "aggr_p1w_leakctrl_04",
    "aggr_bridge_lhs_fine_05",
]

SELECTION_REASONS = {
    "aggr_lhs_retention_dy_05": (
        "Most aggressive selected row: retains short lhs-like p1/p2 geometry and high internal_dy "
        "to keep the 60 deg phase-shift ingredients."
    ),
    "aggr_p1w_leakctrl_04": (
        "Leakage-control row: keeps high internal_dy but relaxes p1_width and p2_width away from "
        "the most aggressive lhs-like geometry."
    ),
    "aggr_bridge_lhs_fine_05": (
        "Bridge row: interpolates between doe_lhs_like_01 and the low-leakage fine p1w_dx anchors "
        "without collapsing back to the 96 deg conservative geometry."
    ),
}


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv_rows(rows: Iterable[dict[str, object]], path: str | Path, fieldnames: Sequence[str]) -> Path:
    row_list = list(rows)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fieldnames} for row in row_list)
    return output_path


def build_aggressive_phase_gap_candidate_pool() -> list[dict[str, object]]:
    specs = [
        ("aggr_lhs_retention_dy_01", "lhs_like_retention_high_dy", "doe_lhs_like_01", 110, 55, 70, 130, -40, 24, "high_leakage_risk"),
        ("aggr_lhs_retention_dy_02", "lhs_like_retention_high_dy", "doe_lhs_like_01", 110, 56, 70, 135, -40, 26, "high_leakage_risk"),
        ("aggr_lhs_retention_dy_03", "lhs_like_retention_high_dy", "doe_lhs_like_01", 115, 55, 70, 130, -40, 28, "high_leakage_risk"),
        ("aggr_lhs_retention_dy_04", "lhs_like_retention_high_dy", "doe_lhs_like_01", 115, 56, 75, 130, -38, 30, "high_leakage_risk"),
        ("aggr_lhs_retention_dy_05", "lhs_like_retention_high_dy", "doe_lhs_like_01", 115, 55, 75, 135, -40, 32, "high_leakage_risk"),
        ("aggr_lhs_retention_dy_06", "lhs_like_retention_high_dy", "doe_lhs_like_01", 120, 55, 75, 130, -38, 34, "high_leakage_risk"),
        ("aggr_p1w_leakctrl_01", "lhs_like_leakage_control_p1w", "doe_lhs_like_01|fine_p1w_dx_03", 115, 57, 75, 135, -38, 24, "moderate_to_high_leakage_risk"),
        ("aggr_p1w_leakctrl_02", "lhs_like_leakage_control_p1w", "doe_lhs_like_01|fine_p1w_dx_08", 115, 58, 75, 135, -38, 26, "moderate_to_high_leakage_risk"),
        ("aggr_p1w_leakctrl_03", "lhs_like_leakage_control_p1w", "doe_lhs_like_01|gap_lhs_leakred_06", 120, 57, 80, 135, -38, 28, "moderate_to_high_leakage_risk"),
        ("aggr_p1w_leakctrl_04", "lhs_like_leakage_control_p1w", "doe_lhs_like_01|gap_bridge_03", 120, 58, 80, 140, -36, 30, "moderate_to_high_leakage_risk"),
        ("aggr_p1w_leakctrl_05", "lhs_like_leakage_control_p1w", "doe_lhs_like_01|fine_p1w_dx_03", 125, 58, 80, 140, -36, 28, "moderate_leakage_risk"),
        ("aggr_p1w_leakctrl_06", "lhs_like_leakage_control_p1w", "doe_lhs_like_01|fine_p1w_dx_08", 125, 60, 80, 140, -36, 30, "moderate_leakage_risk"),
        ("aggr_p2w_trim_01", "lhs_like_p2w_trim", "doe_lhs_like_01|p2W_p10", 110, 55, 70, 135, -40, 24, "high_leakage_risk"),
        ("aggr_p2w_trim_02", "lhs_like_p2w_trim", "doe_lhs_like_01|p2W_p10", 115, 55, 70, 140, -40, 26, "high_leakage_risk"),
        ("aggr_p2w_trim_03", "lhs_like_p2w_trim", "doe_lhs_like_01|p2W_p10", 115, 56, 75, 140, -38, 28, "moderate_to_high_leakage_risk"),
        ("aggr_p2w_trim_04", "lhs_like_p2w_trim", "doe_lhs_like_01|p2W_p10", 120, 56, 75, 145, -38, 30, "moderate_to_high_leakage_risk"),
        ("aggr_p2w_trim_05", "lhs_like_p2w_trim", "doe_lhs_like_01|p2W_p10", 120, 58, 80, 145, -36, 32, "moderate_to_high_leakage_risk"),
        ("aggr_bridge_lhs_fine_01", "lhs_to_fine_bridge_aggressive", "doe_lhs_like_01|fine_p1w_dx_03", 120, 56, 80, 140, -38, 20, "moderate_to_high_leakage_risk"),
        ("aggr_bridge_lhs_fine_02", "lhs_to_fine_bridge_aggressive", "doe_lhs_like_01|fine_p1w_dx_08", 120, 57, 80, 140, -38, 22, "moderate_to_high_leakage_risk"),
        ("aggr_bridge_lhs_fine_03", "lhs_to_fine_bridge_aggressive", "doe_lhs_like_01|gap_lhs_leakred_06", 125, 56, 80, 140, -38, 24, "moderate_to_high_leakage_risk"),
        ("aggr_bridge_lhs_fine_04", "lhs_to_fine_bridge_aggressive", "doe_lhs_like_01|gap_bridge_03", 125, 57, 80, 145, -36, 24, "moderate_leakage_risk"),
        ("aggr_bridge_lhs_fine_05", "lhs_to_fine_bridge_aggressive", "doe_lhs_like_01|fine_p1w_dx_03|gap_lhs_leakred_06", 120, 56, 75, 140, -38, 26, "moderate_to_high_leakage_risk"),
        ("aggr_dy_sweep_01", "dy_sweep_near_lhs", "doe_lhs_like_01", 115, 55, 75, 135, -40, 18, "high_leakage_risk"),
        ("aggr_dy_sweep_02", "dy_sweep_near_lhs", "doe_lhs_like_01", 115, 55, 75, 135, -40, 22, "high_leakage_risk"),
        ("aggr_dy_sweep_03", "dy_sweep_near_lhs", "doe_lhs_like_01", 115, 55, 75, 135, -40, 26, "high_leakage_risk"),
        ("aggr_dy_sweep_04", "dy_sweep_near_lhs", "doe_lhs_like_01", 115, 55, 75, 135, -40, 30, "high_leakage_risk"),
        ("aggr_dy_sweep_05", "dy_sweep_near_lhs", "doe_lhs_like_01", 115, 55, 75, 135, -40, 36, "high_leakage_risk"),
        ("aggr_mixed_safe_01", "mixed_aggressive_but_safe", "doe_lhs_like_01|gap_bridge_03", 120, 58, 80, 140, -36, 22, "moderate_leakage_risk"),
        ("aggr_mixed_safe_02", "mixed_aggressive_but_safe", "doe_lhs_like_01|gap_lhs_leakred_06", 125, 58, 80, 145, -36, 24, "moderate_leakage_risk"),
        ("aggr_mixed_safe_03", "mixed_aggressive_but_safe", "doe_lhs_like_01|fine_p1w_dx_08", 125, 60, 85, 140, -34, 26, "moderate_leakage_risk"),
        ("aggr_mixed_safe_04", "mixed_aggressive_but_safe", "doe_lhs_like_01|fine_p1w_dx_03", 130, 58, 85, 140, -34, 28, "moderate_leakage_risk"),
        ("aggr_mixed_safe_05", "mixed_aggressive_but_safe", "doe_lhs_like_01|gap_lhs_leakred_06", 130, 60, 85, 145, -34, 30, "moderate_leakage_risk"),
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
    _validate_candidate_pool_policy(candidates)
    return candidates


def validate_aggressive_phase_gap_candidate_pool(
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
        notes = [] if row["notes"] == "geometry sanity validation passed; optical response still unknown" else [str(row["notes"])]
        row["duplicate_geometry_pass"] = duplicate_pass
        row["overall_geometry_pass"] = bool(row["overall_geometry_pass"] and duplicate_pass)
        row["recommended_for_fdtd"] = row["overall_geometry_pass"]
        if not duplicate_pass:
            notes.append("duplicates an existing evaluated or scaffold geometry")
        if not notes:
            notes.append("geometry sanity validation passed; duplicate check passed; optical response still unknown")
        row["notes"] = "; ".join(notes)
        rows.append(row)
        seen.add(key)
    return rows


def select_aggressive_phase_gap_fdtd_candidates(
    candidates: Sequence[dict[str, object]],
    validation_rows: Sequence[dict[str, object]],
    selected_ids: Sequence[str] = SELECTED_AGGRESSIVE_PHASE_GAP_IDS,
) -> list[dict[str, object]]:
    candidate_by_id = {str(row["candidate_id"]): row for row in candidates}
    validation_by_id = {str(row["candidate_id"]): row for row in validation_rows}
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
                "notes": "09-P17 selection only; no FDTD; no config YAML; no surrogate prediction; not a steering result.",
            }
        )
    _validate_selection_policy(selected)
    return selected


def summarize_aggressive_phase_gap_candidate_pool(candidates: Sequence[dict[str, object]]) -> dict[str, object]:
    return {
        "candidate_count": len(candidates),
        "family_counts": dict(sorted(Counter(str(row["candidate_family"]) for row in candidates).items())),
        "candidate_ids_unique": len({str(row["candidate_id"]) for row in candidates}) == len(candidates),
        "internal_dy_range": _range_text([float(row["internal_dy_nm"]) for row in candidates]),
        "p1_length_range": _range_text([float(row["p1_length_nm"]) for row in candidates]),
        "p2_width_range": _range_text([float(row["p2_width_nm"]) for row in candidates]),
    }


def write_aggressive_phase_gap_candidate_pool_summary(path: str | Path, candidates: Sequence[dict[str, object]]) -> Path:
    summary = summarize_aggressive_phase_gap_candidate_pool(candidates)
    lines = [
        "# APCD K=6 Aggressive Phase-Gap Candidate Pool v1 Summary",
        "",
        "Scope: 09-P17 aggressive candidate pool scaffold only. No FDTD was run. No lumapi call was made. No model was trained. No `.fsp` file was exported. This is not a steering result.",
        "",
        f"Candidate count: {summary['candidate_count']}",
        f"Candidate IDs unique: {summary['candidate_ids_unique']}",
        f"internal_dy range nm: {summary['internal_dy_range']}",
        f"p1_length range nm: {summary['p1_length_range']}",
        f"p2_width range nm: {summary['p2_width_range']}",
        "",
        "Family distribution:",
        "",
        *[f"- `{family}`: {count}" for family, count in summary["family_counts"].items()],
        "",
        "Design target: return closer to `doe_lhs_like_01` phase-shift geometry while retaining selected leakage-control anchors from P16 and p1w_dx fine candidates.",
    ]
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def summarize_aggressive_phase_gap_validation(rows: Sequence[dict[str, object]]) -> dict[str, object]:
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


def write_aggressive_phase_gap_selection_summary(
    path: str | Path,
    selection_rows: Sequence[dict[str, object]],
    validation_rows: Sequence[dict[str, object]],
) -> Path:
    validation_summary = summarize_aggressive_phase_gap_validation(validation_rows)
    lines = [
        "# APCD K=6 Aggressive Phase-Gap FDTD Selection v1 Summary",
        "",
        "Scope: 09-P17 geometry validation plus selection only. No FDTD was run. No config YAML was generated. No model was trained. This is not a steering result.",
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
        "These candidates are selected_not_run. They are only inputs for a later small real-FDTD batch.",
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
            "design_intent": "Aggressive 60-90 deg phase-gap scaffold retaining lhs-like phase-shift factors; no surrogate prediction.",
            "p1_length_nm": p1_length_nm,
            "p1_width_nm": p1_width_nm,
            "p2_length_nm": p2_length_nm,
            "p2_width_nm": p2_width_nm,
            "internal_dx_nm": internal_dx_nm,
            "internal_dy_nm": internal_dy_nm,
            "intended_phase_region": "60_to_90_deg_aggressive_leakage_controlled_probe",
            "expected_risk": expected_risk,
            "requires_geometry_validation": "true",
            "requires_fdtd": "true",
            "status": "not_evaluated",
            "notes": "Candidate pool scaffold only; no FDTD, no lumapi, no training, no .fsp, no steering result, and no predicted phase/leakage.",
        }
    )
    row["p1_rotation_deg"] = 67.5
    row["p2_rotation_deg"] = 112.5
    return row


def _validate_candidate_pool_policy(candidates: Sequence[dict[str, object]]) -> None:
    if not 24 <= len(candidates) <= 36:
        raise ValueError("aggressive phase-gap candidate count must be 24-36")
    ids = [str(row["candidate_id"]) for row in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError("candidate_id values must be unique")
    for row in candidates:
        validate_candidate_bounds(row)
        if float(row["p1_rotation_deg"]) != 67.5 or float(row["p2_rotation_deg"]) != 112.5:
            raise ValueError("rotations must remain fixed")
        if float(row["p2_length_nm"]) == 150.0 and float(row["p2_width_nm"]) == 85.0:
            raise ValueError("beta-selective p2 geometry is not allowed")


def _validate_selection_policy(rows: Sequence[dict[str, object]]) -> None:
    if len(rows) != 3:
        raise ValueError("09-P17 selection must contain exactly 3 candidates")
    families = Counter(str(row["candidate_family"]) for row in rows)
    if families.get("lhs_like_retention_high_dy", 0) < 1:
        raise ValueError("selection must include one aggressive lhs-like retention candidate")
    if families.get("lhs_like_leakage_control_p1w", 0) < 1:
        raise ValueError("selection must include one leakage-control candidate")
    if families.get("lhs_to_fine_bridge_aggressive", 0) < 1:
        raise ValueError("selection must include one aggressive bridge candidate")
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


def _range_text(values: Sequence[float]) -> str:
    if not values:
        return "none"
    return f"{min(values):.12g} to {max(values):.12g}"
