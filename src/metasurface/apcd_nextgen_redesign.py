from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence

from metasurface.apcd_active_learning import wrap_phase_deg
from metasurface.apcd_candidate_validation import estimate_periodic_image_gap_nm, estimate_same_cell_gap_nm


TARGET_BINS = [0.0, 60.0, 120.0, -180.0, -120.0, -60.0]
NEXTGEN_SELECTED_IDS = [
    "ng_zero_rot_release_07",
    "ng_neg60_dxdy_release_08",
    "ng_neg120_swap_asym_05",
    "ng_pi_wrap_lowleak_06",
    "ng_neg60_bridge_release_04",
]

ACCUMULATED_DIAGNOSIS_FIELDS = [
    "candidate_id",
    "candidate_family",
    "phase_deg",
    "target_bin_deg",
    "phase_error_to_target_deg",
    "target_conversion",
    "opposite_spin_leakage",
    "conversion_to_leakage_ratio",
    "PD",
    "overall_early_pass",
    "target_bin_status",
    "phase_region",
    "diagnosis_class",
    "usable_phase_region",
    "notes",
]

NEXTGEN_CANDIDATE_FIELDS = [
    "candidate_id",
    "candidate_family",
    "source_stage",
    "target_bin_deg",
    "anchor_candidate",
    "design_strategy",
    "design_rationale",
    "risk_level",
    "expected_phase_direction",
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
    "requires_geometry_validation",
    "requires_fdtd",
    "status",
    "notes",
]

NEXTGEN_VALIDATION_FIELDS = [
    "candidate_id",
    "candidate_family",
    "target_bin_deg",
    "same_cell_min_gap_nm",
    "periodic_image_min_gap_nm",
    "minimum_gap_nm_threshold",
    "bounds_pass",
    "same_cell_gap_pass",
    "periodic_gap_pass",
    "beta_selective_geometry_pass",
    "rotation_release_policy_pass",
    "duplicate_candidate_id_pass",
    "overall_geometry_pass",
    "recommended_for_fdtd",
    "notes",
]

NEXTGEN_SELECTION_FIELDS = [
    "selection_rank",
    "candidate_id",
    "candidate_family",
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

NEXTGEN_BOUNDS = {
    "p1_length_nm": (105.0, 155.0),
    "p1_width_nm": (50.0, 95.0),
    "p2_length_nm": (65.0, 112.0),
    "p2_width_nm": (125.0, 175.0),
    "internal_dx_nm": (-60.0, 60.0),
    "internal_dy_nm": (-60.0, 60.0),
    "p1_rotation_deg": (0.0, 180.0),
    "p2_rotation_deg": (0.0, 180.0),
    "period_x_nm": (320.0, 360.0),
    "period_y_nm": (320.0, 360.0),
    "height_nm": (280.0, 330.0),
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


def build_accumulated_fdtd_diagnosis(dataset_rows: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    rows = []
    for row in dataset_rows:
        phase = float(row["phase_deg"])
        target_bin = _optional_float(row.get("target_bin_deg"))
        error = "" if target_bin is None else abs(wrap_phase_deg(phase - target_bin))
        early = _is_true(row.get("overall_early_pass"))
        target_status = str(row.get("target_bin_status", ""))
        diagnosis = diagnose_result(row, error)
        rows.append(
            {
                "candidate_id": row["variant_id"],
                "candidate_family": row["candidate_family"],
                "phase_deg": phase,
                "target_bin_deg": "" if target_bin is None else _number(target_bin),
                "phase_error_to_target_deg": error,
                "target_conversion": row["target_conversion"],
                "opposite_spin_leakage": row["opposite_spin_leakage"],
                "conversion_to_leakage_ratio": row["conversion_to_leakage_ratio"],
                "PD": row["PD"],
                "overall_early_pass": early,
                "target_bin_status": target_status,
                "phase_region": row.get("phase_region", ""),
                "diagnosis_class": diagnosis,
                "usable_phase_region": usable_phase_region(phase, early),
                "notes": diagnosis_notes(diagnosis),
            }
        )
    return rows


def diagnose_result(row: dict[str, object], phase_error: object = "") -> str:
    early = _is_true(row.get("overall_early_pass"))
    status = str(row.get("target_bin_status", ""))
    phase = float(row["phase_deg"])
    target = _optional_float(row.get("target_bin_deg"))
    leakage = float(row["opposite_spin_leakage"])
    ratio = float(row["conversion_to_leakage_ratio"])
    if early and target is None and 60.0 <= phase <= 120.0:
        return "usable_existing_60_120_cluster"
    if status in {"strong_covered", "early_covered"} and early:
        return "usable_target_covered"
    if early and status in {"open_gap", "near_but_not_covered"}:
        return "early_pass_but_not_target"
    if target is not None and target < 0 and phase > 0 and status == "open_gap":
        return "negative_target_pulled_positive"
    if status == "evidence_only" and target is not None and abs(target) == 180 and (leakage > 0.2 or ratio < 6):
        return "phase_wrap_evidence_high_leakage"
    if status == "evidence_only" and (leakage > 0.2 or ratio < 6):
        return "phase_near_target_high_leakage"
    if not early and leakage > 0.2:
        return "high_leakage_not_usable"
    if phase_error != "" and float(phase_error) > 35:
        return "phase_far_from_target"
    return "other"


def usable_phase_region(phase: float, early: bool) -> str:
    if not early:
        return "not_usable"
    if 60.0 <= phase <= 120.0:
        return "usable_60_120_span"
    if 0.0 <= phase < 60.0:
        return "usable_0_60_span"
    if phase < 0.0:
        return "usable_negative_phase"
    return "usable_positive_above_120"


def diagnosis_notes(diagnosis: str) -> str:
    notes = {
        "usable_target_covered": "phase-near and early-pass; usable for its target bin",
        "early_pass_but_not_target": "optically good but phase is not close enough to the intended bin",
        "negative_target_pulled_positive": "negative-bin design returned to positive phase",
        "phase_wrap_evidence_high_leakage": "phase is near pi-wrap target but leakage/ratio fails",
        "phase_near_target_high_leakage": "phase evidence exists but leakage/ratio fails",
        "high_leakage_not_usable": "leakage bottleneck prevents using this phase point",
        "phase_far_from_target": "phase is too far from target bin",
        "usable_existing_60_120_cluster": "early-pass row in the dominant usable 60-120 deg phase cluster",
    }
    return notes.get(diagnosis, "diagnostic category not specific")


def summarize_phase_span(diagnosis_rows: Sequence[dict[str, object]]) -> dict[str, object]:
    usable = [row for row in diagnosis_rows if _is_true(row["overall_early_pass"])]
    phases = [float(row["phase_deg"]) for row in usable]
    target_usable = [row for row in usable if row["target_bin_status"] in {"strong_covered", "early_covered"}]
    return {
        "usable_count": len(usable),
        "usable_phase_min_deg": min(phases) if phases else "",
        "usable_phase_max_deg": max(phases) if phases else "",
        "usable_phase_span_deg": (max(phases) - min(phases)) if phases else "",
        "usable_60_120_count": sum(row["usable_phase_region"] == "usable_60_120_span" for row in usable),
        "usable_negative_count": sum(row["usable_phase_region"] == "usable_negative_phase" for row in usable),
        "target_covered_count": len(target_usable),
        "diagnosis_counts": dict(Counter(str(row["diagnosis_class"]) for row in diagnosis_rows)),
    }


def build_nextgen_candidate_pool() -> list[dict[str, object]]:
    specs: list[tuple[object, ...]] = []
    specs.extend(_zero_rotation_release_specs())
    specs.extend(_neg60_dxdy_release_specs())
    specs.extend(_neg120_swap_asym_specs())
    specs.extend(_pi_wrap_lowleak_specs())
    specs.extend(_expanded_dxdy_negative_specs())
    specs.extend(_height_period_optional_specs())
    rows = [_candidate_row(*spec) for spec in specs]
    if len(rows) != 60:
        raise ValueError(f"expected 60 nextgen candidates, got {len(rows)}")
    if len({row["candidate_id"] for row in rows}) != len(rows):
        raise ValueError("nextgen candidate_id values must be unique")
    return rows


def validate_nextgen_candidate_pool(candidates: Sequence[dict[str, object]], minimum_gap_nm: float = 5.0) -> list[dict[str, object]]:
    counts = Counter(str(row["candidate_id"]) for row in candidates)
    rows = []
    for candidate in candidates:
        same_cell = estimate_same_cell_gap_nm(candidate)
        periodic = estimate_periodic_image_gap_nm(candidate)
        bounds_errors = nextgen_bounds_errors(candidate)
        beta_pass = not (
            float(candidate["p2_length_nm"]) == 150.0 and float(candidate["p2_width_nm"]) == 85.0
        )
        rotation_pass = 0.0 <= float(candidate["p1_rotation_deg"]) <= 180.0 and 0.0 <= float(candidate["p2_rotation_deg"]) <= 180.0
        duplicate_pass = counts[str(candidate["candidate_id"])] == 1
        same_pass = same_cell >= minimum_gap_nm
        periodic_pass = periodic >= minimum_gap_nm
        overall = not bounds_errors and same_pass and periodic_pass and beta_pass and rotation_pass and duplicate_pass
        notes = []
        notes.extend(bounds_errors)
        if not same_pass:
            notes.append("same-cell gap below threshold")
        if not periodic_pass:
            notes.append("periodic-image gap below threshold")
        if not beta_pass:
            notes.append("beta-selective p2=150x85 geometry is forbidden")
        if not rotation_pass:
            notes.append("rotation release policy violated")
        if not duplicate_pass:
            notes.append("duplicate candidate_id")
        if not notes:
            notes.append("geometry sanity validation passed; optical response unknown")
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "candidate_family": candidate["candidate_family"],
                "target_bin_deg": candidate["target_bin_deg"],
                "same_cell_min_gap_nm": same_cell,
                "periodic_image_min_gap_nm": periodic,
                "minimum_gap_nm_threshold": minimum_gap_nm,
                "bounds_pass": not bounds_errors,
                "same_cell_gap_pass": same_pass,
                "periodic_gap_pass": periodic_pass,
                "beta_selective_geometry_pass": beta_pass,
                "rotation_release_policy_pass": rotation_pass,
                "duplicate_candidate_id_pass": duplicate_pass,
                "overall_geometry_pass": overall,
                "recommended_for_fdtd": overall,
                "notes": "; ".join(notes),
            }
        )
    return rows


def nextgen_bounds_errors(candidate: dict[str, object]) -> list[str]:
    errors = []
    for key, (lo, hi) in NEXTGEN_BOUNDS.items():
        value = float(candidate[key])
        if value < lo or value > hi:
            errors.append(f"{key}={value:g} outside [{lo:g}, {hi:g}]")
    return errors


def select_nextgen_fdtd_candidates(
    candidates: Sequence[dict[str, object]],
    validation_rows: Sequence[dict[str, object]],
) -> list[dict[str, object]]:
    recommended = {str(row["candidate_id"]): _is_true(row["recommended_for_fdtd"]) for row in validation_rows}
    by_id = {str(row["candidate_id"]): row for row in candidates}
    selected = []
    reasons = {
        "ng_zero_rot_release_07": "zero-bin top priority: rotation release plus moderated dy to attack 0 deg without repeating high-leakage evidence.",
        "ng_neg60_dxdy_release_08": "-60 top priority: strongest negative-bin dx/dy and rotation-release push while retaining low-leakage dimensions.",
        "ng_neg120_swap_asym_05": "-120 coverage: controlled swap/asymmetry probe without beta-selective p2 baseline.",
        "ng_pi_wrap_lowleak_06": "-180 coverage: pi-wrap evidence follow-up with leakage-control widths.",
        "ng_neg60_bridge_release_04": "bridge backup: tests whether positive 90 deg usable points can be pulled toward -60 with less leakage risk.",
    }
    priorities = {
        "ng_zero_rot_release_07": "top2_next_round",
        "ng_neg60_dxdy_release_08": "top2_next_round",
        "ng_neg120_swap_asym_05": "backup_selected_not_run",
        "ng_pi_wrap_lowleak_06": "backup_selected_not_run",
        "ng_neg60_bridge_release_04": "backup_selected_not_run",
    }
    for rank, candidate_id in enumerate(NEXTGEN_SELECTED_IDS, start=1):
        row = by_id[candidate_id]
        if not recommended[candidate_id]:
            raise ValueError(f"selected nextgen candidate failed geometry validation: {candidate_id}")
        selected.append(
            {
                "selection_rank": rank,
                "candidate_id": candidate_id,
                "candidate_family": row["candidate_family"],
                "target_bin_deg": row["target_bin_deg"],
                "anchor_candidate": row["anchor_candidate"],
                "selection_reason": reasons[candidate_id],
                "risk_level": row["risk_level"],
                "expected_phase_direction": row["expected_phase_direction"],
                "next_round_priority": priorities[candidate_id],
                "geometry_pass": True,
                "recommended_for_fdtd": True,
                "requires_fdtd": row["requires_fdtd"],
                "status": "selected_not_run",
                "notes": "Selection only for next round; no YAML/FDTD/lumapi/.fsp generated in 09-P33/P35.",
            }
        )
    return selected


def write_phase_span_bottleneck_analysis(path: str | Path, summary: dict[str, object], coverage_rows: Sequence[dict[str, object]]) -> Path:
    coverage = {float(row["phase_bin_deg"]): row["coverage_status"] for row in coverage_rows}
    lines = [
        "# APCD K=6 Phase-Span Bottleneck Analysis v5",
        "",
        "Scope: 09-P33/P35 accumulated diagnosis only. No FDTD/lumapi/.fsp/YAML/training was run or generated in this stage. No phase-ramp supercell was built.",
        "",
        f"Usable phase span: {summary['usable_phase_min_deg']} to {summary['usable_phase_max_deg']} deg.",
        f"Usable 60-120 deg count: {summary['usable_60_120_count']} of {summary['usable_count']} early-pass rows.",
        f"Usable negative-phase count: {summary['usable_negative_count']}.",
        "",
        "Coverage v5:",
        *[f"- `{bin_deg:g}` deg: `{status}`" for bin_deg, status in coverage.items()],
        "",
        "Diagnosis: the current APCD dimer family produces many low-leakage usable states between roughly 60 and 120 deg, but attempts to move to 0 deg, negative bins, or pi-wrap usually fail by leakage/ratio or return to positive phase.",
        "",
        "Failure modes:",
        "- phase-near target but leakage high: 0 deg and pi-wrap evidence points exist, but leakage/ratio fail.",
        "- early-pass but not target: some negative-bin candidates remain optically good but sit near positive phase.",
        "- phase-wrap evidence but leakage high: `pl_pi_wrap_04` is close to -180 deg but not usable.",
        "- negative target pulled back to positive phase: -60 redesign repeatedly returns near 80-100 deg.",
        "",
        "The K=6 phase-state library remains incomplete. This is not a +15 deg steering proof.",
    ]
    return _write_text(path, lines)


def write_nextgen_report(
    path: str | Path,
    summary: dict[str, object],
    candidates: Sequence[dict[str, object]],
    validation_rows: Sequence[dict[str, object]],
    selected_rows: Sequence[dict[str, object]],
) -> Path:
    family_counts = Counter(str(row["candidate_family"]) for row in candidates)
    pass_count = sum(_is_true(row["overall_geometry_pass"]) for row in validation_rows)
    lines = [
        "# APCD K=6 v5 Diagnosis and Next-Generation Redesign Plan",
        "",
        "## Scope",
        "",
        "This is 09-P33/P35. It summarizes accumulated real FDTD rows through dataset v5, diagnoses phase-span/leakage bottlenecks, and creates a next-generation candidate planning scaffold.",
        "",
        "No FDTD, lumapi, `.fsp`, YAML generation, old-pool run, K=7, phase-ramp supercell, TiO2/450 nm, Micro-LED integration, ML training, +15 deg steering claim, or complete K=6 phase-state library claim was made in this stage.",
        "",
        "## Accumulated Diagnosis",
        "",
        f"Usable phase span is {summary['usable_phase_min_deg']} to {summary['usable_phase_max_deg']} deg. The usable set is mainly concentrated in the 60-120 deg region, with no usable negative-phase state.",
        "",
        "Main bottleneck: expanding phase away from the 60-120 deg cluster tends to raise leakage or collapse back to positive phase. 0 deg and -180 deg have evidence-only rows, not usable states.",
        "",
        "## Next-Generation Strategy",
        "",
        "- Release fixed rotations 67.5/112.5 deg in a controlled way.",
        "- Expand internal dx/dy beyond the previous conservative neighborhood.",
        "- Redesign p1/p2 aspect-ratio families and test controlled swap/inversion without using beta-selective p2=150x85 nm.",
        "- Keep height/period as optional future knobs in a small scaffold, not as a broad sweep.",
        "- Separate zero-bin and negative-bin strategies instead of using one bridge pattern for all gaps.",
        "",
        "## Candidate Pool v6",
        "",
        f"Nextgen candidate count: {len(candidates)}",
        f"Geometry pass: {pass_count}/{len(validation_rows)}",
        "",
        "Family counts:",
        *[f"- `{key}`: {value}" for key, value in sorted(family_counts.items())],
        "",
        "## Selected Not Run",
        "",
        "| rank | candidate | target | family | next priority |",
        "|---:|---|---:|---|---|",
        *[
            f"| {row['selection_rank']} | `{row['candidate_id']}` | {row['target_bin_deg']} | `{row['candidate_family']}` | {row['next_round_priority']} |"
            for row in selected_rows
        ],
        "",
        "Next round should run the top-2 only first: `ng_zero_rot_release_07` and `ng_neg60_dxdy_release_08`.",
    ]
    return _write_text(path, lines)


def _candidate_row(
    candidate_id: str,
    family: str,
    target: float,
    anchor: str,
    strategy: str,
    rationale: str,
    risk: str,
    direction: str,
    p1_l: float,
    p1_w: float,
    p2_l: float,
    p2_w: float,
    dx: float,
    dy: float,
    r1: float,
    r2: float,
    period: float = 340.0,
    height: float = 300.0,
) -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "candidate_family": family,
        "source_stage": "09-P33/P35",
        "target_bin_deg": _number(target),
        "anchor_candidate": anchor,
        "design_strategy": strategy,
        "design_rationale": rationale,
        "risk_level": risk,
        "expected_phase_direction": direction,
        "p1_length_nm": _number(p1_l),
        "p1_width_nm": _number(p1_w),
        "p2_length_nm": _number(p2_l),
        "p2_width_nm": _number(p2_w),
        "p1_frac_x": 0.75,
        "p1_frac_y": 0.75,
        "p2_frac_x": 0.25,
        "p2_frac_y": 0.25,
        "internal_dx_nm": _number(dx),
        "internal_dy_nm": _number(dy),
        "p1_rotation_deg": _number(r1),
        "p2_rotation_deg": _number(r2),
        "period_x_nm": _number(period),
        "period_y_nm": _number(period),
        "height_nm": _number(height),
        "material": "c-Si",
        "substrate": "Al2O3",
        "requires_geometry_validation": "true",
        "requires_fdtd": "true",
        "status": "not_evaluated",
        "notes": "nextgen scaffold only; no YAML/FDTD/lumapi/.fsp generated; optical response unknown",
    }


def _zero_rotation_release_specs() -> list[tuple[object, ...]]:
    specs = []
    for i, (r1, r2, dx, dy, p1w, p2w) in enumerate(
        [
            (15, 60, -42, 32, 58, 140),
            (20, 70, -46, 36, 60, 142),
            (25, 80, -50, 40, 62, 144),
            (30, 90, -54, 44, 64, 146),
            (35, 95, -48, 48, 58, 148),
            (40, 100, -52, 52, 60, 150),
            (45, 105, -56, 56, 62, 152),
            (50, 110, -44, 50, 64, 154),
            (55, 115, -38, 46, 66, 150),
            (60, 120, -34, 42, 68, 148),
        ],
        start=1,
    ):
        specs.append((f"ng_zero_rot_release_{i:02d}", "rotation_released_zero_bin", 0, "next_zero_rot_anchor_03|pl_zero_bridge_04", "zero-bin rotation release", "Release rotations while keeping moderated widths to lower zero-bin leakage.", "moderate_to_high_risk", "toward 0 deg without high leakage", 116, p1w, 78, p2w, dx, dy, r1, r2))
    return specs


def _neg60_dxdy_release_specs() -> list[tuple[object, ...]]:
    specs = []
    for i, (r1, r2, dx, dy, p1l, p2w) in enumerate(
        [
            (55, 125, -44, -42, 120, 144),
            (60, 130, -48, -46, 122, 146),
            (65, 135, -52, -50, 124, 148),
            (70, 140, -56, -54, 126, 150),
            (75, 145, -60, -58, 128, 152),
            (80, 150, -50, -56, 130, 154),
            (85, 155, -54, -52, 132, 156),
            (90, 160, -58, -48, 134, 158),
            (95, 165, -46, -44, 128, 150),
            (100, 170, -42, -40, 126, 148),
        ],
        start=1,
    ):
        specs.append((f"ng_neg60_dxdy_release_{i:02d}", "rotation_released_neg60_dxdy", -60, "focus_neg60_geom_04|pl_neg60_focus_push_05", "negative-bin dx/dy expansion", "Push -60 using coupled negative dy and released rotations while preserving low-leakage dimensions.", "moderate_to_high_risk", "pull positive 90 deg usable point toward -60 deg", p1l, 58, 84, p2w, dx, dy, r1, r2))
    return specs


def _neg120_swap_asym_specs() -> list[tuple[object, ...]]:
    specs = []
    for i, (p1l, p1w, p2l, p2w, dx, dy, r1, r2) in enumerate(
        [
            (112, 66, 100, 136, 40, -36, 60, 135),
            (110, 68, 102, 138, 44, -40, 65, 145),
            (108, 70, 104, 140, 48, -44, 70, 155),
            (106, 72, 106, 142, 52, -48, 75, 165),
            (118, 64, 100, 134, 56, -52, 80, 150),
            (120, 66, 98, 132, 50, -56, 85, 140),
            (122, 68, 96, 130, 46, -50, 90, 130),
            (124, 70, 94, 128, 42, -46, 95, 120),
            (116, 74, 108, 144, 38, -42, 100, 110),
            (114, 76, 110, 146, 34, -38, 105, 100),
        ],
        start=1,
    ):
        specs.append((f"ng_neg120_swap_asym_{i:02d}", "controlled_swap_inversion_neg120", -120, "pl_neg120_aspect_03|gap_lhs_leakred_06", "controlled swap/inversion", "Probe p1/p2 aspect-ratio inversion without beta-selective p2 baseline.", "high_risk", "toward -120 deg with leakage-aware asymmetry", p1l, p1w, p2l, p2w, dx, dy, r1, r2))
    return specs


def _pi_wrap_lowleak_specs() -> list[tuple[object, ...]]:
    specs = []
    for i, (p1w, p2w, dx, dy, r1, r2) in enumerate(
        [
            (66, 136, 40, 40, 70, 130),
            (68, 138, 44, 44, 75, 140),
            (70, 140, 48, 48, 80, 150),
            (72, 142, 52, 52, 85, 160),
            (74, 144, 56, 56, 90, 170),
            (76, 146, 60, 50, 95, 165),
            (78, 148, 54, 46, 100, 155),
            (80, 150, 50, 42, 105, 145),
            (82, 152, 46, 38, 110, 135),
            (84, 154, 42, 34, 115, 125),
        ],
        start=1,
    ):
        specs.append((f"ng_pi_wrap_lowleak_{i:02d}", "pi_wrap_leakage_control", -180, "pl_pi_wrap_04|pl_neg120_aspect_03", "pi-wrap leakage control", "Follow pi-wrap evidence while widening p1 and trimming p2 width for lower leakage.", "high_risk", "retain -180 evidence while reducing leakage", 116, p1w, 100, p2w, dx, dy, r1, r2))
    return specs


def _expanded_dxdy_negative_specs() -> list[tuple[object, ...]]:
    specs = []
    for i, (target, dx, dy, r1, r2, p1w, p2w) in enumerate(
        [
            (-60, -60, -60, 45, 135, 58, 146),
            (-120, 60, -60, 55, 145, 62, 140),
            (-180, 60, 60, 65, 155, 70, 138),
            (-60, -56, 60, 75, 165, 60, 150),
            (-120, 56, -56, 85, 125, 64, 142),
            (-180, -52, 52, 95, 115, 72, 136),
            (0, -60, 56, 25, 95, 60, 144),
            (-60, -48, -60, 105, 175, 62, 148),
            (-120, 48, -52, 115, 105, 66, 146),
            (-180, 52, 48, 125, 95, 74, 140),
        ],
        start=1,
    ):
        candidate_id = "ng_neg60_bridge_release_04" if i == 4 else f"ng_expanded_dxdy_{i:02d}"
        specs.append((candidate_id, "expanded_internal_separation_negative_push", target, "pl_selected_v5|focus_neg60_geom_04", "expanded internal separation", "Expand dx/dy beyond earlier local neighborhoods while retaining safe gaps.", "moderate_to_high_risk", "test whether larger internal separation unlocks negative phase", 120, p1w, 90, p2w, dx, dy, r1, r2))
    return specs


def _height_period_optional_specs() -> list[tuple[object, ...]]:
    specs = []
    for i, (target, period, height, r1, r2, dx, dy) in enumerate(
        [
            (0, 330, 290, 30, 90, -44, 44),
            (-60, 330, 310, 70, 140, -52, -52),
            (-120, 330, 320, 85, 155, 48, -48),
            (-180, 330, 330, 95, 165, 52, 52),
            (0, 350, 290, 35, 95, -48, 48),
            (-60, 350, 310, 75, 145, -56, -48),
            (-120, 350, 320, 90, 160, 52, -44),
            (-180, 350, 330, 100, 170, 56, 44),
            (-60, 360, 300, 80, 150, -50, -50),
            (-120, 320, 300, 90, 140, 50, -50),
        ],
        start=1,
    ):
        specs.append((f"ng_optional_period_height_{i:02d}", "height_period_future_knob_scout", target, "dataset_v5_bottleneck", "optional height/period scout", "Small future-knob scaffold row; not a broad sweep and not prioritized before geometry/readiness review.", "future_knob_high_risk", "test optional period/height only after rotation/dxdy evidence", 118, 62, 88, 144, dx, dy, r1, r2, period, height))
    return specs


def _optional_float(value: object) -> float | None:
    if value in {"", None}:
        return None
    return float(value)


def _is_true(value: object) -> bool:
    return value is True or str(value) == "True"


def _number(value: object) -> int | float:
    number = float(value)
    return int(number) if number.is_integer() else number


def _write_text(path: str | Path, lines: Sequence[str]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
