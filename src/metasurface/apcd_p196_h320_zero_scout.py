from __future__ import annotations

import copy
import csv
import math
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import yaml

from metasurface.apcd_candidate_validation import polygon_min_distance_nm, rectangle_corners_nm


HEIGHT_NM = 320
PERIOD_X_NM = 340
PERIOD_Y_NM = 340
MIN_GAP_NM = 5.0
TARGET_BIN_DEG = 0

POOL_FIELDS = [
    "candidate_id",
    "group",
    "family",
    "base_anchor",
    "target_bin_deg",
    "height_nm",
    "period_x_nm",
    "period_y_nm",
    "p1_length_nm",
    "p1_width_nm",
    "p1_rotation_deg",
    "p1_x_nm",
    "p1_y_nm",
    "p2_length_nm",
    "p2_width_nm",
    "p2_rotation_deg",
    "p2_x_nm",
    "p2_y_nm",
    "helper_length_nm",
    "helper_width_nm",
    "helper_rotation_deg",
    "helper_x_nm",
    "helper_y_nm",
    "geometry_changes",
    "expected_mechanism",
    "risk_level",
    "status",
    "config_path",
    "notes",
]

VALIDATION_FIELDS = [
    "candidate_id",
    "group",
    "same_cell_min_gap_nm",
    "periodic_image_min_gap_nm",
    "minimum_gap_nm_threshold",
    "no_overlap_pass",
    "same_cell_gap_pass",
    "periodic_gap_pass",
    "boundary_pass",
    "height_fixed_pass",
    "dimension_bounds_pass",
    "duplicate_candidate_id_pass",
    "duplicate_geometry_pass",
    "overall_geometry_pass",
    "recommended_for_fdtd",
    "notes",
]


@dataclass(frozen=True)
class PillarSpec:
    length_nm: int
    width_nm: int
    rotation_deg: float
    x_nm: int
    y_nm: int
    shape: str = "rectangle"
    notch_depth_nm: int | None = None
    notch_width_nm: int | None = None
    notch_side: str | None = None


@dataclass(frozen=True)
class CandidateSpec:
    candidate_id: str
    group: str
    family: str
    base_anchor: str
    p1: PillarSpec
    p2: PillarSpec
    geometry_changes: str
    expected_mechanism: str
    risk_level: str
    helper: PillarSpec | None = None
    notes: str = ""


def build_p196_candidate_specs() -> list[CandidateSpec]:
    base_p1 = PillarSpec(130, 70, 67.5, 79, 79)
    base_p2 = PillarSpec(85, 150, 112.5, -79, -79)
    return [
        CandidateSpec(
            "cpk_p196_zgap_dx_in_01",
            "dimer_gap_coupling_offset",
            "h320_zero_gap_coupling_offset",
            "P190_-120_anchor",
            PillarSpec(130, 70, 67.5, 75, 79),
            PillarSpec(85, 150, 112.5, -75, -79),
            "balanced x inward shift from safe h320 core: p1 x 79->75, p2 x -79->-75",
            "change dimer coupling phase without common rotation",
            "medium",
        ),
        CandidateSpec(
            "cpk_p196_zgap_dx_out_02",
            "dimer_gap_coupling_offset",
            "h320_zero_gap_coupling_offset",
            "strong_-180_anchor_family",
            PillarSpec(130, 70, 67.5, 83, 79),
            PillarSpec(85, 150, 112.5, -83, -79),
            "balanced x outward shift from safe h320 core: p1 x 79->83, p2 x -79->-83",
            "test opposite coupling sign while preserving p1/p2 rotations",
            "medium",
        ),
        CandidateSpec(
            "cpk_p196_zgap_dy_in_03",
            "dimer_gap_coupling_offset",
            "h320_zero_gap_coupling_offset",
            "120_anchor_family",
            PillarSpec(130, 70, 67.5, 79, 75),
            PillarSpec(85, 150, 112.5, -79, -75),
            "balanced y inward shift from safe h320 core: p1 y 79->75, p2 y -79->-75",
            "change vertical coupling and retardance balance at fixed h320",
            "medium",
        ),
        CandidateSpec(
            "cpk_p196_zgap_shear_04",
            "dimer_gap_coupling_offset",
            "h320_zero_gap_coupling_offset",
            "P195_C_dynamic_high_ratio_diagnostic",
            PillarSpec(130, 70, 67.5, 75, 83),
            PillarSpec(85, 150, 112.5, -83, -75),
            "small shear offset around safe h320 core: p1 (-4,+4), p2 (-4,+4) in opposite quadrants",
            "detune coupling asymmetrically without broad rotation recovery",
            "medium_high",
        ),
        CandidateSpec(
            "cpk_p196_znotch_p1r_05",
            "mild_notch_slot_perturbation",
            "h320_zero_mild_notch_slot",
            "P190_-120_anchor",
            PillarSpec(130, 70, 67.5, 79, 79, "notched_rectangle", 4, 18, "right"),
            base_p2,
            "p1 right-side 4 nm notch placeholder using supported notched_rectangle schema",
            "local scalar phase trimming on p1 while keeping APCD dimer orientation",
            "medium",
        ),
        CandidateSpec(
            "cpk_p196_znotch_p2l_06",
            "mild_notch_slot_perturbation",
            "h320_zero_mild_notch_slot",
            "120_anchor_family",
            base_p1,
            PillarSpec(85, 150, 112.5, -79, -79, "notched_rectangle", 4, 18, "left"),
            "p2 left-side 4 nm notch placeholder using supported notched_rectangle schema",
            "rebalance p2 phase loading without using beta-selective baseline",
            "medium",
        ),
        CandidateSpec(
            "cpk_p196_zslot_bal_07",
            "mild_notch_slot_perturbation",
            "h320_zero_mild_notch_slot",
            "P195_C_dynamic_high_ratio_diagnostic",
            PillarSpec(129, 69, 67.5, 79, 79, "notched_rectangle", 3, 16, "right"),
            PillarSpec(86, 149, 112.5, -79, -79, "notched_rectangle", 3, 16, "left"),
            "balanced 1 nm p1/p2 compensation plus symmetric 3 nm notch placeholders",
            "weak phase trim with compensated conversion channel",
            "medium_high",
        ),
        CandidateSpec(
            "cpk_p196_zhelper_sq_far_08",
            "weak_scalar_helper",
            "h320_zero_weak_scalar_helper",
            "strong_-180_anchor_family",
            base_p1,
            base_p2,
            "add far weak square helper 38x38 nm at (0, 125)",
            "standalone weak scalar phase loading away from the APCD core",
            "medium",
            helper=PillarSpec(38, 38, 0, 0, 125),
        ),
        CandidateSpec(
            "cpk_p196_zhelper_diag_09",
            "weak_scalar_helper",
            "h320_zero_weak_scalar_helper",
            "120_anchor_family",
            base_p1,
            base_p2,
            "add diagonal weak helper 42x36 nm at (-118, 0)",
            "weak detour phase perturbation with large core-helper gap",
            "medium",
            helper=PillarSpec(42, 36, 45, -118, 0),
        ),
        CandidateSpec(
            "cpk_p196_zhelper_mid_10",
            "weak_scalar_helper",
            "h320_zero_weak_scalar_helper",
            "P190_-120_anchor",
            base_p1,
            base_p2,
            "add weak scalar helper 34x44 nm at (118, 0)",
            "test side-loaded scalar phase without adding a second APCD dimer",
            "medium",
            helper=PillarSpec(34, 44, 0, 118, 0),
        ),
        CandidateSpec(
            "cpk_p196_zbal_geom_a_11",
            "balanced_p1_p2_geometry_compensation",
            "h320_zero_balanced_geometry_compensation",
            "P190_-120_anchor",
            PillarSpec(128, 71, 67.5, 79, 79),
            PillarSpec(87, 148, 112.5, -79, -79),
            "p1 130x70->128x71 and p2 85x150->87x148",
            "balanced aspect-ratio compensation to move phase while preserving selectivity",
            "low_medium",
        ),
        CandidateSpec(
            "cpk_p196_zbal_geom_b_12",
            "balanced_p1_p2_geometry_compensation",
            "h320_zero_balanced_geometry_compensation",
            "P195_C_dynamic_high_ratio_diagnostic",
            PillarSpec(132, 69, 67.5, 79, 79),
            PillarSpec(83, 152, 112.5, -79, -79),
            "p1 130x70->132x69 and p2 85x150->83x152",
            "opposite balanced compensation to probe zero-bin phase crossing",
            "medium",
        ),
    ]


def candidate_to_row(spec: CandidateSpec, config_path: Path | str = "") -> dict[str, object]:
    helper = spec.helper
    return {
        "candidate_id": spec.candidate_id,
        "group": spec.group,
        "family": spec.family,
        "base_anchor": spec.base_anchor,
        "target_bin_deg": TARGET_BIN_DEG,
        "height_nm": HEIGHT_NM,
        "period_x_nm": PERIOD_X_NM,
        "period_y_nm": PERIOD_Y_NM,
        "p1_length_nm": spec.p1.length_nm,
        "p1_width_nm": spec.p1.width_nm,
        "p1_rotation_deg": spec.p1.rotation_deg,
        "p1_x_nm": spec.p1.x_nm,
        "p1_y_nm": spec.p1.y_nm,
        "p2_length_nm": spec.p2.length_nm,
        "p2_width_nm": spec.p2.width_nm,
        "p2_rotation_deg": spec.p2.rotation_deg,
        "p2_x_nm": spec.p2.x_nm,
        "p2_y_nm": spec.p2.y_nm,
        "helper_length_nm": "" if helper is None else helper.length_nm,
        "helper_width_nm": "" if helper is None else helper.width_nm,
        "helper_rotation_deg": "" if helper is None else helper.rotation_deg,
        "helper_x_nm": "" if helper is None else helper.x_nm,
        "helper_y_nm": "" if helper is None else helper.y_nm,
        "geometry_changes": spec.geometry_changes,
        "expected_mechanism": spec.expected_mechanism,
        "risk_level": spec.risk_level,
        "status": "not_evaluated",
        "config_path": str(config_path).replace("\\", "/") if config_path else "",
        "notes": spec.notes or "P196 h320 zero-bin mechanism scout only; optical response unknown until real FDTD",
    }


def build_config(spec: CandidateSpec) -> dict[str, object]:
    config: dict[str, object] = {
        "project": {
            "name": "blue_plane_wave_metasurface",
            "stage": "09_p196_h320_zero_bin_mechanism_scout_yaml_only",
        },
        "candidate": {
            "variant_id": spec.candidate_id,
            "candidate_type": spec.family,
            "scheme_name": "p196_h320_zero_bin_mechanism_scout",
            "description": f"P196 fixed-height h320 zero-bin mechanism scout candidate {spec.candidate_id}",
            "target_bins_deg": "0",
            "source_stage": "09-P196",
            "anchor_candidate_id": spec.base_anchor,
            "mechanism_group": spec.group,
            "expected_mechanism": spec.expected_mechanism,
            "geometry_changes": spec.geometry_changes,
            "risk_level": spec.risk_level,
            "notes": "Stage 09 fixed-height h320 candidate; not K6 phase-ramp, not steering, not mixed-height, not ML training.",
        },
        "boundary": {
            "no_k7": True,
            "not_phase_ramp_supercell": True,
            "not_steering_result": True,
            "not_complete_k6_library_claim": True,
            "not_mixed_height": True,
            "no_fdtd_run_by_generator": True,
            "no_lumapi_by_generator": True,
            "no_fsp_export_by_generator": True,
            "fixed_height_nm": HEIGHT_NM,
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
            "period_x_nm": PERIOD_X_NM,
            "period_y_nm": PERIOD_Y_NM,
            "height_nm": HEIGHT_NM,
            "minimum_gap_nm": MIN_GAP_NM,
            "nanopillar_1": _pillar_config(spec.p1),
            "nanopillar_2": _pillar_config(spec.p2),
        },
        "simulation": {
            "substrate_thickness_nm": 220,
            "source_offset_nm": 120,
            "monitor_offset_nm": 180,
            "z_padding_above_nm": 260,
            "mesh_accuracy": 1,
            "simulation_time_fs": 250,
        },
        "output": {
            "result_dir": f"outputs/apcd_k6_metagrating_633nm/phase_state_candidates/{spec.candidate_id}",
        },
    }
    if spec.helper is not None:
        helper = _pillar_config(spec.helper)
        helper["role"] = "weak_auxiliary_phase_helper"
        helper["helper_role"] = "weak_auxiliary_phase_helper"
        config["geometry"]["nanopillar_helper"] = helper
    return config


def validate_p196_pool(specs: Sequence[CandidateSpec]) -> list[dict[str, object]]:
    id_counts = Counter(spec.candidate_id for spec in specs)
    geometry_counts = Counter(_geometry_key(spec) for spec in specs)
    rows = []
    for spec in specs:
        polygons = _polygons(spec)
        same_cell_gap = min(
            polygon_min_distance_nm(a, b)
            for index, a in enumerate(polygons)
            for b in polygons[index + 1 :]
        )
        periodic_gap = _periodic_gap(polygons)
        boundary_pass = all(_polygon_inside_period(poly) for poly in polygons)
        no_overlap_pass = same_cell_gap > 0.0
        same_pass = same_cell_gap >= MIN_GAP_NM
        periodic_pass = periodic_gap >= MIN_GAP_NM
        height_pass = HEIGHT_NM == 320
        bounds_pass = _dimension_bounds_pass(spec)
        duplicate_id_pass = id_counts[spec.candidate_id] == 1
        duplicate_geometry_pass = geometry_counts[_geometry_key(spec)] == 1
        overall = all(
            [
                no_overlap_pass,
                same_pass,
                periodic_pass,
                boundary_pass,
                height_pass,
                bounds_pass,
                duplicate_id_pass,
                duplicate_geometry_pass,
            ]
        )
        notes = []
        if not no_overlap_pass:
            notes.append("pillar overlap detected")
        if not same_pass:
            notes.append("same-cell gap below 5 nm")
        if not periodic_pass:
            notes.append("periodic image gap below 5 nm")
        if not boundary_pass:
            notes.append("pillar crosses unit-cell boundary")
        if not bounds_pass:
            notes.append("dimension bounds failed")
        if not duplicate_id_pass:
            notes.append("duplicate candidate_id")
        if not duplicate_geometry_pass:
            notes.append("duplicate geometry")
        if overall:
            notes.append("geometry sanity checks passed; not optically evaluated")
        rows.append(
            {
                "candidate_id": spec.candidate_id,
                "group": spec.group,
                "same_cell_min_gap_nm": round(same_cell_gap, 6),
                "periodic_image_min_gap_nm": round(periodic_gap, 6),
                "minimum_gap_nm_threshold": MIN_GAP_NM,
                "no_overlap_pass": no_overlap_pass,
                "same_cell_gap_pass": same_pass,
                "periodic_gap_pass": periodic_pass,
                "boundary_pass": boundary_pass,
                "height_fixed_pass": height_pass,
                "dimension_bounds_pass": bounds_pass,
                "duplicate_candidate_id_pass": duplicate_id_pass,
                "duplicate_geometry_pass": duplicate_geometry_pass,
                "overall_geometry_pass": overall,
                "recommended_for_fdtd": overall,
                "notes": "; ".join(notes),
            }
        )
    return rows


def export_p196_outputs(
    specs: Sequence[CandidateSpec],
    *,
    config_dir: Path,
    summary_csv: Path,
    validation_csv: Path,
    report_md: Path,
) -> None:
    config_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for spec in specs:
        config_path = config_dir / f"{spec.candidate_id}.yaml"
        write_yaml(config_path, build_config(spec))
        rows.append(candidate_to_row(spec, _display_path(config_path)))
    write_csv_rows(rows, summary_csv, POOL_FIELDS)
    validation_rows = validate_p196_pool(specs)
    write_csv_rows(validation_rows, validation_csv, VALIDATION_FIELDS)
    write_report(report_md, rows, validation_rows)


def write_csv_rows(rows: Iterable[dict[str, object]], path: Path, fieldnames: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fieldnames} for row in rows)


def write_yaml(path: Path, data: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)


def _display_path(path: Path) -> str:
    try:
        return path.relative_to(Path.cwd()).as_posix()
    except ValueError:
        return path.as_posix()


def write_report(report_md: Path, rows: Sequence[dict[str, object]], validation_rows: Sequence[dict[str, object]]) -> None:
    report_md.parent.mkdir(parents=True, exist_ok=True)
    pass_count = sum(row["overall_geometry_pass"] is True for row in validation_rows)
    lines = [
        "# APCD P196 h320 zero-bin mechanism scout",
        "",
        "## Scope",
        "",
        "This is a Stage 09 fixed-height h320 single-dimer zero-bin mechanism scout. It generates configs, a small candidate table, and geometry sanity validation only.",
        "",
        "It does not run FDTD, does not call lumapi, does not export `.fsp`, does not enter K6 phase-ramp supercell, does not use mixed height, and does not claim steering or a complete K6 phase-state library.",
        "",
        "## Starting Context",
        "",
        "- Current h320 fixed-height coverage from the task context is `[-180, -120, 120]`.",
        "- Missing h320 bins remain `[-60, 0, 60]`.",
        "- P195 -60 scout found phase hits but severe APCD selectivity collapse, so this plan avoids broad common-rotation leakage recovery.",
        "- P195 C_dynamic high-ratio -180 variants are used as diagnostics only, not as a route to keep polishing -180.",
        "",
        "## Candidate Strategy",
        "",
        "The pool contains 12 integer-nm candidates at `height_nm = 320` targeting the 0 deg phase bin through orthogonal mechanisms:",
        "",
        "- dimer gap/coupling offset",
        "- mild notch/slot perturbation using existing notched-rectangle schema",
        "- weak scalar helper, kept standalone and away from the APCD core",
        "- balanced p1/p2 geometry compensation",
        "",
        "## Geometry Sanity",
        "",
        f"- candidate count: {len(rows)}",
        f"- geometry pass: {pass_count}/{len(validation_rows)}",
        "- checks: no overlap, minimum same-cell gap, periodic-image gap, boundary containment, fixed height, dimension bounds, duplicate id, duplicate geometry",
        "",
        "## Candidate Summary",
        "",
        "| candidate | group | anchor | mechanism | status |",
        "|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| `{row['candidate_id']}` | {row['group']} | {row['base_anchor']} | {row['expected_mechanism']} | {row['status']} |"
        )
    lines.extend(
        [
            "",
            "## Recommendation",
            "",
            "Do not run the whole pool blindly. If a follow-up FDTD task is opened, first review the 12 configs and choose at most a top-2 or top-3 subset from different mechanism groups, with priority on geometry-pass candidates that keep APCD selectivity least disturbed.",
        ]
    )
    report_md.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _pillar_config(pillar: PillarSpec) -> dict[str, object]:
    data: dict[str, object] = {
        "shape": pillar.shape,
        "length_nm": pillar.length_nm,
        "width_nm": pillar.width_nm,
        "rotation_deg": pillar.rotation_deg,
        "x_nm": float(pillar.x_nm),
        "y_nm": float(pillar.y_nm),
        "frac_x": round(pillar.x_nm / PERIOD_X_NM + 0.5, 6),
        "frac_y": round(pillar.y_nm / PERIOD_Y_NM + 0.5, 6),
    }
    if pillar.notch_depth_nm is not None:
        data["notch_depth_nm"] = pillar.notch_depth_nm
        data["notch_width_nm"] = pillar.notch_width_nm
        data["notch_side"] = pillar.notch_side
    return data


def _polygons(spec: CandidateSpec) -> list[list[tuple[float, float]]]:
    pillars = [spec.p1, spec.p2] + ([] if spec.helper is None else [spec.helper])
    return [
        rectangle_corners_nm(
            pillar.length_nm,
            pillar.width_nm,
            pillar.rotation_deg,
            pillar.x_nm,
            pillar.y_nm,
        )
        for pillar in pillars
    ]


def _periodic_gap(polygons: Sequence[Sequence[tuple[float, float]]]) -> float:
    gap = math.inf
    for a in polygons:
        for b in polygons:
            for sx in (-PERIOD_X_NM, 0.0, PERIOD_X_NM):
                for sy in (-PERIOD_Y_NM, 0.0, PERIOD_Y_NM):
                    if sx == 0.0 and sy == 0.0:
                        continue
                    shifted = [(x + sx, y + sy) for x, y in b]
                    gap = min(gap, polygon_min_distance_nm(a, shifted))
    return gap


def _polygon_inside_period(poly: Sequence[tuple[float, float]]) -> bool:
    half_x = PERIOD_X_NM / 2.0
    half_y = PERIOD_Y_NM / 2.0
    return all(-half_x <= x <= half_x and -half_y <= y <= half_y for x, y in poly)


def _dimension_bounds_pass(spec: CandidateSpec) -> bool:
    pillars = [spec.p1, spec.p2] + ([] if spec.helper is None else [spec.helper])
    positive_dims = all(pillar.length_nm > 0 and pillar.width_nm > 0 for pillar in pillars)
    p1_bounds = 110 <= spec.p1.length_nm <= 150 and 55 <= spec.p1.width_nm <= 90
    p2_bounds = 70 <= spec.p2.length_nm <= 105 and 130 <= spec.p2.width_nm <= 170
    helper_bounds = spec.helper is None or (
        25 <= spec.helper.length_nm <= 90 and 25 <= spec.helper.width_nm <= 120
    )
    beta_selective_forbidden = spec.p2.length_nm == 150 and spec.p2.width_nm == 85
    return positive_dims and p1_bounds and p2_bounds and helper_bounds and not beta_selective_forbidden


def _geometry_key(spec: CandidateSpec) -> tuple[object, ...]:
    helper_key = None if spec.helper is None else _pillar_key(spec.helper)
    return (_pillar_key(spec.p1), _pillar_key(spec.p2), helper_key)


def _pillar_key(pillar: PillarSpec) -> tuple[object, ...]:
    return (
        pillar.length_nm,
        pillar.width_nm,
        pillar.rotation_deg,
        pillar.x_nm,
        pillar.y_nm,
        pillar.shape,
        pillar.notch_depth_nm,
        pillar.notch_width_nm,
        pillar.notch_side,
    )
