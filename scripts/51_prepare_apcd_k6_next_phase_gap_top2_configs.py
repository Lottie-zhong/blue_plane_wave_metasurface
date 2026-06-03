from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Iterable, Sequence

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.config import load_apcd_single_dimer_config  # noqa: E402


TOP2_IDS = ["next_zero_rot_anchor_03", "next_rot_anchor_04"]
SKIPPED_SELECTED_IDS = ["next_mixed_bridge_03", "next_pi_mixed_bridge_03"]
DEFAULT_SELECTION_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/next_phase_gap_fdtd_selection_v2.csv"
DEFAULT_POOL_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/next_phase_gap_candidate_pool_v2.csv"
DEFAULT_CONFIG_DIR = REPO_ROOT / "configs/apcd_k6_phase_state_candidates"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare APCD K=6 next phase-gap top-2 YAML configs.")
    parser.add_argument("--selection-csv", type=Path, default=DEFAULT_SELECTION_CSV)
    parser.add_argument("--pool-csv", type=Path, default=DEFAULT_POOL_CSV)
    parser.add_argument("--config-dir", type=Path, default=DEFAULT_CONFIG_DIR)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate generated YAML configs locally. This does not run FDTD or call lumapi.",
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only validate existing top-2 YAML configs; do not write files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selection_rows = read_csv_rows(args.selection_csv)
    pool_rows = read_csv_rows(args.pool_csv)
    top2_rows = top2_candidate_rows(selection_rows, pool_rows)

    if args.check_only:
        config_paths = [args.config_dir / f"{row['candidate_id']}.yaml" for row in top2_rows]
    else:
        config_paths = write_top2_configs(top2_rows, args.config_dir)

    validation_rows = validate_top2_configs(config_paths, top2_rows) if args.dry_run or args.check_only else []
    print(f"top2_candidate_ids={[row['candidate_id'] for row in top2_rows]}")
    print(f"configs={','.join(str(path) for path in config_paths)}")
    print(f"skipped_selected_candidate_ids={SKIPPED_SELECTED_IDS}")
    if validation_rows:
        print(f"dry_run_validation_pass={all(row['validation_pass'] for row in validation_rows)}")
    print("status=config_prepare_and_local_dry_run_only_no_fdtd_no_lumapi_no_fsp_no_results_no_training_not_steering_result")
    return 0


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def top2_candidate_rows(
    selection_rows: Iterable[dict[str, str]],
    pool_rows: Iterable[dict[str, str]],
    top2_ids: Sequence[str] = TOP2_IDS,
) -> list[dict[str, str]]:
    selected_by_rank = sorted(selection_rows, key=lambda row: int(row["selection_rank"]))
    actual_top2 = [row["candidate_id"] for row in selected_by_rank[:2]]
    if actual_top2 != list(top2_ids):
        raise ValueError(f"unexpected top-2 selection: {actual_top2}")
    skipped = [row["candidate_id"] for row in selected_by_rank[2:]]
    if skipped != SKIPPED_SELECTED_IDS:
        raise ValueError(f"unexpected skipped selected candidates: {skipped}")

    pool_by_id = {row["candidate_id"]: row for row in pool_rows}
    missing = [candidate_id for candidate_id in top2_ids if candidate_id not in pool_by_id]
    if missing:
        raise ValueError(f"top-2 candidates missing from pool: {missing}")
    return [pool_by_id[candidate_id] for candidate_id in top2_ids]


def write_top2_configs(candidate_rows: Sequence[dict[str, str]], config_dir: str | Path) -> list[Path]:
    output_dir = Path(config_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for row in candidate_rows:
        path = output_dir / f"{row['candidate_id']}.yaml"
        path.write_text(build_next_phase_gap_candidate_config(row), encoding="utf-8")
        written.append(path)
    return written


def build_next_phase_gap_candidate_config(candidate: dict[str, str]) -> str:
    period_x = float(candidate["period_x_nm"])
    period_y = float(candidate["period_y_nm"])
    p1_frac_x = float(candidate["p1_frac_x"])
    p1_frac_y = float(candidate["p1_frac_y"])
    p2_frac_x = float(candidate["p2_frac_x"])
    p2_frac_y = float(candidate["p2_frac_y"])
    internal_dx = float(candidate["internal_dx_nm"])
    internal_dy = float(candidate["internal_dy_nm"])
    p1_x = (p1_frac_x - 0.5) * period_x + internal_dx / 2.0
    p1_y = (p1_frac_y - 0.5) * period_y + internal_dy / 2.0
    p2_x = (p2_frac_x - 0.5) * period_x - internal_dx / 2.0
    p2_y = (p2_frac_y - 0.5) * period_y - internal_dy / 2.0
    data = {
        "project": {
            "name": "blue_plane_wave_metasurface",
            "stage": "09_p22_apcd_k6_next_phase_gap_top2_config_prepare",
        },
        "candidate": {
            "variant_id": candidate["candidate_id"],
            "candidate_type": candidate["candidate_family"],
            "description": "next phase-gap selected top-2 candidate; config prepare only",
            "target_bin_deg": _number(candidate["target_bin_deg"]),
            "source_stage": candidate["source_stage"],
            "anchor_candidate": candidate["anchor_candidate"],
            "risk_level": candidate["risk_level"],
            "design_rationale": candidate["design_rationale"],
            "source_pool_csv": "outputs/apcd_k6_active_learning/next_phase_gap_candidate_pool_v2.csv",
            "source_selection_csv": "outputs/apcd_k6_active_learning/next_phase_gap_fdtd_selection_v2.csv",
            "notes": "09-P22 generated config for next phase-gap top-2 only; no config generated for selected ranks 3-4.",
        },
        "boundary": {
            "no_k7": True,
            "not_phase_ramp_supercell": True,
            "not_steering_result": True,
            "no_fdtd_run_in_09_p22": True,
            "no_fsp_export_in_09_p22": True,
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
            "period_x_nm": _number(period_x),
            "period_y_nm": _number(period_y),
            "height_nm": _number(candidate["height_nm"]),
            "minimum_gap_nm": 5,
            "nanopillar_1": {
                "length_nm": _number(candidate["p1_length_nm"]),
                "width_nm": _number(candidate["p1_width_nm"]),
                "rotation_deg": _number(candidate["p1_rotation_deg"]),
                "x_nm": _number(p1_x),
                "y_nm": _number(p1_y),
                "frac_x": _number(p1_frac_x),
                "frac_y": _number(p1_frac_y),
            },
            "nanopillar_2": {
                "length_nm": _number(candidate["p2_length_nm"]),
                "width_nm": _number(candidate["p2_width_nm"]),
                "rotation_deg": _number(candidate["p2_rotation_deg"]),
                "x_nm": _number(p2_x),
                "y_nm": _number(p2_y),
                "frac_x": _number(p2_frac_x),
                "frac_y": _number(p2_frac_y),
            },
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
            "result_dir": f"outputs/apcd_k6_metagrating_633nm/phase_state_candidates/{candidate['candidate_id']}",
        },
    }
    return yaml.safe_dump(data, sort_keys=False)


def validate_top2_configs(config_paths: Sequence[str | Path], candidate_rows: Sequence[dict[str, str]]) -> list[dict[str, object]]:
    candidate_by_id = {row["candidate_id"]: row for row in candidate_rows}
    validation_rows = []
    for config_path in config_paths:
        path = Path(config_path)
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        candidate_id = str(data["candidate"]["variant_id"])
        expected = candidate_by_id[candidate_id]
        config = load_apcd_single_dimer_config(path)
        checks = [
            candidate_id in TOP2_IDS,
            data["candidate"]["target_bin_deg"] == _number(expected["target_bin_deg"]),
            data["candidate"]["source_stage"] == expected["source_stage"],
            config.geometry.nanopillar_1.length_nm == float(expected["p1_length_nm"]),
            config.geometry.nanopillar_1.width_nm == float(expected["p1_width_nm"]),
            config.geometry.nanopillar_2.length_nm == float(expected["p2_length_nm"]),
            config.geometry.nanopillar_2.width_nm == float(expected["p2_width_nm"]),
            config.geometry.nanopillar_1.rotation_deg == float(expected["p1_rotation_deg"]),
            config.geometry.nanopillar_2.rotation_deg == float(expected["p2_rotation_deg"]),
            config.output.result_dir.as_posix().endswith(f"/{candidate_id}"),
        ]
        validation_rows.append(
            {
                "candidate_id": candidate_id,
                "config_path": str(path),
                "validation_pass": all(checks),
                "notes": "local config load/dry-run validation only; no FDTD/lumapi/.fsp/results",
            }
        )
    return validation_rows


def _number(value: object) -> int | float:
    number = float(value)
    return int(number) if number.is_integer() else number


if __name__ == "__main__":
    raise SystemExit(main())
