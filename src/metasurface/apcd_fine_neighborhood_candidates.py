from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence


FINE_CANDIDATE_FIELDS = [
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

BASE_GEOMETRY = {
    "p1_length_nm": 130.0,
    "p1_width_nm": 60.0,
    "p2_length_nm": 85.0,
    "p2_width_nm": 150.0,
    "p1_frac_x": 0.75,
    "p1_frac_y": 0.75,
    "p2_frac_x": 0.25,
    "p2_frac_y": 0.25,
    "internal_dx_nm": -30.0,
    "internal_dy_nm": 0.0,
    "p1_rotation_deg": 67.5,
    "p2_rotation_deg": 112.5,
    "period_x_nm": 340.0,
    "period_y_nm": 340.0,
    "height_nm": 300.0,
    "material": "c-Si",
    "substrate": "Al2O3",
}

EXISTING_REFERENCE_GEOMETRIES = {
    # doe_p1w_dx_01
    (130.0, 60.0, 85.0, 150.0, -30.0, 0.0),
    # nhood_p1w_dx_05
    (130.0, 60.0, 85.0, 150.0, -35.0, 0.0),
    # nhood_p1w_dx_02
    (130.0, 55.0, 85.0, 150.0, -30.0, 0.0),
}


def load_p1w_dx_reference_results(path: str | Path) -> dict[str, dict[str, str]]:
    with Path(path).open("r", newline="", encoding="utf-8") as handle:
        return {row["candidate_id"]: row for row in csv.DictReader(handle)}


def build_p1w_dx_fine_candidates() -> list[dict[str, object]]:
    rows = []
    index = 1
    for p1_width in [56, 57, 58, 59]:
        for internal_dx in [-31, -32, -33, -34]:
            rows.append(
                _candidate_row(
                    candidate_id=f"fine_p1w_dx_{index:02d}",
                    candidate_family="p1w_dx_fine_leakage_control",
                    source_reference="doe_p1w_dx_01|nhood_p1w_dx_05|nhood_p1w_dx_02",
                    design_intent="fine p1_width/internal_dx interpolation to trade phase lowering against leakage control",
                    intended_phase_region="90_to_100_deg_low_leakage_probe",
                    expected_risk="low_to_moderate_leakage_risk",
                    notes="Fine candidate scaffold only; no surrogate prediction and no FDTD run in 09-P10.",
                    **_with_base_geometry({"p1_width_nm": p1_width, "internal_dx_nm": internal_dx}),
                )
            )
            index += 1
    return rows


def build_p1w_dx_p2w_leakage_trim_candidates() -> list[dict[str, object]]:
    specs = [
        {"p1_width_nm": 56, "internal_dx_nm": -32, "p2_width_nm": 145},
        {"p1_width_nm": 57, "internal_dx_nm": -33, "p2_width_nm": 145},
        {"p1_width_nm": 58, "internal_dx_nm": -32, "p2_width_nm": 155},
        {"p1_width_nm": 59, "internal_dx_nm": -33, "p2_width_nm": 155},
    ]
    rows = []
    for index, delta in enumerate(specs, start=1):
        rows.append(
            _candidate_row(
                candidate_id=f"fine_p1w_dx_p2w_trim_{index:02d}",
                candidate_family="p1w_dx_p2w_leakage_trim",
                source_reference="doe_p1w_dx_01|nhood_p1w_dx_05|nhood_p1w_dx_02",
                design_intent="small p2_width trim near p1w_dx fine region to test leakage recovery without a large geometry jump",
                intended_phase_region="90_to_100_deg_leakage_trim_probe",
                expected_risk="moderate_leakage_risk",
                notes="Fine candidate scaffold only; p2_width trim is small and optical response is unknown.",
                **_with_base_geometry(delta),
            )
        )
    return rows


def deduplicate_candidate_geometries(
    candidates: Iterable[dict[str, object]],
    existing_geometries: Iterable[tuple[float, float, float, float, float, float]] = EXISTING_REFERENCE_GEOMETRIES,
) -> list[dict[str, object]]:
    existing = set(existing_geometries)
    seen: set[tuple[float, float, float, float, float, float]] = set()
    output = []
    for candidate in candidates:
        key = _geometry_key(candidate)
        candidate_id = str(candidate["candidate_id"])
        if key in existing:
            raise ValueError(f"{candidate_id} duplicates an existing p1w_dx reference geometry")
        if key in seen:
            raise ValueError(f"{candidate_id} duplicates another fine candidate geometry")
        seen.add(key)
        output.append(candidate)
    return output


def validate_fine_candidate_bounds(candidate: dict[str, object], *, strict: bool = True) -> list[str]:
    violations = []
    for name, (min_value, max_value) in BOUNDS.items():
        if name not in candidate:
            violations.append(f"{name}: missing")
            continue
        value = float(candidate[name])
        if value < min_value or value > max_value:
            violations.append(f"{name}: {value:g} outside [{min_value:g}, {max_value:g}]")

    fixed_values = {
        "p1_rotation_deg": 67.5,
        "p2_rotation_deg": 112.5,
        "period_x_nm": 340.0,
        "period_y_nm": 340.0,
        "height_nm": 300.0,
        "material": "c-Si",
        "substrate": "Al2O3",
    }
    for name, expected in fixed_values.items():
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


def export_fine_candidate_pool(candidates: Iterable[dict[str, object]], path: str | Path) -> Path:
    row_list = list(candidates)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FINE_CANDIDATE_FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FINE_CANDIDATE_FIELDS} for row in row_list)
    return output_path


def summarize_fine_candidate_pool(candidates: Sequence[dict[str, object]]) -> dict[str, object]:
    family_counts = Counter(str(row["candidate_family"]) for row in candidates)
    ids = [str(row["candidate_id"]) for row in candidates]
    violations = []
    for row in candidates:
        violations.extend(f"{row['candidate_id']}: {item}" for item in validate_fine_candidate_bounds(row, strict=False))
    p1_widths = [float(row["p1_width_nm"]) for row in candidates]
    internal_dx_values = [float(row["internal_dx_nm"]) for row in candidates]
    return {
        "candidate_count": len(candidates),
        "family_counts": dict(sorted(family_counts.items())),
        "unique_candidate_ids": len(ids) == len(set(ids)),
        "bounds_ok": len(violations) == 0,
        "bounds_violations": violations,
        "p1_width_range": (min(p1_widths), max(p1_widths)) if p1_widths else None,
        "internal_dx_range": (min(internal_dx_values), max(internal_dx_values)) if internal_dx_values else None,
        "deduplicated_against_references": True,
        "status_values": sorted({str(row["status"]) for row in candidates}),
    }


def build_fine_candidate_pool() -> list[dict[str, object]]:
    candidates = []
    candidates.extend(build_p1w_dx_fine_candidates())
    candidates.extend(build_p1w_dx_p2w_leakage_trim_candidates())
    return deduplicate_candidate_geometries(candidates)


def write_fine_candidate_pool_summary(path: str | Path, candidates: Sequence[dict[str, object]]) -> Path:
    summary = summarize_fine_candidate_pool(candidates)
    family_lines = [f"- `{family}`: {count}" for family, count in summary["family_counts"].items()]
    lines = [
        "# APCD K=6 p1w_dx Fine Candidate Pool v1 Summary",
        "",
        "Scope: 09-P10 candidate pool only. No FDTD run was performed. No lumapi call was made. No `.fsp` file was exported. No model was trained. No surrogate prediction was generated. This is not a steering result.",
        "",
        f"Candidate count: {summary['candidate_count']}",
        f"Unique candidate IDs: {summary['unique_candidate_ids']}",
        f"Bounds check: {'passed' if summary['bounds_ok'] else 'failed'}",
        f"p1_width range: {summary['p1_width_range'][0]:g} to {summary['p1_width_range'][1]:g} nm",
        f"internal_dx range: {summary['internal_dx_range'][0]:g} to {summary['internal_dx_range'][1]:g} nm",
        f"Deduplicated against references: {summary['deduplicated_against_references']}",
        f"Status values: {', '.join(summary['status_values'])}",
        "",
        "Candidate family distribution:",
        "",
        *family_lines,
        "",
        "The pool targets the leakage/phase tradeoff between `nhood_p1w_dx_05` and `nhood_p1w_dx_02`.",
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
    validate_fine_candidate_bounds(row)
    return row


def _with_base_geometry(delta: dict[str, object]) -> dict[str, object]:
    row = dict(BASE_GEOMETRY)
    row.update(delta)
    return row


def _geometry_key(candidate: dict[str, object]) -> tuple[float, float, float, float, float, float]:
    return (
        float(candidate["p1_length_nm"]),
        float(candidate["p1_width_nm"]),
        float(candidate["p2_length_nm"]),
        float(candidate["p2_width_nm"]),
        float(candidate["internal_dx_nm"]),
        float(candidate["internal_dy_nm"]),
    )


def _number(value: object) -> int | float:
    number = float(value)
    return int(number) if number.is_integer() else number
