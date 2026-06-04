from __future__ import annotations

import csv
import math
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence

from metasurface.apcd_candidate_validation import polygon_min_distance_nm, rectangle_corners_nm


SELECTED_COMBINED_IDS = [
    "cpk_rot_release_02",
    "cpk_height_prop_05",
    "cpk_period_phase_04",
    "cpk_position_scout_01",
    "cpk_strong_delay_07",
]

DIAGNOSIS_FIELDS = [
    "candidate_id",
    "source_stage",
    "helper_group",
    "phase_deg",
    "opposite_spin_leakage",
    "conversion_to_leakage_ratio",
    "early_pass",
    "target_bin_status",
    "diagnosis_class",
    "notes",
]

COMBINED_POOL_FIELDS = [
    "candidate_id",
    "family",
    "target_bin_deg",
    "anchor_candidate",
    "helper_role",
    "p1_length_nm",
    "p1_width_nm",
    "p1_rotation_deg",
    "p1_frac_x",
    "p1_frac_y",
    "p2_length_nm",
    "p2_width_nm",
    "p2_rotation_deg",
    "p2_frac_x",
    "p2_frac_y",
    "p3_length_nm",
    "p3_width_nm",
    "p3_rotation_deg",
    "p3_frac_x",
    "p3_frac_y",
    "p3_x_nm",
    "p3_y_nm",
    "height_nm",
    "period_x_nm",
    "period_y_nm",
    "expected_phase_direction",
    "design_rationale",
    "risk_level",
    "requires_fdtd",
    "status",
    "notes",
]

COMBINED_VALIDATION_FIELDS = [
    "candidate_id",
    "family",
    "target_bin_deg",
    "same_cell_min_gap_nm",
    "periodic_image_min_gap_nm",
    "helper_core_min_gap_nm",
    "minimum_gap_nm_threshold",
    "no_pillar_overlap_pass",
    "same_cell_gap_pass",
    "periodic_gap_pass",
    "helper_core_gap_pass",
    "dimensions_bounds_pass",
    "height_period_bounds_pass",
    "helper_role_pass",
    "helper_not_apcd_dimer_pass",
    "beta_selective_geometry_pass",
    "duplicate_candidate_id_pass",
    "duplicate_geometry_pass",
    "overall_geometry_pass",
    "recommended_for_fdtd",
    "notes",
]

COMBINED_SELECTION_FIELDS = [
    "selection_rank",
    "candidate_id",
    "family",
    "target_bin_deg",
    "selection_reason",
    "risk_level",
    "expected_phase_direction",
    "geometry_pass",
    "recommended_for_fdtd",
    "requires_fdtd",
    "status",
    "next_round_priority",
    "notes",
]


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


def build_helper_plateau_diagnosis(v7_rows: Sequence[dict[str, str]], v8_rows: Sequence[dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    for row in list(v7_rows) + list(v8_rows):
        if str(row["run_status"]) != "completed":
            continue
        phase = float(row["phase_deg"])
        helper_group = _helper_group(row)
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "source_stage": "09-P42/P44" if str(row["candidate_id"]).startswith("h2_") else "09-P45/P47",
                "helper_group": helper_group,
                "phase_deg": phase,
                "opposite_spin_leakage": row["opposite_spin_leakage"],
                "conversion_to_leakage_ratio": row["conversion_to_leakage_ratio"],
                "early_pass": row["early_pass"],
                "target_bin_status": row["target_bin_status"],
                "diagnosis_class": _diagnosis_class(phase, row),
                "notes": _diagnosis_notes(helper_group, phase, row),
            }
        )
    return rows


def build_combined_phase_knob_candidate_pool() -> list[dict[str, object]]:
    specs: list[tuple[object, ...]] = []
    specs.extend(_rotation_specs())
    specs.extend(_height_specs())
    specs.extend(_period_specs())
    specs.extend(_position_specs())
    specs.extend(_strong_delay_specs())
    rows = [_candidate_row(*spec) for spec in specs]
    if len(rows) != 45:
        raise ValueError(f"expected 45 combined phase-knob candidates, got {len(rows)}")
    return rows


def validate_combined_candidate_pool(candidates: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    id_counts = Counter(str(row["candidate_id"]) for row in candidates)
    seen_geometry: set[tuple[float, ...]] = set()
    rows = []
    for candidate in candidates:
        same_cell, periodic = combined_candidate_gaps(candidate)
        helper_core_gap = _helper_core_gap(candidate)
        threshold = 60.0 if candidate["family"] == "strong_but_safe_phase_delay_helper" else 55.0
        geometry_key = _geometry_key(candidate)
        duplicate_geometry_pass = geometry_key not in seen_geometry
        seen_geometry.add(geometry_key)
        no_overlap = same_cell > 0.0
        same_pass = same_cell >= threshold
        periodic_pass = periodic >= threshold
        helper_core_pass = helper_core_gap >= threshold
        dimensions_pass = _dimension_bounds_pass(candidate)
        height_period_pass = _height_period_bounds_pass(candidate)
        role_pass = candidate["helper_role"] == "weak_auxiliary_phase_helper"
        not_dimer_pass = candidate["family"] in {
            "helper_plus_released_rotation",
            "helper_plus_height_propagation",
            "helper_plus_period_phase",
            "helper_position_phase_scout",
            "strong_but_safe_phase_delay_helper",
        }
        beta_pass = not (float(candidate["p2_length_nm"]) == 150.0 and float(candidate["p2_width_nm"]) == 85.0)
        duplicate_id_pass = id_counts[str(candidate["candidate_id"])] == 1
        overall = all(
            [
                no_overlap,
                same_pass,
                periodic_pass,
                helper_core_pass,
                dimensions_pass,
                height_period_pass,
                role_pass,
                not_dimer_pass,
                beta_pass,
                duplicate_id_pass,
                duplicate_geometry_pass,
            ]
        )
        notes = []
        if not same_pass:
            notes.append("same-cell gap below family threshold")
        if not periodic_pass:
            notes.append("periodic-image gap below family threshold")
        if not helper_core_pass:
            notes.append("helper-core gap below family threshold")
        if not dimensions_pass:
            notes.append("geometry dimension bounds failed")
        if not height_period_pass:
            notes.append("height/period bounds failed")
        if not duplicate_geometry_pass:
            notes.append("duplicate geometry")
        if not notes:
            notes.append("geometry/gap/sanity validation passed; optical response unknown")
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "family": candidate["family"],
                "target_bin_deg": candidate["target_bin_deg"],
                "same_cell_min_gap_nm": same_cell,
                "periodic_image_min_gap_nm": periodic,
                "helper_core_min_gap_nm": helper_core_gap,
                "minimum_gap_nm_threshold": threshold,
                "no_pillar_overlap_pass": no_overlap,
                "same_cell_gap_pass": same_pass,
                "periodic_gap_pass": periodic_pass,
                "helper_core_gap_pass": helper_core_pass,
                "dimensions_bounds_pass": dimensions_pass,
                "height_period_bounds_pass": height_period_pass,
                "helper_role_pass": role_pass,
                "helper_not_apcd_dimer_pass": not_dimer_pass,
                "beta_selective_geometry_pass": beta_pass,
                "duplicate_candidate_id_pass": duplicate_id_pass,
                "duplicate_geometry_pass": duplicate_geometry_pass,
                "overall_geometry_pass": overall,
                "recommended_for_fdtd": overall,
                "notes": "; ".join(notes),
            }
        )
    return rows


def select_combined_phase_knob_candidates(candidates: Sequence[dict[str, object]], validation_rows: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    valid = {str(row["candidate_id"]) for row in validation_rows if row["recommended_for_fdtd"] is True or str(row["recommended_for_fdtd"]) == "True"}
    by_id = {str(row["candidate_id"]): row for row in candidates}
    reasons = {
        "cpk_rot_release_02": "moderate released-rotation scout with helper similar to hr_aniso_push_08.",
        "cpk_height_prop_05": "top height propagation scout at 420 nm for material/propagation phase.",
        "cpk_period_phase_04": "largest period scout to test local environment phase without supercell assembly.",
        "cpk_position_scout_01": "safe helper-position scout near the empty diagonal corner at larger period.",
        "cpk_strong_delay_07": "strong but geometry-safe phase-delay helper at 400 nm period.",
    }
    selected = []
    for rank, candidate_id in enumerate(SELECTED_COMBINED_IDS, start=1):
        if candidate_id not in valid:
            raise ValueError(f"selected candidate failed geometry validation: {candidate_id}")
        row = by_id[candidate_id]
        selected.append(
            {
                "selection_rank": rank,
                "candidate_id": candidate_id,
                "family": row["family"],
                "target_bin_deg": row["target_bin_deg"],
                "selection_reason": reasons[candidate_id],
                "risk_level": row["risk_level"],
                "expected_phase_direction": row["expected_phase_direction"],
                "geometry_pass": True,
                "recommended_for_fdtd": True,
                "requires_fdtd": row["requires_fdtd"],
                "status": "selected_not_run",
                "next_round_priority": "top2_next_run" if rank <= 2 else "backup_selected_not_run",
                "notes": "selection only; no YAML/FDTD/lumapi/.fsp in 09-P48/P50",
            }
        )
    return selected


def write_diagnosis_summary(path: str | Path, diagnosis_rows: Sequence[dict[str, object]]) -> Path:
    early = [row for row in diagnosis_rows if str(row["early_pass"]) == "True"]
    max_phase = max(float(row["phase_deg"]) for row in early)
    plateau = [row for row in early if 120.0 <= float(row["phase_deg"]) <= 132.0]
    lines = [
        "# APCD K=6 Helper Plateau Diagnosis v8",
        "",
        f"Early-pass helper rows: {len(early)}",
        f"Early-pass helper phase maximum: {max_phase:.4f} deg",
        f"Rows in 120-132 deg plateau: {len(plateau)}/{len(early)}",
        "",
        "Conclusion: square/near-square helpers preserve low leakage near 116-121 deg, weak anisotropic helpers push to about 128-132 deg, and gap-fixed phase-delay helpers did not outperform anisotropic helpers. Continuing same-family local helper tuning is likely low yield.",
    ]
    return _write_text(path, lines)


def write_pool_summary(path: str | Path, pool_rows: Sequence[dict[str, object]]) -> Path:
    family_counts = Counter(str(row["family"]) for row in pool_rows)
    lines = [
        "# APCD K=6 Combined Phase-Knob Candidate Pool v9",
        "",
        f"Pool rows: {len(pool_rows)}",
        "",
        "Family distribution:",
        *[f"- `{family}`: {count}" for family, count in sorted(family_counts.items())],
        "",
        "Scope: planning only. No YAML, FDTD, lumapi, .fsp, K=7, phase-ramp supercell, or ML training.",
    ]
    return _write_text(path, lines)


def write_validation_summary(path: str | Path, validation_rows: Sequence[dict[str, object]]) -> Path:
    pass_count = sum(str(row["overall_geometry_pass"]) == "True" for row in validation_rows)
    lines = [
        "# APCD K=6 Combined Phase-Knob Geometry Validation v9",
        "",
        f"Geometry pass: {pass_count}/{len(validation_rows)}",
        "",
        "| candidate | family | same gap | periodic gap | threshold | pass | notes |",
        "|---|---|---:|---:|---:|---|---|",
        *[
            f"| `{row['candidate_id']}` | `{row['family']}` | {row['same_cell_min_gap_nm']} | {row['periodic_image_min_gap_nm']} | {row['minimum_gap_nm_threshold']} | {row['overall_geometry_pass']} | {row['notes']} |"
            for row in validation_rows
        ],
    ]
    return _write_text(path, lines)


def write_selection_summary(path: str | Path, selected_rows: Sequence[dict[str, object]]) -> Path:
    lines = [
        "# APCD K=6 Combined Phase-Knob FDTD Selection v9",
        "",
        "Selection only. No YAML/FDTD/lumapi/.fsp in 09-P48/P50.",
        "",
        "| rank | candidate | family | target | priority |",
        "|---:|---|---|---:|---|",
        *[
            f"| {row['selection_rank']} | `{row['candidate_id']}` | `{row['family']}` | {row['target_bin_deg']} | {row['next_round_priority']} |"
            for row in selected_rows
        ],
        "",
        "Recommended next run top-2: `cpk_rot_release_02` and `cpk_height_prop_05`.",
    ]
    return _write_text(path, lines)


def write_report(
    path: str | Path,
    diagnosis_rows: Sequence[dict[str, object]],
    pool_rows: Sequence[dict[str, object]],
    validation_rows: Sequence[dict[str, object]],
    selected_rows: Sequence[dict[str, object]],
) -> Path:
    max_phase = max(float(row["phase_deg"]) for row in diagnosis_rows if str(row["early_pass"]) == "True")
    pass_count = sum(str(row["overall_geometry_pass"]) == "True" for row in validation_rows)
    lines = [
        "# APCD K=6 Helper Plateau and Combined Phase-Knob Plan",
        "",
        "## Scope",
        "",
        "This is 09-P48/P50. It diagnoses the v8 helper phase plateau and plans a combined phase-knob v9 candidate pool.",
        "",
        "No FDTD, lumapi, `.fsp`, YAML generation, full old-pool run, K=7, phase-ramp supercell, TiO2/450 nm, Micro-LED integration, ML/DenseNet/cVAE training, random/freeform helper, +15 deg steering claim, or complete K=6 phase-state library claim was made.",
        "",
        "## Plateau Diagnosis",
        "",
        f"The highest early-pass helper phase is {max_phase:.4f} deg. Helper prototype/refinement results show a low-leakage plateau around 120-132 deg.",
        "",
        "- Square/near-square helpers keep leakage low but stay near 116-121 deg.",
        "- Weak anisotropic helpers are the best helper-only phase-push family but saturate near 128-132 deg.",
        "- Gap-fixed phase-delay helpers preserve low leakage but did not push phase beyond anisotropic helpers.",
        "- 0 deg, -60 deg, -120 deg, and -180 deg are still not covered by usable phase states.",
        "",
        "## Why Combined Knobs",
        "",
        "The next step needs coupled phase knobs because helper-only local geometry appears to preserve amplitude but offers limited phase span. Released rotations may perturb the complex amplitude direction; height and period are propagation/material phase scouts rather than supercell or steering tests.",
        "",
        "## v9 Pool",
        "",
        f"Pool rows: {len(pool_rows)}",
        f"Geometry pass: {pass_count}/{len(validation_rows)}",
        "",
        "## Selected Not Run",
        "",
        "| rank | candidate | family | target | priority |",
        "|---:|---|---|---:|---|",
        *[
            f"| {row['selection_rank']} | `{row['candidate_id']}` | `{row['family']}` | {row['target_bin_deg']} | {row['next_round_priority']} |"
            for row in selected_rows
        ],
        "",
        "Recommended next run top-2: `cpk_rot_release_02` and `cpk_height_prop_05`.",
    ]
    return _write_text(path, lines)


def combined_candidate_gaps(candidate: dict[str, object]) -> tuple[float, float]:
    period_x = float(candidate["period_x_nm"])
    period_y = float(candidate["period_y_nm"])
    polygons = _polygons(candidate)
    same = min(polygon_min_distance_nm(a, b) for index, a in enumerate(polygons) for b in polygons[index + 1 :])
    periodic = math.inf
    for a in polygons:
        for b in polygons:
            for sx in (-period_x, 0.0, period_x):
                for sy in (-period_y, 0.0, period_y):
                    if sx == 0.0 and sy == 0.0:
                        continue
                    shifted = [(x + sx, y + sy) for x, y in b]
                    periodic = min(periodic, polygon_min_distance_nm(a, shifted))
    return same, periodic


def _rotation_specs() -> list[tuple[object, ...]]:
    params = [
        (-15, 80, 110, 135, "medium_high_risk"),
        (-7.5, 80, 110, 135, "medium_risk"),
        (7.5, 80, 110, 135, "medium_risk"),
        (15, 80, 110, 135, "high_risk"),
        (-7.5, 70, 120, 135, "medium_risk"),
        (7.5, 70, 120, 90, "medium_risk"),
        (-15, 60, 120, 135, "medium_high_risk"),
        (15, 60, 120, 90, "high_risk"),
        (0, 90, 110, 90, "medium_risk"),
    ]
    return [
        (f"cpk_rot_release_{i:02d}", "helper_plus_released_rotation", -180, "hr_aniso_push_08", 130, 70, 67.5 + off, 85, 150, 112.5 + off, h_l, h_w, h_r, 0.25, 0.75, 300, 340, "rotation offset scout with weak anisotropic helper", risk)
        for i, (off, h_l, h_w, h_r, risk) in enumerate(params, start=1)
    ]


def _height_specs() -> list[tuple[object, ...]]:
    heights = [260, 300, 340, 380, 420, 260, 340, 380, 420]
    helpers = [(80, 110, 135), (75, 115, 120), (90, 110, 90), (70, 120, 135), (70, 120, 135), (60, 120, 90), (65, 120, 135), (85, 110, 90), (90, 120, 135)]
    return [
        (f"cpk_height_prop_{i:02d}", "helper_plus_height_propagation", -180, "hr_aniso_push_08" if i % 2 else "hr_phase_delay_03", 130, 70, 67.5, 85, 150, 112.5, l, w, r, 0.25, 0.75, h, 340, "height/material propagation phase scout", "medium_risk" if h <= 340 else "medium_high_risk")
        for i, (h, (l, w, r)) in enumerate(zip(heights, helpers), start=1)
    ]


def _period_specs() -> list[tuple[object, ...]]:
    periods = [340, 370, 400, 430, 370, 400, 430, 400, 430]
    helpers = [(80, 110, 135), (80, 120, 135), (90, 110, 90), (90, 120, 135), (75, 115, 120), (100, 130, 135), (90, 130, 135), (80, 120, 90), (65, 120, 135)]
    return [
        (f"cpk_period_phase_{i:02d}", "helper_plus_period_phase", -180, "hr_aniso_push_08", 130, 70, 67.5, 85, 150, 112.5, l, w, r, 0.25, 0.75, 300, p, "period/local environment phase scout without supercell", "medium_risk" if p <= 400 else "medium_high_risk")
        for i, (p, (l, w, r)) in enumerate(zip(periods, helpers), start=1)
    ]


def _position_specs() -> list[tuple[object, ...]]:
    positions = [(-85, 85), (-105, 85), (-65, 85), (-85, 65), (-85, 105), (-105, 65), (-65, 105), (-105, 105), (-65, 65)]
    periods = [370, 370, 370, 370, 370, 400, 400, 400, 400]
    specs = []
    for i, ((x, y), period) in enumerate(zip(positions, periods), start=1):
        specs.append((f"cpk_position_scout_{i:02d}", "helper_position_phase_scout", -180, "hr_aniso_push_08", 130, 70, 67.5, 85, 150, 112.5, 80, 110, 135, x / period + 0.5, y / period + 0.5, 300, period, "helper detour-position phase scout with safe shifts", "medium_risk"))
    return specs


def _strong_delay_specs() -> list[tuple[object, ...]]:
    params = [
        (80, 120, 135, 370),
        (90, 120, 135, 370),
        (90, 130, 135, 370),
        (100, 130, 135, 370),
        (80, 120, 90, 400),
        (90, 120, 90, 400),
        (90, 130, 135, 400),
        (100, 130, 135, 400),
        (100, 130, 90, 430),
    ]
    return [
        (f"cpk_strong_delay_{i:02d}", "strong_but_safe_phase_delay_helper", -180, "h2_phase_delay_04", 130, 70, 67.5, 85, 150, 112.5, l, w, r, 0.25, 0.75, 300, p, "stronger safe rectangular helper toward pi-near phase", "high_risk")
        for i, (l, w, r, p) in enumerate(params, start=1)
    ]


def _candidate_row(
    candidate_id: str,
    family: str,
    target: float,
    anchor: str,
    p1_l: float,
    p1_w: float,
    p1_r: float,
    p2_l: float,
    p2_w: float,
    p2_r: float,
    h_l: float,
    h_w: float,
    h_r: float,
    h_fx: float,
    h_fy: float,
    height: float,
    period: float,
    direction: str,
    risk: str,
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "family": family,
        "target_bin_deg": target,
        "anchor_candidate": anchor,
        "helper_role": "weak_auxiliary_phase_helper",
        "p1_length_nm": p1_l,
        "p1_width_nm": p1_w,
        "p1_rotation_deg": p1_r,
        "p1_frac_x": 0.75,
        "p1_frac_y": 0.75,
        "p2_length_nm": p2_l,
        "p2_width_nm": p2_w,
        "p2_rotation_deg": p2_r,
        "p2_frac_x": 0.25,
        "p2_frac_y": 0.25,
        "p3_length_nm": h_l,
        "p3_width_nm": h_w,
        "p3_rotation_deg": h_r,
        "p3_frac_x": h_fx,
        "p3_frac_y": h_fy,
        "p3_x_nm": (h_fx - 0.5) * period,
        "p3_y_nm": (h_fy - 0.5) * period,
        "height_nm": height,
        "period_x_nm": period,
        "period_y_nm": period,
        "expected_phase_direction": direction,
        "design_rationale": "Combined phase-knob scout: keep APCD core spin-selective role while combining helper with rotation/height/period/position propagation phase knobs.",
        "risk_level": risk,
        "requires_fdtd": "true",
        "status": "not_evaluated",
        "notes": "planning only; standalone weak helper, not another APCD dimer; no YAML/FDTD/lumapi/.fsp in 09-P48/P50",
    }


def _helper_group(row: dict[str, str]) -> str:
    candidate_id = str(row["candidate_id"])
    family = str(row.get("family", ""))
    if "square" in candidate_id or "control" in candidate_id:
        return "square_or_nearsquare_loading"
    if "phase_delay" in candidate_id:
        return "phase_delay_helper"
    if "aniso" in candidate_id or family == "aniso_helper_phase_push":
        return "weak_anisotropic_helper"
    return "other_helper"


def _diagnosis_class(phase: float, row: dict[str, str]) -> str:
    if str(row["early_pass"]) != "True":
        return "quality_failed"
    if 120.0 <= phase <= 132.0:
        return "low_leakage_phase_plateau_120_132"
    if phase < 120.0:
        return "low_leakage_lower_positive_phase"
    return "low_leakage_high_positive_extension"


def _diagnosis_notes(helper_group: str, phase: float, row: dict[str, str]) -> str:
    return (
        f"{helper_group}; phase={phase:.4f}; leakage={row['opposite_spin_leakage']}; "
        f"ratio={row['conversion_to_leakage_ratio']}; helper-only local tuning did not cover 0/-60/-120/-180 bins"
    )


def _polygons(candidate: dict[str, object]) -> list[list[tuple[float, float]]]:
    return [
        rectangle_corners_nm(candidate["p1_length_nm"], candidate["p1_width_nm"], candidate["p1_rotation_deg"], *_center(candidate, "p1")),
        rectangle_corners_nm(candidate["p2_length_nm"], candidate["p2_width_nm"], candidate["p2_rotation_deg"], *_center(candidate, "p2")),
        rectangle_corners_nm(candidate["p3_length_nm"], candidate["p3_width_nm"], candidate["p3_rotation_deg"], candidate["p3_x_nm"], candidate["p3_y_nm"]),
    ]


def _center(candidate: dict[str, object], prefix: str) -> tuple[float, float]:
    period_x = float(candidate["period_x_nm"])
    period_y = float(candidate["period_y_nm"])
    if prefix == "p1":
        return ((float(candidate["p1_frac_x"]) - 0.5) * period_x, (float(candidate["p1_frac_y"]) - 0.5) * period_y)
    return ((float(candidate["p2_frac_x"]) - 0.5) * period_x, (float(candidate["p2_frac_y"]) - 0.5) * period_y)


def _helper_core_gap(candidate: dict[str, object]) -> float:
    p1, p2, helper = _polygons(candidate)
    return min(polygon_min_distance_nm(helper, p1), polygon_min_distance_nm(helper, p2))


def _dimension_bounds_pass(candidate: dict[str, object]) -> bool:
    return (
        110.0 <= float(candidate["p1_length_nm"]) <= 150.0
        and 55.0 <= float(candidate["p1_width_nm"]) <= 90.0
        and 70.0 <= float(candidate["p2_length_nm"]) <= 105.0
        and 130.0 <= float(candidate["p2_width_nm"]) <= 170.0
        and 50.0 <= float(candidate["p3_length_nm"]) <= 110.0
        and 70.0 <= float(candidate["p3_width_nm"]) <= 130.0
        and 45.0 <= float(candidate["p1_rotation_deg"]) <= 90.0
        and 90.0 <= float(candidate["p2_rotation_deg"]) <= 135.0
        and 0.0 <= float(candidate["p3_rotation_deg"]) <= 180.0
    )


def _height_period_bounds_pass(candidate: dict[str, object]) -> bool:
    return 250.0 <= float(candidate["height_nm"]) <= 430.0 and 330.0 <= float(candidate["period_x_nm"]) <= 440.0 and float(candidate["period_x_nm"]) == float(candidate["period_y_nm"])


def _geometry_key(candidate: dict[str, object]) -> tuple[float, ...]:
    keys = [
        "p1_length_nm",
        "p1_width_nm",
        "p1_rotation_deg",
        "p2_length_nm",
        "p2_width_nm",
        "p2_rotation_deg",
        "p3_length_nm",
        "p3_width_nm",
        "p3_rotation_deg",
        "p3_x_nm",
        "p3_y_nm",
        "height_nm",
        "period_x_nm",
    ]
    return tuple(float(candidate[key]) for key in keys)


def _write_text(path: str | Path, lines: Sequence[str]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
