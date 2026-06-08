from __future__ import annotations

import argparse
import copy
import csv
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_candidate_validation import polygon_min_distance_nm, rectangle_corners_nm  # noqa: E402


ANCHOR_ID = "aggr_lhs_retention_dy_05"
OFFICIAL_HEIGHT_NM = 232
MIN_GAP_NM = 50.0
CONFIG_DIR = REPO_ROOT / "configs/apcd_k6_phase_state_candidates"
ANCHOR_CONFIG = CONFIG_DIR / f"{ANCHOR_ID}.yaml"
ACTIVE_DIR = REPO_ROOT / "outputs/apcd_k6_active_learning"
PLAN_CSV = ACTIVE_DIR / "p176_h232_zero_coupled_candidate_plan.csv"
REPORT_MD = REPO_ROOT / "reports/p176_h232_zero_coupled_plan.md"

PLAN_FIELDS = [
    "candidate_id",
    "group",
    "family",
    "anchor_candidate_id",
    "height_nm",
    "period_x_nm",
    "period_y_nm",
    "p1_length_nm",
    "p1_width_nm",
    "p2_length_nm",
    "p2_width_nm",
    "same_cell_min_gap_nm",
    "periodic_image_min_gap_nm",
    "minimum_gap_nm_threshold",
    "geometry_pass",
    "target_bin_deg",
    "config_path",
    "fdtd_status",
    "rationale",
]


@dataclass(frozen=True)
class CandidateSpec:
    candidate_id: str
    group: str
    family: str
    p1_length_nm: int
    p1_width_nm: int
    p2_length_nm: int
    p2_width_nm: int
    rationale: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Stage 09 P176 fixed-h232 coupled zero-bin recovery candidate YAMLs only."
    )
    parser.add_argument("--anchor-config", type=Path, default=ANCHOR_CONFIG)
    parser.add_argument("--config-dir", type=Path, default=CONFIG_DIR)
    parser.add_argument("--plan-csv", type=Path, default=PLAN_CSV)
    parser.add_argument("--report", type=Path, default=REPORT_MD)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    specs = build_candidate_specs()
    anchor_config = load_yaml(args.anchor_config)
    rows = []
    for spec in specs:
        config = build_candidate_config(anchor_config, spec)
        gap = validate_min_gap(config)
        config_path = args.config_dir / f"{spec.candidate_id}.yaml"
        write_yaml(config_path, config)
        rows.append(plan_row(spec, config, config_path, gap))
    assert_integer_geometry(rows)
    write_csv_rows(rows, args.plan_csv, PLAN_FIELDS)
    write_report(args.report, rows)
    print(f"plan_csv={args.plan_csv}")
    print(f"report={args.report}")
    print(f"candidate_yaml_count={len(rows)}")
    print("status=stage09_h232_zero_coupled_yaml_generated_no_fdtd_no_lumapi")
    return 0


def build_candidate_specs() -> list[CandidateSpec]:
    return [
        CandidateSpec(
            candidate_id="cpk_zero_l60_h232_p1geom120x58_p2geom75x136_01",
            group="p2_size_up_selection_recovery",
            family="h232_zero_coupled_p2_size_width_recovery",
            p1_length_nm=120,
            p1_width_nm=58,
            p2_length_nm=75,
            p2_width_nm=136,
            rationale="p2 width/size-up selection recovery using the h232 zero-bin phase budget.",
        ),
        CandidateSpec(
            candidate_id="cpk_zero_l60_h232_p1geom120x58_p2geom76x136_01",
            group="p2_size_up_selection_recovery",
            family="h232_zero_coupled_p2_size_width_recovery",
            p1_length_nm=120,
            p1_width_nm=58,
            p2_length_nm=76,
            p2_width_nm=136,
            rationale="coupled p2 length + width-up selection recovery using the h232 phase budget.",
        ),
        CandidateSpec(
            candidate_id="cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01",
            group="p2_size_up_selection_recovery",
            family="h232_zero_coupled_p2_size_width_recovery",
            p1_length_nm=120,
            p1_width_nm=58,
            p2_length_nm=76,
            p2_width_nm=137,
            rationale="slightly stronger p2 size-up selection recovery using the h232 phase budget.",
        ),
        CandidateSpec(
            candidate_id="cpk_zero_l60_h232_p1geom120x58_p2geom77x137_01",
            group="p2_size_up_selection_recovery",
            family="h232_zero_coupled_p2_size_width_recovery",
            p1_length_nm=120,
            p1_width_nm=58,
            p2_length_nm=77,
            p2_width_nm=137,
            rationale="upper coupled p2 size-up selection recovery check at fixed h232.",
        ),
        CandidateSpec(
            candidate_id="cpk_zero_l60_h232_p1geom120x58_p2geom74x136_01",
            group="p2_length_down_width_up_control",
            family="h232_zero_coupled_p2_compensation_control",
            p1_length_nm=120,
            p1_width_nm=58,
            p2_length_nm=74,
            p2_width_nm=136,
            rationale="length-down plus width-up p2 compensation control.",
        ),
        CandidateSpec(
            candidate_id="cpk_zero_l60_h232_p1geom119x58_p2geom76x136_01",
            group="weak_p1_secondary_trim",
            family="h232_zero_coupled_p1_secondary_trim",
            p1_length_nm=119,
            p1_width_nm=58,
            p2_length_nm=76,
            p2_width_nm=136,
            rationale="weak secondary p1 length trim combined with p2 selection recovery; p1 is not the primary phase knob.",
        ),
    ]


def build_candidate_config(anchor: dict[str, object], spec: CandidateSpec) -> dict[str, object]:
    config = copy.deepcopy(anchor)
    config.setdefault("project", {})
    config["project"]["stage"] = "09_p176_h232_zero_coupled_recovery_candidate_yaml_only"
    config["candidate"] = {
        "variant_id": spec.candidate_id,
        "candidate_type": spec.family,
        "scheme_name": "h232_zero_coupled_selectivity_recovery_stage09",
        "description": f"P176 h232 zero-bin coupled selectivity recovery candidate {spec.candidate_id}",
        "target_bins_deg": "0",
        "source_stage": "09-P176",
        "anchor_candidate_id": ANCHOR_ID,
        "baseline_candidate_id": "cpk_zero_l60_lhs_h232_p1geom120x58_01",
        "baseline_phase_deg": 19.94,
        "baseline_target_conversion": 0.817,
        "baseline_opposite_spin_leakage": 0.179,
        "baseline_ratio": 4.57,
        "source_plan_csv": relative_path(PLAN_CSV),
        "fabrication_rule": "official candidates use integer-nm geometry at fixed height_nm=232; no sub-nm official candidates",
        "notes": (
            "Stage 09 YAML-only h232 zero-bin coupled recovery candidate; not K=6 phase-ramp, "
            "not steering, not stage 10, and not a Micro-LED result."
        ),
    }
    config["boundary"] = {
        "no_k7": True,
        "not_phase_ramp_supercell": True,
        "not_steering_result": True,
        "not_complete_k6_library_claim": True,
        "not_stage10": True,
        "no_fdtd_run_by_generator": True,
        "integer_nm_official_geometry": True,
        "fixed_height_nm": OFFICIAL_HEIGHT_NM,
        "minimum_gap_nm_threshold": MIN_GAP_NM,
        "no_notch_in_p176_batch": True,
    }
    geometry = config.setdefault("geometry", {})
    geometry["period_x_nm"] = 340
    geometry["period_y_nm"] = 340
    geometry["height_nm"] = OFFICIAL_HEIGHT_NM
    geometry["minimum_gap_nm"] = int(MIN_GAP_NM)
    p1 = geometry.setdefault("nanopillar_1", {})
    p1["shape"] = "rectangle"
    p1["length_nm"] = spec.p1_length_nm
    p1["width_nm"] = spec.p1_width_nm
    clear_shape_extensions(p1)
    p2 = geometry.setdefault("nanopillar_2", {})
    p2["shape"] = "rectangle"
    p2["length_nm"] = spec.p2_length_nm
    p2["width_nm"] = spec.p2_width_nm
    clear_shape_extensions(p2)
    output = config.setdefault("output", {})
    output["result_dir"] = f"outputs/apcd_k6_metagrating_633nm/phase_state_candidates/{spec.candidate_id}"
    return config


def clear_shape_extensions(pillar: dict[str, object]) -> None:
    for key in (
        "notch_depth_nm",
        "notch_width_nm",
        "notch_side",
        "corner_radius_nm",
        "chamfer_nm",
        "shape_radius_nm",
    ):
        pillar.pop(key, None)


def validate_min_gap(config: dict[str, object]) -> dict[str, object]:
    geometry = config["geometry"]
    p1 = geometry["nanopillar_1"]
    p2 = geometry["nanopillar_2"]
    p1_poly = polygon_for_pillar(p1)
    p2_poly = polygon_for_pillar(p2)
    same_cell = polygon_min_distance_nm(p1_poly, p2_poly)
    periodic = periodic_min_gap_nm([p1_poly, p2_poly], float(geometry["period_x_nm"]), float(geometry["period_y_nm"]))
    minimum_gap = min(same_cell, periodic)
    if minimum_gap < MIN_GAP_NM:
        candidate_id = config["candidate"]["variant_id"]
        raise ValueError(f"{candidate_id} min gap {minimum_gap:.3f} nm is below {MIN_GAP_NM:.1f} nm")
    return {
        "same_cell_min_gap_nm": same_cell,
        "periodic_image_min_gap_nm": periodic,
        "minimum_gap_nm_threshold": MIN_GAP_NM,
        "geometry_pass": True,
    }


def polygon_for_pillar(pillar: dict[str, object]) -> list[tuple[float, float]]:
    return rectangle_corners_nm(
        length_nm=float(pillar["length_nm"]),
        width_nm=float(pillar["width_nm"]),
        rotation_deg=float(pillar["rotation_deg"]),
        center_x_nm=float(pillar["x_nm"]),
        center_y_nm=float(pillar["y_nm"]),
    )


def periodic_min_gap_nm(polygons: Sequence[Sequence[tuple[float, float]]], period_x_nm: float, period_y_nm: float) -> float:
    minimum = math.inf
    for central in polygons:
        for image in polygons:
            for ix in (-1, 0, 1):
                for iy in (-1, 0, 1):
                    if ix == 0 and iy == 0:
                        continue
                    shifted = [(x + ix * period_x_nm, y + iy * period_y_nm) for x, y in image]
                    minimum = min(minimum, polygon_min_distance_nm(central, shifted))
    return minimum


def plan_row(spec: CandidateSpec, config: dict[str, object], config_path: Path, gap: dict[str, object]) -> dict[str, object]:
    geometry = config["geometry"]
    return {
        "candidate_id": spec.candidate_id,
        "group": spec.group,
        "family": spec.family,
        "anchor_candidate_id": ANCHOR_ID,
        "height_nm": OFFICIAL_HEIGHT_NM,
        "period_x_nm": geometry["period_x_nm"],
        "period_y_nm": geometry["period_y_nm"],
        "p1_length_nm": spec.p1_length_nm,
        "p1_width_nm": spec.p1_width_nm,
        "p2_length_nm": spec.p2_length_nm,
        "p2_width_nm": spec.p2_width_nm,
        "same_cell_min_gap_nm": gap["same_cell_min_gap_nm"],
        "periodic_image_min_gap_nm": gap["periodic_image_min_gap_nm"],
        "minimum_gap_nm_threshold": gap["minimum_gap_nm_threshold"],
        "geometry_pass": gap["geometry_pass"],
        "target_bin_deg": 0,
        "config_path": relative_path(config_path),
        "fdtd_status": "not_run",
        "rationale": spec.rationale,
    }


def assert_integer_geometry(rows: Sequence[dict[str, object]]) -> None:
    integer_fields = [
        "height_nm",
        "period_x_nm",
        "period_y_nm",
        "p1_length_nm",
        "p1_width_nm",
        "p2_length_nm",
        "p2_width_nm",
    ]
    for row in rows:
        for field in integer_fields:
            value = row.get(field, "")
            if value == "":
                continue
            if float(value) != int(float(value)):
                raise ValueError(f"Non-integer official geometry found for {row['candidate_id']}: {field}={value}")


def load_yaml(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle)
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected a YAML mapping: {path}")
    return loaded


def write_yaml(path: Path, data: dict[str, object]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(data, handle, sort_keys=False)
    return path


def write_csv_rows(rows: Iterable[dict[str, object]], path: Path, fieldnames: Sequence[str]) -> Path:
    row_list = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fieldnames} for row in row_list)
    return path


def write_report(path: Path, rows: Sequence[dict[str, object]]) -> Path:
    lines = [
        "# P176 h232 zero coupled recovery plan",
        "",
        "## Scope",
        "",
        "Stage 09 YAML generation only. This script does not run FDTD, call lumapi, edit `configs/runtime.yaml`, or claim K=6 phase-ramp steering or Micro-LED results.",
        "",
        "## Design Basis",
        "",
        "- coverage before this planning step: [-180, -120, -60, 60, 120]; missing [0]",
        "- h232 p1geom120x58 is already a 0-bin phase-hit but fails selectivity ratio",
        "- target: recover leakage/ratio while keeping phase within +/-30 deg",
        "- p2 width/size-up is the primary selection-recovery knob using the h232 phase budget",
        "- p2 74x136 is the length-down plus width-up compensation control",
        "- p1 119x58 is a weak secondary trim, not the primary phase knob",
        "- no notch candidates are generated in the first P176 batch",
        "- all official candidates use integer-nm geometry and `height_nm = 232`",
        "",
        "## Candidate Count",
        "",
        f"- planned YAML candidates: {len(rows)}",
        f"- minimum same-cell gap nm: {min(float(row['same_cell_min_gap_nm']) for row in rows):.6g}",
        f"- minimum periodic-image gap nm: {min(float(row['periodic_image_min_gap_nm']) for row in rows):.6g}",
        f"- minimum gap threshold nm: {MIN_GAP_NM:g}",
        "",
        "## Next Step",
        "",
        "Review these YAMLs, then run real FDTD manually on the server if approved. Do not commit raw `results.csv`, raw `summary.md`, `.fsp`, `pre_run`, `.npy`, or large outputs.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
