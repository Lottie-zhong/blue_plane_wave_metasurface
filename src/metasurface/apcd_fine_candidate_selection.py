from __future__ import annotations

import csv
import cmath
import math
from collections import Counter
from pathlib import Path
from typing import Iterable, Sequence


FINE_SELECTION_FIELDS = [
    "selection_rank",
    "candidate_id",
    "candidate_family",
    "selection_reason",
    "expected_risk",
    "intended_phase_region",
    "will_run_now",
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

FINE_RESULT_FIELDS = [
    "candidate_id",
    "candidate_family",
    "status",
    "target_conversion",
    "opposite_spin_leakage",
    "conversion_to_leakage_ratio",
    "PD",
    "total_transmission",
    "t_alpha_star_from_alpha",
    "phase_deg",
    "phase_shift_vs_baseline_deg",
    "early_target_pass",
    "early_leakage_pass",
    "early_ratio_pass",
    "overall_early_pass",
    "inside_90_100_deg_region",
    "phase_below_doe_p1w_dx_01",
    "priority",
    "notes",
]

SELECTED_IDS = [
    "fine_p1w_dx_08",
    "fine_p1w_dx_03",
    "fine_p1w_dx_p2w_trim_02",
]

RUN_TOP_N = 2
BASELINE_PHASE_DEG = 111.31665091018952
DOE_P1W_DX_01_PHASE_DEG = 100.8199

SELECTION_REASONS = {
    "fine_p1w_dx_08": "Conservative balance point: p1_width=57 nm with internal_dx=-34 nm, using stronger dx offset to protect leakage while narrowing p1.",
    "fine_p1w_dx_03": "Lower-phase risk point: p1_width=56 nm with internal_dx=-33 nm, testing phase reduction without going to the known 55/-30 high-leakage boundary.",
    "fine_p1w_dx_p2w_trim_02": "Backup p2W trim point: p1_width=57 nm and internal_dx=-33 nm with a small p2_width trim to test later leakage recovery.",
}

RESULT_PRIORITY = {
    "fine_p1w_dx_08": "top2_conservative_balance",
    "fine_p1w_dx_03": "top2_lower_phase_risk",
    "fine_p1w_dx_p2w_trim_02": "backup_not_run",
}


def load_fine_candidate_pool(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def load_fine_geometry_validation(path: str | Path) -> dict[str, dict[str, str]]:
    with Path(path).open("r", newline="", encoding="utf-8") as handle:
        return {row["candidate_id"]: row for row in csv.DictReader(handle)}


def filter_recommended_fine_candidates(
    candidates: Iterable[dict[str, str]],
    validation_by_id: dict[str, dict[str, str]],
) -> list[dict[str, str]]:
    rows = []
    for candidate in candidates:
        validation = validation_by_id.get(candidate["candidate_id"], {})
        if validation.get("overall_geometry_pass") == "True" and validation.get("recommended_for_fdtd") == "True":
            rows.append(
                {
                    **candidate,
                    "geometry_pass": validation.get("overall_geometry_pass", ""),
                    "recommended_for_fdtd": validation.get("recommended_for_fdtd", ""),
                }
            )
    return rows


def select_fine_fdtd_candidates(
    candidates: Iterable[dict[str, str]],
    validation_by_id: dict[str, dict[str, str]],
    *,
    selected_ids: Sequence[str] = SELECTED_IDS,
    run_top_n: int = RUN_TOP_N,
) -> list[dict[str, object]]:
    if not 2 <= len(selected_ids) <= 3:
        raise ValueError("selected_ids should contain 2-3 candidates")
    if run_top_n != 2:
        raise ValueError("09-P12 should only run the top 2 candidates")
    eligible = filter_recommended_fine_candidates(candidates, validation_by_id)
    by_id = {row["candidate_id"]: row for row in eligible}
    missing = [candidate_id for candidate_id in selected_ids if candidate_id not in by_id]
    if missing:
        raise ValueError(f"selected candidates are not geometry-pass/recommended: {missing}")
    selected = [
        _selection_row(rank, by_id[candidate_id], will_run_now=rank <= run_top_n)
        for rank, candidate_id in enumerate(selected_ids, start=1)
    ]
    _validate_selection_policy(selected)
    return selected


def export_fine_fdtd_selection_csv(rows: Iterable[dict[str, object]], path: str | Path) -> Path:
    row_list = list(rows)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FINE_SELECTION_FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FINE_SELECTION_FIELDS} for row in row_list)
    return output_path


def summarize_fine_fdtd_selection(rows: Sequence[dict[str, object]]) -> dict[str, object]:
    families = Counter(str(row["candidate_family"]) for row in rows)
    run_ids = [str(row["candidate_id"]) for row in rows if row["will_run_now"] is True]
    backup_ids = [str(row["candidate_id"]) for row in rows if row["will_run_now"] is False]
    return {
        "selected_count": len(rows),
        "run_now_count": len(run_ids),
        "selected_candidate_ids": [str(row["candidate_id"]) for row in rows],
        "run_now_candidate_ids": run_ids,
        "backup_candidate_ids": backup_ids,
        "family_counts": dict(sorted(families.items())),
        "unique_candidate_ids": len({str(row["candidate_id"]) for row in rows}) == len(rows),
        "status_values": sorted({str(row["status"]) for row in rows}),
        "selection_reasons": {str(row["candidate_id"]): str(row["selection_reason"]) for row in rows},
    }


def write_fine_fdtd_selection_summary(path: str | Path, rows: Sequence[dict[str, object]]) -> Path:
    summary = summarize_fine_fdtd_selection(rows)
    family_lines = [f"- `{family}`: {count}" for family, count in summary["family_counts"].items()]
    reason_lines = [
        f"- `{candidate_id}`: {reason}" for candidate_id, reason in summary["selection_reasons"].items()
    ]
    lines = [
        "# APCD K=6 p1w_dx Fine FDTD Selection v1 Summary",
        "",
        "Scope: 09-P12 selection output. Only top-2 are marked to run now. No surrogate prediction is included.",
        "",
        f"Selected count: {summary['selected_count']}",
        f"Run-now count: {summary['run_now_count']}",
        f"Run-now candidate IDs: {', '.join(summary['run_now_candidate_ids'])}",
        f"Backup candidate IDs: {', '.join(summary['backup_candidate_ids'])}",
        f"Unique candidate IDs: {summary['unique_candidate_ids']}",
        f"Status values: {', '.join(summary['status_values'])}",
        "",
        "Family distribution:",
        "",
        *family_lines,
        "",
        "Selection reasons:",
        "",
        *reason_lines,
    ]
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def build_candidate_config(candidate: dict[str, object]) -> str:
    candidate_id = str(candidate["candidate_id"])
    internal_dx = float(candidate["internal_dx_nm"])
    internal_dy = float(candidate["internal_dy_nm"])
    p1_x = (float(candidate.get("p1_frac_x", 0.75)) - 0.5) * float(candidate.get("period_x_nm", 340)) + internal_dx / 2.0
    p1_y = (float(candidate.get("p1_frac_y", 0.75)) - 0.5) * float(candidate.get("period_y_nm", 340)) + internal_dy / 2.0
    p2_x = (float(candidate.get("p2_frac_x", 0.25)) - 0.5) * float(candidate.get("period_x_nm", 340)) - internal_dx / 2.0
    p2_y = (float(candidate.get("p2_frac_y", 0.25)) - 0.5) * float(candidate.get("period_y_nm", 340)) - internal_dy / 2.0
    return f"""project:
  name: blue_plane_wave_metasurface
  stage: 09_p12_apcd_k6_p1w_dx_fine_real_eval
candidate:
  variant_id: {candidate_id}
  candidate_type: {candidate['candidate_family']}
  description: p1w_dx fine leakage-controlled perturbation
  source_pool_csv: outputs/apcd_k6_active_learning/p1w_dx_fine_candidate_pool_v1.csv
  source_selection_csv: outputs/apcd_k6_active_learning/p1w_dx_fine_fdtd_selection_v1.csv
  notes: 09-P12 generated config from fine candidate selection; no setup-only export in config generation step
boundary:
  no_k7: true
  not_phase_ramp_supercell: true
  not_steering_result: true
target:
  wavelength_nm: 633
  incident_wave: plane_wave
  output_basis: alpha_beta
  target_polarization_type: elliptical
  psi_deg: 112.5
  chi_deg: 22.5
  eps: 1.0e-12
  spin_er_threshold_db: 8
  conversion_to_leakage_threshold: 6
material:
  substrate: Al2O3
  meta_material: c-Si
  substrate_material_lumerical: <Object defined dielectric>
  meta_material_lumerical: <Object defined dielectric>
  substrate_index: 1.76
  meta_index: 3.88
geometry:
  layout_mode: manual_absolute
  period_x_nm: 340
  period_y_nm: 340
  height_nm: 300
  minimum_gap_nm: 5
  nanopillar_1:
    length_nm: {_number(candidate['p1_length_nm'])}
    width_nm: {_number(candidate['p1_width_nm'])}
    rotation_deg: 67.5
    x_nm: {_format_float(p1_x)}
    y_nm: {_format_float(p1_y)}
    frac_x: 0.75
    frac_y: 0.75
  nanopillar_2:
    length_nm: {_number(candidate['p2_length_nm'])}
    width_nm: {_number(candidate['p2_width_nm'])}
    rotation_deg: 112.5
    x_nm: {_format_float(p2_x)}
    y_nm: {_format_float(p2_y)}
    frac_x: 0.25
    frac_y: 0.25
simulation:
  substrate_thickness_nm: 220
  source_offset_nm: 120
  monitor_offset_nm: 180
  z_padding_above_nm: 260
  mesh_accuracy: 1
  simulation_time_fs: 250
output:
  result_dir: outputs/apcd_k6_metagrating_633nm/phase_state_candidates/{candidate_id}
"""


def export_candidate_configs(rows: Iterable[dict[str, object]], config_dir: str | Path) -> list[Path]:
    output_dir = Path(config_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for row in rows:
        if row["will_run_now"] is not True:
            continue
        path = output_dir / f"{row['candidate_id']}.yaml"
        path.write_text(build_candidate_config(row), encoding="utf-8")
        written.append(path)
    return written


def result_row_from_csv(
    candidate_id: str,
    candidate_family: str,
    result_csv: str | Path,
) -> dict[str, object]:
    with Path(result_csv).open("r", newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))
    target = float(row["target_conversion"])
    leakage = float(row["opposite_spin_leakage"])
    ratio = float(row["conversion_to_leakage_ratio"])
    t_alpha = complex(row["t_alpha_star_from_alpha"])
    phase = math.degrees(cmath.phase(t_alpha))
    phase_shift = _wrap_phase_deg(phase - BASELINE_PHASE_DEG)
    early_target_pass = target >= 0.5
    early_leakage_pass = leakage <= 0.2
    early_ratio_pass = ratio >= 6.0
    overall = early_target_pass and early_leakage_pass and early_ratio_pass
    inside_region = 90.0 <= phase <= 100.0
    below_reference = phase < DOE_P1W_DX_01_PHASE_DEG
    usable = overall and inside_region
    return {
        "candidate_id": candidate_id,
        "candidate_family": candidate_family,
        "status": row["status"],
        "target_conversion": target,
        "opposite_spin_leakage": leakage,
        "conversion_to_leakage_ratio": ratio,
        "PD": float(row["PD"]),
        "total_transmission": float(row["total_transmission"]),
        "t_alpha_star_from_alpha": row["t_alpha_star_from_alpha"],
        "phase_deg": phase,
        "phase_shift_vs_baseline_deg": phase_shift,
        "early_target_pass": early_target_pass,
        "early_leakage_pass": early_leakage_pass,
        "early_ratio_pass": early_ratio_pass,
        "overall_early_pass": overall,
        "inside_90_100_deg_region": inside_region,
        "phase_below_doe_p1w_dx_01": below_reference,
        "priority": "usable_phase_candidate" if usable else RESULT_PRIORITY.get(candidate_id, "record_only"),
        "notes": _result_notes(candidate_id, usable, inside_region, overall, leakage, ratio),
    }


def explicit_result_row(
    *,
    candidate_id: str,
    candidate_family: str,
    status: str,
    target_conversion: float,
    opposite_spin_leakage: float,
    conversion_to_leakage_ratio: float,
    pd: float,
    total_transmission: float,
    t_alpha_star_from_alpha: str,
) -> dict[str, object]:
    row = {
        "status": status,
        "target_conversion": str(target_conversion),
        "opposite_spin_leakage": str(opposite_spin_leakage),
        "conversion_to_leakage_ratio": str(conversion_to_leakage_ratio),
        "PD": str(pd),
        "total_transmission": str(total_transmission),
        "t_alpha_star_from_alpha": t_alpha_star_from_alpha,
    }
    temp_path = None
    target = float(row["target_conversion"])
    leakage = float(row["opposite_spin_leakage"])
    ratio = float(row["conversion_to_leakage_ratio"])
    t_alpha = complex(row["t_alpha_star_from_alpha"])
    phase = math.degrees(cmath.phase(t_alpha))
    phase_shift = _wrap_phase_deg(phase - BASELINE_PHASE_DEG)
    early_target_pass = target >= 0.5
    early_leakage_pass = leakage <= 0.2
    early_ratio_pass = ratio >= 6.0
    overall = early_target_pass and early_leakage_pass and early_ratio_pass
    inside_region = 90.0 <= phase <= 100.0
    below_reference = phase < DOE_P1W_DX_01_PHASE_DEG
    usable = overall and inside_region
    return {
        "candidate_id": candidate_id,
        "candidate_family": candidate_family,
        "status": status,
        "target_conversion": target,
        "opposite_spin_leakage": leakage,
        "conversion_to_leakage_ratio": ratio,
        "PD": float(pd),
        "total_transmission": float(total_transmission),
        "t_alpha_star_from_alpha": t_alpha_star_from_alpha,
        "phase_deg": phase,
        "phase_shift_vs_baseline_deg": phase_shift,
        "early_target_pass": early_target_pass,
        "early_leakage_pass": early_leakage_pass,
        "early_ratio_pass": early_ratio_pass,
        "overall_early_pass": overall,
        "inside_90_100_deg_region": inside_region,
        "phase_below_doe_p1w_dx_01": below_reference,
        "priority": "usable_phase_candidate" if usable else RESULT_PRIORITY.get(candidate_id, "record_only"),
        "notes": _result_notes(candidate_id, usable, inside_region, overall, leakage, ratio),
    }


def export_fine_result_csv(rows: Iterable[dict[str, object]], path: str | Path) -> Path:
    row_list = list(rows)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FINE_RESULT_FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FINE_RESULT_FIELDS} for row in row_list)
    return output_path


def _selection_row(rank: int, candidate: dict[str, str], *, will_run_now: bool) -> dict[str, object]:
    candidate_id = candidate["candidate_id"]
    return {
        "selection_rank": rank,
        "candidate_id": candidate_id,
        "candidate_family": candidate["candidate_family"],
        "selection_reason": SELECTION_REASONS[candidate_id],
        "expected_risk": candidate["expected_risk"],
        "intended_phase_region": candidate["intended_phase_region"],
        "will_run_now": will_run_now,
        "p1_length_nm": _number(candidate["p1_length_nm"]),
        "p1_width_nm": _number(candidate["p1_width_nm"]),
        "p2_length_nm": _number(candidate["p2_length_nm"]),
        "p2_width_nm": _number(candidate["p2_width_nm"]),
        "internal_dx_nm": _number(candidate["internal_dx_nm"]),
        "internal_dy_nm": _number(candidate["internal_dy_nm"]),
        "p1_rotation_deg": _number(candidate["p1_rotation_deg"]),
        "p2_rotation_deg": _number(candidate["p2_rotation_deg"]),
        "geometry_pass": candidate["geometry_pass"],
        "recommended_for_fdtd": candidate["recommended_for_fdtd"],
        "requires_fdtd": candidate["requires_fdtd"],
        "status": "selected_for_run" if will_run_now else "selected_backup_not_run",
        "notes": "09-P12 selection only; no surrogate prediction; top-2 only are run now.",
    }


def _validate_selection_policy(rows: Sequence[dict[str, object]]) -> None:
    if not 2 <= len(rows) <= 3:
        raise ValueError("selected count must be 2-3")
    ids = [str(row["candidate_id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate selected candidate_id")
    families = Counter(str(row["candidate_family"]) for row in rows)
    if families.get("p1w_dx_fine_leakage_control", 0) < 2:
        raise ValueError("selection must include at least two p1w_dx_fine_leakage_control candidates")
    if families.get("p1w_dx_p2w_leakage_trim", 0) > 1:
        raise ValueError("selection can include at most one p1w_dx_p2w_leakage_trim candidate")
    if sum(1 for row in rows if row["will_run_now"] is True) != 2:
        raise ValueError("exactly top-2 rows should be marked will_run_now")
    if any(str(row["geometry_pass"]) != "True" or str(row["recommended_for_fdtd"]) != "True" for row in rows):
        raise ValueError("all selected rows must be geometry-pass/recommended")


def _wrap_phase_deg(value: float) -> float:
    return ((value + 180.0) % 360.0) - 180.0


def _result_notes(candidate_id: str, usable: bool, inside_region: bool, early_pass: bool, leakage: float, ratio: float) -> str:
    if usable:
        return "09-P12 real FDTD row; usable 90-100 deg early-pass phase candidate."
    details = []
    if not inside_region:
        details.append("outside 90-100 deg region")
    if not early_pass:
        if leakage > 0.2:
            details.append("leakage exceeds 0.2")
        if ratio < 6.0:
            details.append("ratio below 6")
    return f"09-P12 real FDTD row; {'; '.join(details) if details else 'recorded but not prioritized'}."


def _number(value: object) -> int | float:
    number = float(value)
    return int(number) if number.is_integer() else number


def _format_float(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.6g}"
