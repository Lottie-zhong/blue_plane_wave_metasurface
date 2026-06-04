from __future__ import annotations

import cmath
import csv
import math
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence

import yaml

from metasurface.apcd_active_learning import wrap_phase_deg
from metasurface.apcd_candidate_validation import polygon_min_distance_nm, rectangle_corners_nm
from metasurface.apcd_phase_lowering_candidates import (
    PHASE_COVERAGE_V4_FIELDS,
    analyze_phase_coverage_v4,
    classify_phase_region,
)
from metasurface.config import load_apcd_single_dimer_config


BASELINE_PHASE_DEG = 111.31665091018952
TARGET_BINS = [0.0, 60.0, 120.0, -180.0, -120.0, -60.0]
PROTOTYPE_IDS = [
    "h2_square_load_01",
    "h2_nearsquare_load_02",
    "h2_weak_aniso_03",
    "h2_phase_delay_04",
]

HELPER_PROTOTYPE_POOL_FIELDS = [
    "candidate_id",
    "family",
    "helper_role",
    "target_bin_deg",
    "helper_type",
    "p3_shape",
    "p3_length_nm",
    "p3_width_nm",
    "p3_rotation_deg",
    "p3_frac_x",
    "p3_frac_y",
    "p3_x_nm",
    "p3_y_nm",
    "requested_p3_frac_x",
    "requested_p3_frac_y",
    "position_adjustment_note",
    "purpose",
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
    "internal_dx_nm",
    "internal_dy_nm",
    "period_x_nm",
    "period_y_nm",
    "height_nm",
    "material",
    "substrate",
    "requires_fdtd",
    "status",
    "notes",
]

HELPER_PROTOTYPE_VALIDATION_FIELDS = [
    "candidate_id",
    "family",
    "target_bin_deg",
    "same_cell_min_gap_nm",
    "periodic_image_min_gap_nm",
    "minimum_gap_nm_threshold",
    "no_pillar_overlap_pass",
    "same_cell_gap_pass",
    "periodic_gap_pass",
    "helper_role_pass",
    "helper_not_apcd_dimer_pass",
    "fabrication_friendly_shape_pass",
    "core_geometry_pass",
    "helper_dimensions_pass",
    "beta_selective_geometry_pass",
    "duplicate_candidate_id_pass",
    "duplicate_geometry_pass",
    "overall_geometry_pass",
    "recommended_for_fdtd",
    "notes",
]

HELPER_PROTOTYPE_RESULT_FIELDS = [
    "candidate_id",
    "family",
    "helper_role",
    "target_bin_deg",
    "run_status",
    "status",
    "phase_deg",
    "phase_error_to_target_deg",
    "target_conversion",
    "opposite_spin_leakage",
    "conversion_to_leakage_ratio",
    "PD",
    "total_transmission",
    "t_alpha_star_from_alpha",
    "phase_shift_vs_baseline_deg",
    "early_target_pass",
    "early_leakage_pass",
    "early_ratio_pass",
    "early_pass",
    "target_bin_status",
    "source_result_csv",
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


def build_helper_prototype_candidate_pool() -> list[dict[str, object]]:
    specs = [
        {
            "candidate_id": "h2_square_load_01",
            "target_bin_deg": 0,
            "helper_type": "low-leakage loading helper",
            "p3_shape": "square",
            "p3_length_nm": 60,
            "p3_width_nm": 60,
            "p3_rotation_deg": 0,
            "requested_p3_frac_x": 0.25,
            "requested_p3_frac_y": 0.75,
            "p3_frac_x": 0.25,
            "p3_frac_y": 0.75,
            "purpose": "test weakest helper loading without destroying APCD core",
            "position_adjustment_note": "kept requested empty-corner position",
        },
        {
            "candidate_id": "h2_nearsquare_load_02",
            "target_bin_deg": 0,
            "helper_type": "near-square loading helper",
            "p3_shape": "near-square rectangle",
            "p3_length_nm": 80,
            "p3_width_nm": 70,
            "p3_rotation_deg": 0,
            "requested_p3_frac_x": 0.75,
            "requested_p3_frac_y": 0.25,
            "p3_frac_x": 0.25,
            "p3_frac_y": 0.75,
            "purpose": "test slightly stronger dielectric loading / phase pulling",
            "position_adjustment_note": "requested (0.75,0.25) was below 50 nm gap; moved to opposite empty corner for safe gap",
        },
        {
            "candidate_id": "h2_weak_aniso_03",
            "target_bin_deg": -60,
            "helper_type": "weak anisotropic nanofin helper",
            "p3_shape": "rectangular nanofin",
            "p3_length_nm": 60,
            "p3_width_nm": 110,
            "p3_rotation_deg": 45,
            "requested_p3_frac_x": 0.25,
            "requested_p3_frac_y": 0.75,
            "p3_frac_x": 0.25,
            "p3_frac_y": 0.75,
            "purpose": "test whether weak anisotropy can move target-channel phase while keeping leakage controlled",
            "position_adjustment_note": "kept requested empty-corner position",
        },
        {
            "candidate_id": "h2_phase_delay_04",
            "target_bin_deg": -180,
            "helper_type": "phase-delay nanofin helper",
            "p3_shape": "rectangular nanofin",
            "p3_length_nm": 90,
            "p3_width_nm": 130,
            "p3_rotation_deg": 90,
            "requested_p3_frac_x": 0.75,
            "requested_p3_frac_y": 0.25,
            "p3_frac_x": 0.25,
            "p3_frac_y": 0.75,
            "purpose": "test moderate propagation/material phase delay, higher risk",
            "position_adjustment_note": "requested (0.75,0.25) was unsafe; safest empty-corner placement still fails 50 nm gap and is not run",
        },
    ]
    return [_prototype_row(spec) for spec in specs]


def validate_helper_prototype_pool(candidates: Sequence[dict[str, object]], minimum_gap_nm: float = 50.0) -> list[dict[str, object]]:
    id_counts = {str(row["candidate_id"]): 0 for row in candidates}
    for row in candidates:
        id_counts[str(row["candidate_id"])] += 1
    seen_geometry: set[tuple[float, ...]] = set()
    rows = []
    for candidate in candidates:
        same_cell, periodic = helper_prototype_gaps(candidate)
        geometry_key = _geometry_key(candidate)
        duplicate_geometry_pass = geometry_key not in seen_geometry
        seen_geometry.add(geometry_key)
        no_overlap = same_cell > 0.0
        same_pass = same_cell >= minimum_gap_nm
        periodic_pass = periodic >= minimum_gap_nm
        role_pass = candidate["helper_role"] == "weak_auxiliary_phase_helper"
        not_dimer_pass = candidate["family"] == "apcd_core_plus_helper_prototype"
        shape_pass = candidate["p3_shape"] in {"square", "near-square rectangle", "rectangular nanofin"}
        core_pass = _core_geometry_pass(candidate)
        helper_pass = _helper_dimensions_pass(candidate)
        beta_pass = not (float(candidate["p2_length_nm"]) == 150.0 and float(candidate["p2_width_nm"]) == 85.0)
        duplicate_id_pass = id_counts[str(candidate["candidate_id"])] == 1
        overall = all(
            [
                no_overlap,
                same_pass,
                periodic_pass,
                role_pass,
                not_dimer_pass,
                shape_pass,
                core_pass,
                helper_pass,
                beta_pass,
                duplicate_id_pass,
                duplicate_geometry_pass,
            ]
        )
        notes = []
        if not no_overlap:
            notes.append("pillar overlap detected")
        if not same_pass:
            notes.append("same-cell gap below 50 nm prototype threshold")
        if not periodic_pass:
            notes.append("periodic-image gap below 50 nm prototype threshold")
        if not role_pass:
            notes.append("helper role must be weak_auxiliary_phase_helper")
        if not not_dimer_pass:
            notes.append("helper must be standalone, not another APCD dimer")
        if not shape_pass:
            notes.append("helper shape is not fabrication-friendly")
        if not core_pass:
            notes.append("APCD core does not match alpha-pass baseline")
        if not helper_pass:
            notes.append("helper dimensions outside prototype fabrication bounds")
        if not beta_pass:
            notes.append("beta-selective p2=150x85 geometry forbidden")
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
                "minimum_gap_nm_threshold": minimum_gap_nm,
                "no_pillar_overlap_pass": no_overlap,
                "same_cell_gap_pass": same_pass,
                "periodic_gap_pass": periodic_pass,
                "helper_role_pass": role_pass,
                "helper_not_apcd_dimer_pass": not_dimer_pass,
                "fabrication_friendly_shape_pass": shape_pass,
                "core_geometry_pass": core_pass,
                "helper_dimensions_pass": helper_pass,
                "beta_selective_geometry_pass": beta_pass,
                "duplicate_candidate_id_pass": duplicate_id_pass,
                "duplicate_geometry_pass": duplicate_geometry_pass,
                "overall_geometry_pass": overall,
                "recommended_for_fdtd": overall,
                "notes": "; ".join(notes),
            }
        )
    return rows


def valid_prototype_candidates(candidates: Sequence[dict[str, object]], validation_rows: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    valid = {
        str(row["candidate_id"])
        for row in validation_rows
        if row["recommended_for_fdtd"] is True or str(row["recommended_for_fdtd"]) == "True"
    }
    return [row for row in candidates if str(row["candidate_id"]) in valid]


def write_helper_prototype_configs(candidate_rows: Sequence[dict[str, object]], config_dir: str | Path) -> list[Path]:
    output_dir = Path(config_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for candidate in candidate_rows:
        path = output_dir / f"{candidate['candidate_id']}.yaml"
        path.write_text(build_helper_prototype_config(candidate), encoding="utf-8")
        paths.append(path)
    return paths


def build_helper_prototype_config(candidate: dict[str, object]) -> str:
    data = {
        "project": {"name": "blue_plane_wave_metasurface", "stage": "09_p42_p44_helper_prototype_fdtd"},
        "candidate": {
            "variant_id": candidate["candidate_id"],
            "candidate_type": candidate["family"],
            "description": "physics-guided standalone helper prototype candidate",
            "target_bin_deg": _number(candidate["target_bin_deg"]),
            "source_stage": "09-P42/P44",
            "helper_role": candidate["helper_role"],
            "helper_type": candidate["helper_type"],
            "helper_shape": candidate["p3_shape"],
            "design_rationale": candidate["purpose"],
            "source_pool_csv": "outputs/apcd_k6_active_learning/helper_prototype_candidate_pool_v7.csv",
            "notes": "helper prototype config; not a full helper-v2 pool run; not a steering result",
        },
        "boundary": {
            "no_k7": True,
            "not_phase_ramp_supercell": True,
            "not_steering_result": True,
            "not_complete_k6_library_claim": True,
            "not_random_helper_shape": True,
            "not_freeform_helper_shape": True,
        },
        "target": {
            "wavelength_nm": 633,
            "incident_wave": "plane_wave",
            "output_basis": "alpha_beta",
            "target_polarization_type": "elliptical",
            "psi_deg": 112.5,
            "chi_deg": 22.5,
            "eps": 1.0e-12,
            "spin_er_threshold_db": 8,
            "conversion_to_leakage_threshold": 6,
        },
        "material": {
            "substrate": "Al2O3",
            "meta_material": "c-Si",
            "substrate_material_lumerical": "<Object defined dielectric>",
            "meta_material_lumerical": "<Object defined dielectric>",
            "substrate_index": 1.76,
            "meta_index": 3.88,
        },
        "geometry": {
            "layout_mode": "manual_absolute",
            "period_x_nm": _number(candidate["period_x_nm"]),
            "period_y_nm": _number(candidate["period_y_nm"]),
            "height_nm": _number(candidate["height_nm"]),
            "minimum_gap_nm": 50,
            "nanopillar_1": _pillar_mapping(candidate, "p1"),
            "nanopillar_2": _pillar_mapping(candidate, "p2"),
            "nanopillar_helper": _helper_mapping(candidate),
        },
        "simulation": {
            "substrate_thickness_nm": 220,
            "source_offset_nm": 120,
            "monitor_offset_nm": 180,
            "z_padding_above_nm": 260,
            "mesh_accuracy": 1,
            "simulation_time_fs": 250,
        },
        "output": {"result_dir": f"outputs/apcd_k6_metagrating_633nm/phase_state_candidates/{candidate['candidate_id']}"},
    }
    return yaml.safe_dump(data, sort_keys=False)


def validate_helper_prototype_configs(config_paths: Sequence[str | Path]) -> list[dict[str, object]]:
    rows = []
    for path_like in config_paths:
        path = Path(path_like)
        config = load_apcd_single_dimer_config(path)
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        helper = config.geometry.nanopillar_helper
        candidate_id = data["candidate"]["variant_id"]
        passed = (
            candidate_id in PROTOTYPE_IDS
            and helper is not None
            and helper.role == "weak_auxiliary_phase_helper"
            and data["boundary"]["not_phase_ramp_supercell"] is True
            and data["boundary"]["not_random_helper_shape"] is True
            and data["boundary"]["not_freeform_helper_shape"] is True
        )
        rows.append(
            {
                "candidate_id": candidate_id,
                "config_path": str(path),
                "validation_pass": passed,
                "notes": "config-load validation only; no FDTD/lumapi/.fsp",
            }
        )
    return rows


def run_helper_prototype_candidates(candidate_rows: Sequence[dict[str, object]], config_dir: Path, runtime: Path, python_executable: str, repo_root: Path) -> None:
    if len(candidate_rows) > 4:
        raise ValueError("helper prototype run is limited to four candidates")
    runner = repo_root / "scripts/13_run_apcd_single_dimer.py"
    for row in candidate_rows:
        candidate_id = str(row["candidate_id"])
        command = [python_executable, str(runner), "--config", str(config_dir / f"{candidate_id}.yaml"), "--runtime", str(runtime)]
        print(f"running_helper_prototype={candidate_id}")
        subprocess.run(command, cwd=repo_root, check=True)


def summarize_helper_prototype_results(
    candidates: Sequence[dict[str, object]],
    validation_rows: Sequence[dict[str, object]],
    repo_root: str | Path,
) -> list[dict[str, object]]:
    root = Path(repo_root)
    validation_by_id = {str(row["candidate_id"]): row for row in validation_rows}
    rows = []
    for candidate in candidates:
        validation = validation_by_id[str(candidate["candidate_id"])]
        if str(validation["recommended_for_fdtd"]) != "True" and validation["recommended_for_fdtd"] is not True:
            rows.append(not_run_geometry_failed_result(candidate, validation))
            continue
        result_path = root / "outputs/apcd_k6_metagrating_633nm/phase_state_candidates" / str(candidate["candidate_id"]) / "results.csv"
        if not result_path.exists():
            rows.append(not_run_missing_result(candidate))
            continue
        raw = read_csv_rows(result_path)[0]
        rows.append(result_row_from_raw(candidate, raw, result_path, root))
    return rows


def result_row_from_raw(candidate: dict[str, object], raw: dict[str, str], result_path: Path, repo_root: Path) -> dict[str, object]:
    status = raw.get("status", "")
    t_value = raw.get("t_alpha_star_from_alpha", "")
    phase = phase_deg_from_complex(t_value) if t_value else ""
    target = float(candidate["target_bin_deg"])
    error = angular_distance_deg(float(phase), target) if phase != "" else ""
    target_conversion = _float_or_blank(raw.get("target_conversion", ""))
    leakage = _float_or_blank(raw.get("opposite_spin_leakage", ""))
    ratio = _float_or_blank(raw.get("conversion_to_leakage_ratio", ""))
    early_target = target_conversion != "" and float(target_conversion) >= 0.5
    early_leakage = leakage != "" and float(leakage) <= 0.2
    early_ratio = ratio != "" and float(ratio) >= 6.0
    early = early_target and early_leakage and early_ratio
    target_status = target_bin_status(float(error), early, status) if error != "" else "failed"
    return {
        "candidate_id": candidate["candidate_id"],
        "family": candidate["family"],
        "helper_role": candidate["helper_role"],
        "target_bin_deg": _number(target),
        "run_status": "completed" if status == "ok" else "failed",
        "status": status,
        "phase_deg": phase,
        "phase_error_to_target_deg": error,
        "target_conversion": target_conversion,
        "opposite_spin_leakage": leakage,
        "conversion_to_leakage_ratio": ratio,
        "PD": _float_or_blank(raw.get("PD", "")),
        "total_transmission": _float_or_blank(raw.get("total_transmission", "")),
        "t_alpha_star_from_alpha": t_value,
        "phase_shift_vs_baseline_deg": wrap_phase_deg(float(phase) - BASELINE_PHASE_DEG) if phase != "" else "",
        "early_target_pass": early_target,
        "early_leakage_pass": early_leakage,
        "early_ratio_pass": early_ratio,
        "early_pass": early,
        "target_bin_status": target_status,
        "source_result_csv": result_path.resolve().relative_to(repo_root.resolve()).as_posix(),
        "notes": f"09-P42/P44 helper prototype real FDTD; target_bin_status={target_status}; not a steering result",
    }


def not_run_geometry_failed_result(candidate: dict[str, object], validation: dict[str, object]) -> dict[str, object]:
    row = _blank_result(candidate)
    row.update(
        {
            "run_status": "not_run_geometry_failed",
            "status": "not_run",
            "target_bin_status": "not_run_geometry_failed",
            "notes": f"not run because geometry validation failed: {validation['notes']}",
        }
    )
    return row


def not_run_missing_result(candidate: dict[str, object]) -> dict[str, object]:
    row = _blank_result(candidate)
    row.update(
        {
            "run_status": "not_run_missing_result",
            "status": "not_run",
            "target_bin_status": "not_run",
            "notes": "candidate was valid but result file is missing; no result fabricated",
        }
    )
    return row


def build_dataset_v7(dataset_v6_rows: Sequence[dict[str, str]], result_rows: Sequence[dict[str, object]], candidate_rows: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = list(dataset_v6_rows)
    fieldnames = list(rows[0].keys())
    candidate_by_id = {str(row["candidate_id"]): row for row in candidate_rows}
    existing = {str(row["variant_id"]) for row in rows}
    for result in result_rows:
        if result["run_status"] != "completed" or result["status"] != "ok" or result["candidate_id"] in existing:
            continue
        rows.append(dataset_row_from_result(candidate_by_id[str(result["candidate_id"])], result, fieldnames))
    return rows


def dataset_row_from_result(candidate: dict[str, object], result: dict[str, object], fieldnames: Sequence[str]) -> dict[str, object]:
    t_value = complex(str(result["t_alpha_star_from_alpha"]))
    row: dict[str, object] = {field: "" for field in fieldnames}
    row.update(
        {
            "variant_id": candidate["candidate_id"],
            "candidate_family": candidate["family"],
            "p1_length_nm": candidate["p1_length_nm"],
            "p1_width_nm": candidate["p1_width_nm"],
            "p2_length_nm": candidate["p2_length_nm"],
            "p2_width_nm": candidate["p2_width_nm"],
            "p1_frac_x": candidate["p1_frac_x"],
            "p1_frac_y": candidate["p1_frac_y"],
            "p2_frac_x": candidate["p2_frac_x"],
            "p2_frac_y": candidate["p2_frac_y"],
            "internal_dx_nm": candidate["internal_dx_nm"],
            "internal_dy_nm": candidate["internal_dy_nm"],
            "p1_rotation_deg": candidate["p1_rotation_deg"],
            "p2_rotation_deg": candidate["p2_rotation_deg"],
            "period_x_nm": candidate["period_x_nm"],
            "period_y_nm": candidate["period_y_nm"],
            "height_nm": candidate["height_nm"],
            "material": candidate["material"],
            "substrate": candidate["substrate"],
            "t_alpha_star_from_alpha_real": t_value.real,
            "t_alpha_star_from_alpha_imag": t_value.imag,
            "t_alpha_star_from_alpha_abs": abs(t_value),
            "phase_deg": result["phase_deg"],
            "phase_shift_vs_baseline_deg": result["phase_shift_vs_baseline_deg"],
            "target_conversion": result["target_conversion"],
            "opposite_spin_leakage": result["opposite_spin_leakage"],
            "conversion_to_leakage_ratio": result["conversion_to_leakage_ratio"],
            "PD": result["PD"],
            "overall_early_pass": result["early_pass"],
            "source_result_csv": result["source_result_csv"],
            "notes": "09-P42/P44 real FDTD helper prototype; helper p3 geometry is in prototype pool; raw results not committed; not a steering result",
            "phase_region": classify_phase_region(
                {
                    "phase_deg": result["phase_deg"],
                    "target_bin_status": result["target_bin_status"],
                    "overall_early_pass": result["early_pass"],
                    "target_conversion": result["target_conversion"],
                    "opposite_spin_leakage": result["opposite_spin_leakage"],
                    "conversion_to_leakage_ratio": result["conversion_to_leakage_ratio"],
                }
            ),
            "target_bin_deg": result["target_bin_deg"],
            "target_bin_status": result["target_bin_status"],
        }
    )
    return row


def write_summary(path: str | Path, result_rows: Sequence[dict[str, object]], validation_rows: Sequence[dict[str, object]], dataset_rows: Sequence[dict[str, object]], coverage_rows: Sequence[dict[str, object]]) -> Path:
    lines = [
        "# APCD K=6 Helper Prototype FDTD Results v7 Summary",
        "",
        "Scope: 09-P42/P44 physics-guided helper prototype batch. Only valid helper prototype YAML configs were run.",
        "",
        f"Geometry pass: {sum(str(row['overall_geometry_pass']) == 'True' for row in validation_rows)}/{len(validation_rows)}",
        f"Dataset v7 rows: {len(dataset_rows)}",
        "",
        "| candidate | target | phase | leakage | ratio | early pass | target status | run status |",
        "|---|---:|---:|---:|---:|---|---|---|",
        *[
            f"| `{row['candidate_id']}` | {row['target_bin_deg']} | {row['phase_deg']} | {row['opposite_spin_leakage']} | {row['conversion_to_leakage_ratio']} | {row['early_pass']} | {row['target_bin_status']} | {row['run_status']} |"
            for row in result_rows
        ],
        "",
        "Coverage v7:",
        "",
        "| bin deg | status |",
        "|---:|---|",
        *[f"| {row['phase_bin_deg']} | {row['coverage_status']} |" for row in coverage_rows],
        "",
        "No K=7, phase-ramp supercell, TiO2/450 nm, Micro-LED, ML training, freeform helper, +15 deg steering claim, or complete K=6 library claim.",
    ]
    return _write_text(path, lines)


def write_gap_analysis(path: str | Path, coverage_rows: Sequence[dict[str, object]], result_rows: Sequence[dict[str, object]]) -> Path:
    lines = [
        "# APCD K=6 Phase Gap Analysis v7",
        "",
        "Scope: helper prototype v7 update. Only completed valid prototype FDTD rows were added to dataset v7.",
        "",
        "| bin deg | status | nearest early-pass | early error | nearest evidence-only | evidence error |",
        "|---:|---|---|---:|---|---:|",
        *[
            f"| {row['phase_bin_deg']} | {row['coverage_status']} | {row['nearest_candidate_early_pass']} | {row['nearest_error_early_pass']} | {row['nearest_candidate_evidence_only']} | {row['nearest_error_evidence_only']} |"
            for row in coverage_rows
        ],
        "",
        "Prototype result statuses:",
        *[
            f"- `{row['candidate_id']}`: run_status={row['run_status']}, phase={row['phase_deg']}, leakage={row['opposite_spin_leakage']}, ratio={row['conversion_to_leakage_ratio']}, target_bin_status={row['target_bin_status']}"
            for row in result_rows
        ],
        "",
        "Do not claim a complete K=6 phase-state library or +15 deg steering from these prototype results.",
    ]
    return _write_text(path, lines)


def write_readiness(path: str | Path, coverage_rows: Sequence[dict[str, object]]) -> Path:
    open_rows = [row for row in coverage_rows if row["coverage_status"] not in {"strong_covered", "early_covered"}]
    lines = [
        "# APCD K=6 Phase-State Readiness v7",
        "",
        "Readiness decision: not ready for K=6 phase-ramp supercell assembly.",
        "",
        f"Bins not yet usable: {', '.join(str(row['phase_bin_deg']) for row in open_rows)}",
        "",
        "No +15 deg steering claim is supported.",
    ]
    return _write_text(path, lines)


def write_report(
    path: str | Path,
    candidate_rows: Sequence[dict[str, object]],
    validation_rows: Sequence[dict[str, object]],
    result_rows: Sequence[dict[str, object]],
    dataset_rows: Sequence[dict[str, object]],
    coverage_rows: Sequence[dict[str, object]],
) -> Path:
    run_rows = [row for row in result_rows if row["run_status"] == "completed"]
    invalid_rows = [row for row in result_rows if row["run_status"] == "not_run_geometry_failed"]
    lines = [
        "# APCD K=6 Helper Prototype FDTD v7 Note",
        "",
        "## Scope",
        "",
        "This is 09-P42/P44. It tests four physics-guided helper prototype records with fabrication-friendly dielectric pillar helpers.",
        "",
        "The helper is a third standalone weak auxiliary phase shifter. It is not another APCD dimer and not half of another APCD pair. APCD core pillar1/pillar2 remains responsible for spin-selective conversion; pillar3 helper only probes weak dielectric loading, phase pulling, or phase-delay behavior.",
        "",
        "No full 48-row helper v2 pool, old pool, K=7, phase-ramp supercell, TiO2/450 nm, Micro-LED integration, ML/DenseNet/cVAE training, random/freeform helper shape, +15 deg steering claim, or complete K=6 phase-state library claim was made.",
        "",
        "## Geometry Validation",
        "",
        f"Prototype records: {len(candidate_rows)}",
        f"Geometry pass: {sum(str(row['overall_geometry_pass']) == 'True' for row in validation_rows)}/{len(validation_rows)}",
        "",
        "| candidate | target | same-cell gap | periodic gap | recommended | notes |",
        "|---|---:|---:|---:|---|---|",
        *[
            f"| `{row['candidate_id']}` | {row['target_bin_deg']} | {row['same_cell_min_gap_nm']} | {row['periodic_image_min_gap_nm']} | {row['recommended_for_fdtd']} | {row['notes']} |"
            for row in validation_rows
        ],
        "",
        "YAML configs were generated only for geometry-passing candidates.",
        "",
        "## FDTD Results",
        "",
        f"Actual run candidates: {', '.join(str(row['candidate_id']) for row in run_rows)}",
        f"Geometry-failed not-run candidates: {', '.join(str(row['candidate_id']) for row in invalid_rows) if invalid_rows else 'none'}",
        "",
        "| candidate | helper type | target | phase | leakage | ratio | early pass | target status |",
        "|---|---|---:|---:|---:|---:|---|---|",
        *[
            f"| `{row['candidate_id']}` | `{_candidate_by_id(candidate_rows, row['candidate_id'])['helper_type']}` | {row['target_bin_deg']} | {row['phase_deg']} | {row['opposite_spin_leakage']} | {row['conversion_to_leakage_ratio']} | {row['early_pass']} | {row['target_bin_status']} |"
            for row in result_rows
        ],
        "",
        "Interpretation: the three geometry-passing prototypes preserved low leakage and early-pass quality, but they pulled the phase to positive 115-129 deg rather than filling 0 deg or -60 deg. This expands the high-positive usable phase evidence beyond v6, but it does not close the remaining major target gaps.",
        "",
        "## Dataset and Coverage v7",
        "",
        f"Dataset v7 rows: {len(dataset_rows)}",
        "",
        "| bin deg | status |",
        "|---:|---|",
        *[f"| {row['phase_bin_deg']} | {row['coverage_status']} |" for row in coverage_rows],
        "",
        "## Next Step",
        "",
        "Use these prototype results to decide whether weak helper loading is worth a small neighborhood follow-up. Do not assemble a phase-ramp supercell until all K=6 bins have usable phase states.",
    ]
    return _write_text(path, lines)


def phase_deg_from_complex(value: str) -> float:
    return wrap_phase_deg(math.degrees(cmath.phase(complex(value))))


def angular_distance_deg(phase_deg: float, target_deg: float) -> float:
    return abs(wrap_phase_deg(float(phase_deg) - float(target_deg)))


def target_bin_status(phase_error_deg: float, early_pass: bool, status: str = "ok") -> str:
    if status != "ok":
        return "failed"
    if early_pass and phase_error_deg <= 10.0:
        return "strong_covered"
    if early_pass and phase_error_deg <= 20.0:
        return "early_covered"
    if early_pass and phase_error_deg <= 35.0:
        return "near_but_not_covered"
    if phase_error_deg <= 35.0:
        return "evidence_only"
    if early_pass:
        return "usable_but_not_target"
    return "open_gap"


def helper_prototype_gaps(candidate: dict[str, object]) -> tuple[float, float]:
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


def _prototype_row(spec: dict[str, object]) -> dict[str, object]:
    period = 340.0
    row = {
        "candidate_id": spec["candidate_id"],
        "family": "apcd_core_plus_helper_prototype",
        "helper_role": "weak_auxiliary_phase_helper",
        "target_bin_deg": spec["target_bin_deg"],
        "helper_type": spec["helper_type"],
        "p3_shape": spec["p3_shape"],
        "p3_length_nm": spec["p3_length_nm"],
        "p3_width_nm": spec["p3_width_nm"],
        "p3_rotation_deg": spec["p3_rotation_deg"],
        "p3_frac_x": spec["p3_frac_x"],
        "p3_frac_y": spec["p3_frac_y"],
        "p3_x_nm": (float(spec["p3_frac_x"]) - 0.5) * period,
        "p3_y_nm": (float(spec["p3_frac_y"]) - 0.5) * period,
        "requested_p3_frac_x": spec["requested_p3_frac_x"],
        "requested_p3_frac_y": spec["requested_p3_frac_y"],
        "position_adjustment_note": spec["position_adjustment_note"],
        "purpose": spec["purpose"],
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
        "internal_dx_nm": 0,
        "internal_dy_nm": 0,
        "period_x_nm": 340,
        "period_y_nm": 340,
        "height_nm": 300,
        "material": "c-Si",
        "substrate": "Al2O3",
        "requires_fdtd": "true",
        "status": "not_evaluated",
        "notes": "physics-guided helper prototype; fabrication-friendly standalone helper; not another APCD dimer; not a steering result",
    }
    return row


def _polygons(candidate: dict[str, object]) -> list[list[tuple[float, float]]]:
    return [
        rectangle_corners_nm(candidate["p1_length_nm"], candidate["p1_width_nm"], candidate["p1_rotation_deg"], *_core_center(candidate, "p1")),
        rectangle_corners_nm(candidate["p2_length_nm"], candidate["p2_width_nm"], candidate["p2_rotation_deg"], *_core_center(candidate, "p2")),
        rectangle_corners_nm(candidate["p3_length_nm"], candidate["p3_width_nm"], candidate["p3_rotation_deg"], candidate["p3_x_nm"], candidate["p3_y_nm"]),
    ]


def _core_center(candidate: dict[str, object], prefix: str) -> tuple[float, float]:
    period_x = float(candidate["period_x_nm"])
    period_y = float(candidate["period_y_nm"])
    dx = float(candidate["internal_dx_nm"])
    dy = float(candidate["internal_dy_nm"])
    if prefix == "p1":
        return ((float(candidate["p1_frac_x"]) - 0.5) * period_x + dx / 2.0, (float(candidate["p1_frac_y"]) - 0.5) * period_y + dy / 2.0)
    return ((float(candidate["p2_frac_x"]) - 0.5) * period_x - dx / 2.0, (float(candidate["p2_frac_y"]) - 0.5) * period_y - dy / 2.0)


def _pillar_mapping(candidate: dict[str, object], prefix: str) -> dict[str, object]:
    x, y = _core_center(candidate, prefix)
    return {
        "length_nm": _number(candidate[f"{prefix}_length_nm"]),
        "width_nm": _number(candidate[f"{prefix}_width_nm"]),
        "rotation_deg": _number(candidate[f"{prefix}_rotation_deg"]),
        "x_nm": _number(x),
        "y_nm": _number(y),
        "frac_x": _number(candidate[f"{prefix}_frac_x"]),
        "frac_y": _number(candidate[f"{prefix}_frac_y"]),
    }


def _helper_mapping(candidate: dict[str, object]) -> dict[str, object]:
    return {
        "role": "weak_auxiliary_phase_helper",
        "helper_role": "weak_auxiliary_phase_helper",
        "shape": candidate["p3_shape"],
        "length_nm": _number(candidate["p3_length_nm"]),
        "width_nm": _number(candidate["p3_width_nm"]),
        "rotation_deg": _number(candidate["p3_rotation_deg"]),
        "x_nm": _number(candidate["p3_x_nm"]),
        "y_nm": _number(candidate["p3_y_nm"]),
        "frac_x": _number(candidate["p3_frac_x"]),
        "frac_y": _number(candidate["p3_frac_y"]),
    }


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
        "p3_length_nm",
        "p3_width_nm",
        "p3_rotation_deg",
        "p3_x_nm",
        "p3_y_nm",
    ]
    return tuple(float(candidate[key]) for key in keys)


def _core_geometry_pass(candidate: dict[str, object]) -> bool:
    return (
        float(candidate["p1_length_nm"]) == 130.0
        and float(candidate["p1_width_nm"]) == 70.0
        and float(candidate["p1_rotation_deg"]) == 67.5
        and float(candidate["p2_length_nm"]) == 85.0
        and float(candidate["p2_width_nm"]) == 150.0
        and float(candidate["p2_rotation_deg"]) == 112.5
        and float(candidate["period_x_nm"]) == 340.0
        and float(candidate["period_y_nm"]) == 340.0
        and float(candidate["height_nm"]) == 300.0
    )


def _helper_dimensions_pass(candidate: dict[str, object]) -> bool:
    return (
        40.0 <= float(candidate["p3_length_nm"]) <= 140.0
        and 40.0 <= float(candidate["p3_width_nm"]) <= 140.0
        and 0.0 <= float(candidate["p3_rotation_deg"]) <= 180.0
        and 0.05 <= float(candidate["p3_frac_x"]) <= 0.95
        and 0.05 <= float(candidate["p3_frac_y"]) <= 0.95
    )


def _blank_result(candidate: dict[str, object]) -> dict[str, object]:
    return {
        "candidate_id": candidate["candidate_id"],
        "family": candidate["family"],
        "helper_role": candidate["helper_role"],
        "target_bin_deg": candidate["target_bin_deg"],
        "run_status": "",
        "status": "",
        "phase_deg": "",
        "phase_error_to_target_deg": "",
        "target_conversion": "",
        "opposite_spin_leakage": "",
        "conversion_to_leakage_ratio": "",
        "PD": "",
        "total_transmission": "",
        "t_alpha_star_from_alpha": "",
        "phase_shift_vs_baseline_deg": "",
        "early_target_pass": False,
        "early_leakage_pass": False,
        "early_ratio_pass": False,
        "early_pass": False,
        "target_bin_status": "",
        "source_result_csv": "",
        "notes": "",
    }


def _candidate_by_id(candidate_rows: Sequence[dict[str, object]], candidate_id: object) -> dict[str, object]:
    by_id = {str(row["candidate_id"]): row for row in candidate_rows}
    return by_id[str(candidate_id)]


def _float_or_blank(value: object) -> float | str:
    if value in {"", None}:
        return ""
    return float(value)


def _number(value: object) -> int | float:
    number = float(value)
    return int(number) if number.is_integer() else number


def _write_text(path: str | Path, lines: Sequence[str]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
