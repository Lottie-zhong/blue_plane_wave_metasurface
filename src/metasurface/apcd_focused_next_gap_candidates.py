from __future__ import annotations

import csv
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence

from metasurface.apcd_active_learning import DEFAULT_BASELINE, wrap_phase_deg
from metasurface.apcd_candidate_validation import estimate_periodic_image_gap_nm, estimate_same_cell_gap_nm


BASELINE_PHASE_DEG = 111.31665091018952
TARGET_BINS = [0.0, 60.0, 120.0, -180.0, -120.0, -60.0]
EARLY_TARGET_CONVERSION_MIN = 0.5
EARLY_OPPOSITE_SPIN_LEAKAGE_MAX = 0.2
EARLY_CONVERSION_TO_LEAKAGE_RATIO_MIN = 6.0

PHASE_COVERAGE_V3_FIELDS = [
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

FOCUSED_NEXT_GAP_CANDIDATE_FIELDS = [
    "candidate_id",
    "candidate_family",
    "source_stage",
    "target_bin_deg",
    "anchor_candidate",
    "source_reference",
    "design_rationale",
    "risk_level",
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

FOCUSED_NEXT_GAP_VALIDATION_FIELDS = [
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

FOCUSED_NEXT_GAP_SELECTION_FIELDS = [
    "selection_rank",
    "candidate_id",
    "candidate_family",
    "target_bin_deg",
    "anchor_candidate",
    "selection_reason",
    "design_rationale",
    "risk_level",
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

SELECTED_FOCUSED_IDS = [
    "focus_zero_leakred_07",
    "focus_neg60_geom_04",
    "focus_neg120_asym_03",
    "focus_pi_wrap_04",
]

SELECTION_REASONS = {
    "focus_zero_leakred_07": "Top zero-bin leakage-reduction candidate: close to next_zero evidence while reducing dy and widening p1 for leakage control.",
    "focus_neg60_geom_04": "-60 deg geometry-driven candidate using coupled dx/dy and asymmetry, not a pure global-rotation offset.",
    "focus_neg120_asym_03": "-120 deg candidate probing stronger dimer asymmetry and aspect-ratio contrast.",
    "focus_pi_wrap_04": "-180 deg pi-bin candidate using controlled swap-like bridge without beta-selective p2 geometry.",
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
    for pool_path in pool_paths:
        path = Path(pool_path)
        if not path.exists():
            continue
        for row in read_csv_rows(path):
            candidate_id = row.get("candidate_id") or row.get("variant_id")
            if candidate_id:
                lookup[candidate_id] = row
    return lookup


def build_ml_dataset_v3(
    v2_rows: Iterable[dict[str, str]],
    p23_result_rows: Iterable[dict[str, str]],
    geometry_lookup: dict[str, dict[str, str]],
    columns: Sequence[str],
) -> tuple[list[dict[str, object]], list[str]]:
    output_columns = list(columns)
    for column in ("phase_region", "target_bin_deg", "target_bin_status"):
        if column not in output_columns:
            output_columns.append(column)

    rows: list[dict[str, object]] = []
    seen = set()
    for row in v2_rows:
        enriched = dict(row)
        enriched["phase_region"] = classify_phase_region(enriched)
        enriched.setdefault("target_bin_deg", "")
        enriched.setdefault("target_bin_status", "")
        rows.append({column: enriched.get(column, "") for column in output_columns})
        seen.add(str(row["variant_id"]))

    for result in p23_result_rows:
        candidate_id = str(result["candidate_id"])
        if candidate_id in seen:
            continue
        geometry = geometry_lookup.get(candidate_id, {})
        row = {column: "" for column in output_columns}
        t_alpha = complex(result["t_alpha_star_from_alpha"])
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
                "source_result_csv": "summary_only:outputs/apcd_k6_active_learning/next_phase_gap_top2_fdtd_results_v2.csv",
                "notes": (
                    f"09-P24 dataset v3 row from 09-P23 summary; target_bin_status={result['target_bin_status']}; "
                    "not usable if early_pass is false; no new FDTD in this stage; not steering result"
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
    if status == "evidence_only":
        return "target_bin_evidence_only"
    if status == "open_gap":
        return "target_bin_open_gap"
    phase = float(row["phase_deg"])
    early = is_early_pass(row)
    if early and 60.0 <= phase <= 90.0:
        return "60_90_usable"
    if early and 90.0 < phase <= 120.0:
        return "90_120_usable"
    if 45.0 <= phase <= 75.0 and not early:
        return "high_leakage_phase_evidence"
    return "other"


def is_early_pass(row: dict[str, object]) -> bool:
    if "early_pass" in row and row["early_pass"] not in {"", None}:
        return str(row["early_pass"]) == "True" or row["early_pass"] is True
    if "overall_early_pass" in row and row["overall_early_pass"] not in {"", None}:
        return str(row["overall_early_pass"]) == "True" or row["overall_early_pass"] is True
    return (
        float(row["target_conversion"]) >= EARLY_TARGET_CONVERSION_MIN
        and float(row["opposite_spin_leakage"]) <= EARLY_OPPOSITE_SPIN_LEAKAGE_MAX
        and float(row["conversion_to_leakage_ratio"]) >= EARLY_CONVERSION_TO_LEAKAGE_RATIO_MIN
    )


def angular_distance_deg(phase_deg: float, target_deg: float) -> float:
    return abs(wrap_phase_deg(float(phase_deg) - float(target_deg)))


def analyze_phase_coverage_v3(dataset_rows: Sequence[dict[str, object]], targets: Sequence[float] = TARGET_BINS) -> list[dict[str, object]]:
    early_rows = [row for row in dataset_rows if is_early_pass(row)]
    evidence_rows = [row for row in dataset_rows if _is_phase_evidence_row(row)]
    rows = []
    for target in targets:
        nearest_all = _nearest_phase_row(dataset_rows, target)
        nearest_early = _nearest_phase_row(early_rows, target)
        nearest_evidence = _nearest_phase_row(evidence_rows, target)
        status = _coverage_status(nearest_early, nearest_evidence)
        rows.append(
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
    return rows


def _is_phase_evidence_row(row: dict[str, object]) -> bool:
    if is_early_pass(row):
        return False
    target_status = str(row.get("target_bin_status", ""))
    phase_region = str(row.get("phase_region", ""))
    if target_status == "evidence_only":
        return True
    return "evidence" in phase_region


def build_focused_next_gap_candidate_pool() -> list[dict[str, object]]:
    specs: list[tuple[object, ...]] = []
    specs.extend(_zero_leakage_reduction_specs())
    specs.extend(_negative_phase_redesign_specs())
    rows = [_candidate_row(*spec) for spec in specs]
    _validate_pool_policy(rows)
    return rows


def validate_focused_next_gap_candidate_pool(
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
        overall = all(
            [
                bounds_pass,
                same_pass,
                periodic_pass,
                duplicate_candidate_id_pass,
                duplicate_geometry_pass,
                rotation_reasonable_pass,
                beta_pass,
            ]
        )
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


def select_focused_next_gap_fdtd_candidates(
    candidates: Sequence[dict[str, object]],
    validation_rows: Sequence[dict[str, object]],
    selected_ids: Sequence[str] = SELECTED_FOCUSED_IDS,
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
                "notes": "09-P25 selection only; recommend running top-2 only next; no YAML/FDTD/lumapi/.fsp in this stage",
            }
        )
    _validate_selection_policy(rows)
    return rows


def write_dataset_v3_report(path: str | Path, rows: Sequence[dict[str, object]]) -> Path:
    new_rows = [row for row in rows if str(row["variant_id"]).startswith("next_")]
    lines = [
        "# APCD K=6 ML-Ready Dataset v3 Collection Report",
        "",
        "Scope: 09-P24 dataset/evidence update only. No FDTD was run in this stage. No lumapi call was made. No `.fsp` file was generated.",
        "",
        f"Dataset v3 rows: {len(rows)}",
        f"Early-pass rows: {sum(is_early_pass(row) for row in rows)}",
        "",
        "Added 09-P23 rows:",
        "",
        *[
            f"- `{row['variant_id']}`: phase `{row['phase_deg']}` deg, target_bin_status `{row['target_bin_status']}`, early_pass `{row['overall_early_pass']}`."
            for row in new_rows
        ],
        "",
        "`next_zero_rot_anchor_03` is evidence_only for 0 deg, not a usable phase state. `next_rot_anchor_04` remains open_gap for -60 deg.",
    ]
    return _write_text(path, lines)


def write_phase_gap_analysis_v3(path: str | Path, coverage_rows: Sequence[dict[str, object]]) -> Path:
    row_by_bin = {float(row["phase_bin_deg"]): row for row in coverage_rows}
    lines = [
        "# APCD K=6 Phase Gap Analysis v3",
        "",
        "Scope: 09-P24 phase coverage update only. No FDTD was run in this stage. No model was trained.",
        "",
        f"60 deg bin status: `{row_by_bin[60.0]['coverage_status']}`.",
        f"120 deg bin status: `{row_by_bin[120.0]['coverage_status']}`.",
        f"0 deg bin status: `{row_by_bin[0.0]['coverage_status']}` with evidence `{row_by_bin[0.0]['nearest_candidate_evidence_only']}` at `{row_by_bin[0.0]['nearest_phase_evidence_only']}` deg.",
        f"-60 deg bin status: `{row_by_bin[-60.0]['coverage_status']}`.",
        f"-120 deg bin status: `{row_by_bin[-120.0]['coverage_status']}`.",
        f"-180 deg bin status: `{row_by_bin[-180.0]['coverage_status']}`.",
        "",
        "| bin deg | nearest early-pass | early error | nearest evidence-only | evidence error | status |",
        "|---:|---|---:|---|---:|---|",
        *[
            f"| {row['phase_bin_deg']} | {row['nearest_candidate_early_pass']} | {row['nearest_error_early_pass']} | "
            f"{row['nearest_candidate_evidence_only']} | {row['nearest_error_evidence_only']} | {row['coverage_status']} |"
            for row in coverage_rows
        ],
        "",
        "The K=6 phase-state library is still incomplete. No phase-ramp supercell was built and this is not a +15 deg steering proof.",
    ]
    return _write_text(path, lines)


def write_k6_readiness_v3(path: str | Path, coverage_rows: Sequence[dict[str, object]]) -> Path:
    open_or_evidence = [
        row
        for row in coverage_rows
        if row["coverage_status"] in {"evidence_only", "open_gap", "near_but_not_covered"}
    ]
    lines = [
        "# APCD K=6 Phase-State Readiness v3",
        "",
        "Readiness decision: not ready for K=6 phase-ramp supercell assembly.",
        "",
        f"Bins still not usable: {', '.join(str(row['phase_bin_deg']) for row in open_or_evidence)}",
        "",
        "Reason: the 0 deg bin has evidence only, while -60, -120, and -180 deg remain major gaps. No steering claim is supported.",
    ]
    return _write_text(path, lines)


def write_focused_pool_summary(path: str | Path, candidates: Sequence[dict[str, object]]) -> Path:
    family_counts = Counter(str(row["candidate_family"]) for row in candidates)
    target_counts = Counter(str(row["target_bin_deg"]) for row in candidates)
    lines = [
        "# APCD K=6 Focused Next-Gap Candidate Pool v3 Summary",
        "",
        "Scope: 09-P25 focused candidate planning only. No FDTD/lumapi/.fsp/training.",
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


def write_focused_validation_summary(path: str | Path, rows: Sequence[dict[str, object]]) -> Path:
    lines = [
        "# APCD K=6 Focused Next-Gap Geometry Validation v3 Summary",
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


def write_focused_selection_summary(path: str | Path, rows: Sequence[dict[str, object]]) -> Path:
    lines = [
        "# APCD K=6 Focused Next-Gap FDTD Selection v3 Summary",
        "",
        "Scope: selected_not_run planning only. No YAML config was generated. No FDTD was run.",
        "",
        f"Selected count: {len(rows)}",
        "",
        "Selected candidates:",
        *[
            f"- rank {row['selection_rank']}: `{row['candidate_id']}` target `{row['target_bin_deg']}` family `{row['candidate_family']}` risk `{row['risk_level']}`."
            for row in rows
        ],
        "",
        "Recommended next action: run only the top-2 selected candidates first; do not run the full focused pool.",
    ]
    return _write_text(path, lines)


def write_focused_redesign_report(
    path: str | Path,
    coverage_rows: Sequence[dict[str, object]],
    candidates: Sequence[dict[str, object]],
    validation_rows: Sequence[dict[str, object]],
    selection_rows: Sequence[dict[str, object]],
) -> Path:
    row_by_bin = {float(row["phase_bin_deg"]): row for row in coverage_rows}
    lines = [
        "# APCD K=6 Focused Next-Gap Redesign v3 Note",
        "",
        "## Scope",
        "",
        "This is 09-P24/P25. This stage updates the dataset/coverage with the 09-P23 results and designs a focused next-gap candidate pool. No FDTD was run, no lumapi call was made, and no `.fsp` file was generated in this stage.",
        "",
        "## 09-P23 Interpretation",
        "",
        "`next_zero_rot_anchor_03` did not fill the 0 deg gap: it reached phase 20.788972844777305 deg, but leakage and ratio failed, so it is evidence_only rather than usable.",
        "",
        "`next_rot_anchor_04` did not fill the -60 deg gap: its phase stayed far from -60 deg and the optical metrics failed. The -60 deg bin remains open_gap.",
        "",
        "The top-2 rotation-assisted hypothesis was therefore not successful as a gap-closing strategy.",
        "",
        "## Coverage v3",
        "",
        f"60 deg remains `{row_by_bin[60.0]['coverage_status']}` and 120 deg remains `{row_by_bin[120.0]['coverage_status']}`.",
        f"0 deg is `{row_by_bin[0.0]['coverage_status']}` because the nearest phase evidence fails early-pass thresholds.",
        f"-60, -120, and -180 deg statuses are `{row_by_bin[-60.0]['coverage_status']}`, `{row_by_bin[-120.0]['coverage_status']}`, and `{row_by_bin[-180.0]['coverage_status']}`.",
        "",
        "## Focused Redesign Logic",
        "",
        "The next pool splits into zero-bin leakage reduction and negative-phase redesign. The zero branch stays near the 0 deg evidence point while reducing high-risk dy/asymmetry and moving toward low-leakage anchors. The negative branch avoids blind global-rotation continuation and instead varies internal dx/dy coupling, dimer asymmetry, aspect-ratio contrast, and controlled swap-like/pi-bin bridges.",
        "",
        f"Focused pool count: {len(candidates)}.",
        f"Geometry pass: {sum(str(row['overall_geometry_pass']) == 'True' for row in validation_rows)}.",
        "",
        "## Selected Candidates",
        "",
        *[
            f"- `{row['candidate_id']}` target `{row['target_bin_deg']}`: {row['selection_reason']}"
            for row in selection_rows
        ],
        "",
        "Recommended next step: generate YAML and run only the top-2 selected candidates first. Do not run the full pool.",
        "",
        "## Boundaries",
        "",
        "No K=7, no phase-ramp supercell, no TiO2/450 nm, no Micro-LED integration, no DenseNet/cVAE training, no +15 deg steering claim, and no claim that the K=6 phase-state library is complete.",
    ]
    return _write_text(path, lines)


def existing_geometry_rows_from_paths(paths: Iterable[str | Path]) -> list[dict[str, object]]:
    rows = []
    for path in paths:
        candidate_path = Path(path)
        if candidate_path.exists():
            rows.extend(read_csv_rows(candidate_path))
    return rows


def _zero_leakage_reduction_specs() -> list[tuple[object, ...]]:
    return [
        ("focus_zero_leakred_01", "zero_bin_leakage_reduction", 0, "next_zero_rot_anchor_03|aggr_lhs_retention_dy_05", 115, 57, 75, 138, -38, 32, 22.5, 67.5, "moderate_to_high_risk", "Reduce dy and widen p1 relative to next_zero evidence to reduce leakage while preserving 0-deg pull."),
        ("focus_zero_leakred_02", "zero_bin_leakage_reduction", 0, "next_zero_rot_anchor_03|aggr_p1w_leakctrl_04", 118, 58, 78, 140, -36, 30, 22.5, 67.5, "moderate_risk", "Move partway toward the low-leakage 81-deg anchor while retaining the 0-deg rotation family."),
        ("focus_zero_leakred_03", "zero_bin_leakage_reduction", 0, "next_zero_rot_anchor_03|fine_p1w_dx_03", 122, 56, 80, 140, -36, 28, 22.5, 67.5, "moderate_risk", "Introduce fine p1w_dx leakage control with smaller dy."),
        ("focus_zero_leakred_04", "zero_bin_leakage_reduction", 0, "next_zero_rot_anchor_03|fine_p1w_dx_08", 124, 57, 82, 142, -34, 28, 22.5, 67.5, "moderate_risk", "Fine-anchor leakage-control bridge with reduced dx/dy aggressiveness."),
        ("focus_zero_leakred_05", "zero_bin_leakage_reduction", 0, "next_zero_rot_anchor_03|gap_lhs_leakred_06", 116, 59, 78, 142, -34, 30, 22.5, 67.5, "moderate_risk", "Use gap_lhs leakage-reduced geometry as a soft landing from the zero evidence point."),
        ("focus_zero_leakred_06", "zero_bin_leakage_reduction", 0, "next_zero_rot_anchor_03", 115, 60, 75, 140, -40, 30, 22.5, 67.5, "moderate_to_high_risk", "Increase p1 width while preserving high dx to test leakage reduction without losing phase evidence."),
        ("focus_zero_leakred_07", "zero_bin_leakage_reduction", 0, "next_zero_rot_anchor_03|aggr_lhs_retention_dy_05", 116, 58, 76, 138, -38, 30, 22.5, 67.5, "moderate_risk", "Balanced top zero candidate: lower dy, slightly wider p1, and modest p2 trim to reduce leakage."),
        ("focus_zero_leakred_08", "zero_bin_leakage_reduction", 0, "next_zero_rot_anchor_03", 118, 56, 76, 136, -40, 34, 22.5, 67.5, "high_risk", "Retain stronger zero-bin phase evidence with only mild p2 trim."),
        ("focus_zero_leakred_09", "zero_bin_leakage_reduction", 0, "next_zero_rot_anchor_03|aggr_p1w_leakctrl_04", 120, 58, 80, 138, -36, 32, 22.5, 67.5, "moderate_risk", "Use p1w leakage-control anchor while keeping zero-bin rotations."),
        ("focus_zero_leakred_10", "zero_bin_leakage_reduction", 0, "next_zero_rot_anchor_03|fine_p1w_dx_03", 126, 56, 82, 142, -34, 24, 22.5, 67.5, "moderate_risk", "Lower dy bridge toward fine p1w_dx for leakage reduction."),
        ("focus_zero_leakred_11", "zero_bin_leakage_reduction", 0, "next_zero_rot_anchor_03|gap_lhs_leakred_06", 118, 60, 80, 144, -32, 28, 22.5, 67.5, "low_to_moderate_risk", "Conservative zero evidence retention with broader widths and reduced displacement."),
        ("focus_zero_leakred_12", "zero_bin_leakage_reduction", 0, "next_zero_rot_anchor_03|aggr_lhs_retention_dy_05", 114, 58, 74, 136, -38, 34, 22.5, 67.5, "moderate_to_high_risk", "Keep lhs-like dimensions but soften leakage through p1 widening."),
        ("focus_zero_leakred_13", "zero_bin_leakage_reduction", 0, "next_zero_rot_anchor_03|fine_p1w_dx_08", 128, 57, 84, 144, -32, 26, 22.5, 67.5, "moderate_risk", "Blend zero evidence with low-leakage fine anchor at reduced displacement."),
        ("focus_zero_leakred_14", "zero_bin_leakage_reduction", 0, "next_zero_rot_anchor_03|aggr_p1w_leakctrl_04", 120, 60, 78, 136, -38, 28, 22.5, 67.5, "moderate_risk", "Wider p1 leakage-control test retaining zero-bin rotation."),
        ("focus_zero_leakred_15", "zero_bin_leakage_reduction", 0, "next_zero_rot_anchor_03", 116, 56, 78, 140, -36, 36, 22.5, 67.5, "high_risk", "Retain dy evidence while trimming widths to test whether phase survives leakage-control geometry."),
        ("focus_zero_leakred_16", "zero_bin_leakage_reduction", 0, "next_zero_rot_anchor_03|gap_lhs_leakred_06", 122, 60, 82, 146, -30, 24, 22.5, 67.5, "low_to_moderate_risk", "Most conservative zero leakage-reduction bridge; may lose 0-deg phase pull."),
    ]


def _negative_phase_redesign_specs() -> list[tuple[object, ...]]:
    rows = []
    base_specs = [
        ("neg60_geom", "negative_phase_redesign", -60, 120, 58, 82, 146, -38, -30, 67.5, 112.5, "moderate_to_high_risk", "Geometry-driven -60 probe using opposite-sign dx/dy coupling and moderate asymmetry."),
        ("neg60_geom", "negative_phase_redesign", -60, 116, 56, 78, 150, -40, -34, 67.5, 112.5, "high_risk", "Stronger -60 probe with high displacement coupling and p2 width emphasis."),
        ("neg60_geom", "negative_phase_redesign", -60, 124, 60, 84, 144, -34, -28, 67.5, 112.5, "moderate_risk", "Lower-risk -60 bridge with softened displacement and aspect contrast."),
        ("neg60_geom", "negative_phase_redesign", -60, 118, 58, 80, 148, -36, -32, 67.5, 112.5, "moderate_risk", "Selected -60 redesign candidate with balanced coupled dx/dy and leakage control."),
        ("neg60_geom", "negative_phase_redesign", -60, 112, 56, 72, 154, -38, -36, 67.5, 112.5, "high_risk", "Aggressive lhs-like -60 phase pull with p2 width boost."),
        ("neg60_geom", "negative_phase_redesign", -60, 128, 62, 86, 142, -30, -24, 67.5, 112.5, "low_to_moderate_risk", "Conservative -60 geometry probe avoiding pure rotation offset."),
        ("neg120_asym", "negative_phase_redesign", -120, 112, 60, 100, 138, 34, -34, 67.5, 112.5, "moderate_to_high_risk", "Aspect-ratio inversion tendency with strong dimer asymmetry for -120."),
        ("neg120_asym", "negative_phase_redesign", -120, 110, 58, 104, 136, 38, -36, 67.5, 112.5, "high_risk", "Aggressive -120 asymmetry, close to swap-like but avoids beta-selective p2."),
        ("neg120_asym", "negative_phase_redesign", -120, 114, 60, 102, 140, 36, -32, 67.5, 112.5, "moderate_to_high_risk", "Selected -120 candidate combining strong asymmetry with moderated p2 width."),
        ("neg120_asym", "negative_phase_redesign", -120, 118, 62, 98, 142, 32, -30, 67.5, 112.5, "moderate_risk", "Softer -120 aspect-ratio inversion tendency."),
        ("neg120_asym", "negative_phase_redesign", -120, 112, 64, 104, 134, 40, -28, 67.5, 112.5, "high_risk", "High dx asymmetry and narrow p2 width for phase wrapping test."),
        ("neg120_asym", "negative_phase_redesign", -120, 120, 60, 96, 146, 30, -26, 67.5, 112.5, "moderate_risk", "Lower-risk -120 bridge with reduced displacement."),
        ("pi_wrap", "negative_phase_redesign", -180, 110, 66, 105, 132, 40, 40, 67.5, 112.5, "high_risk", "Pi-bin phase wrapping probe using strong same-sign displacement and near-inversion aspect contrast."),
        ("pi_wrap", "negative_phase_redesign", -180, 112, 68, 104, 134, 36, 38, 67.5, 112.5, "high_risk", "Controlled swap-like bridge toward pi-bin while avoiding p2=150x85 beta geometry."),
        ("pi_wrap", "negative_phase_redesign", -180, 116, 66, 100, 136, 34, 36, 67.5, 112.5, "moderate_to_high_risk", "Moderated pi-bin bridge with reduced aspect inversion."),
        ("pi_wrap", "negative_phase_redesign", -180, 114, 64, 102, 138, 38, 34, 67.5, 112.5, "moderate_to_high_risk", "Selected pi-bin candidate balancing phase wrapping and geometry safety."),
        ("pi_wrap", "negative_phase_redesign", -180, 120, 66, 98, 140, 32, 32, 67.5, 112.5, "moderate_risk", "Lower-risk pi-bin bridge with less extreme asymmetry."),
        ("pi_wrap", "negative_phase_redesign", -180, 118, 70, 104, 132, 36, 30, 67.5, 112.5, "moderate_to_high_risk", "Wider p1 pi-bin bridge with p2 length emphasis."),
        ("neg_mixed", "negative_phase_redesign", -60, 122, 58, 90, 148, -32, -34, 45.0, 90.0, "moderate_to_high_risk", "Limited rotation change plus geometry-driven displacement; not a global offset continuation."),
        ("neg_mixed", "negative_phase_redesign", -120, 118, 62, 100, 140, 34, -34, 45.0, 90.0, "moderate_to_high_risk", "Limited rotation/asymmetry bridge for -120 target."),
        ("neg_mixed", "negative_phase_redesign", -180, 116, 68, 102, 136, 38, 38, 45.0, 90.0, "high_risk", "Limited rotation pi-bin bridge, kept geometry-safe."),
        ("neg_mixed", "negative_phase_redesign", -60, 126, 60, 88, 144, -30, -30, 90.0, 135.0, "moderate_risk", "Alternative limited-rotation -60 geometry bridge."),
        ("neg_mixed", "negative_phase_redesign", -120, 116, 64, 102, 138, 36, -30, 90.0, 135.0, "moderate_to_high_risk", "Alternative limited-rotation -120 asymmetry bridge."),
        ("neg_mixed", "negative_phase_redesign", -180, 114, 70, 104, 134, 40, 34, 90.0, 135.0, "high_risk", "Alternative limited-rotation pi-bin probe with swap-like aspect trend."),
    ]
    counters = Counter()
    for prefix, family, target, p1l, p1w, p2l, p2w, dx, dy, r1, r2, risk, rationale in base_specs:
        counters[prefix] += 1
        rows.append(
            (
                f"focus_{prefix}_{counters[prefix]:02d}",
                family,
                target,
                "next_rot_anchor_04|next_zero_rot_anchor_03|low_leakage_anchors",
                p1l,
                p1w,
                p2l,
                p2w,
                dx,
                dy,
                r1,
                r2,
                risk,
                rationale,
            )
        )
    return rows


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
    design_rationale: str,
) -> dict[str, object]:
    row = dict(DEFAULT_BASELINE)
    row.update(
        {
            "candidate_id": candidate_id,
            "candidate_family": candidate_family,
            "source_stage": "09-P24/P25",
            "target_bin_deg": target_bin_deg,
            "anchor_candidate": anchor_candidate,
            "source_reference": anchor_candidate,
            "design_rationale": design_rationale,
            "risk_level": risk_level,
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
            "notes": "Focused next-gap scaffold only; no FDTD/lumapi/.fsp/training in this stage; not a steering result.",
        }
    )
    return row


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
        raise ValueError("focused next-gap candidate count must be 36-48")
    ids = [str(row["candidate_id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("candidate ids must be unique")
    for row in rows:
        if not str(row["design_rationale"]).strip():
            raise ValueError("design_rationale is required")
        if not str(row["risk_level"]).strip():
            raise ValueError("risk_level is required")
        errors = _bounds_errors(row)
        if errors:
            raise ValueError("; ".join(errors))


def _validate_selection_policy(rows: Sequence[dict[str, object]]) -> None:
    if len(rows) != 4:
        raise ValueError("selection must contain exactly 4 candidates")
    targets = {float(row["target_bin_deg"]) for row in rows}
    families = {str(row["candidate_family"]) for row in rows}
    risk_values = [str(row["risk_level"]) for row in rows]
    if 0.0 not in targets:
        raise ValueError("selection must include a zero-bin candidate")
    if -60.0 not in targets:
        raise ValueError("selection must include a -60 deg candidate")
    if not ({-120.0, -180.0} & targets):
        raise ValueError("selection must include -120 or -180")
    if len(targets) < 3:
        raise ValueError("selection must cover at least 3 target bins")
    if len(families) == 1:
        raise ValueError("selection cannot all come from one family")
    if all("high" in risk for risk in risk_values):
        raise ValueError("selection cannot be all high risk")


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
