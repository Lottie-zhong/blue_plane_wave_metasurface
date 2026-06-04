from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence

from metasurface.apcd_candidate_validation import polygon_min_distance_nm, rectangle_corners_nm


HELPER_V2_POOL_FIELDS = [
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
    "period_x_nm",
    "period_y_nm",
    "height_nm",
    "internal_dx_nm",
    "internal_dy_nm",
    "p3_helper_length_nm",
    "p3_helper_width_nm",
    "p3_helper_rotation_deg",
    "p3_helper_frac_x",
    "p3_helper_frac_y",
    "p3_helper_x_nm",
    "p3_helper_y_nm",
    "expected_phase_direction",
    "design_rationale",
    "risk_level",
    "requires_fdtd",
    "status",
    "notes",
]

HELPER_V2_VALIDATION_FIELDS = [
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
    "dimensions_bounds_pass",
    "helper_core_gap_pass",
    "beta_selective_geometry_pass",
    "duplicate_candidate_id_pass",
    "duplicate_geometry_pass",
    "overall_geometry_pass",
    "recommended_for_fdtd",
    "notes",
]

HELPER_V2_SELECTION_FIELDS = [
    "selection_rank",
    "candidate_id",
    "family",
    "target_bin_deg",
    "anchor_candidate",
    "selection_reason",
    "risk_level",
    "expected_phase_direction",
    "next_round_priority",
    "geometry_pass",
    "recommended_for_fdtd",
    "requires_fdtd",
    "status",
    "notes",
]

DIAGNOSIS_FIELDS = [
    "candidate_id",
    "family",
    "target_bin_deg",
    "phase_deg",
    "phase_error_to_target_deg",
    "target_conversion",
    "opposite_spin_leakage",
    "conversion_to_leakage_ratio",
    "early_pass",
    "target_bin_status",
    "failure_mode",
    "diagnosis",
]

SELECTED_IDS = [
    "wh2_zero_far_06",
    "wh2_neg60_detour_05",
    "wh2_pi_wrap_04",
    "wh2_lowleak_trim_03",
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


def build_v6_pilot_failure_diagnosis(result_rows: Sequence[dict[str, str]], helper_validation_rows: Sequence[dict[str, str]], dataset_rows: Sequence[dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    usable = [row for row in dataset_rows if str(row.get("overall_early_pass")) == "True"]
    usable_min = min(float(row["phase_deg"]) for row in usable)
    usable_max = max(float(row["phase_deg"]) for row in usable)
    helper_pass = sum(row["overall_geometry_pass"] == "True" for row in helper_validation_rows)
    helper_total = len(helper_validation_rows)
    overlap_fail = sum(_helper_v1_same_cell_gap_failed(row) for row in helper_validation_rows)
    for row in result_rows:
        failure_mode = classify_pilot_failure(row)
        rows.append(
            {
                "candidate_id": row["candidate_id"],
                "family": row["family"],
                "target_bin_deg": row["target_bin_deg"],
                "phase_deg": row["phase_deg"],
                "phase_error_to_target_deg": row["phase_error_to_target_deg"],
                "target_conversion": row["target_conversion"],
                "opposite_spin_leakage": row["opposite_spin_leakage"],
                "conversion_to_leakage_ratio": row["conversion_to_leakage_ratio"],
                "early_pass": row["early_pass"],
                "target_bin_status": row["target_bin_status"],
                "failure_mode": failure_mode,
                "diagnosis": (
                    f"{failure_mode}; helper_v1_geometry_pass={helper_pass}/{helper_total}; "
                    f"helper_v1_same_cell_overlap_or_gap_fail={overlap_fail}; "
                    f"current_usable_phase_span={usable_min:.4f}-{usable_max:.4f} deg"
                ),
            }
        )
    return rows


def classify_pilot_failure(row: dict[str, str]) -> str:
    if row["early_pass"] == "True" and row["target_bin_status"] in {"strong_covered", "early_covered"}:
        return "success"
    family = row["family"]
    leakage = float(row["opposite_spin_leakage"])
    ratio = float(row["conversion_to_leakage_ratio"])
    error = float(row["phase_error_to_target_deg"])
    if family == "rotation_released_zero_bin":
        return "released_rotation_zero_failed_leakage_and_phase_far"
    if family == "rotation_released_neg60_dxdy":
        return "released_dxdy_neg60_failed_leakage_and_phase_far"
    if family == "apcd_core_plus_weak_helper" and leakage > 0.2 and ratio < 6:
        return "weak_helper_failed_leakage_ratio_and_insufficient_phase_shift"
    if error <= 35 and (leakage > 0.2 or ratio < 6):
        return "phase_near_target_but_quality_failed"
    return "open_gap_quality_and_phase_failed"


def _helper_v1_same_cell_gap_failed(row: dict[str, str]) -> bool:
    if "same_cell_gap_pass" in row:
        return row["same_cell_gap_pass"] != "True"
    threshold = float(row.get("minimum_gap_nm_threshold") or 5.0)
    return float(row["same_cell_min_gap_nm"]) < threshold


def build_helper_v2_candidate_pool() -> list[dict[str, object]]:
    specs: list[tuple[object, ...]] = []
    specs.extend(_far_detour_specs())
    specs.extend(_medium_phase_delay_specs())
    specs.extend(_low_leakage_trim_specs())
    specs.extend(_zero_bridge_specs())
    specs.extend(_neg60_detour_specs())
    specs.extend(_pi_wrap_probe_specs())
    rows = [_candidate_row(*spec) for spec in specs]
    if len(rows) != 48:
        raise ValueError(f"expected 48 helper v2 candidates, got {len(rows)}")
    if len({row["candidate_id"] for row in rows}) != len(rows):
        raise ValueError("candidate_id values must be unique")
    return rows


def validate_helper_v2_pool(candidates: Sequence[dict[str, object]], minimum_gap_nm: float = 8.0) -> list[dict[str, object]]:
    seen_geometry: set[tuple[float, ...]] = set()
    id_counts = Counter(str(row["candidate_id"]) for row in candidates)
    rows = []
    for candidate in candidates:
        same_cell, periodic = _helper_v2_gaps(candidate)
        helper_core_gap = _helper_core_gap(candidate)
        bounds_pass = _bounds_pass(candidate)
        beta_pass = not (float(candidate["p2_length_nm"]) == 150.0 and float(candidate["p2_width_nm"]) == 85.0)
        geometry_key = _geometry_key(candidate)
        duplicate_geometry_pass = geometry_key not in seen_geometry
        seen_geometry.add(geometry_key)
        duplicate_id_pass = id_counts[str(candidate["candidate_id"])] == 1
        same_pass = same_cell >= minimum_gap_nm
        periodic_pass = periodic >= minimum_gap_nm
        helper_core_pass = helper_core_gap >= 18.0
        no_overlap_pass = same_cell > 0.0
        overall = all(
            [
                no_overlap_pass,
                same_pass,
                periodic_pass,
                bounds_pass,
                helper_core_pass,
                beta_pass,
                duplicate_id_pass,
                duplicate_geometry_pass,
            ]
        )
        notes = []
        if not no_overlap_pass:
            notes.append("pillar overlap detected")
        if not same_pass:
            notes.append("same-cell gap below threshold")
        if not periodic_pass:
            notes.append("periodic-image gap below threshold")
        if not bounds_pass:
            notes.append("dimension or position bounds failed")
        if not helper_core_pass:
            notes.append("helper-core gap below conservative threshold")
        if not beta_pass:
            notes.append("beta-selective p2=150x85 forbidden")
        if not duplicate_id_pass:
            notes.append("duplicate candidate_id")
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
                "minimum_gap_nm_threshold": minimum_gap_nm,
                "no_pillar_overlap_pass": no_overlap_pass,
                "same_cell_gap_pass": same_pass,
                "periodic_gap_pass": periodic_pass,
                "dimensions_bounds_pass": bounds_pass,
                "helper_core_gap_pass": helper_core_pass,
                "beta_selective_geometry_pass": beta_pass,
                "duplicate_candidate_id_pass": duplicate_id_pass,
                "duplicate_geometry_pass": duplicate_geometry_pass,
                "overall_geometry_pass": overall,
                "recommended_for_fdtd": overall,
                "notes": "; ".join(notes),
            }
        )
    return rows


def select_helper_v2_candidates(candidates: Sequence[dict[str, object]], validation_rows: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    valid = {row["candidate_id"] for row in validation_rows if str(row["recommended_for_fdtd"]) == "True" or row["recommended_for_fdtd"] is True}
    by_id = {row["candidate_id"]: row for row in candidates}
    reasons = {
        "wh2_zero_far_06": "top zero candidate: far detour helper with conservative gap and moderate helper strength.",
        "wh2_neg60_detour_05": "top -60 candidate: off-diagonal detour helper, selected to avoid v1 center-overlap failure.",
        "wh2_pi_wrap_04": "pi-wrap candidate: tests whether far helper can add phase delay without destroying core conversion.",
        "wh2_lowleak_trim_03": "low-risk leakage-trim backup: weakest helper for checking whether helper can preserve early pass.",
    }
    selected = []
    for rank, candidate_id in enumerate(SELECTED_IDS, start=1):
        if candidate_id not in valid:
            raise ValueError(f"selected helper v2 candidate failed validation: {candidate_id}")
        row = by_id[candidate_id]
        selected.append(
            {
                "selection_rank": rank,
                "candidate_id": candidate_id,
                "family": row["family"],
                "target_bin_deg": row["target_bin_deg"],
                "anchor_candidate": row["anchor_candidate"],
                "selection_reason": reasons[candidate_id],
                "risk_level": row["risk_level"],
                "expected_phase_direction": row["expected_phase_direction"],
                "next_round_priority": "top2_next_round" if rank <= 2 else "backup_selected_not_run",
                "geometry_pass": True,
                "recommended_for_fdtd": True,
                "requires_fdtd": row["requires_fdtd"],
                "status": "selected_not_run",
                "notes": "selection only; next round should run top-2 first; no YAML/FDTD/lumapi/.fsp in 09-P39/P41",
            }
        )
    return selected


def write_diagnosis_summary(path: str | Path, diagnosis_rows: Sequence[dict[str, object]], helper_validation_rows: Sequence[dict[str, str]], dataset_rows: Sequence[dict[str, str]]) -> Path:
    usable = [row for row in dataset_rows if row["overall_early_pass"] == "True"]
    lines = [
        "# APCD K=6 v6 Pilot Failure Diagnosis Summary",
        "",
        "Scope: 09-P39/P41 diagnosis only. No FDTD/lumapi/.fsp/YAML/training.",
        "",
        f"Current usable phase span: {min(float(row['phase_deg']) for row in usable)} to {max(float(row['phase_deg']) for row in usable)} deg.",
        f"Weak-helper v1 geometry pass: {sum(row['overall_geometry_pass'] == 'True' for row in helper_validation_rows)}/{len(helper_validation_rows)}.",
        "",
        "Failure modes:",
        *[f"- `{row['candidate_id']}`: {row['failure_mode']}" for row in diagnosis_rows],
        "",
        "Conclusion: released rotations, released dx/dy, and the first weak-helper pilot did not open a new usable phase region. The helper v1 pool failed mainly because center/near-core helper positions caused same-cell overlap or too-small gaps.",
    ]
    return _write_text(path, lines)


def write_selection_summary(path: str | Path, selected_rows: Sequence[dict[str, object]]) -> Path:
    lines = [
        "# APCD K=6 Weak-Helper v2 FDTD Selection Summary",
        "",
        "Scope: selection only. No YAML/FDTD/lumapi/.fsp.",
        "",
        "| rank | candidate | target | family | priority |",
        "|---:|---|---:|---|---|",
        *[
            f"| {row['selection_rank']} | `{row['candidate_id']}` | {row['target_bin_deg']} | `{row['family']}` | {row['next_round_priority']} |"
            for row in selected_rows
        ],
        "",
        "Next round should run top-2 first: `wh2_zero_far_06` and `wh2_neg60_detour_05`.",
    ]
    return _write_text(path, lines)


def write_report(
    path: str | Path,
    diagnosis_rows: Sequence[dict[str, object]],
    pool_rows: Sequence[dict[str, object]],
    validation_rows: Sequence[dict[str, object]],
    selected_rows: Sequence[dict[str, object]],
    dataset_rows: Sequence[dict[str, str]],
) -> Path:
    usable = [row for row in dataset_rows if row["overall_early_pass"] == "True"]
    family_counts = Counter(str(row["family"]) for row in pool_rows)
    pass_count = sum(str(row["overall_geometry_pass"]) == "True" for row in validation_rows)
    lines = [
        "# APCD K=6 v6 Pilot Diagnosis and Weak-Helper v2 Plan",
        "",
        "## Scope",
        "",
        "This is 09-P39/P41. It diagnoses the failed v6 pilot and designs a weak-helper / triatomic meta-molecule v2 candidate scaffold.",
        "",
        "No FDTD, lumapi, `.fsp`, YAML generation, old-pool run, full nextgen pool run, K=7, phase-ramp supercell, TiO2/450 nm, Micro-LED integration, ML training, +15 deg steering claim, or complete K=6 phase-state library claim was made.",
        "",
        "## v6 Diagnosis",
        "",
        f"Current usable phase span remains {min(float(row['phase_deg']) for row in usable)} to {max(float(row['phase_deg']) for row in usable)} deg, concentrated in 60-120 deg.",
        "",
        "- Released rotation did not fill 0 deg: it landed near 75.9 deg and failed leakage/ratio.",
        "- Released dx/dy did not fill -60 deg: it moved to positive 154.7 deg and failed leakage/ratio.",
        "- Weak-helper v1 did not early-pass: phase stayed near 78.6 deg and leakage/ratio failed.",
        "- Helper v1 geometry pass was low because center/near-core helper placements overlapped or violated same-cell gap.",
        "",
        "## Helper v2 Strategy",
        "",
        "APCD core remains responsible for spin-selective conversion. The helper is a standalone weak auxiliary phase shifter that provides additional target-channel phase freedom; it is not another APCD dimer and not half of another APCD pair.",
        "",
        f"Helper v2 pool rows: {len(pool_rows)}",
        f"Geometry pass: {pass_count}/{len(validation_rows)}",
        "",
        "Family counts:",
        *[f"- `{key}`: {value}" for key, value in sorted(family_counts.items())],
        "",
        "## Selected Not Run",
        "",
        "| rank | candidate | target | family | priority |",
        "|---:|---|---:|---|---|",
        *[
            f"| {row['selection_rank']} | `{row['candidate_id']}` | {row['target_bin_deg']} | `{row['family']}` | {row['next_round_priority']} |"
            for row in selected_rows
        ],
        "",
        "Next round: run only top-2 first, `wh2_zero_far_06` and `wh2_neg60_detour_05`.",
    ]
    return _write_text(path, lines)


def _far_detour_specs() -> list[tuple[object, ...]]:
    return [
        ("wh2_far_detour_01", 0, "ng_zero_rot_release_07", 38, 22, 0.16, 0.84, 0, "toward 0 with far weak detour"),
        ("wh2_far_detour_02", -60, "ng_neg60_dxdy_release_08", 38, 22, 0.84, 0.16, 20, "toward -60 with far weak detour"),
        ("wh2_far_detour_03", -120, "ng_neg120_swap_asym_05", 40, 24, 0.16, 0.16, 40, "negative-bin far detour"),
        ("wh2_far_detour_04", -180, "ng_pi_wrap_lowleak_06", 40, 24, 0.84, 0.84, 60, "pi-wrap far detour"),
        ("wh2_far_detour_05", 0, "ng_zero_rot_release_07", 42, 24, 0.18, 0.78, 80, "zero-bin off-diagonal detour"),
        ("wh2_zero_far_06", 0, "ng_zero_rot_release_07", 44, 24, 0.78, 0.18, 100, "selected zero-bin far detour"),
        ("wh2_far_detour_07", -60, "ng_neg60_dxdy_release_08", 44, 24, 0.22, 0.82, 120, "neg60 off-diagonal detour"),
        ("wh2_far_detour_08", -180, "ng_pi_wrap_lowleak_06", 46, 26, 0.82, 0.22, 140, "pi-wrap off-diagonal detour"),
    ]


def _medium_phase_delay_specs() -> list[tuple[object, ...]]:
    return [
        (f"wh2_medium_delay_{i:02d}", target, anchor, length, width, fx, fy, rot, direction)
        for i, (target, anchor, length, width, fx, fy, rot, direction) in enumerate(
            [
                (0, "ng_zero_rot_release_07", 52, 30, 0.15, 0.75, 15, "medium helper material phase for zero"),
                (-60, "ng_neg60_dxdy_release_08", 52, 30, 0.85, 0.25, 35, "medium helper material phase for -60"),
                (-120, "ng_neg120_swap_asym_05", 54, 32, 0.18, 0.18, 55, "medium negative-bin phase delay"),
                (-180, "ng_pi_wrap_lowleak_06", 54, 32, 0.82, 0.82, 75, "medium pi-wrap phase delay"),
                (0, "ng_zero_rot_release_07", 56, 34, 0.20, 0.70, 95, "stronger zero bridge delay"),
                (-60, "ng_neg60_dxdy_release_08", 56, 34, 0.80, 0.30, 115, "stronger -60 detour delay"),
                (-120, "ng_neg120_swap_asym_05", 58, 34, 0.24, 0.76, 135, "stronger -120 detour"),
                (-180, "ng_pi_wrap_lowleak_06", 58, 34, 0.76, 0.24, 155, "stronger pi-wrap detour"),
            ],
            start=1,
        )
    ]


def _low_leakage_trim_specs() -> list[tuple[object, ...]]:
    return [
        (f"wh2_lowleak_trim_{i:02d}", target, anchor, length, width, fx, fy, rot, "weak perturbation leakage trim")
        for i, (target, anchor, length, width, fx, fy, rot) in enumerate(
            [
                (0, "aggr_lhs_retention_dy_05", 32, 18, 0.12, 0.88, 0),
                (-60, "focus_neg60_geom_04", 32, 18, 0.88, 0.12, 30),
                (0, "ng_zero_rot_release_07", 34, 20, 0.24, 0.86, 60),
                (-60, "ng_neg60_dxdy_release_08", 34, 20, 0.86, 0.24, 90),
                (-120, "ng_neg120_swap_asym_05", 36, 20, 0.14, 0.14, 120),
                (-180, "ng_pi_wrap_lowleak_06", 36, 20, 0.86, 0.86, 150),
                (0, "aggr_p1w_leakctrl_04", 34, 18, 0.10, 0.70, 45),
                (-60, "pl_neg60_focus_push_05", 34, 18, 0.90, 0.30, 135),
            ],
            start=1,
        )
    ]


def _zero_bridge_specs() -> list[tuple[object, ...]]:
    return [
        (f"wh2_zero_bridge_{i:02d}", 0, anchor, length, width, fx, fy, rot, "zero-bin detour/material bridge")
        for i, (anchor, length, width, fx, fy, rot) in enumerate(
            [
                ("next_zero_rot_anchor_03", 42, 24, 0.14, 0.72, 10),
                ("focus_zero_leakred_07", 46, 26, 0.18, 0.68, 30),
                ("pl_zero_bridge_04", 50, 28, 0.22, 0.64, 50),
                ("ng_zero_rot_release_07", 54, 30, 0.26, 0.60, 70),
                ("aggr_lhs_retention_dy_05", 48, 26, 0.74, 0.14, 90),
                ("wh_zero_aux_phase_01", 44, 24, 0.70, 0.18, 110),
                ("ng_zero_rot_release_07", 52, 30, 0.30, 0.86, 130),
                ("pl_zero_bridge_04", 40, 22, 0.86, 0.30, 150),
            ],
            start=1,
        )
    ]


def _neg60_detour_specs() -> list[tuple[object, ...]]:
    specs = [
        ("wh2_neg60_detour_01", -60, "focus_neg60_geom_04", 42, 24, 0.12, 0.68, 15, "-60 far detour avoiding core center"),
        ("wh2_neg60_detour_02", -60, "pl_neg60_focus_push_05", 44, 24, 0.88, 0.32, 35, "-60 off-diagonal detour"),
        ("wh2_neg60_detour_03", -60, "ng_neg60_dxdy_release_08", 46, 26, 0.18, 0.62, 55, "-60 helper farther from core"),
        ("wh2_neg60_detour_04", -60, "ng_neg60_bridge_release_04", 48, 26, 0.82, 0.38, 75, "-60 bridge detour"),
        ("wh2_neg60_detour_05", -60, "ng_neg60_dxdy_release_08", 50, 28, 0.10, 0.46, 95, "selected -60 detour helper"),
        ("wh2_neg60_detour_06", -60, "focus_neg60_geom_04", 52, 28, 0.78, 0.42, 115, "-60 medium helper"),
        ("wh2_neg60_detour_07", -60, "pl_neg60_focus_push_05", 54, 30, 0.28, 0.54, 135, "-60 material phase helper"),
        ("wh2_neg60_detour_08", -60, "ng_neg60_dxdy_release_08", 56, 30, 0.72, 0.46, 155, "-60 stronger helper"),
    ]
    return specs


def _pi_wrap_probe_specs() -> list[tuple[object, ...]]:
    return [
        (f"wh2_pi_wrap_{i:02d}", target, anchor, length, width, fx, fy, rot, direction)
        for i, (target, anchor, length, width, fx, fy, rot, direction) in enumerate(
            [
                (-180, "pl_pi_wrap_04", 42, 24, 0.15, 0.15, 20, "pi-wrap weak detour"),
                (-180, "ng_pi_wrap_lowleak_06", 46, 26, 0.85, 0.85, 40, "pi-wrap leakage-control helper"),
                (-120, "pl_neg120_aspect_03", 48, 28, 0.15, 0.85, 60, "-120/pi bridge helper"),
                (-180, "ng_pi_wrap_lowleak_06", 50, 28, 0.85, 0.15, 80, "selected pi-wrap detour"),
                (-120, "ng_neg120_swap_asym_05", 52, 30, 0.20, 0.80, 100, "-120 medium phase helper"),
                (-180, "pl_pi_wrap_04", 54, 30, 0.80, 0.20, 120, "pi-wrap medium helper"),
                (-120, "ng_neg120_swap_asym_05", 56, 32, 0.24, 0.76, 140, "-120 stronger helper"),
                (-180, "ng_pi_wrap_lowleak_06", 58, 32, 0.76, 0.24, 160, "pi-wrap stronger helper"),
            ],
            start=1,
        )
    ]


def _candidate_row(
    candidate_id: str,
    target: float,
    anchor: str,
    helper_l: float,
    helper_w: float,
    helper_fx: float,
    helper_fy: float,
    helper_rot: float,
    direction: str,
) -> dict[str, object]:
    family = _family_from_id(candidate_id)
    p1_l, p1_w, p1_r, p2_l, p2_w, p2_r, dx, dy = _core_for_target(target)
    period = 340.0
    return {
        "candidate_id": candidate_id,
        "family": family,
        "target_bin_deg": _number(target),
        "anchor_candidate": anchor,
        "helper_role": "weak_auxiliary_phase_helper",
        "p1_length_nm": _number(p1_l),
        "p1_width_nm": _number(p1_w),
        "p1_rotation_deg": _number(p1_r),
        "p1_frac_x": 0.75,
        "p1_frac_y": 0.75,
        "p2_length_nm": _number(p2_l),
        "p2_width_nm": _number(p2_w),
        "p2_rotation_deg": _number(p2_r),
        "p2_frac_x": 0.25,
        "p2_frac_y": 0.25,
        "period_x_nm": _number(period),
        "period_y_nm": _number(period),
        "height_nm": 300,
        "internal_dx_nm": _number(dx),
        "internal_dy_nm": _number(dy),
        "p3_helper_length_nm": _number(helper_l),
        "p3_helper_width_nm": _number(helper_w),
        "p3_helper_rotation_deg": _number(helper_rot),
        "p3_helper_frac_x": helper_fx,
        "p3_helper_frac_y": helper_fy,
        "p3_helper_x_nm": (helper_fx - 0.5) * period,
        "p3_helper_y_nm": (helper_fy - 0.5) * period,
        "expected_phase_direction": direction,
        "design_rationale": "APCD core handles spin-selective conversion; standalone weak helper supplies extra target-channel phase freedom with safer detour placement.",
        "risk_level": _risk_for_family(family),
        "requires_fdtd": "true",
        "status": "not_evaluated",
        "notes": "helper v2 planning only; no YAML/FDTD/lumapi/.fsp; helper is not another APCD dimer",
    }


def _family_from_id(candidate_id: str) -> str:
    if "far_detour" in candidate_id or "zero_far" in candidate_id:
        return "helper_v2_weak_far_detour"
    if "medium_delay" in candidate_id:
        return "helper_v2_medium_phase_delay"
    if "lowleak_trim" in candidate_id:
        return "helper_v2_low_leakage_trim"
    if "zero_bridge" in candidate_id:
        return "helper_v2_zero_bridge"
    if "neg60_detour" in candidate_id:
        return "helper_v2_neg60_detour"
    return "helper_v2_pi_wrap_probe"


def _risk_for_family(family: str) -> str:
    if family in {"helper_v2_weak_far_detour", "helper_v2_low_leakage_trim"}:
        return "moderate_risk"
    if family in {"helper_v2_medium_phase_delay", "helper_v2_zero_bridge", "helper_v2_neg60_detour"}:
        return "moderate_to_high_risk"
    return "high_risk"


def _core_for_target(target: float) -> tuple[float, float, float, float, float, float, float, float]:
    if target == 0:
        return 116, 60, 35, 78, 144, 95, -46, 42
    if target == -60:
        return 122, 58, 75, 86, 148, 145, -54, -44
    if target == -120:
        return 112, 68, 80, 102, 138, 150, 44, -42
    return 116, 70, 90, 100, 140, 160, 48, 48


def _helper_v2_gaps(candidate: dict[str, object]) -> tuple[float, float]:
    polygons = _polygons(candidate)
    period_x = float(candidate["period_x_nm"])
    period_y = float(candidate["period_y_nm"])
    same = min(polygon_min_distance_nm(a, b) for i, a in enumerate(polygons) for b in polygons[i + 1 :])
    periodic = 1.0e9
    for a in polygons:
        for b in polygons:
            for sx in (-period_x, 0.0, period_x):
                for sy in (-period_y, 0.0, period_y):
                    if sx == 0.0 and sy == 0.0:
                        continue
                    shifted = [(x + sx, y + sy) for x, y in b]
                    periodic = min(periodic, polygon_min_distance_nm(a, shifted))
    return same, periodic


def _helper_core_gap(candidate: dict[str, object]) -> float:
    p1, p2, helper = _polygons(candidate)
    return min(polygon_min_distance_nm(helper, p1), polygon_min_distance_nm(helper, p2))


def _polygons(candidate: dict[str, object]) -> list[list[tuple[float, float]]]:
    p1_x, p1_y = _core_center(candidate, "p1")
    p2_x, p2_y = _core_center(candidate, "p2")
    return [
        rectangle_corners_nm(candidate["p1_length_nm"], candidate["p1_width_nm"], candidate["p1_rotation_deg"], p1_x, p1_y),
        rectangle_corners_nm(candidate["p2_length_nm"], candidate["p2_width_nm"], candidate["p2_rotation_deg"], p2_x, p2_y),
        rectangle_corners_nm(candidate["p3_helper_length_nm"], candidate["p3_helper_width_nm"], candidate["p3_helper_rotation_deg"], candidate["p3_helper_x_nm"], candidate["p3_helper_y_nm"]),
    ]


def _core_center(candidate: dict[str, object], prefix: str) -> tuple[float, float]:
    period_x = float(candidate["period_x_nm"])
    period_y = float(candidate["period_y_nm"])
    dx = float(candidate["internal_dx_nm"])
    dy = float(candidate["internal_dy_nm"])
    if prefix == "p1":
        return ((float(candidate["p1_frac_x"]) - 0.5) * period_x + dx / 2, (float(candidate["p1_frac_y"]) - 0.5) * period_y + dy / 2)
    return ((float(candidate["p2_frac_x"]) - 0.5) * period_x - dx / 2, (float(candidate["p2_frac_y"]) - 0.5) * period_y - dy / 2)


def _bounds_pass(candidate: dict[str, object]) -> bool:
    return (
        105 <= float(candidate["p1_length_nm"]) <= 155
        and 50 <= float(candidate["p1_width_nm"]) <= 95
        and 65 <= float(candidate["p2_length_nm"]) <= 112
        and 125 <= float(candidate["p2_width_nm"]) <= 175
        and 28 <= float(candidate["p3_helper_length_nm"]) <= 65
        and 16 <= float(candidate["p3_helper_width_nm"]) <= 40
        and -60 <= float(candidate["internal_dx_nm"]) <= 60
        and -60 <= float(candidate["internal_dy_nm"]) <= 60
        and 0 <= float(candidate["p3_helper_rotation_deg"]) <= 180
        and 0.08 <= float(candidate["p3_helper_frac_x"]) <= 0.92
        and 0.08 <= float(candidate["p3_helper_frac_y"]) <= 0.92
    )


def _geometry_key(candidate: dict[str, object]) -> tuple[float, ...]:
    keys = [
        "p1_length_nm",
        "p1_width_nm",
        "p1_rotation_deg",
        "p2_length_nm",
        "p2_width_nm",
        "p2_rotation_deg",
        "internal_dx_nm",
        "internal_dy_nm",
        "p3_helper_length_nm",
        "p3_helper_width_nm",
        "p3_helper_rotation_deg",
        "p3_helper_x_nm",
        "p3_helper_y_nm",
    ]
    return tuple(float(candidate[key]) for key in keys)


def _number(value: object) -> int | float:
    number = float(value)
    return int(number) if number.is_integer() else number


def _write_text(path: str | Path, lines: Sequence[str]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
