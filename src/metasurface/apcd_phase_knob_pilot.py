from __future__ import annotations

import cmath
import csv
import math
from pathlib import Path
from typing import Iterable, Sequence

import yaml

from metasurface.apcd_active_learning import wrap_phase_deg
from metasurface.apcd_candidate_validation import polygon_min_distance_nm, rectangle_corners_nm
from metasurface.apcd_nextgen_redesign import (
    NEXTGEN_CANDIDATE_FIELDS,
    NEXTGEN_SELECTED_IDS,
    read_csv_rows,
    write_csv_rows,
)
from metasurface.apcd_phase_lowering_candidates import (
    PHASE_COVERAGE_V4_FIELDS,
    analyze_phase_coverage_v4,
    classify_phase_region,
)
from metasurface.config import load_apcd_single_dimer_config


BASELINE_PHASE_DEG = 111.31665091018952
NEXTGEN_TOP2_IDS = ["ng_zero_rot_release_07", "ng_neg60_dxdy_release_08"]
WEAK_HELPER_TOP_ID = "wh_zero_aux_phase_04"

WEAK_HELPER_FIELDS = [
    *NEXTGEN_CANDIDATE_FIELDS,
    "helper_role",
    "helper_length_nm",
    "helper_width_nm",
    "helper_frac_x",
    "helper_frac_y",
    "helper_x_nm",
    "helper_y_nm",
    "helper_rotation_deg",
]

WEAK_HELPER_VALIDATION_FIELDS = [
    "candidate_id",
    "candidate_family",
    "target_bin_deg",
    "helper_role_pass",
    "helper_not_apcd_dimer_pass",
    "same_cell_min_gap_nm",
    "periodic_image_min_gap_nm",
    "minimum_gap_nm_threshold",
    "core_bounds_pass",
    "helper_bounds_pass",
    "beta_selective_geometry_pass",
    "overall_geometry_pass",
    "recommended_for_fdtd",
    "notes",
]

PILOT_RESULT_FIELDS = [
    "candidate_id",
    "family",
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


def helper_family_exists(nextgen_rows: Sequence[dict[str, str]]) -> bool:
    return any("helper" in row["candidate_family"] or "auxiliary" in row["candidate_family"] for row in nextgen_rows)


def build_weak_helper_candidate_pool(nextgen_rows: Sequence[dict[str, str]]) -> list[dict[str, object]]:
    by_id = {row["candidate_id"]: row for row in nextgen_rows}
    zero_core = by_id["ng_zero_rot_release_07"]
    neg60_core = by_id["ng_neg60_dxdy_release_08"]
    specs = [
        ("wh_zero_aux_phase_01", zero_core, 0, 42, 28, 0.50, 0.50, 0),
        ("wh_zero_aux_phase_02", zero_core, 0, 46, 30, 0.47, 0.53, 20),
        ("wh_zero_aux_phase_03", zero_core, 0, 50, 32, 0.53, 0.47, 40),
        ("wh_zero_aux_phase_04", zero_core, 0, 54, 34, 0.50, 0.44, 60),
        ("wh_zero_aux_phase_05", zero_core, 0, 58, 36, 0.44, 0.50, 80),
        ("wh_neg60_aux_phase_01", neg60_core, -60, 42, 28, 0.50, 0.50, 15),
        ("wh_neg60_aux_phase_02", neg60_core, -60, 46, 30, 0.47, 0.53, 35),
        ("wh_neg60_aux_phase_03", neg60_core, -60, 50, 32, 0.53, 0.47, 55),
        ("wh_neg60_aux_phase_04", neg60_core, -60, 54, 34, 0.50, 0.44, 75),
        ("wh_neg60_aux_phase_05", neg60_core, -60, 58, 36, 0.44, 0.50, 95),
    ]
    rows = []
    for candidate_id, core, target, helper_l, helper_w, helper_fx, helper_fy, helper_rot in specs:
        row = dict(core)
        row.update(
            {
                "candidate_id": candidate_id,
                "candidate_family": "apcd_core_plus_weak_helper",
                "source_stage": "09-P36/P38",
                "target_bin_deg": target,
                "anchor_candidate": core["candidate_id"],
                "design_strategy": "APCD core plus standalone weak auxiliary phase helper",
                "design_rationale": (
                    "Keep APCD core responsible for spin-selective conversion and add one weak helper pillar "
                    "as an extra phase knob; helper is not another APCD dimer or half-dimer."
                ),
                "risk_level": "pilot_moderate_risk",
                "expected_phase_direction": "test weak auxiliary phase knob for 0/-60 gap",
                "requires_geometry_validation": "true",
                "requires_fdtd": "true",
                "status": "not_evaluated",
                "notes": "weak-helper mini-pool scaffold only before pilot selection",
                "helper_role": "weak_auxiliary_phase_helper",
                "helper_length_nm": helper_l,
                "helper_width_nm": helper_w,
                "helper_frac_x": helper_fx,
                "helper_frac_y": helper_fy,
                "helper_x_nm": (helper_fx - 0.5) * float(core["period_x_nm"]),
                "helper_y_nm": (helper_fy - 0.5) * float(core["period_y_nm"]),
                "helper_rotation_deg": helper_rot,
            }
        )
        rows.append(row)
    return rows


def validate_weak_helper_candidate_pool(candidates: Sequence[dict[str, object]], minimum_gap_nm: float = 5.0) -> list[dict[str, object]]:
    return [validate_weak_helper_candidate(row, minimum_gap_nm=minimum_gap_nm) for row in candidates]


def validate_weak_helper_candidate(candidate: dict[str, object], minimum_gap_nm: float = 5.0) -> dict[str, object]:
    same_cell, periodic = helper_gaps(candidate)
    helper_role_pass = candidate.get("helper_role") == "weak_auxiliary_phase_helper"
    helper_not_apcd_pass = str(candidate["candidate_family"]) == "apcd_core_plus_weak_helper"
    core_bounds_pass = _core_bounds_pass(candidate)
    helper_bounds_pass = (
        35 <= float(candidate["helper_length_nm"]) <= 65
        and 24 <= float(candidate["helper_width_nm"]) <= 45
        and 0.35 <= float(candidate["helper_frac_x"]) <= 0.65
        and 0.35 <= float(candidate["helper_frac_y"]) <= 0.65
        and 0 <= float(candidate["helper_rotation_deg"]) <= 180
    )
    beta_pass = not (float(candidate["p2_length_nm"]) == 150.0 and float(candidate["p2_width_nm"]) == 85.0)
    same_pass = same_cell >= minimum_gap_nm
    periodic_pass = periodic >= minimum_gap_nm
    overall = all([helper_role_pass, helper_not_apcd_pass, core_bounds_pass, helper_bounds_pass, beta_pass, same_pass, periodic_pass])
    notes = []
    if not helper_role_pass:
        notes.append("helper_role must be weak_auxiliary_phase_helper")
    if not helper_not_apcd_pass:
        notes.append("helper must be standalone auxiliary, not another APCD dimer")
    if not core_bounds_pass:
        notes.append("core geometry outside nextgen bounds")
    if not helper_bounds_pass:
        notes.append("helper bounds failed")
    if not beta_pass:
        notes.append("beta-selective p2=150x85 geometry forbidden")
    if not same_pass:
        notes.append("same-cell gap below threshold")
    if not periodic_pass:
        notes.append("periodic-image gap below threshold")
    if not notes:
        notes.append("weak helper geometry validation passed; optical response unknown")
    return {
        "candidate_id": candidate["candidate_id"],
        "candidate_family": candidate["candidate_family"],
        "target_bin_deg": candidate["target_bin_deg"],
        "helper_role_pass": helper_role_pass,
        "helper_not_apcd_dimer_pass": helper_not_apcd_pass,
        "same_cell_min_gap_nm": same_cell,
        "periodic_image_min_gap_nm": periodic,
        "minimum_gap_nm_threshold": minimum_gap_nm,
        "core_bounds_pass": core_bounds_pass,
        "helper_bounds_pass": helper_bounds_pass,
        "beta_selective_geometry_pass": beta_pass,
        "overall_geometry_pass": overall,
        "recommended_for_fdtd": overall,
        "notes": "; ".join(notes),
    }


def select_top_helper_candidate(
    candidates: Sequence[dict[str, object]],
    validation_rows: Sequence[dict[str, object]],
) -> dict[str, object] | None:
    valid = {row["candidate_id"]: row for row in validation_rows if str(row["recommended_for_fdtd"]) == "True" or row["recommended_for_fdtd"] is True}
    by_id = {row["candidate_id"]: row for row in candidates}
    if WEAK_HELPER_TOP_ID in valid:
        return by_id[WEAK_HELPER_TOP_ID]
    for row in candidates:
        if row["candidate_id"] in valid:
            return row
    return None


def selected_pilot_rows(nextgen_rows: Sequence[dict[str, str]], helper_row: dict[str, object] | None) -> list[dict[str, object]]:
    by_id = {row["candidate_id"]: row for row in nextgen_rows}
    rows: list[dict[str, object]] = [by_id[candidate_id] for candidate_id in NEXTGEN_TOP2_IDS]
    if helper_row is not None:
        rows.append(helper_row)
    return rows


def write_pilot_configs(candidate_rows: Sequence[dict[str, object]], config_dir: str | Path) -> list[Path]:
    output_dir = Path(config_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for row in candidate_rows:
        path = output_dir / f"{row['candidate_id']}.yaml"
        path.write_text(build_pilot_config(row), encoding="utf-8")
        paths.append(path)
    return paths


def build_pilot_config(candidate: dict[str, object]) -> str:
    data = {
        "project": {"name": "blue_plane_wave_metasurface", "stage": "09_p36_p38_nextgen_phase_knob_pilot"},
        "candidate": {
            "variant_id": candidate["candidate_id"],
            "candidate_type": candidate["candidate_family"],
            "description": "nextgen phase-knob pilot candidate",
            "target_bin_deg": _number(candidate["target_bin_deg"]),
            "source_stage": "09-P36/P38",
            "anchor_candidate": candidate["anchor_candidate"],
            "risk_level": candidate["risk_level"],
            "design_rationale": candidate["design_rationale"],
            "source_pool_csv": _source_pool(candidate),
            "notes": "pilot config only; no full nextgen pool run; not a steering result",
        },
        "boundary": {
            "no_k7": True,
            "not_phase_ramp_supercell": True,
            "not_steering_result": True,
            "not_complete_k6_library_claim": True,
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
            "minimum_gap_nm": 5,
            "nanopillar_1": _pillar_mapping(candidate, "p1"),
            "nanopillar_2": _pillar_mapping(candidate, "p2"),
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
    if candidate.get("helper_role"):
        data["candidate"]["helper_role"] = candidate["helper_role"]
        data["geometry"]["nanopillar_helper"] = _helper_mapping(candidate)
    return yaml.safe_dump(data, sort_keys=False)


def validate_pilot_configs(config_paths: Sequence[str | Path]) -> list[dict[str, object]]:
    rows = []
    for path_like in config_paths:
        path = Path(path_like)
        config = load_apcd_single_dimer_config(path)
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        candidate_id = data["candidate"]["variant_id"]
        helper = config.geometry.nanopillar_helper
        if str(candidate_id).startswith("wh_"):
            passed = helper is not None and helper.role == "weak_auxiliary_phase_helper"
        else:
            passed = helper is None
        rows.append({"candidate_id": candidate_id, "config_path": str(path), "validation_pass": passed, "notes": "config load validation only; no FDTD/lumapi/.fsp"})
    return rows


def summarize_pilot_results(candidate_rows: Sequence[dict[str, object]], repo_root: str | Path) -> list[dict[str, object]]:
    root = Path(repo_root)
    rows = []
    for candidate in candidate_rows:
        result_path = root / "outputs/apcd_k6_metagrating_633nm/phase_state_candidates" / str(candidate["candidate_id"]) / "results.csv"
        if not result_path.exists():
            rows.append(not_run_result(candidate))
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
        "family": candidate["candidate_family"],
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
        "notes": result_notes(candidate, target_status, early, error),
    }


def not_run_result(candidate: dict[str, object]) -> dict[str, object]:
    return {
        "candidate_id": candidate["candidate_id"],
        "family": candidate["candidate_family"],
        "target_bin_deg": candidate["target_bin_deg"],
        "run_status": "not_run",
        "status": "not_run",
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
        "target_bin_status": "not_run",
        "source_result_csv": "",
        "notes": "candidate was not run; no result fabricated",
    }


def build_dataset_v6(dataset_v5_rows: Sequence[dict[str, str]], result_rows: Sequence[dict[str, object]], candidate_rows: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = list(dataset_v5_rows)
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
            "candidate_family": candidate["candidate_family"],
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
            "notes": _dataset_notes(candidate),
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


def helper_gaps(candidate: dict[str, object]) -> tuple[float, float]:
    period_x = float(candidate["period_x_nm"])
    period_y = float(candidate["period_y_nm"])
    polygons = _polygons(candidate)
    same = min(
        polygon_min_distance_nm(poly_a, poly_b)
        for index, poly_a in enumerate(polygons)
        for poly_b in polygons[index + 1 :]
    )
    periodic = math.inf
    for poly_a in polygons:
        for poly_b in polygons:
            for sx in (-period_x, 0.0, period_x):
                for sy in (-period_y, 0.0, period_y):
                    if sx == 0.0 and sy == 0.0:
                        continue
                    shifted = [(x + sx, y + sy) for x, y in poly_b]
                    periodic = min(periodic, polygon_min_distance_nm(poly_a, shifted))
    return same, periodic


def _polygons(candidate: dict[str, object]) -> list[list[tuple[float, float]]]:
    return [
        rectangle_corners_nm(candidate["p1_length_nm"], candidate["p1_width_nm"], candidate["p1_rotation_deg"], *_core_center(candidate, "p1")),
        rectangle_corners_nm(candidate["p2_length_nm"], candidate["p2_width_nm"], candidate["p2_rotation_deg"], *_core_center(candidate, "p2")),
        rectangle_corners_nm(candidate["helper_length_nm"], candidate["helper_width_nm"], candidate["helper_rotation_deg"], candidate["helper_x_nm"], candidate["helper_y_nm"]),
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
        "length_nm": _number(candidate["helper_length_nm"]),
        "width_nm": _number(candidate["helper_width_nm"]),
        "rotation_deg": _number(candidate["helper_rotation_deg"]),
        "x_nm": _number(candidate["helper_x_nm"]),
        "y_nm": _number(candidate["helper_y_nm"]),
        "frac_x": _number(candidate["helper_frac_x"]),
        "frac_y": _number(candidate["helper_frac_y"]),
    }


def _source_pool(candidate: dict[str, object]) -> str:
    if candidate.get("helper_role"):
        return "outputs/apcd_k6_active_learning/weak_helper_candidate_pool_v6.csv"
    return "outputs/apcd_k6_active_learning/nextgen_candidate_pool_v6.csv"


def result_notes(candidate: dict[str, object], target_status: str, early: bool, error: object) -> str:
    helper = "; includes weak auxiliary phase helper" if candidate.get("helper_role") else ""
    return f"09-P36/P38 nextgen phase-knob pilot{helper}; wrapped_error={error}; target_bin_status={target_status}; early_pass={early}; not a steering result"


def _dataset_notes(candidate: dict[str, object]) -> str:
    if candidate.get("helper_role"):
        return "09-P36/P38 real FDTD weak-helper pilot; helper columns are in candidate pool; raw results not committed; not a steering result"
    return "09-P36/P38 real FDTD nextgen phase-knob pilot; raw results not committed; not a steering result"


def _core_bounds_pass(candidate: dict[str, object]) -> bool:
    return (
        105 <= float(candidate["p1_length_nm"]) <= 155
        and 50 <= float(candidate["p1_width_nm"]) <= 95
        and 65 <= float(candidate["p2_length_nm"]) <= 112
        and 125 <= float(candidate["p2_width_nm"]) <= 175
        and -60 <= float(candidate["internal_dx_nm"]) <= 60
        and -60 <= float(candidate["internal_dy_nm"]) <= 60
    )


def _float_or_blank(value: object) -> float | str:
    if value in {"", None}:
        return ""
    return float(value)


def _number(value: object) -> int | float:
    number = float(value)
    return int(number) if number.is_integer() else number
