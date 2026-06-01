from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


VARIANT_IDS = [
    "baseline",
    "p1L_m10",
    "p1L_m5",
    "p1L_p5",
    "p1L_p10",
    "p1W_m5",
    "p1W_p5",
    "p2L_m5",
    "p2L_p5",
    "p2W_m10",
    "p2W_m5",
    "p2W_p5",
    "p2W_p10",
]

INDEX_FIELDS = [
    "variant_id",
    "config_path",
    "candidate_type",
    "changed_parameter",
    "delta_nm",
    "pillar_1_length_nm",
    "pillar_1_width_nm",
    "pillar_1_rotation_deg",
    "pillar_2_length_nm",
    "pillar_2_width_nm",
    "pillar_2_rotation_deg",
    "notes",
]

BOUNDARY_FLAGS = {
    "no_fdtd_run_in_this_step": True,
    "no_fsp_export_in_this_step": True,
    "not_k7": True,
    "not_sweep": True,
    "not_phase_ramp_supercell": True,
    "not_steering_result": True,
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate APCD K=6 candidate config scaffold.")
    parser.add_argument("--dry-run", action="store_true", help="Generate deterministic YAML/CSV scaffold only.")
    parser.add_argument(
        "--route-csv",
        default="outputs/apcd_k6_metagrating_633nm/phase_state_candidate_route.csv",
        help="Input one-factor candidate route CSV.",
    )
    parser.add_argument(
        "--config-dir",
        default="configs/apcd_k6_phase_state_candidates",
        help="Output directory for candidate YAML configs.",
    )
    parser.add_argument(
        "--index-csv",
        default="outputs/apcd_k6_metagrating_633nm/phase_state_candidate_config_index.csv",
        help="Output index CSV path.",
    )
    return parser.parse_args()


def read_candidate_route(path: str | Path) -> list[dict[str, str]]:
    route_path = Path(path)
    if not route_path.is_absolute():
        route_path = REPO_ROOT / route_path
    with route_path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rows.sort(key=lambda row: VARIANT_IDS.index(row["variant_id"]))
    return rows


def build_candidate_config(row: dict[str, str]) -> dict[str, object]:
    variant_id = row["variant_id"]
    p1_length = _as_number(row["pillar_1_length_nm"])
    p1_width = _as_number(row["pillar_1_width_nm"])
    p2_length = _as_number(row["pillar_2_length_nm"])
    p2_width = _as_number(row["pillar_2_width_nm"])
    if p2_length == 150 and p2_width == 85:
        raise ValueError("original beta-selective pillar 2 geometry 150 x 85 nm is not allowed")

    return {
        "project": {
            "name": "blue_plane_wave_metasurface",
            "stage": "08_p5_apcd_k6_phase_state_candidate_config_scaffold",
        },
        "candidate": {
            "variant_id": variant_id,
            "candidate_type": row["candidate_type"],
            "description": row["description"],
            "changed_parameter": row["changed_parameter"],
            "delta_nm": _as_number(row["delta_nm"]),
            "source_route_csv": "outputs/apcd_k6_metagrating_633nm/phase_state_candidate_route.csv",
            "notes": "single-dimer candidate config scaffold only; not evaluated; not a steering result",
        },
        "boundary": dict(BOUNDARY_FLAGS),
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
            "layout_mode": "apcd_fractional",
            "period_x_nm": 340,
            "period_y_nm": 340,
            "height_nm": 300,
            "minimum_gap_nm": 5,
            "nanopillar_1": {
                "length_nm": p1_length,
                "width_nm": p1_width,
                "frac_x": 0.75,
                "frac_y": 0.75,
                "rotation_deg": _as_number(row["pillar_1_rotation_deg"]),
            },
            "nanopillar_2": {
                "length_nm": p2_length,
                "width_nm": p2_width,
                "frac_x": 0.25,
                "frac_y": 0.25,
                "rotation_deg": _as_number(row["pillar_2_rotation_deg"]),
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
            "result_dir": f"outputs/apcd_k6_metagrating_633nm/phase_state_candidates/{variant_id}",
        },
    }


def write_candidate_configs(
    rows: list[dict[str, str]],
    config_dir: str | Path,
) -> list[dict[str, object]]:
    output_dir = Path(config_dir)
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    index_rows = []
    for row in rows:
        config = build_candidate_config(row)
        variant_id = row["variant_id"]
        config_path = output_dir / f"{variant_id}.yaml"
        config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
        index_rows.append(
            {
                "variant_id": variant_id,
                "config_path": _relative_posix(config_path),
                "candidate_type": row["candidate_type"],
                "changed_parameter": row["changed_parameter"],
                "delta_nm": row["delta_nm"],
                "pillar_1_length_nm": row["pillar_1_length_nm"],
                "pillar_1_width_nm": row["pillar_1_width_nm"],
                "pillar_1_rotation_deg": row["pillar_1_rotation_deg"],
                "pillar_2_length_nm": row["pillar_2_length_nm"],
                "pillar_2_width_nm": row["pillar_2_width_nm"],
                "pillar_2_rotation_deg": row["pillar_2_rotation_deg"],
                "notes": "config scaffold only; no FDTD run; no .fsp export; not a steering result",
            }
        )
    return index_rows


def write_index_csv(rows: list[dict[str, object]], path: str | Path) -> Path:
    index_path = Path(path)
    if not index_path.is_absolute():
        index_path = REPO_ROOT / index_path
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with index_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=INDEX_FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in INDEX_FIELDS} for row in rows)
    return index_path


def generate_candidate_config_scaffold(
    *,
    route_csv: str | Path,
    config_dir: str | Path,
    index_csv: str | Path,
) -> tuple[list[dict[str, str]], list[dict[str, object]], Path]:
    rows = read_candidate_route(route_csv)
    _validate_route_rows(rows)
    index_rows = write_candidate_configs(rows, config_dir)
    index_path = write_index_csv(index_rows, index_csv)
    return rows, index_rows, index_path


def main() -> int:
    args = parse_args()
    if not args.dry_run:
        raise SystemExit("Pass --dry-run for the current scaffold-only workflow.")
    rows, index_rows, index_path = generate_candidate_config_scaffold(
        route_csv=args.route_csv,
        config_dir=args.config_dir,
        index_csv=args.index_csv,
    )
    print(f"candidate_count={len(rows)}")
    print(f"config_count={len(index_rows)}")
    print(f"variant_ids={','.join(row['variant_id'] for row in rows)}")
    print(f"index_csv={index_path}")
    print("status=dry_run_config_scaffold_only_no_fdtd_no_fsp_not_steering_result")
    return 0


def _validate_route_rows(rows: list[dict[str, str]]) -> None:
    variant_ids = [row["variant_id"] for row in rows]
    if variant_ids != VARIANT_IDS:
        raise ValueError(f"Unexpected variant order: {variant_ids}")
    if len(set(variant_ids)) != len(variant_ids):
        raise ValueError("variant_id values must be unique")


def _as_number(value: object) -> int | float:
    number = float(value)
    if number.is_integer():
        return int(number)
    return number


def _relative_posix(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
