from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence

from metasurface.apcd_active_learning import DEFAULT_BASELINE, wrap_phase_deg
from metasurface.apcd_candidate_validation import estimate_periodic_image_gap_nm, estimate_same_cell_gap_nm


EARLY_TARGET_CONVERSION_MIN = 0.5
EARLY_OPPOSITE_SPIN_LEAKAGE_MAX = 0.2
EARLY_CONVERSION_TO_LEAKAGE_RATIO_MIN = 6.0
TARGET_BINS = [0.0, 60.0, 120.0, -180.0, -120.0, -60.0]

PHASE_COVERAGE_V4_FIELDS = [
    "phase_bin_deg",
    "nearest_candidate_all",
    "nearest_phase_all",
    "nearest_error_all",
    "nearest_candidate_early_pass",
    "nearest_phase_early_pass",
    "nearest_error_early_pass",
    "nearest_candidate_evidence_only",
    "nearest_phase_evidence_only",
    "nearest_error_evidence_only",
    "coverage_status",
    "notes",
]

PHASE_LOWERING_CANDIDATE_FIELDS = [
    "candidate_id",
    "candidate_family",
    "source_stage",
    "target_bin_deg",
    "anchor_candidate",
    "source_reference",
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

PHASE_LOWERING_VALIDATION_FIELDS = [
    "candidate_id",
    "candidate_family",
    "target_bin_deg",
    "same_cell_min_gap_nm",
    "periodic_image_min_gap_nm",
    "minimum_gap_nm_threshold",
    "bounds_pass",
    "same_cell_gap_pass",
    "periodic_gap_pass",
    "duplicate_candidate_id_pass",
    "duplicate_geometry_pass",
    "rotation_reasonable_pass",
    "beta_selective_geometry_pass",
    "overall_geometry_pass",
    "recommended_for_fdtd",
    "notes",
]

PHASE_LOWERING_SELECTION_FIELDS = [
    "selection_rank",
    "candidate_id",
    "candidate_family",
    "target_bin_deg",
    "anchor_candidate",
    "selection_reason",
    "design_rationale",
    "risk_level",
    "expected_phase_direction",
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

SELECTED_PHASE_LOWERING_IDS = [
    "pl_zero_bridge_04",
    "pl_neg60_focus_push_05",
    "pl_neg120_aspect_03",
    "pl_pi_wrap_04",
]

SELECTION_REASONS = {
    "pl_zero_bridge_04": "0 deg bridge from focus_neg60 toward the strongest 0 deg evidence, with moderated leakage risk.",
    "pl_neg60_focus_push_05": "-60 deg phase-lowering candidate using coupled dx/dy and width coordination from the low-leakage focus anchor.",
    "pl_neg120_aspect_03": "-120 deg candidate probing controlled aspect-ratio inversion without beta-selective p2 geometry.",
    "pl_pi_wrap_04": "-180 deg pi-wrap hypothesis candidate using stronger dimer asymmetry from the focus anchor.",
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


def build_geometry_lookup(pool_paths: Iterable[str | Path]) -> dict[str, dict[str, str]]:
    lookup: dict[str, dict[str, str]] = {}
    for path in pool_paths:
        candidate_path = Path(path)
        if not candidate_path.exists():
            continue
        for row in read_csv_rows(candidate_path):
            candidate_id = row.get("candidate_id") or row.get("variant_id")
            if candidate_id:
                lookup[candidate_id] = row
    return lookup


def build_ml_dataset_v4(
    v3_rows: Iterable[dict[str, str]],
    p26_result_rows: Iterable[dict[str, str]],
    geometry_lookup: dict[str, dict[str, str]],
    columns: Sequence[str],
) -> tuple[list[dict[str, object]], list[str]]:
    output_columns = list(columns)
    for column in ("phase_region", "target_bin_deg", "target_bin_status"):
        if column not in output_columns:
            output_columns.append(column)
    rows: list[dict[str, object]] = []
    seen = set()
    for row in v3_rows:
        enriched = dict(row)
        enriched["phase_region"] = classify_phase_region(enriched)
        rows.append({column: enriched.get(column, "") for column in output_columns})
        seen.add(str(row["variant_id"]))

    for result in p26_result_rows:
        candidate_id = str(result["candidate_id"])
        if candidate_id in seen:
            continue
        geometry = geometry_lookup.get(candidate_id, {})
        t_alpha = complex(result["t_alpha_star_from_alpha"])
        row = {column: "" for column in output_columns}
        row.update(
            {
                "variant_id": candidate_id,
                "candidate_family": result["candidate_family"],
                "phase_deg": result["phase_deg"],
                "phase_shift_vs_baseline_deg": result["phase_shift_vs_baseline_deg"],
                "target_conversion": result["target_conversion"],
                "opposite_spin_leakage": result["opposite_spin_leakage"],
                "conversion_to_leakage_ratio": result["conversion_to_leakage_ratio"],
                "PD": result["PD"],
                "overall_early_pass": result["early_pass"],
                "t_alpha_star_from_alpha_real": t_alpha.real,
                "t_alpha_star_from_alpha_imag": t_alpha.imag,
                "t_alpha_star_from_alpha_abs": abs(t_alpha),
                "target_bin_deg": result["target_bin_deg"],
                "target_bin_status": result["target_bin_status"],
                "source_result_csv": "summary_only:outputs/apcd_k6_active_learning/focused_next_gap_top2_fdtd_results_v3.csv",
                "notes": (
                    f"09-P27 dataset v4 row from 09-P26 summary; target_bin_status={result['target_bin_status']}; "
                    "usable only if early-pass and close to target; no new FDTD in this stage; not steering result"
                ),
            }
        )
        for field in (
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
            row[field] = geometry.get(field, row.get(field, ""))
        row["phase_region"] = classify_phase_region(row)
        rows.append({column: row.get(column, "") for column in output_columns})
        seen.add(candidate_id)
    return rows, output_columns


def classify_phase_region(row: dict[str, object]) -> str:
    status = str(row.get("target_bin_status", ""))
    early = is_early_pass(row)
    if status == "evidence_only":
        return "target_bin_evidence_only"
    if status == "open_gap" and early:
        return "usable_but_not_target"
    if status == "open_gap":
        return "target_bin_open_gap"
    phase = float(row["phase_deg"])
    if early and 60.0 <= phase <= 90.0:
        return "60_90_usable"
    if early and 90.0 < phase <= 120.0:
        return "90_120_usable"
    if 45.0 <= phase <= 75.0 and not early:
        return "high_leakage_phase_evidence"
    return "other"


def is_early_pass(row: dict[str, object]) -> bool:
    for key in ("early_pass", "overall_early_pass"):
        if key in row and row[key] not in {"", None}:
            return str(row[key]) == "True" or row[key] is True
    return (
        float(row["target_conversion"]) >= EARLY_TARGET_CONVERSION_MIN
        and float(row["opposite_spin_leakage"]) <= EARLY_OPPOSITE_SPIN_LEAKAGE_MAX
        and float(row["conversion_to_leakage_ratio"]) >= EARLY_CONVERSION_TO_LEAKAGE_RATIO_MIN
    )


def angular_distance_deg(phase_deg: float, target_deg: float) -> float:
    return abs(wrap_phase_deg(float(phase_deg) - float(target_deg)))


def analyze_phase_coverage_v4(dataset_rows: Sequence[dict[str, object]], targets: Sequence[float] = TARGET_BINS) -> list[dict[str, object]]:
    early_rows = [row for row in dataset_rows if is_early_pass(row)]
    evidence_rows = [row for row in dataset_rows if _is_phase_evidence_row(row)]
    coverage = []
    for target in targets:
        nearest_all = _nearest_phase_row(dataset_rows, target)
        nearest_early = _nearest_phase_row(early_rows, target)
        nearest_evidence = _nearest_phase_row(evidence_rows, target)
        status = _coverage_status(nearest_early, nearest_evidence)
        coverage.append(
            {
                "phase_bin_deg": float(target),
                "nearest_candidate_all": nearest_all.get("variant_id", ""),
                "nearest_phase_all": nearest_all.get("phase_deg", ""),
                "nearest_error_all": nearest_all.get("phase_error_deg", ""),
                "nearest_candidate_early_pass": nearest_early.get("variant_id", ""),
                "nearest_phase_early_pass": nearest_early.get("phase_deg", ""),
                "nearest_error_early_pass": nearest_early.get("phase_error_deg", ""),
                "nearest_candidate_evidence_only": nearest_evidence.get("variant_id", ""),
                "nearest_phase_evidence_only": nearest_evidence.get("phase_deg", ""),
                "nearest_error_evidence_only": nearest_evidence.get("phase_error_deg", ""),
                "coverage_status": status,
                "notes": _coverage_notes(float(target), status, nearest_early, nearest_evidence),
            }
        )
    return coverage


def build_phase_lowering_candidate_pool() -> list[dict[str, object]]:
    specs: list[tuple[object, ...]] = []
    specs.extend(_focus_push_specs())
    specs.extend(_zero_bridge_specs())
    specs.extend(_pi_wrap_specs())
    specs.extend(_coupled_dx_dy_specs())
    specs.extend(_aspect_ratio_specs())
    specs.extend(_mixed_safe_specs())
    rows = [_candidate_row(*spec) for spec in specs]
    _validate_pool_policy(rows)
    return rows


def validate_phase_lowering_candidate_pool(
    candidates: Iterable[dict[str, object]],
    existing_candidates: Iterable[dict[str, object]] = (),
    minimum_gap_nm: float = 5.0,
) -> list[dict[str, object]]:
    candidate_list = list(candidates)
    id_counts = Counter(str(row["candidate_id"]) for row in candidate_list)
    existing_keys = {_geometry_key(row) for row in existing_candidates}
    seen: set[tuple[float, ...]] = set()
    rows = []
    for candidate in candidate_list:
        same_cell_gap = estimate_same_cell_gap_nm(candidate)
        periodic_gap = estimate_periodic_image_gap_nm(candidate)
        bounds_errors = _bounds_errors(candidate)
        key = _geometry_key(candidate)
        duplicate_candidate_id_pass = id_counts[str(candidate["candidate_id"])] == 1
        duplicate_geometry_pass = key not in existing_keys and key not in seen
        rotation_reasonable_pass = 0.0 <= float(candidate["p1_rotation_deg"]) < 180.0 and 0.0 <= float(candidate["p2_rotation_deg"]) < 180.0
        beta_pass = not (float(candidate["p2_length_nm"]) == 150.0 and float(candidate["p2_width_nm"]) == 85.0)
        same_pass = same_cell_gap >= minimum_gap_nm
        periodic_pass = periodic_gap >= minimum_gap_nm
        bounds_pass = not bounds_errors
        overall = all([bounds_pass, same_pass, periodic_pass, duplicate_candidate_id_pass, duplicate_geometry_pass, rotation_reasonable_pass, beta_pass])
        notes = []
        notes.extend(bounds_errors)
        if not duplicate_candidate_id_pass:
            notes.append("duplicate candidate_id")
        if not duplicate_geometry_pass:
            notes.append("duplicate geometry")
        if not rotation_reasonable_pass:
            notes.append("rotation outside [0, 180)")
        if not beta_pass:
            notes.append("beta-selective p2 geometry is not allowed")
        if not same_pass:
            notes.append("same-cell gap below threshold")
        if not periodic_pass:
            notes.append("periodic-image gap below threshold")
        if not notes:
            notes.append("geometry sanity validation passed; optical response unknown")
        rows.append(
            {
                "candidate_id": candidate["candidate_id"],
                "candidate_family": candidate["candidate_family"],
                "target_bin_deg": candidate["target_bin_deg"],
                "same_cell_min_gap_nm": same_cell_gap,
                "periodic_image_min_gap_nm": periodic_gap,
                "minimum_gap_nm_threshold": minimum_gap_nm,
                "bounds_pass": bounds_pass,
                "same_cell_gap_pass": same_pass,
                "periodic_gap_pass": periodic_pass,
                "duplicate_candidate_id_pass": duplicate_candidate_id_pass,
                "duplicate_geometry_pass": duplicate_geometry_pass,
                "rotation_reasonable_pass": rotation_reasonable_pass,
                "beta_selective_geometry_pass": beta_pass,
                "overall_geometry_pass": overall,
                "recommended_for_fdtd": overall,
                "notes": "; ".join(notes),
            }
        )
        seen.add(key)
    return rows


def select_phase_lowering_fdtd_candidates(
    candidates: Sequence[dict[str, object]],
    validation_rows: Sequence[dict[str, object]],
    selected_ids: Sequence[str] = SELECTED_PHASE_LOWERING_IDS,
) -> list[dict[str, object]]:
    candidate_by_id = {str(row["candidate_id"]): row for row in candidates}
    validation_by_id = {str(row["candidate_id"]): row for row in validation_rows}
    rows = []
    for rank, candidate_id in enumerate(selected_ids, start=1):
        candidate = candidate_by_id[candidate_id]
        validation = validation_by_id[candidate_id]
        if str(validation["overall_geometry_pass"]) != "True" or str(validation["recommended_for_fdtd"]) != "True":
            raise ValueError(f"{candidate_id} is not geometry-pass/recommended")
        rows.append(
            {
                "selection_rank": rank,
                "candidate_id": candidate_id,
                "candidate_family": candidate["candidate_family"],
                "target_bin_deg": candidate["target_bin_deg"],
                "anchor_candidate": candidate["anchor_candidate"],
                "selection_reason": SELECTION_REASONS[candidate_id],
                "design_rationale": candidate["design_rationale"],
                "risk_level": candidate["risk_level"],
                "expected_phase_direction": candidate["expected_phase_direction"],
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
                "notes": "09-P28 selection only; recommend running top-2 only next; no YAML/FDTD/lumapi/.fsp in this stage",
            }
        )
    _validate_selection_policy(rows)
    return rows


def write_dataset_v4_report(path: str | Path, rows: Sequence[dict[str, object]]) -> Path:
    new_rows = [row for row in rows if str(row["variant_id"]).startswith("focus_")]
    lines = [
        "# APCD K=6 ML-Ready Dataset v4 Collection Report",
        "",
        "Scope: 09-P27 dataset/evidence update only. No FDTD was run in this stage. No lumapi call was made. No `.fsp` file was generated.",
        "",
        f"Dataset v4 rows: {len(rows)}",
        f"Early-pass rows: {sum(is_early_pass(row) for row in rows)}",
        "",
        "Added 09-P26 rows:",
        *[
            f"- `{row['variant_id']}`: phase `{row['phase_deg']}` deg, phase_region `{row['phase_region']}`, target_bin_status `{row['target_bin_status']}`, early_pass `{row['overall_early_pass']}`."
            for row in new_rows
        ],
        "",
        "`focus_zero_leakred_07` remains evidence_only, not usable. `focus_neg60_geom_04` is early-pass but usable_but_not_target for -60 deg.",
    ]
    return _write_text(path, lines)


def write_phase_gap_analysis_v4(path: str | Path, coverage_rows: Sequence[dict[str, object]]) -> Path:
    by_bin = {float(row["phase_bin_deg"]): row for row in coverage_rows}
    lines = [
        "# APCD K=6 Phase Gap Analysis v4",
        "",
        "Scope: 09-P27 phase coverage update only. No FDTD was run in this stage. No phase-ramp supercell was built.",
        "",
        f"60 deg bin status: `{by_bin[60.0]['coverage_status']}`.",
        f"120 deg bin status: `{by_bin[120.0]['coverage_status']}`.",
        f"0 deg bin status: `{by_bin[0.0]['coverage_status']}`.",
        f"-60 deg bin status: `{by_bin[-60.0]['coverage_status']}`.",
        f"-120 deg bin status: `{by_bin[-120.0]['coverage_status']}`.",
        f"-180 deg bin status: `{by_bin[-180.0]['coverage_status']}`.",
        "",
        "`focus_neg60_geom_04` is a high-quality positive-phase candidate, not a -60 deg phase-state candidate.",
        "",
        "| bin deg | nearest early-pass | early error | nearest evidence-only | evidence error | status |",
        "|---:|---|---:|---|---:|---|",
        *[
            f"| {row['phase_bin_deg']} | {row['nearest_candidate_early_pass']} | {row['nearest_error_early_pass']} | "
            f"{row['nearest_candidate_evidence_only']} | {row['nearest_error_evidence_only']} | {row['coverage_status']} |"
            for row in coverage_rows
        ],
        "",
        "The K=6 phase-state library is still incomplete. This is not a +15 deg steering proof.",
    ]
    return _write_text(path, lines)


def write_k6_readiness_v4(path: str | Path, coverage_rows: Sequence[dict[str, object]]) -> Path:
    not_ready = [row for row in coverage_rows if row["coverage_status"] not in {"strong_covered", "early_covered"}]
    lines = [
        "# APCD K=6 Phase-State Readiness v4",
        "",
        "Readiness decision: not ready for K=6 phase-ramp supercell assembly.",
        "",
        f"Bins still not usable: {', '.join(str(row['phase_bin_deg']) for row in not_ready)}",
        "",
        "Reason: 0 deg remains evidence-only, while -60, -120, and -180 deg remain open gaps. No steering claim is supported.",
    ]
    return _write_text(path, lines)


def write_phase_lowering_pool_summary(path: str | Path, candidates: Sequence[dict[str, object]]) -> Path:
    family_counts = Counter(str(row["candidate_family"]) for row in candidates)
    target_counts = Counter(str(row["target_bin_deg"]) for row in candidates)
    lines = [
        "# APCD K=6 Phase-Lowering Candidate Pool v4 Summary",
        "",
        "Scope: 09-P28 phase-lowering candidate planning only. No FDTD/lumapi/.fsp/training.",
        "",
        f"Candidate count: {len(candidates)}",
        "",
        "Family counts:",
        *[f"- `{key}`: {value}" for key, value in sorted(family_counts.items())],
        "",
        "Target bin counts:",
        *[f"- `{key}`: {value}" for key, value in sorted(target_counts.items())],
    ]
    return _write_text(path, lines)


def write_phase_lowering_validation_summary(path: str | Path, rows: Sequence[dict[str, object]]) -> Path:
    lines = [
        "# APCD K=6 Phase-Lowering Geometry Validation v4 Summary",
        "",
        "Scope: geometry/gap/sanity validation only. Geometry pass does not imply optical pass.",
        "",
        f"Candidate count: {len(rows)}",
        f"Geometry pass: {sum(str(row['overall_geometry_pass']) == 'True' for row in rows)}",
        f"Recommended for FDTD: {sum(str(row['recommended_for_fdtd']) == 'True' for row in rows)}",
        f"Minimum same-cell gap nm: {min(float(row['same_cell_min_gap_nm']) for row in rows)}",
        f"Minimum periodic-image gap nm: {min(float(row['periodic_image_min_gap_nm']) for row in rows)}",
    ]
    return _write_text(path, lines)


def write_phase_lowering_selection_summary(path: str | Path, rows: Sequence[dict[str, object]]) -> Path:
    lines = [
        "# APCD K=6 Phase-Lowering FDTD Selection v4 Summary",
        "",
        "Scope: selected_not_run planning only. No YAML config was generated. No FDTD was run.",
        "",
        f"Selected count: {len(rows)}",
        *[
            f"- rank {row['selection_rank']}: `{row['candidate_id']}` target `{row['target_bin_deg']}` family `{row['candidate_family']}` risk `{row['risk_level']}`."
            for row in rows
        ],
        "",
        "Recommended next action: generate YAML and run only the top-2 selected candidates first; do not run the full pool.",
    ]
    return _write_text(path, lines)


def write_phase_lowering_report(
    path: str | Path,
    coverage_rows: Sequence[dict[str, object]],
    candidates: Sequence[dict[str, object]],
    validation_rows: Sequence[dict[str, object]],
    selection_rows: Sequence[dict[str, object]],
) -> Path:
    by_bin = {float(row["phase_bin_deg"]): row for row in coverage_rows}
    lines = [
        "# APCD K=6 Phase-Lowering Redesign v4 Note",
        "",
        "## Scope",
        "",
        "This is 09-P27/P28. This stage updates dataset/coverage with 09-P26 results and designs a phase-lowering candidate pool. No FDTD was run, no lumapi call was made, and no `.fsp` file was generated in this stage.",
        "",
        "## Why 09-P26 Did Not Fill the Gaps",
        "",
        "`focus_zero_leakred_07` did not fill 0 deg: it stayed evidence_only and its leakage did not improve over the previous zero evidence point.",
        "",
        "`focus_neg60_geom_04` is valuable because it is low leakage, high ratio, and early-pass, but its phase is 83.13394588891055 deg. It is a high-quality positive-phase candidate, not a -60 deg candidate.",
        "",
        "## Coverage v4",
        "",
        f"0 deg: `{by_bin[0.0]['coverage_status']}`; 60 deg: `{by_bin[60.0]['coverage_status']}`; 120 deg: `{by_bin[120.0]['coverage_status']}`.",
        f"-60 deg: `{by_bin[-60.0]['coverage_status']}`; -120 deg: `{by_bin[-120.0]['coverage_status']}`; -180 deg: `{by_bin[-180.0]['coverage_status']}`.",
        "",
        "## Phase-Lowering Redesign Logic",
        "",
        "The new pool uses `focus_neg60_geom_04` as the low-leakage/high-quality anchor and explores geometry-driven phase-lowering: coupled dx/dy, coordinated widths, length asymmetry, aspect-ratio inversion tendency, dimer asymmetry strengthening, pi-wrap probes, and bridges toward existing 0 deg evidence.",
        "",
        f"Pool count: {len(candidates)}.",
        f"Geometry pass: {sum(str(row['overall_geometry_pass']) == 'True' for row in validation_rows)}.",
        "",
        "## Selected Candidates",
        *[
            f"- `{row['candidate_id']}` target `{row['target_bin_deg']}`: {row['selection_reason']}"
            for row in selection_rows
        ],
        "",
        "Recommended next step: generate YAML and run only the top-2 selected candidates first. Do not run the full pool.",
        "",
        "## Boundaries",
        "",
        "No FDTD, no lumapi, no `.fsp`, no K=7, no phase-ramp supercell, no TiO2/450 nm, no Micro-LED integration, no DenseNet/cVAE training, no +15 deg steering claim, and no claim that the K=6 phase-state library is complete.",
    ]
    return _write_text(path, lines)


def existing_geometry_rows_from_paths(paths: Iterable[str | Path]) -> list[dict[str, object]]:
    rows = []
    for path in paths:
        candidate_path = Path(path)
        if candidate_path.exists():
            rows.extend(read_csv_rows(candidate_path))
    return rows


def _focus_push_specs() -> list[tuple[object, ...]]:
    return [
        ("pl_neg60_focus_push_01", "neg60_phase_lowering_from_focus_anchor", -60, "focus_neg60_geom_04", 118, 56, 80, 148, -38, -36, 67.5, 112.5, "moderate_to_high_risk", "toward -60 via stronger negative dy coupling", "Increase negative dy from focus anchor while keeping low-leakage widths."),
        ("pl_neg60_focus_push_02", "neg60_phase_lowering_from_focus_anchor", -60, "focus_neg60_geom_04", 116, 56, 78, 150, -40, -36, 67.5, 112.5, "high_risk", "toward -60 via stronger asymmetry", "More lhs-like p1 and p2 width emphasis to lower phase from 83 deg."),
        ("pl_neg60_focus_push_03", "neg60_phase_lowering_from_focus_anchor", -60, "focus_neg60_geom_04", 120, 58, 82, 146, -40, -34, 67.5, 112.5, "moderate_risk", "toward -60 while preserving leakage", "Maintain focus widths but increase dx/dy phase push."),
        ("pl_neg60_focus_push_04", "neg60_phase_lowering_from_focus_anchor", -60, "focus_neg60_geom_04", 118, 60, 80, 150, -36, -38, 67.5, 112.5, "moderate_risk", "toward -60 with p1 widening leakage control", "Test if wider p1 controls leakage during negative dy push."),
        ("pl_neg60_focus_push_05", "neg60_phase_lowering_from_focus_anchor", -60, "focus_neg60_geom_04|fine_p1w_dx_08", 120, 58, 84, 146, -38, -34, 67.5, 112.5, "moderate_risk", "selected top phase-lowering -60 probe", "Balanced dx/dy phase-lowering from focus anchor with low-leakage width control."),
        ("pl_neg60_focus_push_06", "neg60_phase_lowering_from_focus_anchor", -60, "focus_neg60_geom_04|gap_lhs_leakred_06", 122, 60, 82, 144, -34, -32, 67.5, 112.5, "low_to_moderate_risk", "conservative -60 phase lowering", "Lower-risk focus bridge; may not move phase enough."),
        ("pl_neg60_focus_push_07", "neg60_phase_lowering_from_focus_anchor", -60, "focus_neg60_geom_04|next_zero_rot_anchor_03", 116, 58, 78, 146, -40, -30, 45.0, 90.0, "moderate_to_high_risk", "toward 0/-60 using limited rotation plus geometry", "Limited rotation change with geometry push, not pure global offset."),
    ]


def _zero_bridge_specs() -> list[tuple[object, ...]]:
    return [
        ("pl_zero_bridge_01", "zero_bridge_from_focus_anchor", 0, "focus_neg60_geom_04|next_zero_rot_anchor_03", 116, 58, 78, 142, -38, 26, 45.0, 90.0, "moderate_risk", "toward 0 from 83 deg", "Bridge focus low-leakage geometry toward 0 evidence with reduced dy."),
        ("pl_zero_bridge_02", "zero_bridge_from_focus_anchor", 0, "focus_neg60_geom_04|focus_zero_leakred_07", 116, 60, 78, 140, -36, 24, 45.0, 90.0, "moderate_risk", "toward 0 with leakage control", "Retain focus quality while moving toward zero evidence geometry."),
        ("pl_zero_bridge_03", "zero_bridge_from_focus_anchor", 0, "focus_neg60_geom_04|aggr_p1w_leakctrl_04", 120, 58, 80, 140, -34, 22, 45.0, 90.0, "moderate_risk", "toward 0 with p1w control", "Use p1w leakage-control anchor in a lower-dy zero bridge."),
        ("pl_zero_bridge_04", "zero_bridge_from_focus_anchor", 0, "focus_neg60_geom_04|next_zero_rot_anchor_03", 118, 58, 80, 142, -36, 24, 45.0, 90.0, "moderate_risk", "selected 0 deg bridge", "Balanced 0 deg bridge from focus anchor toward zero evidence with moderated leakage risk."),
        ("pl_zero_bridge_05", "zero_bridge_from_focus_anchor", 0, "focus_neg60_geom_04|fine_p1w_dx_03", 124, 56, 82, 144, -34, 18, 45.0, 90.0, "low_to_moderate_risk", "conservative 0 deg bridge", "Move toward low-leakage fine anchor; may not reach 0 deg."),
        ("pl_zero_bridge_06", "zero_bridge_from_focus_anchor", 0, "focus_neg60_geom_04|aggr_lhs_retention_dy_05", 114, 58, 76, 138, -38, 28, 45.0, 90.0, "moderate_to_high_risk", "toward 0 preserving phase evidence", "More aggressive bridge toward lhs retention evidence."),
        ("pl_zero_bridge_07", "zero_bridge_from_focus_anchor", 0, "focus_neg60_geom_04|gap_lhs_leakred_06", 122, 60, 82, 144, -32, 20, 45.0, 90.0, "low_to_moderate_risk", "toward 0 with leakage reduction", "Conservative geometry bridge for leakage-controlled 0 deg attempt."),
    ]


def _pi_wrap_specs() -> list[tuple[object, ...]]:
    return [
        ("pl_pi_wrap_01", "pi_wrap_from_focus_anchor", -180, "focus_neg60_geom_04", 112, 66, 102, 136, 38, 36, 67.5, 112.5, "high_risk", "toward -180 via pi wrap", "Strong same-sign displacement and aspect contrast from focus anchor."),
        ("pl_pi_wrap_02", "pi_wrap_from_focus_anchor", -180, "focus_neg60_geom_04|next_zero_rot_anchor_03", 114, 64, 100, 138, 36, 34, 67.5, 112.5, "moderate_to_high_risk", "toward -180 with moderated asymmetry", "Pi-wrap bridge with slightly safer dimensions."),
        ("pl_pi_wrap_03", "pi_wrap_from_focus_anchor", -180, "focus_neg60_geom_04|gap_lhs_leakred_06", 118, 66, 98, 140, 34, 32, 67.5, 112.5, "moderate_risk", "toward -180 conservative pi bridge", "Lower-risk pi-wrap probe from focus quality anchor."),
        ("pl_pi_wrap_04", "pi_wrap_from_focus_anchor", -180, "focus_neg60_geom_04", 116, 64, 102, 138, 38, 34, 67.5, 112.5, "moderate_to_high_risk", "selected pi-bin phase-lowering probe", "Controlled pi-wrap probe using focus anchor asymmetry without beta-selective p2."),
        ("pl_pi_wrap_05", "pi_wrap_from_focus_anchor", -180, "focus_neg60_geom_04|fine_p1w_dx_08", 122, 66, 96, 142, 32, 30, 67.5, 112.5, "moderate_risk", "toward -180 with fine leakage control", "Blend pi-wrap tendency with fine-anchor leakage control."),
        ("pl_pi_wrap_06", "pi_wrap_from_focus_anchor", -180, "focus_neg60_geom_04", 110, 68, 105, 134, 40, 38, 67.5, 112.5, "high_risk", "aggressive pi-wrap", "Most aggressive aspect inversion tendency within bounds."),
        ("pl_pi_wrap_07", "pi_wrap_from_focus_anchor", -180, "focus_neg60_geom_04|aggr_p1w_leakctrl_04", 120, 66, 100, 136, 36, 30, 90.0, 135.0, "moderate_to_high_risk", "limited-rotation pi bridge", "Limited rotation plus pi-wrap geometry, not global offset only."),
    ]


def _coupled_dx_dy_specs() -> list[tuple[object, ...]]:
    return [
        ("pl_coupled_push_01", "coupled_dx_dy_phase_push", -60, "focus_neg60_geom_04", 118, 58, 80, 148, -40, -40, 67.5, 112.5, "high_risk", "strong coupled push toward -60", "Extreme coupled dx/dy from focus anchor."),
        ("pl_coupled_push_02", "coupled_dx_dy_phase_push", 0, "focus_neg60_geom_04", 118, 58, 80, 148, -40, 0, 45.0, 90.0, "moderate_to_high_risk", "toward 0 by removing dy", "Separate dx and dy effects while keeping focus geometry."),
        ("pl_coupled_push_03", "coupled_dx_dy_phase_push", -120, "focus_neg60_geom_04", 116, 60, 82, 146, 36, -36, 67.5, 112.5, "high_risk", "toward -120 via dx sign flip", "Flip dx sign while retaining negative dy to test phase reversal."),
        ("pl_coupled_push_04", "coupled_dx_dy_phase_push", -60, "focus_neg60_geom_04|fine_p1w_dx_03", 124, 56, 84, 146, -34, -38, 67.5, 112.5, "moderate_risk", "toward -60 with fine width control", "Use fine p1w width while increasing negative dy."),
        ("pl_coupled_push_05", "coupled_dx_dy_phase_push", -120, "focus_neg60_geom_04", 116, 58, 84, 144, 34, -38, 67.5, 112.5, "moderate_to_high_risk", "toward -120 with coupled inversion", "Moderated dx sign flip for negative phase."),
        ("pl_coupled_push_06", "coupled_dx_dy_phase_push", 0, "focus_neg60_geom_04|next_zero_rot_anchor_03", 116, 58, 78, 142, -38, 12, 45.0, 90.0, "moderate_risk", "toward 0 with controlled dy", "Reduced dy from zero evidence to control leakage."),
        ("pl_coupled_push_07", "coupled_dx_dy_phase_push", -180, "focus_neg60_geom_04", 112, 64, 104, 134, 40, 40, 67.5, 112.5, "high_risk", "toward -180 via same-sign coupling", "Test phase wrap with same-sign dx/dy from focus anchor."),
    ]


def _aspect_ratio_specs() -> list[tuple[object, ...]]:
    return [
        ("pl_neg120_aspect_01", "aspect_ratio_inversion_probe", -120, "focus_neg60_geom_04", 112, 62, 104, 136, 34, -34, 67.5, 112.5, "moderate_to_high_risk", "toward -120 with aspect inversion", "Length asymmetry and p2 length increase without beta-selective width swap."),
        ("pl_neg120_aspect_02", "aspect_ratio_inversion_probe", -120, "focus_neg60_geom_04", 110, 64, 104, 134, 38, -36, 67.5, 112.5, "high_risk", "strong aspect inversion toward -120", "Aggressive aspect-ratio inversion tendency."),
        ("pl_neg120_aspect_03", "aspect_ratio_inversion_probe", -120, "focus_neg60_geom_04|gap_lhs_leakred_06", 114, 62, 102, 138, 36, -34, 67.5, 112.5, "moderate_to_high_risk", "selected -120 aspect probe", "Controlled aspect-ratio inversion with leakage-aware dimensions."),
        ("pl_neg120_aspect_04", "aspect_ratio_inversion_probe", -120, "focus_neg60_geom_04|fine_p1w_dx_08", 120, 60, 98, 142, 32, -32, 67.5, 112.5, "moderate_risk", "toward -120 conservative aspect probe", "Lower-risk asymmetry bridge."),
        ("pl_neg120_aspect_05", "aspect_ratio_inversion_probe", -120, "focus_neg60_geom_04", 116, 66, 104, 132, 40, -30, 67.5, 112.5, "high_risk", "toward -120 with p1 widening", "Push aspect contrast while monitoring leakage risk."),
        ("pl_neg120_aspect_06", "aspect_ratio_inversion_probe", -60, "focus_neg60_geom_04|aggr_p1w_leakctrl_04", 120, 62, 96, 144, 28, -28, 67.5, 112.5, "moderate_risk", "toward -60/-120 bridge", "Moderated aspect contrast, may land between bins."),
        ("pl_neg120_aspect_07", "aspect_ratio_inversion_probe", -180, "focus_neg60_geom_04", 110, 70, 105, 132, 40, 34, 67.5, 112.5, "high_risk", "toward -180 aspect wrap", "Strongest aspect inversion allowed by bounds."),
    ]


def _mixed_safe_specs() -> list[tuple[object, ...]]:
    return [
        ("pl_mixed_safe_01", "mixed_negative_phase_safe_probe", 0, "focus_neg60_geom_04|aggr_lhs_retention_dy_05", 118, 60, 80, 140, -30, 20, 45.0, 90.0, "low_to_moderate_risk", "toward 0 safely", "Low-risk bridge from focus quality anchor toward 0 evidence."),
        ("pl_mixed_safe_02", "mixed_negative_phase_safe_probe", -60, "focus_neg60_geom_04|gap_lhs_leakred_06", 122, 60, 82, 144, -30, -30, 67.5, 112.5, "moderate_risk", "toward -60 safely", "Moderate displacement and known leakage-control dimensions."),
        ("pl_mixed_safe_03", "mixed_negative_phase_safe_probe", -120, "focus_neg60_geom_04|fine_p1w_dx_03", 124, 58, 90, 144, 28, -28, 67.5, 112.5, "moderate_risk", "toward -120 safely", "Bridge to negative phase without aggressive aspect inversion."),
        ("pl_mixed_safe_04", "mixed_negative_phase_safe_probe", -180, "focus_neg60_geom_04|fine_p1w_dx_08", 126, 62, 92, 140, 30, 30, 67.5, 112.5, "moderate_to_high_risk", "toward -180 safely", "Pi-wrap tendency with moderated dimensions."),
        ("pl_mixed_safe_05", "mixed_negative_phase_safe_probe", -60, "focus_neg60_geom_04|next_zero_rot_anchor_03", 116, 58, 82, 146, -34, -24, 45.0, 90.0, "moderate_risk", "toward -60 with limited rotation", "Limited rotation and moderate dx/dy, not global offset only."),
        ("pl_mixed_safe_06", "mixed_negative_phase_safe_probe", 0, "focus_neg60_geom_04|focus_zero_leakred_07", 118, 60, 80, 140, -34, 18, 45.0, 90.0, "low_to_moderate_risk", "toward 0 with low risk", "Safest 0 bridge but may not move phase enough."),
        ("pl_mixed_safe_07", "mixed_negative_phase_safe_probe", -120, "focus_neg60_geom_04|aggr_p1w_leakctrl_04", 120, 60, 96, 142, 30, -26, 90.0, 135.0, "moderate_to_high_risk", "toward -120 with limited rotation", "Alternative limited-rotation negative phase probe."),
    ]


def _candidate_row(
    candidate_id: str,
    candidate_family: str,
    target_bin_deg: float,
    anchor_candidate: str,
    p1_length_nm: float,
    p1_width_nm: float,
    p2_length_nm: float,
    p2_width_nm: float,
    internal_dx_nm: float,
    internal_dy_nm: float,
    p1_rotation_deg: float,
    p2_rotation_deg: float,
    risk_level: str,
    expected_phase_direction: str,
    design_rationale: str,
) -> dict[str, object]:
    row = dict(DEFAULT_BASELINE)
    row.update(
        {
            "candidate_id": candidate_id,
            "candidate_family": candidate_family,
            "source_stage": "09-P27/P28",
            "target_bin_deg": target_bin_deg,
            "anchor_candidate": anchor_candidate,
            "source_reference": anchor_candidate,
            "design_rationale": design_rationale,
            "risk_level": risk_level,
            "expected_phase_direction": expected_phase_direction,
            "p1_length_nm": p1_length_nm,
            "p1_width_nm": p1_width_nm,
            "p2_length_nm": p2_length_nm,
            "p2_width_nm": p2_width_nm,
            "internal_dx_nm": internal_dx_nm,
            "internal_dy_nm": internal_dy_nm,
            "p1_rotation_deg": p1_rotation_deg,
            "p2_rotation_deg": p2_rotation_deg,
            "requires_geometry_validation": "true",
            "requires_fdtd": "true",
            "status": "not_evaluated",
            "notes": "Phase-lowering scaffold only; no FDTD/lumapi/.fsp/training in this stage; not a steering result.",
        }
    )
    return row


def existing_geometry_rows_from_paths(paths: Iterable[str | Path]) -> list[dict[str, object]]:
    rows = []
    for path in paths:
        candidate_path = Path(path)
        if candidate_path.exists():
            rows.extend(read_csv_rows(candidate_path))
    return rows


def _is_phase_evidence_row(row: dict[str, object]) -> bool:
    if is_early_pass(row):
        return False
    target_status = str(row.get("target_bin_status", ""))
    phase_region = str(row.get("phase_region", ""))
    return target_status == "evidence_only" or "evidence" in phase_region


def _nearest_phase_row(rows: Sequence[dict[str, object]], target: float) -> dict[str, object]:
    if not rows:
        return {}
    scored = []
    for row in rows:
        phase = float(row["phase_deg"])
        scored.append({**row, "phase_error_deg": angular_distance_deg(phase, target)})
    return min(scored, key=lambda row: (float(row["phase_error_deg"]), str(row["variant_id"])))


def _coverage_status(nearest_early: dict[str, object], nearest_evidence: dict[str, object]) -> str:
    early_error = _optional_float(nearest_early.get("phase_error_deg"))
    evidence_error = _optional_float(nearest_evidence.get("phase_error_deg"))
    if early_error is not None and early_error <= 10.0:
        return "strong_covered"
    if early_error is not None and early_error <= 20.0:
        return "early_covered"
    if early_error is not None and early_error <= 35.0:
        return "near_but_not_covered"
    if evidence_error is not None and evidence_error <= 35.0:
        return "evidence_only"
    return "open_gap"


def _coverage_notes(target: float, status: str, nearest_early: dict[str, object], nearest_evidence: dict[str, object]) -> str:
    if status in {"strong_covered", "early_covered", "near_but_not_covered"}:
        return f"nearest early-pass candidate is {nearest_early.get('variant_id')} at error {nearest_early.get('phase_error_deg')} deg"
    if status == "evidence_only":
        return f"nearest phase evidence is {nearest_evidence.get('variant_id')} but it fails early-pass thresholds"
    return f"major open gap remains near {target:g} deg"


def _validate_pool_policy(rows: Sequence[dict[str, object]]) -> None:
    if not 36 <= len(rows) <= 48:
        raise ValueError("phase-lowering candidate count must be 36-48")
    ids = [str(row["candidate_id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("candidate_id values must be unique")
    families = {str(row["candidate_family"]) for row in rows}
    if len(families) < 6:
        raise ValueError("phase-lowering pool should include all planned families")
    for row in rows:
        if not str(row["design_rationale"]).strip():
            raise ValueError("design_rationale is required")
        if not str(row["risk_level"]).strip():
            raise ValueError("risk_level is required")
        if not str(row["expected_phase_direction"]).strip():
            raise ValueError("expected_phase_direction is required")
        errors = _bounds_errors(row)
        if errors:
            raise ValueError("; ".join(errors))


def _validate_selection_policy(rows: Sequence[dict[str, object]]) -> None:
    if len(rows) != 4:
        raise ValueError("selection must contain exactly 4 candidates")
    targets = {float(row["target_bin_deg"]) for row in rows}
    families = {str(row["candidate_family"]) for row in rows}
    risks = [str(row["risk_level"]) for row in rows]
    anchors = " ".join(str(row["anchor_candidate"]) for row in rows)
    if 0.0 not in targets:
        raise ValueError("selection must include target 0")
    if -60.0 not in targets:
        raise ValueError("selection must include target -60")
    if not ({-120.0, -180.0} & targets):
        raise ValueError("selection must include -120 or -180")
    if len(targets) < 3:
        raise ValueError("selection must cover at least 3 target bins")
    if len(families) == 1:
        raise ValueError("selection cannot all come from one family")
    if all("high" in risk for risk in risks):
        raise ValueError("selection cannot be all high risk")
    if "focus_neg60_geom_04" not in anchors:
        raise ValueError("selection must include focus_neg60_geom_04 as anchor")


def _bounds_errors(candidate: dict[str, object]) -> list[str]:
    checks = {
        "p1_length_nm": (110.0, 150.0),
        "p1_width_nm": (55.0, 90.0),
        "p2_length_nm": (70.0, 105.0),
        "p2_width_nm": (130.0, 170.0),
        "internal_dx_nm": (-40.0, 40.0),
        "internal_dy_nm": (-40.0, 40.0),
        "period_x_nm": (340.0, 340.0),
        "period_y_nm": (340.0, 340.0),
        "height_nm": (300.0, 300.0),
    }
    errors = []
    for key, (minimum, maximum) in checks.items():
        value = float(candidate[key])
        if value < minimum or value > maximum:
            errors.append(f"{key}: {value:g} outside [{minimum:g}, {maximum:g}]")
    return errors


def _geometry_key(row: dict[str, object]) -> tuple[float, ...]:
    return (
        float(row["p1_length_nm"]),
        float(row["p1_width_nm"]),
        float(row["p2_length_nm"]),
        float(row["p2_width_nm"]),
        float(row.get("internal_dx_nm", 0.0) or 0.0),
        float(row.get("internal_dy_nm", 0.0) or 0.0),
        float(row.get("p1_rotation_deg", 0.0) or 0.0),
        float(row.get("p2_rotation_deg", 0.0) or 0.0),
    )


def _optional_float(value: object) -> float | None:
    if value in {"", None}:
        return None
    return float(value)


def _write_text(path: str | Path, lines: Sequence[str]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
