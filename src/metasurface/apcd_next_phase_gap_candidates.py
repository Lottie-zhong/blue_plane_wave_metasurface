from __future__ import annotations

import csv
import math
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence

from metasurface.apcd_active_learning import DEFAULT_BASELINE, wrap_phase_deg
from metasurface.apcd_candidate_validation import estimate_periodic_image_gap_nm, estimate_same_cell_gap_nm


BASELINE_PHASE_DEG = 111.31665091018952
EARLY_TARGET_CONVERSION_MIN = 0.5
EARLY_OPPOSITE_SPIN_LEAKAGE_MAX = 0.2
EARLY_CONVERSION_TO_LEAKAGE_RATIO_MIN = 6.0

PHASE_COVERAGE_V2_FIELDS = [
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

NEXT_PHASE_GAP_CANDIDATE_FIELDS = [
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

NEXT_PHASE_GAP_VALIDATION_FIELDS = [
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

NEXT_PHASE_GAP_SELECTION_FIELDS = [
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

SELECTED_NEXT_PHASE_GAP_IDS = [
    "next_zero_rot_anchor_03",
    "next_rot_anchor_04",
    "next_mixed_bridge_03",
    "next_pi_mixed_bridge_03",
]

SELECTION_REASONS = {
    "next_zero_rot_anchor_03": "0 deg bin candidate using rotation-assisted hypothesis on a usable 60-90 anchor.",
    "next_rot_anchor_04": "-60 deg bin candidate using global rotation-assisted hypothesis; high-risk but targets a major open gap.",
    "next_mixed_bridge_03": "-120 deg mixed bridge candidate with moderate risk, included to avoid an all-high-risk next batch.",
    "next_pi_mixed_bridge_03": "-180 deg mixed bridge candidate testing phase wrapping/turning without a full supercell.",
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


def angular_distance_deg(a: float, b: float) -> float:
    return abs(wrap_phase_deg(float(a) - float(b)))


def overall_early_pass(row: dict[str, object]) -> bool:
    return (
        float(row["target_conversion"]) >= EARLY_TARGET_CONVERSION_MIN
        and float(row["opposite_spin_leakage"]) <= EARLY_OPPOSITE_SPIN_LEAKAGE_MAX
        and float(row["conversion_to_leakage_ratio"]) >= EARLY_CONVERSION_TO_LEAKAGE_RATIO_MIN
    )


def classify_phase_region(row: dict[str, object]) -> str:
    phase = float(row["phase_deg"])
    early = str(row.get("overall_early_pass")) == "True" or row.get("overall_early_pass") is True
    leakage = float(row["opposite_spin_leakage"])
    ratio = float(row["conversion_to_leakage_ratio"])
    if early and 60.0 <= phase <= 90.0:
        return "60_90_usable"
    if early and 90.0 < phase <= 120.0:
        return "90_120_usable"
    if 45.0 <= phase <= 75.0 and (leakage > 0.2 or ratio < 6.0):
        return "high_leakage_phase_evidence"
    return "other"


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


def build_ml_dataset_v2(
    v1_rows: Iterable[dict[str, str]],
    p18_result_rows: Iterable[dict[str, str]],
    geometry_lookup: dict[str, dict[str, str]],
    columns: Sequence[str],
) -> list[dict[str, object]]:
    output_columns = list(columns)
    if "phase_region" not in output_columns:
        output_columns.append("phase_region")
    rows: list[dict[str, object]] = []
    seen = set()
    for row in v1_rows:
        enriched = dict(row)
        enriched["phase_region"] = classify_phase_region(enriched)
        rows.append({column: enriched.get(column, "") for column in output_columns})
        seen.add(str(row["variant_id"]))

    for result in p18_result_rows:
        candidate_id = str(result["candidate_id"])
        if candidate_id in seen:
            continue
        geometry = geometry_lookup.get(candidate_id, {})
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
                "overall_early_pass": result["overall_early_pass"],
                "source_result_csv": "summary_only:outputs/apcd_k6_active_learning/aggressive_phase_gap_top2_fdtd_results_v1.csv",
                "notes": "09-P19 dataset v2 row from 09-P18 summary; no new FDTD in this stage; no training; not steering result",
            }
        )
        t_alpha = complex(result["t_alpha_star_from_alpha"])
        row["t_alpha_star_from_alpha_real"] = t_alpha.real
        row["t_alpha_star_from_alpha_imag"] = t_alpha.imag
        row["t_alpha_star_from_alpha_abs"] = abs(t_alpha)
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
    return rows


def write_dataset_v2_report(path: str | Path, rows: Sequence[dict[str, object]]) -> Path:
    phases = [float(row["phase_deg"]) for row in rows]
    early = [row for row in rows if str(row["overall_early_pass"]) == "True"]
    new_ids = ["aggr_lhs_retention_dy_05", "aggr_p1w_leakctrl_04"]
    lines = [
        "# APCD K=6 ML-Ready Dataset v2 Collection Report",
        "",
        "Scope: 09-P19 dataset update only. No FDTD was run in this stage. No lumapi call was made. No model was trained. This is not a steering result.",
        "",
        f"Dataset v2 rows: {len(rows)}",
        f"Early-pass count: {len(early)}",
        f"Phase range deg: {_range_text(phases)}",
        f"New 60-90 usable candidates: {', '.join(new_ids)}",
        "",
        "Compared with dataset v1, v2 adds two real 09-P18 summary rows that are both early-pass and inside 60-90 deg.",
        "",
        "The dataset remains a small-data planning dataset. It does not prove a complete K=6 phase-state library.",
    ]
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def analyze_phase_coverage_v2(dataset_rows: Sequence[dict[str, object]], targets: Sequence[float]) -> list[dict[str, object]]:
    early_rows = [row for row in dataset_rows if str(row["overall_early_pass"]) == "True"]
    evidence_rows = [row for row in dataset_rows if str(row["overall_early_pass"]) != "True"]
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


def write_phase_gap_analysis_v2(path: str | Path, coverage_rows: Sequence[dict[str, object]]) -> Path:
    major_gaps = [str(row["phase_bin_deg"]) for row in coverage_rows if row["coverage_status"] == "open_gap"]
    row_60 = next(row for row in coverage_rows if float(row["phase_bin_deg"]) == 60.0)
    row_120 = next(row for row in coverage_rows if float(row["phase_bin_deg"]) == 120.0)
    lines = [
        "# APCD K=6 Phase Gap Analysis v2",
        "",
        "Scope: 09-P20 analysis only. No FDTD was run. No lumapi call was made. No model was trained. This is not a steering result.",
        "",
        f"60 deg bin status: `{row_60['coverage_status']}` using nearest early-pass `{row_60['nearest_candidate_early_pass']}` at `{row_60['nearest_phase_early_pass']}` deg.",
        f"120 deg bin best early-pass candidate: `{row_120['nearest_candidate_early_pass']}` at `{row_120['nearest_phase_early_pass']}` deg.",
        f"Major open gaps: {', '.join(major_gaps) if major_gaps else 'none'}",
        "",
        "Per-bin coverage:",
        "",
        "| bin deg | nearest early-pass | early error | nearest evidence-only | evidence error | status |",
        "|---:|---|---:|---|---:|---|",
        *[
            f"| {row['phase_bin_deg']} | {row['nearest_candidate_early_pass']} | {row['nearest_error_early_pass']} | "
            f"{row['nearest_candidate_evidence_only']} | {row['nearest_error_evidence_only']} | {row['coverage_status']} |"
            for row in coverage_rows
        ],
        "",
        "The K=6 phase-state library is still incomplete. No phase-ramp supercell has been built, and this is not a +15 deg steering proof.",
    ]
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def write_k6_readiness_v2(path: str | Path, coverage_rows: Sequence[dict[str, object]]) -> Path:
    covered = [row for row in coverage_rows if row["coverage_status"] in {"strong_covered", "early_covered"}]
    open_rows = [row for row in coverage_rows if row["coverage_status"] == "open_gap"]
    lines = [
        "# APCD K=6 Phase-State Readiness v2",
        "",
        "Scope: readiness assessment only. No FDTD was run in this stage. No phase-ramp supercell was built. No steering claim is made.",
        "",
        f"Covered or early-covered bins: {len(covered)} / 6",
        f"Open major-gap bins: {', '.join(str(row['phase_bin_deg']) for row in open_rows) if open_rows else 'none'}",
        "",
        "Readiness decision: not ready for K=6 phase-ramp supercell assembly.",
        "",
        "Reason: the 60 deg and 120 deg bins have useful early-pass candidates, but 0, -60, -120, and -180/180 deg remain major gaps.",
    ]
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def build_next_phase_gap_candidate_pool() -> list[dict[str, object]]:
    specs = []
    specs.extend(_rotation_specs())
    specs.extend(_zero_bin_specs())
    specs.extend(_negative_bin_specs())
    specs.extend(_pi_bin_specs())
    specs.extend(_mixed_bridge_specs())
    candidates = [
        _candidate_row(
            candidate_id=spec[0],
            candidate_family=spec[1],
            target_bin_deg=spec[2],
            anchor_candidate=spec[3],
            p1_length_nm=spec[4],
            p1_width_nm=spec[5],
            p2_length_nm=spec[6],
            p2_width_nm=spec[7],
            internal_dx_nm=spec[8],
            internal_dy_nm=spec[9],
            rotation_offset_deg=spec[10],
            risk_level=spec[11],
            design_rationale=spec[12],
        )
        for spec in specs
    ]
    _validate_next_candidate_policy(candidates)
    return candidates


def validate_next_phase_gap_candidate_pool(
    candidates: Iterable[dict[str, object]],
    existing_candidates: Iterable[dict[str, object]] = (),
    minimum_gap_nm: float = 5.0,
) -> list[dict[str, object]]:
    candidate_list = list(candidates)
    id_counts = Counter(str(row["candidate_id"]) for row in candidate_list)
    existing_keys = {_geometry_key(row) for row in existing_candidates}
    seen: set[tuple[float, float, float, float, float, float, float, float]] = set()
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
            notes.append("geometry sanity validation passed; optical response still unknown")
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


def select_next_phase_gap_fdtd_candidates(
    candidates: Sequence[dict[str, object]],
    validation_rows: Sequence[dict[str, object]],
    selected_ids: Sequence[str] = SELECTED_NEXT_PHASE_GAP_IDS,
) -> list[dict[str, object]]:
    candidate_by_id = {str(row["candidate_id"]): row for row in candidates}
    validation_by_id = {str(row["candidate_id"]): row for row in validation_rows}
    selected = []
    for rank, candidate_id in enumerate(selected_ids, start=1):
        candidate = candidate_by_id[candidate_id]
        validation = validation_by_id[candidate_id]
        if str(validation["overall_geometry_pass"]) != "True" or str(validation["recommended_for_fdtd"]) != "True":
            raise ValueError(f"{candidate_id} is not geometry-pass/recommended")
        selected.append(
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
                "notes": "09-P21 selection only; no YAML config; no FDTD; not a steering result",
            }
        )
    _validate_selection_policy(selected)
    return selected


def summarize_next_candidate_pool(candidates: Sequence[dict[str, object]]) -> dict[str, object]:
    return {
        "candidate_count": len(candidates),
        "family_counts": dict(sorted(Counter(str(row["candidate_family"]) for row in candidates).items())),
        "target_bin_counts": dict(sorted(Counter(str(row["target_bin_deg"]) for row in candidates).items())),
        "candidate_ids_unique": len({str(row["candidate_id"]) for row in candidates}) == len(candidates),
    }


def write_next_candidate_pool_summary(path: str | Path, candidates: Sequence[dict[str, object]]) -> Path:
    summary = summarize_next_candidate_pool(candidates)
    lines = [
        "# APCD K=6 Next Phase-Gap Candidate Pool v2 Summary",
        "",
        "Scope: 09-P21 candidate pool scaffold only. No FDTD was run. No lumapi call was made. No `.fsp` file was generated. No model was trained. This is not a steering result.",
        "",
        f"Candidate count: {summary['candidate_count']}",
        f"Candidate IDs unique: {summary['candidate_ids_unique']}",
        "",
        "Family distribution:",
        "",
        *[f"- `{family}`: {count}" for family, count in summary["family_counts"].items()],
        "",
        "Target bin distribution:",
        "",
        *[f"- `{target}`: {count}" for target, count in summary["target_bin_counts"].items()],
    ]
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def write_next_validation_summary(path: str | Path, rows: Sequence[dict[str, object]]) -> Path:
    pass_count = sum(str(row["overall_geometry_pass"]) == "True" for row in rows)
    lines = [
        "# APCD K=6 Next Phase-Gap Geometry Validation Summary",
        "",
        "Scope: geometry/gap/sanity validation only. No FDTD was run. No `.fsp` file was generated. No model was trained.",
        "",
        f"Candidate count: {len(rows)}",
        f"Geometry pass: {pass_count}",
        f"Recommended for FDTD: {sum(str(row['recommended_for_fdtd']) == 'True' for row in rows)}",
        f"Minimum same-cell gap nm: {min(float(row['same_cell_min_gap_nm']) for row in rows)}",
        f"Minimum periodic-image gap nm: {min(float(row['periodic_image_min_gap_nm']) for row in rows)}",
    ]
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def write_next_selection_summary(path: str | Path, rows: Sequence[dict[str, object]]) -> Path:
    lines = [
        "# APCD K=6 Next Phase-Gap FDTD Selection v2 Summary",
        "",
        "Scope: selected_not_run planning only. No YAML config was generated. No FDTD was run. This is not a steering result.",
        "",
        f"Selected count: {len(rows)}",
        "",
        "Selected candidates:",
        "",
        *[
            f"- `{row['candidate_id']}` target `{row['target_bin_deg']}` family `{row['candidate_family']}`: {row['selection_reason']}"
            for row in rows
        ],
        "",
        "Recommended next action: generate YAML and run only the top-2 selected candidates first; do not run the full pool.",
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
    if evidence_error is not None and evidence_error <= 20.0:
        return "evidence_only"
    return "open_gap"


def _coverage_notes(target: float, status: str, nearest_early: dict[str, object], nearest_evidence: dict[str, object]) -> str:
    if status in {"strong_covered", "early_covered", "near_but_not_covered"}:
        return f"nearest early-pass candidate is {nearest_early.get('variant_id')} at error {nearest_early.get('phase_error_deg')} deg"
    if status == "evidence_only":
        return f"nearest phase evidence is {nearest_evidence.get('variant_id')} but it fails early-pass thresholds"
    return f"major open gap remains near {target:g} deg"


def _rotation_specs() -> list[tuple[object, ...]]:
    rows = []
    anchors = [
        ("aggr_lhs_retention_dy_05", 115, 55, 75, 135, -40, 32),
        ("aggr_p1w_leakctrl_04", 120, 58, 80, 140, -36, 30),
        ("fine_p1w_dx_03", 130, 56, 85, 150, -33, 0),
        ("fine_p1w_dx_08", 130, 57, 85, 150, -34, 0),
        ("baseline", 130, 70, 85, 150, 0, 0),
    ]
    offset_by_target = [(0, -60), (-60, -120), (-120, 60), (-180, 90)]
    index = 1
    for target, offset in offset_by_target:
        for anchor, p1l, p1w, p2l, p2w, dx, dy in anchors[:3]:
            rows.append(
                (
                    f"next_rot_anchor_{index:02d}",
                    "rotation_assisted_anchor_probe",
                    target,
                    anchor,
                    p1l,
                    p1w,
                    p2l,
                    p2w,
                    dx,
                    dy,
                    offset,
                    "high_risk",
                    "Global-rotation phase synthesis hypothesis; preserves relative pillar rotation and requires FDTD validation.",
                )
            )
            index += 1
    return rows


def _zero_bin_specs() -> list[tuple[object, ...]]:
    return [
        ("next_zero_rot_anchor_03", "zero_bin_probe", 0, "aggr_lhs_retention_dy_05", 115, 55, 75, 135, -40, 36, -45, "high_risk", "Push beyond 60-90 anchor toward 0 deg using high dy and rotation-assisted hypothesis."),
        ("next_zero_probe_02", "zero_bin_probe", 0, "aggr_p1w_leakctrl_04", 120, 56, 75, 135, -40, 36, -30, "high_risk", "More lhs-like geometry while retaining some p1 width leakage control."),
        ("next_zero_probe_03", "zero_bin_probe", 0, "doe_lhs_like_01", 110, 56, 70, 135, -40, 38, -30, "high_risk", "Near-lhs geometry with p2 width trim for leakage-control attempt."),
        ("next_zero_probe_04", "zero_bin_probe", 0, "aggr_lhs_retention_dy_05", 115, 57, 75, 140, -38, 34, -30, "moderate_to_high_risk", "Slightly relaxed p1/p2 widths to reduce leakage risk."),
        ("next_zero_probe_05", "zero_bin_probe", 0, "aggr_p1w_leakctrl_04", 120, 58, 80, 135, -38, 36, -45, "moderate_to_high_risk", "0 deg probe from leakage-control anchor with stronger dy."),
        ("next_zero_probe_06", "zero_bin_probe", 0, "fine_p1w_dx_03", 125, 56, 80, 140, -38, 30, -60, "moderate_to_high_risk", "Rotation-assisted extrapolation from fine p1w_dx anchor."),
    ]


def _negative_bin_specs() -> list[tuple[object, ...]]:
    return [
        ("next_neg60_rot_anchor_02", "negative_bin_rotation_probe", -60, "aggr_lhs_retention_dy_05", 115, 55, 75, 135, -40, 32, -120, "high_risk", "High-risk -60 deg rotation-assisted probe from 72 deg usable anchor."),
        ("next_neg60_probe_02", "negative_bin_rotation_probe", -60, "aggr_p1w_leakctrl_04", 120, 58, 80, 140, -36, 30, -120, "high_risk", "Rotation-assisted -60 deg probe from 81 deg usable anchor."),
        ("next_neg60_probe_03", "negative_bin_rotation_probe", -60, "fine_p1w_dx_08", 130, 57, 85, 150, -34, 10, -120, "moderate_to_high_risk", "Uses low-leakage fine anchor plus small dy and global rotation."),
        ("next_neg60_probe_04", "negative_bin_rotation_probe", -60, "baseline", 130, 70, 85, 150, 0, 0, -120, "moderate_to_high_risk", "Baseline rotation-assisted control row."),
        ("next_neg120_rot_anchor_02", "negative_bin_rotation_probe", -120, "fine_p1w_dx_03", 130, 56, 85, 150, -33, 0, 60, "moderate_to_high_risk", "Rotation-assisted -120 deg probe from low-leakage p1w_dx anchor."),
        ("next_neg120_probe_02", "negative_bin_rotation_probe", -120, "aggr_p1w_leakctrl_04", 120, 58, 80, 140, -36, 30, 60, "high_risk", "Rotation-assisted -120 deg probe from 60-90 usable anchor."),
        ("next_neg120_probe_03", "negative_bin_rotation_probe", -120, "aggr_lhs_retention_dy_05", 115, 55, 75, 135, -40, 32, 60, "high_risk", "Retains phase-shift anchor but applies global rotation hypothesis."),
        ("next_neg120_probe_04", "negative_bin_rotation_probe", -120, "baseline", 130, 70, 85, 150, 0, 0, 60, "moderate_to_high_risk", "Baseline global-rotation hypothesis control."),
    ]


def _pi_bin_specs() -> list[tuple[object, ...]]:
    return [
        ("next_pi_probe_01", "pi_bin_probe", -180, "aggr_lhs_retention_dy_05", 115, 55, 75, 135, -40, 36, 90, "high_risk", "Pi-bin phase wrapping hypothesis from aggressive 60-90 anchor."),
        ("next_pi_probe_02", "pi_bin_probe", -180, "aggr_p1w_leakctrl_04", 120, 58, 80, 140, -36, 34, 90, "high_risk", "Pi-bin probe with leakage-control geometry."),
        ("next_pi_mixed_bridge_03", "pi_bin_probe", -180, "fine_p1w_dx_03|aggr_lhs_retention_dy_05", 125, 56, 80, 140, -38, 28, 90, "moderate_to_high_risk", "Mixed bridge for phase wrapping/turning trend near -180 deg."),
        ("next_pi_probe_04", "pi_bin_probe", -180, "baseline", 130, 70, 85, 150, 0, 0, 90, "moderate_to_high_risk", "Baseline pi-bin rotation-assisted control."),
        ("next_pi_probe_05", "pi_bin_probe", -180, "p1W_p5", 130, 75, 85, 150, 0, 0, 90, "moderate_to_high_risk", "Uses known 120 deg-side early-pass geometry with pi-bin rotation hypothesis."),
        ("next_pi_probe_06", "pi_bin_probe", -180, "p2W_p10", 130, 70, 85, 160, 0, 0, 90, "moderate_to_high_risk", "Uses low-leakage p2W anchor with pi-bin rotation hypothesis."),
    ]


def _mixed_bridge_specs() -> list[tuple[object, ...]]:
    return [
        ("next_mixed_bridge_01", "mixed_safe_bridge", 0, "aggr_lhs_retention_dy_05|p1W_p5", 120, 60, 80, 145, -30, 24, -30, "moderate_risk", "Bridge from 60-90 anchor to 120-side early-pass candidate; tests phase turning."),
        ("next_mixed_bridge_02", "mixed_safe_bridge", -60, "aggr_p1w_leakctrl_04|p2W_p10", 125, 60, 80, 150, -30, 24, -90, "moderate_risk", "Mixed bridge for -60 bin without fully lhs-like dimensions."),
        ("next_mixed_bridge_03", "mixed_safe_bridge", -120, "fine_p1w_dx_08|p1W_p5", 130, 60, 85, 150, -25, 10, 60, "moderate_risk", "Low-leakage bridge with rotation-assisted -120 hypothesis."),
        ("next_mixed_bridge_04", "mixed_safe_bridge", -180, "aggr_lhs_retention_dy_05|baseline", 125, 60, 80, 145, -30, 20, 90, "moderate_to_high_risk", "Pi-bin mixed bridge, less aggressive than lhs-like retention."),
        ("next_mixed_bridge_05", "mixed_safe_bridge", 0, "aggr_p1w_leakctrl_04|baseline", 125, 62, 80, 145, -28, 20, -45, "moderate_risk", "0-bin bridge from leakage-control anchor."),
        ("next_mixed_bridge_06", "mixed_safe_bridge", -60, "aggr_lhs_retention_dy_05|fine_p1w_dx_03", 120, 58, 80, 140, -36, 26, -90, "moderate_to_high_risk", "Aggressive bridge for -60 target while retaining some leakage-control geometry."),
    ]


def _candidate_row(
    *,
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
    rotation_offset_deg: float,
    risk_level: str,
    design_rationale: str,
) -> dict[str, object]:
    row = dict(DEFAULT_BASELINE)
    row.update(
        {
            "candidate_id": candidate_id,
            "candidate_family": candidate_family,
            "source_stage": "09-P19/P20/P21",
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
            "p1_rotation_deg": _wrap_rotation(67.5 + rotation_offset_deg),
            "p2_rotation_deg": _wrap_rotation(112.5 + rotation_offset_deg),
            "requires_geometry_validation": "true",
            "requires_fdtd": "true",
            "status": "not_evaluated",
            "notes": "Next-gap scaffold only; phase synthesis hypothesis requires real FDTD validation; no FDTD/lumapi/.fsp/training in this stage; not a steering result.",
        }
    )
    return row


def _validate_next_candidate_policy(candidates: Sequence[dict[str, object]]) -> None:
    if not 36 <= len(candidates) <= 48:
        raise ValueError("next phase-gap candidate count must be 36-48")
    ids = [str(row["candidate_id"]) for row in candidates]
    if len(ids) != len(set(ids)):
        raise ValueError("candidate_id values must be unique")
    target_counts = Counter(float(row["target_bin_deg"]) for row in candidates)
    for target in (0.0, -60.0, -120.0, -180.0):
        if target_counts[target] < 4:
            raise ValueError(f"target bin {target:g} needs several candidates")
    for row in candidates:
        errors = _bounds_errors(row)
        if errors:
            raise ValueError("; ".join(errors))
        if str(row["status"]) != "not_evaluated":
            raise ValueError("all candidates must be not_evaluated")


def _validate_selection_policy(rows: Sequence[dict[str, object]]) -> None:
    if len(rows) != 4:
        raise ValueError("selection must contain exactly 4 candidates")
    targets = {float(row["target_bin_deg"]) for row in rows}
    families = {str(row["candidate_family"]) for row in rows}
    risk_values = [str(row["risk_level"]) for row in rows]
    if len(targets) < 2:
        raise ValueError("selection must cover at least 2 target bins")
    if 0.0 not in targets:
        raise ValueError("selection must include a 0 deg candidate")
    if not ({-60.0, -120.0} & targets):
        raise ValueError("selection must include -60 or -120 deg candidate")
    if "rotation_assisted_anchor_probe" not in families and "negative_bin_rotation_probe" not in families:
        raise ValueError("selection must include a rotation-assisted candidate")
    if "mixed_safe_bridge" not in families and "pi_bin_probe" not in families:
        raise ValueError("selection must include a geometry-bridge/mixed candidate")
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


def _geometry_key(row: dict[str, object]) -> tuple[float, float, float, float, float, float, float, float]:
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


def _wrap_rotation(value: float) -> float:
    return float(value) % 180.0


def _optional_float(value: object) -> float | None:
    if value in {"", None}:
        return None
    return float(value)


def _range_text(values: Sequence[float]) -> str:
    if not values:
        return "none"
    return f"{min(values):.12g} to {max(values):.12g}"
