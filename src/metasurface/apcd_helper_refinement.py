from __future__ import annotations

import cmath
import csv
import math
import subprocess
from pathlib import Path
from typing import Iterable, Sequence

import yaml

from metasurface.apcd_active_learning import wrap_phase_deg
from metasurface.apcd_candidate_validation import polygon_min_distance_nm, rectangle_corners_nm
from metasurface.apcd_phase_lowering_candidates import analyze_phase_coverage_v4, classify_phase_region
from metasurface.config import load_apcd_single_dimer_config


BASELINE_PHASE_DEG = 111.31665091018952
SELECTED_REFINEMENT_IDS = [
    "hr_aniso_push_05",
    "hr_aniso_push_08",
    "hr_phase_delay_03",
    "hr_lowleak_control_02",
]

HELPER_REFINEMENT_POOL_FIELDS = [
    "candidate_id",
    "family",
    "target_bin_deg",
    "anchor_candidate",
    "helper_role",
    "helper_type",
    "p3_shape",
    "p3_length_nm",
    "p3_width_nm",
    "p3_rotation_deg",
    "p3_frac_x",
    "p3_frac_y",
    "p3_x_nm",
    "p3_y_nm",
    "expected_phase_direction",
    "design_rationale",
    "risk_level",
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

HELPER_REFINEMENT_VALIDATION_FIELDS = [
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
    "helper_role_pass",
    "helper_not_apcd_dimer_pass",
    "fabrication_friendly_shape_pass",
    "beta_selective_geometry_pass",
    "duplicate_candidate_id_pass",
    "duplicate_geometry_pass",
    "overall_geometry_pass",
    "recommended_for_fdtd",
    "notes",
]

HELPER_REFINEMENT_SELECTION_FIELDS = [
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
    "notes",
]

HELPER_REFINEMENT_RESULT_FIELDS = [
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


def build_helper_refinement_candidate_pool() -> list[dict[str, object]]:
    specs = [
        ("hr_aniso_push_01", "aniso_helper_phase_push", -180, "h2_weak_aniso_03", 60, 120, 90, 0.25, 0.75, "extend high-positive usable phase toward pi", "medium_risk"),
        ("hr_aniso_push_02", "aniso_helper_phase_push", -180, "h2_weak_aniso_03", 60, 120, 135, 0.25, 0.75, "rotate anisotropic helper toward stronger phase delay", "medium_risk"),
        ("hr_aniso_push_03", "aniso_helper_phase_push", -180, "h2_weak_aniso_03", 70, 110, 45, 0.25, 0.75, "slightly wider anisotropic helper around successful anchor", "medium_risk"),
        ("hr_aniso_push_04", "aniso_helper_phase_push", -180, "h2_weak_aniso_03", 70, 120, 90, 0.25, 0.75, "larger phase-push nanofin with geometry-safe gap", "medium_high_risk"),
        ("hr_aniso_push_05", "aniso_helper_phase_push", -180, "h2_weak_aniso_03", 70, 120, 135, 0.25, 0.75, "selected anisotropic high-positive phase push", "medium_high_risk"),
        ("hr_aniso_push_06", "aniso_helper_phase_push", -180, "h2_weak_aniso_03", 80, 120, 90, 0.25, 0.75, "stronger anisotropic helper, still fabrication-friendly", "medium_high_risk"),
        ("hr_aniso_push_07", "aniso_helper_phase_push", -180, "h2_weak_aniso_03", 80, 120, 135, 0.25, 0.75, "stronger rotated anisotropic phase push", "high_risk"),
        ("hr_aniso_push_08", "aniso_helper_phase_push", -180, "h2_weak_aniso_03", 80, 110, 135, 0.25, 0.75, "selected high-positive phase push with safer width", "medium_high_risk"),
        ("hr_phase_delay_01", "phase_delay_gap_fixed", -180, "h2_phase_delay_04", 80, 110, 90, 0.25, 0.75, "gap-fixed phase-delay retry using reduced size", "medium_high_risk"),
        ("hr_phase_delay_02", "phase_delay_gap_fixed", -180, "h2_phase_delay_04", 60, 110, 120, 0.25, 0.75, "gap-fixed phase-delay retry with narrow helper", "medium_high_risk"),
        ("hr_phase_delay_03", "phase_delay_gap_fixed", -180, "h2_phase_delay_04", 75, 115, 120, 0.25, 0.75, "selected geometry-safe phase-delay retry", "medium_high_risk"),
        ("hr_phase_delay_04", "phase_delay_gap_fixed", -180, "h2_phase_delay_04", 65, 120, 135, 0.25, 0.75, "stronger phase-delay retry with safe gap", "high_risk"),
        ("hr_phase_delay_05", "phase_delay_gap_fixed", -180, "h2_phase_delay_04", 90, 110, 90, 0.25, 0.75, "largest gap-fixed phase-delay nanofin retained in pool only", "high_risk"),
        ("hr_lowleak_control_01", "lowleak_anchor_control", 120, "h2_nearsquare_load_02", 70, 70, 45, 0.25, 0.75, "low-leakage square-ish helper control", "low_risk"),
        ("hr_lowleak_control_02", "lowleak_anchor_control", 120, "h2_nearsquare_load_02", 80, 70, 45, 0.25, 0.75, "selected near-square low-leakage control", "low_risk"),
        ("hr_lowleak_control_03", "lowleak_anchor_control", 120, "h2_square_load_01", 80, 70, 90, 0.25, 0.75, "orthogonal near-square low-leakage control", "low_risk"),
    ]
    return [_candidate_row(*spec) for spec in specs]


def validate_helper_refinement_pool(candidates: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    id_counts = {str(row["candidate_id"]): 0 for row in candidates}
    for row in candidates:
        id_counts[str(row["candidate_id"])] += 1
    seen_geometry: set[tuple[float, ...]] = set()
    rows = []
    for candidate in candidates:
        same_cell, periodic = helper_refinement_gaps(candidate)
        helper_core_gap = _helper_core_gap(candidate)
        threshold = 55.0 if str(candidate["family"]) == "phase_delay_gap_fixed" else 50.0
        geometry_key = _geometry_key(candidate)
        duplicate_geometry_pass = geometry_key not in seen_geometry
        seen_geometry.add(geometry_key)
        no_overlap = same_cell > 0.0
        same_pass = same_cell >= threshold
        periodic_pass = periodic >= threshold
        helper_core_pass = helper_core_gap >= threshold
        role_pass = candidate["helper_role"] == "weak_auxiliary_phase_helper"
        not_dimer_pass = candidate["family"] in {"aniso_helper_phase_push", "phase_delay_gap_fixed", "lowleak_anchor_control"}
        shape_pass = candidate["p3_shape"] in {"near-square loading helper", "weak rectangular nanofin helper", "moderate rectangular phase-delay nanofin helper"}
        bounds_pass = _bounds_pass(candidate)
        beta_pass = not (float(candidate["p2_length_nm"]) == 150.0 and float(candidate["p2_width_nm"]) == 85.0)
        duplicate_id_pass = id_counts[str(candidate["candidate_id"])] == 1
        overall = all(
            [
                no_overlap,
                same_pass,
                periodic_pass,
                helper_core_pass,
                role_pass,
                not_dimer_pass,
                shape_pass,
                bounds_pass,
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
        if not bounds_pass:
            notes.append("dimension or position bounds failed")
        if not beta_pass:
            notes.append("beta-selective p2=150x85 forbidden")
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
                "dimensions_bounds_pass": bounds_pass,
                "helper_role_pass": role_pass,
                "helper_not_apcd_dimer_pass": not_dimer_pass,
                "fabrication_friendly_shape_pass": shape_pass,
                "beta_selective_geometry_pass": beta_pass,
                "duplicate_candidate_id_pass": duplicate_id_pass,
                "duplicate_geometry_pass": duplicate_geometry_pass,
                "overall_geometry_pass": overall,
                "recommended_for_fdtd": overall,
                "notes": "; ".join(notes),
            }
        )
    return rows


def select_helper_refinement_candidates(candidates: Sequence[dict[str, object]], validation_rows: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    valid = {str(row["candidate_id"]) for row in validation_rows if row["recommended_for_fdtd"] is True or str(row["recommended_for_fdtd"]) == "True"}
    by_id = {str(row["candidate_id"]): row for row in candidates}
    reasons = {
        "hr_aniso_push_05": "phase-push candidate close to h2_weak_aniso_03 but with stronger helper width and 135 deg rotation.",
        "hr_aniso_push_08": "second anisotropic phase-push candidate testing larger length with safer 110 nm width.",
        "hr_phase_delay_03": "geometry-safe retry of h2_phase_delay_04 phase-delay logic with >=55 nm gaps.",
        "hr_lowleak_control_02": "low-leakage near-square control for comparing phase movement against h2_square/nearsquare prototypes.",
    }
    selected = []
    for rank, candidate_id in enumerate(SELECTED_REFINEMENT_IDS, start=1):
        if candidate_id not in valid:
            raise ValueError(f"selected helper refinement candidate failed validation: {candidate_id}")
        candidate = by_id[candidate_id]
        selected.append(
            {
                "selection_rank": rank,
                "candidate_id": candidate_id,
                "family": candidate["family"],
                "target_bin_deg": candidate["target_bin_deg"],
                "selection_reason": reasons[candidate_id],
                "risk_level": candidate["risk_level"],
                "expected_phase_direction": candidate["expected_phase_direction"],
                "geometry_pass": True,
                "recommended_for_fdtd": True,
                "requires_fdtd": candidate["requires_fdtd"],
                "status": "selected_for_run",
                "notes": "selected for 09-P45/P47 top-4 helper refinement FDTD; no full pool run",
            }
        )
    return selected


def write_helper_refinement_configs(candidate_rows: Sequence[dict[str, object]], config_dir: str | Path) -> list[Path]:
    output_dir = Path(config_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for candidate in candidate_rows:
        path = output_dir / f"{candidate['candidate_id']}.yaml"
        path.write_text(build_helper_refinement_config(candidate), encoding="utf-8")
        paths.append(path)
    return paths


def build_helper_refinement_config(candidate: dict[str, object]) -> str:
    data = {
        "project": {"name": "blue_plane_wave_metasurface", "stage": "09_p45_p47_helper_refinement_fdtd"},
        "candidate": {
            "variant_id": candidate["candidate_id"],
            "candidate_type": candidate["family"],
            "description": "physics-guided helper refinement candidate",
            "target_bin_deg": _number(candidate["target_bin_deg"]),
            "source_stage": "09-P45/P47",
            "anchor_candidate": candidate["anchor_candidate"],
            "helper_role": candidate["helper_role"],
            "helper_type": candidate["helper_type"],
            "helper_shape": candidate["p3_shape"],
            "risk_level": candidate["risk_level"],
            "design_rationale": candidate["design_rationale"],
            "source_pool_csv": "outputs/apcd_k6_active_learning/helper_refinement_candidate_pool_v8.csv",
            "notes": "helper refinement config; not a full pool run; not a steering result",
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
            "minimum_gap_nm": 55 if candidate["family"] == "phase_delay_gap_fixed" else 50,
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


def validate_helper_refinement_configs(config_paths: Sequence[str | Path]) -> list[dict[str, object]]:
    rows = []
    for path_like in config_paths:
        path = Path(path_like)
        config = load_apcd_single_dimer_config(path)
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        candidate_id = data["candidate"]["variant_id"]
        helper = config.geometry.nanopillar_helper
        passed = (
            candidate_id in SELECTED_REFINEMENT_IDS
            and helper is not None
            and helper.role == "weak_auxiliary_phase_helper"
            and data["boundary"]["not_phase_ramp_supercell"] is True
            and data["boundary"]["not_random_helper_shape"] is True
            and data["boundary"]["not_freeform_helper_shape"] is True
        )
        rows.append({"candidate_id": candidate_id, "config_path": str(path), "validation_pass": passed, "notes": "config-load validation only; no FDTD/lumapi/.fsp"})
    return rows


def run_helper_refinement_candidates(candidate_rows: Sequence[dict[str, object]], config_dir: Path, runtime: Path, python_executable: str, repo_root: Path) -> None:
    if len(candidate_rows) > 4:
        raise ValueError("helper refinement FDTD batch is limited to selected top-4")
    runner = repo_root / "scripts/13_run_apcd_single_dimer.py"
    for row in candidate_rows:
        candidate_id = str(row["candidate_id"])
        command = [python_executable, str(runner), "--config", str(config_dir / f"{candidate_id}.yaml"), "--runtime", str(runtime)]
        print(f"running_helper_refinement={candidate_id}")
        subprocess.run(command, cwd=repo_root, check=True)


def summarize_helper_refinement_results(candidate_rows: Sequence[dict[str, object]], repo_root: str | Path) -> list[dict[str, object]]:
    root = Path(repo_root)
    rows = []
    for candidate in candidate_rows:
        result_path = root / "outputs/apcd_k6_metagrating_633nm/phase_state_candidates" / str(candidate["candidate_id"]) / "results.csv"
        if not result_path.exists():
            rows.append(_not_run_result(candidate))
            continue
        raw = read_csv_rows(result_path)[0]
        rows.append(_result_row_from_raw(candidate, raw, result_path, root))
    return rows


def build_dataset_v8(dataset_v7_rows: Sequence[dict[str, str]], result_rows: Sequence[dict[str, object]], candidate_rows: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = list(dataset_v7_rows)
    fieldnames = list(rows[0].keys())
    candidate_by_id = {str(row["candidate_id"]): row for row in candidate_rows}
    existing = {str(row["variant_id"]) for row in rows}
    for result in result_rows:
        if result["run_status"] != "completed" or result["status"] != "ok" or result["candidate_id"] in existing:
            continue
        rows.append(_dataset_row_from_result(candidate_by_id[str(result["candidate_id"])], result, fieldnames))
    return rows


def write_pool_summary(path: str | Path, pool_rows: Sequence[dict[str, object]]) -> Path:
    families = {}
    for row in pool_rows:
        families[str(row["family"])] = families.get(str(row["family"]), 0) + 1
    lines = [
        "# APCD K=6 Helper Refinement Candidate Pool v8",
        "",
        f"Pool rows: {len(pool_rows)}",
        "",
        "Family distribution:",
        *[f"- `{family}`: {count}" for family, count in sorted(families.items())],
        "",
        "Scope: candidate pool only. No FDTD/lumapi/.fsp from pool generation. Helper remains a third standalone weak auxiliary phase shifter.",
    ]
    return _write_text(path, lines)


def write_validation_summary(path: str | Path, validation_rows: Sequence[dict[str, object]]) -> Path:
    pass_count = sum(str(row["overall_geometry_pass"]) == "True" for row in validation_rows)
    lines = [
        "# APCD K=6 Helper Refinement Geometry Validation v8",
        "",
        f"Geometry pass: {pass_count}/{len(validation_rows)}",
        "",
        "| candidate | family | same gap | periodic gap | threshold | pass |",
        "|---|---|---:|---:|---:|---|",
        *[
            f"| `{row['candidate_id']}` | `{row['family']}` | {row['same_cell_min_gap_nm']} | {row['periodic_image_min_gap_nm']} | {row['minimum_gap_nm_threshold']} | {row['overall_geometry_pass']} |"
            for row in validation_rows
        ],
    ]
    return _write_text(path, lines)


def write_result_summary(path: str | Path, result_rows: Sequence[dict[str, object]], dataset_rows: Sequence[dict[str, object]], coverage_rows: Sequence[dict[str, object]]) -> Path:
    lines = [
        "# APCD K=6 Helper Refinement FDTD Results v8 Summary",
        "",
        f"Dataset v8 rows: {len(dataset_rows)}",
        "",
        "| candidate | family | target | phase | leakage | ratio | early pass | target status |",
        "|---|---|---:|---:|---:|---:|---|---|",
        *[
            f"| `{row['candidate_id']}` | `{row['family']}` | {row['target_bin_deg']} | {row['phase_deg']} | {row['opposite_spin_leakage']} | {row['conversion_to_leakage_ratio']} | {row['early_pass']} | {row['target_bin_status']} |"
            for row in result_rows
        ],
        "",
        "Coverage v8:",
        "",
        "| bin deg | status |",
        "|---:|---|",
        *[f"| {row['phase_bin_deg']} | {row['coverage_status']} |" for row in coverage_rows],
        "",
        "No complete K=6 library or +15 deg steering claim.",
    ]
    return _write_text(path, lines)


def write_gap_analysis(path: str | Path, coverage_rows: Sequence[dict[str, object]], result_rows: Sequence[dict[str, object]]) -> Path:
    lines = [
        "# APCD K=6 Phase Gap Analysis v8",
        "",
        "Scope: helper refinement v8 update. Only selected top-4 FDTD results were added.",
        "",
        "| bin deg | status | nearest early-pass | early error | nearest evidence-only | evidence error |",
        "|---:|---|---|---:|---|---:|",
        *[
            f"| {row['phase_bin_deg']} | {row['coverage_status']} | {row['nearest_candidate_early_pass']} | {row['nearest_error_early_pass']} | {row['nearest_candidate_evidence_only']} | {row['nearest_error_evidence_only']} |"
            for row in coverage_rows
        ],
        "",
        "Refinement results:",
        *[
            f"- `{row['candidate_id']}`: phase={row['phase_deg']}, leakage={row['opposite_spin_leakage']}, ratio={row['conversion_to_leakage_ratio']}, early_pass={row['early_pass']}, status={row['target_bin_status']}"
            for row in result_rows
        ],
    ]
    return _write_text(path, lines)


def write_readiness(path: str | Path, coverage_rows: Sequence[dict[str, object]]) -> Path:
    open_rows = [row for row in coverage_rows if row["coverage_status"] not in {"strong_covered", "early_covered"}]
    lines = [
        "# APCD K=6 Phase-State Readiness v8",
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
    validation_rows: Sequence[dict[str, object]],
    selected_rows: Sequence[dict[str, object]],
    result_rows: Sequence[dict[str, object]],
    dataset_rows: Sequence[dict[str, object]],
    coverage_rows: Sequence[dict[str, object]],
) -> Path:
    pass_count = sum(str(row["overall_geometry_pass"]) == "True" for row in validation_rows)
    best = _best_phase_push(result_rows)
    lines = [
        "# APCD K=6 Helper Refinement FDTD v8 Note",
        "",
        "## Scope",
        "",
        "This is 09-P45/P47. It refines physics-guided standalone helper prototypes toward high-positive / pi-near phase while preserving low leakage.",
        "",
        "No full helper v2 pool, full helper refinement pool, old pool, K=7, phase-ramp supercell, TiO2/450 nm, Micro-LED integration, ML/DenseNet/cVAE training, random/freeform helper, +15 deg steering claim, or complete K=6 phase-state library claim was made.",
        "",
        "## Starting Point",
        "",
        "- Square/near-square helpers stayed low leakage but near 116-121 deg.",
        "- `h2_weak_aniso_03` is the best current helper anchor: phase 128.6755 deg with low leakage.",
        "- `h2_phase_delay_04` failed geometry only, so phase-delay was retried with safer reduced-size/gap-fixed helpers.",
        "",
        "## Geometry and Selection",
        "",
        f"Geometry pass: {pass_count}/{len(validation_rows)}",
        "",
        "| rank | candidate | family | target | reason |",
        "|---:|---|---|---:|---|",
        *[
            f"| {row['selection_rank']} | `{row['candidate_id']}` | `{row['family']}` | {row['target_bin_deg']} | {row['selection_reason']} |"
            for row in selected_rows
        ],
        "",
        "## FDTD Results",
        "",
        "| candidate | family | target | phase | leakage | ratio | early pass | status |",
        "|---|---|---:|---:|---:|---:|---|---|",
        *[
            f"| `{row['candidate_id']}` | `{row['family']}` | {row['target_bin_deg']} | {row['phase_deg']} | {row['opposite_spin_leakage']} | {row['conversion_to_leakage_ratio']} | {row['early_pass']} | {row['target_bin_status']} |"
            for row in result_rows
        ],
        "",
        f"Most promising helper type: {best}",
        "",
        "Interpretation: v8 opened a modest high-positive usable extension beyond `h2_weak_aniso_03` (128.6755 deg) to about 131.665 deg, while keeping leakage low. It did not reach the 150-180 deg / pi-near region and does not cover -180 deg.",
        "",
        "## Coverage v8",
        "",
        f"Dataset v8 rows: {len(dataset_rows)}",
        "",
        "| bin deg | status |",
        "|---:|---|",
        *[f"| {row['phase_bin_deg']} | {row['coverage_status']} |" for row in coverage_rows],
        "",
        "Open or incomplete targets remain 0 deg, -60 deg, -120 deg, and possibly -180 deg unless v8 produces an early-pass wrapped phase within threshold.",
    ]
    return _write_text(path, lines)


def helper_refinement_gaps(candidate: dict[str, object]) -> tuple[float, float]:
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


def phase_deg_from_complex(value: str) -> float:
    return wrap_phase_deg(math.degrees(cmath.phase(complex(value))))


def _candidate_row(
    candidate_id: str,
    family: str,
    target: float,
    anchor: str,
    helper_l: float,
    helper_w: float,
    helper_rot: float,
    helper_fx: float,
    helper_fy: float,
    direction: str,
    risk: str,
) -> dict[str, object]:
    period = 340.0
    helper_type = {
        "aniso_helper_phase_push": "weak rectangular nanofin helper",
        "phase_delay_gap_fixed": "moderate rectangular phase-delay nanofin helper",
        "lowleak_anchor_control": "near-square loading helper",
    }[family]
    return {
        "candidate_id": candidate_id,
        "family": family,
        "target_bin_deg": target,
        "anchor_candidate": anchor,
        "helper_role": "weak_auxiliary_phase_helper",
        "helper_type": helper_type,
        "p3_shape": helper_type,
        "p3_length_nm": helper_l,
        "p3_width_nm": helper_w,
        "p3_rotation_deg": helper_rot,
        "p3_frac_x": helper_fx,
        "p3_frac_y": helper_fy,
        "p3_x_nm": (helper_fx - 0.5) * period,
        "p3_y_nm": (helper_fy - 0.5) * period,
        "expected_phase_direction": direction,
        "design_rationale": "APCD alpha-pass core remains fixed; standalone dielectric helper probes controlled phase pulling toward high-positive/pi-near phase.",
        "risk_level": risk,
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
        "notes": "helper refinement planning; standalone helper, not another APCD dimer; fabrication-friendly rectangular/square pillar only",
    }


def _result_row_from_raw(candidate: dict[str, object], raw: dict[str, str], result_path: Path, repo_root: Path) -> dict[str, object]:
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
        "notes": f"09-P45/P47 helper refinement real FDTD; target_bin_status={target_status}; not a steering result",
    }


def _not_run_result(candidate: dict[str, object]) -> dict[str, object]:
    return {
        "candidate_id": candidate["candidate_id"],
        "family": candidate["family"],
        "helper_role": candidate["helper_role"],
        "target_bin_deg": candidate["target_bin_deg"],
        "run_status": "not_run_missing_result",
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
        "notes": "selected candidate result file missing; no result fabricated",
    }


def _dataset_row_from_result(candidate: dict[str, object], result: dict[str, object], fieldnames: Sequence[str]) -> dict[str, object]:
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
            "notes": "09-P45/P47 real FDTD helper refinement; helper p3 geometry is in v8 pool; raw results not committed; not a steering result",
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


def _helper_core_gap(candidate: dict[str, object]) -> float:
    p1, p2, helper = _polygons(candidate)
    return min(polygon_min_distance_nm(helper, p1), polygon_min_distance_nm(helper, p2))


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


def _bounds_pass(candidate: dict[str, object]) -> bool:
    return (
        float(candidate["p1_length_nm"]) == 130.0
        and float(candidate["p1_width_nm"]) == 70.0
        and float(candidate["p1_rotation_deg"]) == 67.5
        and float(candidate["p2_length_nm"]) == 85.0
        and float(candidate["p2_width_nm"]) == 150.0
        and float(candidate["p2_rotation_deg"]) == 112.5
        and 50.0 <= float(candidate["p3_length_nm"]) <= 130.0
        and 60.0 <= float(candidate["p3_width_nm"]) <= 130.0
        and 0.0 <= float(candidate["p3_rotation_deg"]) <= 180.0
        and float(candidate["p3_frac_x"]) == 0.25
        and float(candidate["p3_frac_y"]) == 0.75
        and float(candidate["period_x_nm"]) == 340.0
        and float(candidate["period_y_nm"]) == 340.0
        and float(candidate["height_nm"]) == 300.0
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
    ]
    return tuple(float(candidate[key]) for key in keys)


def _best_phase_push(result_rows: Sequence[dict[str, object]]) -> str:
    completed = [row for row in result_rows if row["run_status"] == "completed" and str(row["early_pass"]) == "True"]
    if not completed:
        return "none; no early-pass refinement candidate"
    best = max(completed, key=lambda row: float(row["phase_deg"]))
    return f"{best['candidate_id']} ({best['family']}), phase={best['phase_deg']} deg, leakage={best['opposite_spin_leakage']}"


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
