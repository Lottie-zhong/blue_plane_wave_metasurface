from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence

from metasurface.apcd_combined_phase_knob_plan import (
    COMBINED_POOL_FIELDS,
    COMBINED_SELECTION_FIELDS,
    COMBINED_VALIDATION_FIELDS,
    combined_candidate_gaps,
    write_csv_rows,
)

V10_FAMILIES = {
    "height_transition_sweep",
    "weak_helper_leakage_recovery",
    "helper_position_gap_recovery",
    "helper_rotation_recovery",
    "conservative_height_comparison",
}

V10_POOL_FIELDS = COMBINED_POOL_FIELDS
V10_VALIDATION_FIELDS = COMBINED_VALIDATION_FIELDS
V10_SELECTION_FIELDS = COMBINED_SELECTION_FIELDS
MIN_GAP_THRESHOLD_NM = 50.0


def build_v10_refinement_pool() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    rows.extend(_height_transition_sweep())
    rows.extend(_weak_helper_leakage_recovery())
    rows.extend(_helper_position_gap_recovery())
    rows.extend(_helper_rotation_recovery())
    rows.extend(_conservative_height_comparison())
    return rows


def validate_v10_refinement_pool(
    candidates: Sequence[dict[str, object]],
) -> list[dict[str, object]]:
    id_counts = Counter(str(row["candidate_id"]) for row in candidates)
    seen_geometry: set[tuple[float, ...]] = set()
    rows: list[dict[str, object]] = []

    for candidate in candidates:
        same_cell_gap, periodic_gap = combined_candidate_gaps(candidate)
        helper_core_gap = same_cell_gap
        geometry_key = _geometry_key(candidate)
        duplicate_geometry_pass = geometry_key not in seen_geometry
        seen_geometry.add(geometry_key)

        no_overlap = same_cell_gap > 0.0 and periodic_gap > 0.0
        same_pass = same_cell_gap >= MIN_GAP_THRESHOLD_NM
        periodic_pass = periodic_gap >= MIN_GAP_THRESHOLD_NM
        helper_core_pass = helper_core_gap >= MIN_GAP_THRESHOLD_NM
        dimensions_pass = _dimension_bounds_pass(candidate)
        height_period_pass = _height_period_bounds_pass(candidate)
        helper_role_pass = candidate["helper_role"] == "weak_auxiliary_phase_helper"
        helper_not_dimer_pass = str(candidate["family"]) in V10_FAMILIES
        beta_pass = not (
            float(candidate["p2_length_nm"]) == 150.0
            and float(candidate["p2_width_nm"]) == 85.0
        )
        duplicate_id_pass = id_counts[str(candidate["candidate_id"])] == 1

        checks = [
            no_overlap,
            same_pass,
            periodic_pass,
            helper_core_pass,
            dimensions_pass,
            height_period_pass,
            helper_role_pass,
            helper_not_dimer_pass,
            beta_pass,
            duplicate_id_pass,
            duplicate_geometry_pass,
        ]
        overall = all(checks)

        notes: list[str] = []
        if not same_pass:
            notes.append("same-cell gap below 50 nm")
        if not periodic_pass:
            notes.append("periodic-image gap below 50 nm")
        if not helper_core_pass:
            notes.append("helper-core gap below 50 nm")
        if not dimensions_pass:
            notes.append("geometry dimension bounds failed")
        if not height_period_pass:
            notes.append("height/period bounds failed")
        if not helper_role_pass:
            notes.append("helper role is not standalone weak auxiliary phase helper")
        if not helper_not_dimer_pass:
            notes.append("helper family is not allowed for v10 refinement")
        if not beta_pass:
            notes.append("rejected beta-selective pillar2 geometry")
        if not duplicate_id_pass:
            notes.append("duplicate candidate id")
        if not duplicate_geometry_pass:
            notes.append("duplicate geometry")
        if overall:
            notes.append("geometry/gap/sanity validation passed; optical response unknown until FDTD")

        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "family": candidate["family"],
                "target_bin_deg": candidate["target_bin_deg"],
                "same_cell_min_gap_nm": same_cell_gap,
                "periodic_image_min_gap_nm": periodic_gap,
                "helper_core_min_gap_nm": helper_core_gap,
                "minimum_gap_nm_threshold": MIN_GAP_THRESHOLD_NM,
                "no_pillar_overlap_pass": no_overlap,
                "same_cell_gap_pass": same_pass,
                "periodic_gap_pass": periodic_pass,
                "helper_core_gap_pass": helper_core_pass,
                "dimensions_bounds_pass": dimensions_pass,
                "height_period_bounds_pass": height_period_pass,
                "helper_role_pass": helper_role_pass,
                "helper_not_apcd_dimer_pass": helper_not_dimer_pass,
                "beta_selective_geometry_pass": beta_pass,
                "duplicate_candidate_id_pass": duplicate_id_pass,
                "duplicate_geometry_pass": duplicate_geometry_pass,
                "overall_geometry_pass": overall,
                "recommended_for_fdtd": overall,
                "notes": "; ".join(notes),
            }
        )

    return rows


def select_v10_refinement_candidates(
    candidates: Sequence[dict[str, object]],
    validation_rows: Sequence[dict[str, object]],
) -> list[dict[str, object]]:
    valid = {
        str(row["candidate_id"])
        for row in validation_rows
        if row["recommended_for_fdtd"] is True or str(row["recommended_for_fdtd"]) == "True"
    }
    by_id = {str(row["candidate_id"]): row for row in candidates}
    selection_plan = [
        (
            "cpk_refine_htrans_04",
            "410 nm transition-height candidate near cpk_height_prop_05; tests whether negative phase is kept while leakage recovers.",
            "top2_next_run",
        ),
        (
            "cpk_refine_weak_helper_03",
            "weaker helper anisotropy at 420 nm; targets leakage recovery around the negative-phase anchor.",
            "top2_next_run",
        ),
        (
            "cpk_refine_pos_gap_01",
            "slightly larger local period and symmetric helper offset; improves gap margin while preserving the height-propagation anchor.",
            "backup_selected_not_run",
        ),
        (
            "cpk_refine_helper_rot_04",
            "helper rotation recovery scout at 120 deg around the same 420 nm anchor.",
            "backup_selected_not_run",
        ),
        (
            "cpk_refine_htrans_05",
            "anchor-like 420 nm reference retained for reproducibility and comparison to cpk_height_prop_05.",
            "comparison_selected_not_run",
        ),
        (
            "cpk_refine_conservative_03",
            "380 nm conservative-height comparison to test whether leakage improves before the full 420 nm height.",
            "comparison_selected_not_run",
        ),
    ]

    selected: list[dict[str, object]] = []
    rank = 1
    for candidate_id, reason, priority in selection_plan:
        if candidate_id not in valid:
            continue
        row = by_id[candidate_id]
        selected.append(
            {
                "selection_rank": rank,
                "candidate_id": candidate_id,
                "family": row["family"],
                "target_bin_deg": row["target_bin_deg"],
                "selection_reason": reason,
                "risk_level": row["risk_level"],
                "expected_phase_direction": row["expected_phase_direction"],
                "geometry_pass": True,
                "recommended_for_fdtd": True,
                "requires_fdtd": row["requires_fdtd"],
                "status": "selected_not_run",
                "next_round_priority": priority,
                "notes": "09-P54/P56 planning only; no YAML/FDTD/lumapi/.fsp in this step",
            }
        )
        rank += 1

    return selected


def write_v10_refinement_report(
    path: str | Path,
    pool_rows: Sequence[dict[str, object]],
    validation_rows: Sequence[dict[str, object]],
    selected_rows: Sequence[dict[str, object]],
) -> Path:
    family_counts = Counter(str(row["family"]) for row in pool_rows)
    pass_count = sum(str(row["overall_geometry_pass"]) == "True" or row["overall_geometry_pass"] is True for row in validation_rows)

    lines = [
        "# 09-P54/P56 combined phase-knob v10 refinement planning",
        "",
        "## Scope",
        "",
        "This remains within the 09 stage. The `v10 refinement pool` is only the candidate-pool version following v9 planning.",
        "",
        "This step is planning only: no FDTD, no lumapi, no `.fsp`, no YAML generation, no K=6 phase-ramp supercell, no K=7 run, no TiO2/450 nm scaling, no Micro-LED integration, no ML/DenseNet/cVAE training, no +15 deg steering claim, and no complete K=6 phase-state library claim.",
        "",
        "## Anchor from 09-P51-P53",
        "",
        "`cpk_height_prop_05` is the key negative-phase anchor: target_conversion = 0.9278, leakage = 0.2058, ratio = 4.5091, PD = 0.6370, phase = -109.64 deg, early_pass = False.",
        "",
        "Interpretation: height/material propagation phase opened a useful negative phase, but leakage is slightly too high and the conversion-to-leakage ratio needs recovery.",
        "",
        "## v10 refinement pool",
        "",
        f"Candidate count: {len(pool_rows)}",
        f"Geometry-pass count: {pass_count}/{len(validation_rows)}",
        "",
        "Family distribution:",
        *[f"- `{family}`: {count}" for family, count in sorted(family_counts.items())],
        "",
        "The pool deliberately stays small and controlled. It focuses on height transition, weak-helper leakage recovery, helper-position gap recovery, helper-rotation recovery, and conservative height comparison.",
        "",
        "## Selected candidates",
        "",
        "| rank | candidate | family | target | priority |",
        "|---:|---|---|---:|---|",
        *[
            f"| {row['selection_rank']} | `{row['candidate_id']}` | `{row['family']}` | {row['target_bin_deg']} | {row['next_round_priority']} |"
            for row in selected_rows
        ],
        "",
        "Recommended first manual FDTD candidates after review: `cpk_refine_htrans_04` and `cpk_refine_weak_helper_03`.",
        "",
        "Do not describe this as completed steering or a completed phase-state library. It is a phase-state library refinement plan around the negative-phase anchor.",
    ]

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def _height_transition_sweep() -> list[dict[str, object]]:
    heights = [360, 380, 400, 410, 420, 430]
    return [
        _candidate_row(
            candidate_id=f"cpk_refine_htrans_{index:02d}",
            family="height_transition_sweep",
            height=height,
            period=340,
            helper_l=70,
            helper_w=120,
            helper_r=135,
            helper_x_nm=-85,
            helper_y_nm=85,
            expected_phase_direction="height transition around cpk_height_prop_05 for -120-like negative phase",
            risk="medium_high_risk" if height >= 410 else "medium_risk",
        )
        for index, height in enumerate(heights, start=1)
    ]


def _weak_helper_leakage_recovery() -> list[dict[str, object]]:
    helpers = [
        (60, 105, 135),
        (60, 110, 135),
        (65, 110, 120),
        (65, 115, 135),
        (70, 110, 150),
    ]
    return [
        _candidate_row(
            candidate_id=f"cpk_refine_weak_helper_{index:02d}",
            family="weak_helper_leakage_recovery",
            height=420,
            period=340,
            helper_l=helper_l,
            helper_w=helper_w,
            helper_r=helper_r,
            helper_x_nm=-85,
            helper_y_nm=85,
            expected_phase_direction="weaken helper perturbation to recover leakage while retaining negative phase",
            risk="medium_risk",
        )
        for index, (helper_l, helper_w, helper_r) in enumerate(helpers, start=1)
    ]


def _helper_position_gap_recovery() -> list[dict[str, object]]:
    params = [
        (360, -90, 90),
        (360, -100, 90),
        (360, -90, 100),
        (380, -95, 95),
        (380, -105, 95),
    ]
    return [
        _candidate_row(
            candidate_id=f"cpk_refine_pos_gap_{index:02d}",
            family="helper_position_gap_recovery",
            height=420,
            period=period,
            helper_l=70,
            helper_w=120,
            helper_r=135,
            helper_x_nm=helper_x,
            helper_y_nm=helper_y,
            expected_phase_direction="helper-position and gap recovery around height-propagation anchor",
            risk="medium_risk",
        )
        for index, (period, helper_x, helper_y) in enumerate(params, start=1)
    ]


def _helper_rotation_recovery() -> list[dict[str, object]]:
    rotations = [75, 90, 105, 120, 150]
    return [
        _candidate_row(
            candidate_id=f"cpk_refine_helper_rot_{index:02d}",
            family="helper_rotation_recovery",
            height=420,
            period=340,
            helper_l=70,
            helper_w=120,
            helper_r=rotation,
            helper_x_nm=-85,
            helper_y_nm=85,
            expected_phase_direction="helper rotation recovery around height-propagation anchor",
            risk="medium_risk" if rotation <= 120 else "medium_high_risk",
        )
        for index, rotation in enumerate(rotations, start=1)
    ]


def _conservative_height_comparison() -> list[dict[str, object]]:
    params = [
        (300, 80, 110, 135),
        (340, 75, 115, 135),
        (380, 70, 115, 135),
        (400, 70, 118, 135),
        (420, 65, 116, 135),
    ]
    return [
        _candidate_row(
            candidate_id=f"cpk_refine_conservative_{index:02d}",
            family="conservative_height_comparison",
            height=height,
            period=340,
            helper_l=helper_l,
            helper_w=helper_w,
            helper_r=helper_r,
            helper_x_nm=-85,
            helper_y_nm=85,
            expected_phase_direction="conservative height/helper comparison before full negative-phase refinement",
            risk="medium_risk" if height <= 380 else "medium_high_risk",
        )
        for index, (height, helper_l, helper_w, helper_r) in enumerate(params, start=1)
    ]


def _candidate_row(
    *,
    candidate_id: str,
    family: str,
    height: float,
    period: float,
    helper_l: float,
    helper_w: float,
    helper_r: float,
    helper_x_nm: float,
    helper_y_nm: float,
    expected_phase_direction: str,
    risk: str,
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "family": family,
        "target_bin_deg": -120,
        "anchor_candidate": "cpk_height_prop_05",
        "helper_role": "weak_auxiliary_phase_helper",
        "p1_length_nm": 130,
        "p1_width_nm": 70,
        "p1_rotation_deg": 67.5,
        "p1_frac_x": 0.75,
        "p1_frac_y": 0.75,
        "p2_length_nm": 85,
        "p2_width_nm": 150,
        "p2_rotation_deg": 112.5,
        "p2_frac_x": 0.25,
        "p2_frac_y": 0.25,
        "p3_length_nm": helper_l,
        "p3_width_nm": helper_w,
        "p3_rotation_deg": helper_r,
        "p3_frac_x": helper_x_nm / period + 0.5,
        "p3_frac_y": helper_y_nm / period + 0.5,
        "p3_x_nm": helper_x_nm,
        "p3_y_nm": helper_y_nm,
        "height_nm": height,
        "period_x_nm": period,
        "period_y_nm": period,
        "expected_phase_direction": expected_phase_direction,
        "design_rationale": "09-P54/P56 v10 refinement: keep APCD-core polarization selection while refining height/helper knobs around the cpk_height_prop_05 negative-phase evidence.",
        "risk_level": risk,
        "requires_fdtd": "true",
        "status": "not_evaluated",
        "notes": "09-P54/P56 planning only; v10 is candidate-pool version; standalone weak helper, not another APCD dimer; no YAML/FDTD/lumapi/.fsp",
    }


def _dimension_bounds_pass(candidate: dict[str, object]) -> bool:
    return (
        110.0 <= float(candidate["p1_length_nm"]) <= 150.0
        and 60.0 <= float(candidate["p1_width_nm"]) <= 90.0
        and 75.0 <= float(candidate["p2_length_nm"]) <= 100.0
        and 130.0 <= float(candidate["p2_width_nm"]) <= 165.0
        and 50.0 <= float(candidate["p3_length_nm"]) <= 130.0
        and 80.0 <= float(candidate["p3_width_nm"]) <= 140.0
        and 45.0 <= float(candidate["p1_rotation_deg"]) <= 90.0
        and 90.0 <= float(candidate["p2_rotation_deg"]) <= 135.0
        and 0.0 <= float(candidate["p3_rotation_deg"]) <= 180.0
    )


def _height_period_bounds_pass(candidate: dict[str, object]) -> bool:
    return (
        300.0 <= float(candidate["height_nm"]) <= 430.0
        and 330.0 <= float(candidate["period_x_nm"]) <= 390.0
        and float(candidate["period_x_nm"]) == float(candidate["period_y_nm"])
    )


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

