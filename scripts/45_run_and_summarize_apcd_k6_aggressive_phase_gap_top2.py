from __future__ import annotations

import argparse
import cmath
import csv
import math
import sys
from pathlib import Path
from typing import Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_active_learning import wrap_phase_deg  # noqa: E402


BASELINE_PHASE_DEG = 111.31665091018952
TOP2_IDS = ["aggr_lhs_retention_dy_05", "aggr_p1w_leakctrl_04"]
DEFAULT_SELECTION_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/aggressive_phase_gap_fdtd_selection_v1.csv"
DEFAULT_CONFIG_DIR = REPO_ROOT / "configs/apcd_k6_phase_state_candidates"
DEFAULT_RESULT_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/aggressive_phase_gap_top2_fdtd_results_v1.csv"

AGGRESSIVE_PHASE_GAP_RESULT_FIELDS = [
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
    "inside_60_90_deg_region",
    "near_60_deg_bin",
    "near_90_100_deg_region",
    "priority",
    "notes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare and summarize APCD K=6 aggressive phase-gap top-2 FDTD rows.")
    parser.add_argument("--write-configs", action="store_true", help="Write config YAML for aggressive top-2 only.")
    parser.add_argument("--selection-csv", type=Path, default=DEFAULT_SELECTION_CSV)
    parser.add_argument("--config-dir", type=Path, default=DEFAULT_CONFIG_DIR)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_RESULT_CSV)
    return parser.parse_args()


def load_selection_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def top2_selection_rows(rows: Iterable[dict[str, str]], top2_ids: Sequence[str] = TOP2_IDS) -> list[dict[str, str]]:
    by_id = {row["candidate_id"]: row for row in rows}
    missing = [candidate_id for candidate_id in top2_ids if candidate_id not in by_id]
    if missing:
        raise ValueError(f"missing aggressive top-2 candidate rows: {missing}")
    selected = [by_id[candidate_id] for candidate_id in top2_ids]
    for row in selected:
        if row["geometry_pass"] != "True" or row["recommended_for_fdtd"] != "True":
            raise ValueError(f"{row['candidate_id']} is not geometry-pass/recommended")
    return selected


def build_aggressive_phase_gap_candidate_config(candidate: dict[str, str]) -> str:
    candidate_id = candidate["candidate_id"]
    internal_dx = float(candidate["internal_dx_nm"])
    internal_dy = float(candidate["internal_dy_nm"])
    period_x = 340.0
    period_y = 340.0
    p1_x = (0.75 - 0.5) * period_x + internal_dx / 2.0
    p1_y = (0.75 - 0.5) * period_y + internal_dy / 2.0
    p2_x = (0.25 - 0.5) * period_x - internal_dx / 2.0
    p2_y = (0.25 - 0.5) * period_y - internal_dy / 2.0
    return f"""project:
  name: blue_plane_wave_metasurface
  stage: 09_p18_apcd_k6_aggressive_phase_gap_top2_real_eval
candidate:
  variant_id: {candidate_id}
  candidate_type: {candidate['candidate_family']}
  description: aggressive phase-gap 60-90 deg selected candidate
  source_pool_csv: outputs/apcd_k6_active_learning/aggressive_phase_gap_candidate_pool_v1.csv
  source_selection_csv: outputs/apcd_k6_active_learning/aggressive_phase_gap_fdtd_selection_v1.csv
  notes: 09-P18 generated config for aggressive top-2 only; no config generated for aggr_bridge_lhs_fine_05
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


def write_top2_configs(selection_rows: Sequence[dict[str, str]], config_dir: str | Path) -> list[Path]:
    output_dir = Path(config_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for row in top2_selection_rows(selection_rows):
        path = output_dir / f"{row['candidate_id']}.yaml"
        path.write_text(build_aggressive_phase_gap_candidate_config(row), encoding="utf-8")
        written.append(path)
    return written


def result_row_from_values(
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
    t_alpha = complex(t_alpha_star_from_alpha)
    phase = wrap_phase_deg(math.degrees(cmath.phase(t_alpha)))
    shift = wrap_phase_deg(phase - BASELINE_PHASE_DEG)
    early_target = float(target_conversion) >= 0.5
    early_leakage = float(opposite_spin_leakage) <= 0.2
    early_ratio = float(conversion_to_leakage_ratio) >= 6.0
    overall = early_target and early_leakage and early_ratio
    inside_60_90 = 60.0 <= phase <= 90.0
    near_60 = abs(wrap_phase_deg(phase - 60.0)) <= 15.0
    near_90_100 = 90.0 <= phase <= 100.0
    usable = overall and inside_60_90
    return {
        "candidate_id": candidate_id,
        "candidate_family": candidate_family,
        "status": status,
        "target_conversion": target_conversion,
        "opposite_spin_leakage": opposite_spin_leakage,
        "conversion_to_leakage_ratio": conversion_to_leakage_ratio,
        "PD": pd,
        "total_transmission": total_transmission,
        "t_alpha_star_from_alpha": t_alpha_star_from_alpha,
        "phase_deg": phase,
        "phase_shift_vs_baseline_deg": shift,
        "early_target_pass": early_target,
        "early_leakage_pass": early_leakage,
        "early_ratio_pass": early_ratio,
        "overall_early_pass": overall,
        "inside_60_90_deg_region": inside_60_90,
        "near_60_deg_bin": near_60,
        "near_90_100_deg_region": near_90_100,
        "priority": "usable_60_90_phase_candidate" if usable else _priority(overall, inside_60_90, near_60),
        "notes": _notes(overall, inside_60_90, near_60),
    }


def write_aggressive_phase_gap_result_csv(rows: Iterable[dict[str, object]], path: str | Path) -> Path:
    row_list = list(rows)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=AGGRESSIVE_PHASE_GAP_RESULT_FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in AGGRESSIVE_PHASE_GAP_RESULT_FIELDS} for row in row_list)
    return output_path


def main() -> int:
    args = parse_args()
    selection_rows = load_selection_rows(args.selection_csv)
    if args.write_configs:
        written = write_top2_configs(selection_rows, args.config_dir)
        print(f"configs_written={','.join(str(path) for path in written)}")
        print("status=config_generation_only_no_fdtd_no_lumapi_no_fsp_no_training_not_steering_result")
        return 0
    print("No action requested. Use --write-configs for top-2 config generation.")
    return 0


def _priority(overall: bool, inside_60_90: bool, near_60: bool) -> str:
    if overall and not inside_60_90:
        return "early_pass_outside_60_90"
    if not overall and near_60:
        return "phase_evidence_high_leakage_or_low_ratio"
    return "record_not_usable"


def _notes(overall: bool, inside_60_90: bool, near_60: bool) -> str:
    parts = ["09-P18 real FDTD row; aggressive top-2 only"]
    parts.append("inside 60-90 deg" if inside_60_90 else "outside 60-90 deg")
    parts.append("early pass" if overall else "not early pass")
    if near_60:
        parts.append("near 60 deg bin")
    parts.append("not a steering result")
    return "; ".join(parts) + "."


def _number(value: object) -> int | float:
    number = float(value)
    return int(number) if number.is_integer() else number


def _format_float(value: float) -> str:
    return str(int(value)) if float(value).is_integer() else f"{value:.6g}"


if __name__ == "__main__":
    raise SystemExit(main())
