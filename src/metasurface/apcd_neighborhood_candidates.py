from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence

import yaml


NEIGHBORHOOD_CANDIDATE_FIELDS = [
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

BOUNDS = {
    "p1_length_nm": (110.0, 150.0),
    "p1_width_nm": (55.0, 90.0),
    "p2_length_nm": (70.0, 105.0),
    "p2_width_nm": (130.0, 170.0),
    "internal_dx_nm": (-40.0, 40.0),
    "internal_dy_nm": (-40.0, 40.0),
}

FIXED_VALUES = {
    "p1_frac_x": 0.75,
    "p1_frac_y": 0.75,
    "p2_frac_x": 0.25,
    "p2_frac_y": 0.25,
    "p1_rotation_deg": 67.5,
    "p2_rotation_deg": 112.5,
    "period_x_nm": 340.0,
    "period_y_nm": 340.0,
    "height_nm": 300.0,
    "material": "c-Si",
    "substrate": "Al2O3",
}

BASELINE_GEOMETRY = {
    "p1_length_nm": 130.0,
    "p1_width_nm": 70.0,
    "p2_length_nm": 85.0,
    "p2_width_nm": 150.0,
    "internal_dx_nm": 0.0,
    "internal_dy_nm": 0.0,
    **FIXED_VALUES,
}


def load_reference_candidate_config(path: str | Path) -> dict[str, object]:
    with Path(path).open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"reference config is not a mapping: {path}")

    candidate = data.get("candidate", {})
    geometry = data.get("geometry", {})
    material = data.get("material", {})
    if not isinstance(candidate, dict) or not isinstance(geometry, dict) or not isinstance(material, dict):
        raise ValueError(f"reference config is missing candidate/geometry/material mappings: {path}")

    p1 = geometry.get("nanopillar_1", {})
    p2 = geometry.get("nanopillar_2", {})
    if not isinstance(p1, dict) or not isinstance(p2, dict):
        raise ValueError(f"reference config is missing nanopillar geometry: {path}")

    row = {
        "candidate_id": str(candidate.get("variant_id", Path(path).stem)),
        "candidate_family": str(candidate.get("candidate_type", "")),
        "p1_length_nm": _number(p1["length_nm"]),
        "p1_width_nm": _number(p1["width_nm"]),
        "p2_length_nm": _number(p2["length_nm"]),
        "p2_width_nm": _number(p2["width_nm"]),
        "p1_frac_x": _number(p1.get("frac_x", FIXED_VALUES["p1_frac_x"])),
        "p1_frac_y": _number(p1.get("frac_y", FIXED_VALUES["p1_frac_y"])),
        "p2_frac_x": _number(p2.get("frac_x", FIXED_VALUES["p2_frac_x"])),
        "p2_frac_y": _number(p2.get("frac_y", FIXED_VALUES["p2_frac_y"])),
        "p1_rotation_deg": _number(p1["rotation_deg"]),
        "p2_rotation_deg": _number(p2["rotation_deg"]),
        "period_x_nm": _number(geometry["period_x_nm"]),
        "period_y_nm": _number(geometry["period_y_nm"]),
        "height_nm": _number(geometry["height_nm"]),
        "material": str(material.get("meta_material", "c-Si")),
        "substrate": str(material.get("substrate", "Al2O3")),
    }
    row.update(_internal_offsets_from_geometry(p1, p2, row))
    validate_neighborhood_candidate_bounds(row)
    return row


def build_p1w_dx_neighborhood(reference: dict[str, object]) -> list[dict[str, object]]:
    specs = [
        {"p1_width_nm": 55, "internal_dx_nm": -35},
        {"p1_width_nm": 55, "internal_dx_nm": -30},
        {"p1_width_nm": 55, "internal_dx_nm": -25},
        {"p1_width_nm": 60, "internal_dx_nm": -40},
        {"p1_width_nm": 60, "internal_dx_nm": -35},
        {"p1_width_nm": 60, "internal_dx_nm": -25},
        {"p1_width_nm": 65, "internal_dx_nm": -35},
        {"p1_width_nm": 65, "internal_dx_nm": -30},
        {"p1_width_nm": 70, "internal_dx_nm": -35},
        {"p1_width_nm": 70, "internal_dx_nm": -25},
    ]
    rows = []
    for index, delta in enumerate(specs, start=1):
        rows.append(
            _candidate_row(
                candidate_id=assign_neighborhood_candidate_id("p1w_dx_neighborhood", index),
                candidate_family="p1w_dx_neighborhood",
                source_reference=str(reference["candidate_id"]),
                design_intent="low-leakage neighborhood around doe_p1w_dx_01; vary p1 width and internal_dx only",
                intended_phase_region="90_to_100_deg_probe",
                expected_risk="low_to_moderate_leakage_risk",
                notes="No surrogate prediction; candidate requires geometry validation before real FDTD.",
                **_merge_reference(reference, delta),
            )
        )
    return rows


def build_lhs_like_leakage_reduction_candidates(reference: dict[str, object]) -> list[dict[str, object]]:
    specs = [
        {"p1_length_nm": 115, "p1_width_nm": 60, "p2_length_nm": 75, "p2_width_nm": 135, "internal_dx_nm": -35, "internal_dy_nm": 20},
        {"p1_length_nm": 120, "p1_width_nm": 60, "p2_length_nm": 80, "p2_width_nm": 140, "internal_dx_nm": -35, "internal_dy_nm": 20},
        {"p1_length_nm": 120, "p1_width_nm": 65, "p2_length_nm": 80, "p2_width_nm": 140, "internal_dx_nm": -30, "internal_dy_nm": 15},
        {"p1_length_nm": 125, "p1_width_nm": 65, "p2_length_nm": 85, "p2_width_nm": 145, "internal_dx_nm": -30, "internal_dy_nm": 10},
        {"p1_length_nm": 125, "p1_width_nm": 60, "p2_length_nm": 85, "p2_width_nm": 150, "internal_dx_nm": -30, "internal_dy_nm": 10},
        {"p1_length_nm": 130, "p1_width_nm": 60, "p2_length_nm": 85, "p2_width_nm": 150, "internal_dx_nm": -30, "internal_dy_nm": 5},
        {"p1_length_nm": 130, "p1_width_nm": 65, "p2_length_nm": 85, "p2_width_nm": 155, "internal_dx_nm": -25, "internal_dy_nm": 10},
        {"p1_length_nm": 130, "p1_width_nm": 60, "p2_length_nm": 85, "p2_width_nm": 160, "internal_dx_nm": -25, "internal_dy_nm": 15},
        {"p1_length_nm": 125, "p1_width_nm": 55, "p2_length_nm": 80, "p2_width_nm": 150, "internal_dx_nm": -35, "internal_dy_nm": 20},
        {"p1_length_nm": 130, "p1_width_nm": 55, "p2_length_nm": 85, "p2_width_nm": 160, "internal_dx_nm": -30, "internal_dy_nm": 20},
    ]
    rows = []
    for index, delta in enumerate(specs, start=1):
        rows.append(
            _candidate_row(
                candidate_id=assign_neighborhood_candidate_id("lhs_like_leakage_reduction", index),
                candidate_family="lhs_like_leakage_reduction",
                source_reference=str(reference["candidate_id"]),
                design_intent="pull aggressive lhs-like geometry toward lower-leakage anchors while retaining mixed displacement",
                intended_phase_region="60_to_90_deg_leakage_reduction_probe",
                expected_risk="moderate_to_high_leakage_risk",
                notes="No surrogate prediction; uses doe_lhs_like_01 only as phase-coverage evidence.",
                **_merge_reference(reference, delta),
            )
        )
    return rows


def build_bridge_dx_lhs_candidates(
    p1w_dx_reference: dict[str, object],
    lhs_reference: dict[str, object],
) -> list[dict[str, object]]:
    specs = [
        {"p1_length_nm": 125, "p1_width_nm": 60, "p2_length_nm": 80, "p2_width_nm": 140, "internal_dx_nm": -35, "internal_dy_nm": 5},
        {"p1_length_nm": 125, "p1_width_nm": 65, "p2_length_nm": 80, "p2_width_nm": 145, "internal_dx_nm": -35, "internal_dy_nm": 15},
        {"p1_length_nm": 130, "p1_width_nm": 60, "p2_length_nm": 85, "p2_width_nm": 145, "internal_dx_nm": -40, "internal_dy_nm": 10},
        {"p1_length_nm": 120, "p1_width_nm": 65, "p2_length_nm": 85, "p2_width_nm": 150, "internal_dx_nm": -25, "internal_dy_nm": 20},
    ]
    rows = []
    source_reference = f"{p1w_dx_reference['candidate_id']}|{lhs_reference['candidate_id']}"
    for index, delta in enumerate(specs, start=1):
        rows.append(
            _candidate_row(
                candidate_id=assign_neighborhood_candidate_id("bridge_dx_lhs", index),
                candidate_family="bridge_dx_lhs",
                source_reference=source_reference,
                design_intent="interpolate between low-leakage p1w_dx result and large-shift lhs-like result",
                intended_phase_region="60_to_100_deg_bridge_probe",
                expected_risk="moderate_leakage_risk",
                notes="No surrogate prediction; bridge row for later geometry validation and small-batch FDTD selection.",
                **_merge_reference(p1w_dx_reference, delta),
            )
        )
    return rows


def validate_neighborhood_candidate_bounds(candidate: dict[str, object], *, strict: bool = True) -> list[str]:
    violations: list[str] = []
    for name, (min_value, max_value) in BOUNDS.items():
        if name not in candidate:
            violations.append(f"{name}: missing")
            continue
        value = float(candidate[name])
        if value < min_value or value > max_value:
            violations.append(f"{name}: {value:g} outside [{min_value:g}, {max_value:g}]")

    fixed_checks = {
        "p1_rotation_deg": 67.5,
        "p2_rotation_deg": 112.5,
        "period_x_nm": 340.0,
        "period_y_nm": 340.0,
        "height_nm": 300.0,
        "material": "c-Si",
        "substrate": "Al2O3",
    }
    for name, expected in fixed_checks.items():
        if name not in candidate:
            violations.append(f"{name}: missing")
        elif isinstance(expected, float) and float(candidate[name]) != expected:
            violations.append(f"{name}: must remain fixed at {expected:g}")
        elif isinstance(expected, str) and str(candidate[name]) != expected:
            violations.append(f"{name}: must remain fixed at {expected}")

    if float(candidate.get("p2_length_nm", 0.0)) == 150.0 and float(candidate.get("p2_width_nm", 0.0)) == 85.0:
        violations.append("p2 geometry 150 x 85 nm is beta-selective and not allowed")

    if violations and strict:
        raise ValueError("; ".join(violations))
    return violations


def assign_neighborhood_candidate_id(candidate_family: str, index: int) -> str:
    prefixes = {
        "p1w_dx_neighborhood": "nhood_p1w_dx",
        "lhs_like_leakage_reduction": "nhood_lhs_leakred",
        "bridge_dx_lhs": "nhood_bridge_dx_lhs",
    }
    prefix = prefixes.get(candidate_family, f"nhood_{candidate_family}")
    return f"{prefix}_{index:02d}"


def export_neighborhood_candidate_pool(candidates: Iterable[dict[str, object]], path: str | Path) -> Path:
    row_list = list(candidates)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=NEIGHBORHOOD_CANDIDATE_FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in NEIGHBORHOOD_CANDIDATE_FIELDS} for row in row_list)
    return output_path


def summarize_neighborhood_candidate_pool(candidates: Sequence[dict[str, object]]) -> dict[str, object]:
    family_counts = Counter(str(row["candidate_family"]) for row in candidates)
    ids = [str(row["candidate_id"]) for row in candidates]
    violations = []
    for row in candidates:
        violations.extend(f"{row['candidate_id']}: {item}" for item in validate_neighborhood_candidate_bounds(row, strict=False))
    return {
        "candidate_count": len(candidates),
        "family_counts": dict(sorted(family_counts.items())),
        "reference_candidates": sorted({str(row["source_reference"]) for row in candidates}),
        "unique_candidate_ids": len(ids) == len(set(ids)),
        "bounds_ok": len(violations) == 0,
        "bounds_violations": violations,
        "status_values": sorted({str(row["status"]) for row in candidates}),
        "requires_fdtd_values": sorted({str(row["requires_fdtd"]) for row in candidates}),
        "requires_geometry_validation_values": sorted({str(row["requires_geometry_validation"]) for row in candidates}),
    }


def build_neighborhood_candidate_pool(
    p1w_dx_reference: dict[str, object],
    lhs_reference: dict[str, object],
) -> list[dict[str, object]]:
    candidates = []
    candidates.extend(build_p1w_dx_neighborhood(p1w_dx_reference))
    candidates.extend(build_lhs_like_leakage_reduction_candidates(lhs_reference))
    candidates.extend(build_bridge_dx_lhs_candidates(p1w_dx_reference, lhs_reference))
    ids = [str(row["candidate_id"]) for row in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate neighborhood candidate_id detected")
    return candidates


def write_neighborhood_candidate_pool_summary(path: str | Path, candidates: Sequence[dict[str, object]]) -> Path:
    summary = summarize_neighborhood_candidate_pool(candidates)
    family_lines = [f"- `{family}`: {count}" for family, count in summary["family_counts"].items()]
    lines = [
        "# APCD K=6 Neighborhood Candidate Pool v1 Summary",
        "",
        "Scope: 09-P6 candidate pool only. No FDTD run was performed. No lumapi call was made. No `.fsp` file was exported. No model was trained. No surrogate prediction was generated. This is not a steering result.",
        "",
        f"Candidate count: {summary['candidate_count']}",
        f"Unique candidate IDs: {summary['unique_candidate_ids']}",
        f"Bounds check: {'passed' if summary['bounds_ok'] else 'failed'}",
        f"Reference candidates: {', '.join(summary['reference_candidates'])}",
        f"Status values: {', '.join(summary['status_values'])}",
        f"requires_fdtd values: {', '.join(summary['requires_fdtd_values'])}",
        f"requires_geometry_validation values: {', '.join(summary['requires_geometry_validation_values'])}",
        "",
        "Candidate family distribution:",
        "",
        *family_lines,
        "",
        "`p1w_dx_neighborhood` explores low-leakage variants around `doe_p1w_dx_01`.",
        "`lhs_like_leakage_reduction` pulls `doe_lhs_like_01` toward lower-leakage anchors while preserving mixed displacement.",
        "`bridge_dx_lhs` interpolates between the low-leakage and large-phase-shift references.",
        "",
        "All rows require geometry validation before any real FDTD job.",
    ]
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def _candidate_row(
    *,
    candidate_id: str,
    candidate_family: str,
    source_reference: str,
    design_intent: str,
    intended_phase_region: str,
    expected_risk: str,
    notes: str,
    p1_length_nm: object,
    p1_width_nm: object,
    p2_length_nm: object,
    p2_width_nm: object,
    p1_frac_x: object,
    p1_frac_y: object,
    p2_frac_x: object,
    p2_frac_y: object,
    internal_dx_nm: object,
    internal_dy_nm: object,
    p1_rotation_deg: object,
    p2_rotation_deg: object,
    period_x_nm: object,
    period_y_nm: object,
    height_nm: object,
    material: object,
    substrate: object,
) -> dict[str, object]:
    row = {
        "candidate_id": candidate_id,
        "candidate_family": candidate_family,
        "source_reference": source_reference,
        "design_intent": design_intent,
        "p1_length_nm": _number(p1_length_nm),
        "p1_width_nm": _number(p1_width_nm),
        "p2_length_nm": _number(p2_length_nm),
        "p2_width_nm": _number(p2_width_nm),
        "p1_frac_x": _number(p1_frac_x),
        "p1_frac_y": _number(p1_frac_y),
        "p2_frac_x": _number(p2_frac_x),
        "p2_frac_y": _number(p2_frac_y),
        "internal_dx_nm": _number(internal_dx_nm),
        "internal_dy_nm": _number(internal_dy_nm),
        "p1_rotation_deg": _number(p1_rotation_deg),
        "p2_rotation_deg": _number(p2_rotation_deg),
        "period_x_nm": _number(period_x_nm),
        "period_y_nm": _number(period_y_nm),
        "height_nm": _number(height_nm),
        "material": str(material),
        "substrate": str(substrate),
        "intended_phase_region": intended_phase_region,
        "expected_risk": expected_risk,
        "requires_geometry_validation": "true",
        "requires_fdtd": "true",
        "status": "not_evaluated",
        "notes": notes,
    }
    validate_neighborhood_candidate_bounds(row)
    return row


def _merge_reference(reference: dict[str, object], delta: dict[str, object]) -> dict[str, object]:
    row = dict(reference)
    row.update({key: value for key, value in FIXED_VALUES.items() if key not in row})
    row.update(delta)
    return {key: row[key] for key in [*BOUNDS.keys(), *FIXED_VALUES.keys()]}


def _internal_offsets_from_geometry(
    p1: dict[str, object],
    p2: dict[str, object],
    row: dict[str, object],
) -> dict[str, object]:
    period_x = float(row["period_x_nm"])
    period_y = float(row["period_y_nm"])
    p1_default_x = (float(row["p1_frac_x"]) - 0.5) * period_x
    p1_default_y = (float(row["p1_frac_y"]) - 0.5) * period_y
    p2_default_x = (float(row["p2_frac_x"]) - 0.5) * period_x
    p2_default_y = (float(row["p2_frac_y"]) - 0.5) * period_y
    p1_x = float(p1.get("x_nm", p1_default_x))
    p1_y = float(p1.get("y_nm", p1_default_y))
    p2_x = float(p2.get("x_nm", p2_default_x))
    p2_y = float(p2.get("y_nm", p2_default_y))
    internal_dx = (p1_x - p1_default_x + p2_default_x - p2_x) / 2.0 * 2.0
    internal_dy = (p1_y - p1_default_y + p2_default_y - p2_y) / 2.0 * 2.0
    return {"internal_dx_nm": _number(internal_dx), "internal_dy_nm": _number(internal_dy)}


def _number(value: object) -> int | float:
    number = float(value)
    return int(number) if number.is_integer() else number
