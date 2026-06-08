from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path
from typing import Iterable, Sequence

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
ACTIVE_DIR = REPO_ROOT / "outputs/apcd_k6_active_learning"

P180_PLAN_CSV = ACTIVE_DIR / "p180_k6_phase_ramp_supercell_plan.csv"
P179_LIBRARY_CSV = ACTIVE_DIR / "p179_stage10_frozen_phase_library.csv"
CONFIG_YAML = REPO_ROOT / "configs/apcd_k6_supercells/p181_k6_phase_ramp_supercell_633nm.yaml"
GEOMETRY_PLAN_CSV = ACTIVE_DIR / "p181_k6_supercell_geometry_plan.csv"
SANITY_CSV = ACTIVE_DIR / "p181_k6_supercell_sanity.csv"
REPORT_MD = REPO_ROOT / "reports/p181_k6_supercell_dryrun_config.md"

K = 6
REQUIRED_BINS = [-180, -120, -60, 0, 60, 120]

GEOMETRY_FIELDS = [
    "supercell_index",
    "target_bin_deg",
    "candidate_id",
    "pillar_name",
    "global_pillar_index",
    "x_nm",
    "y_nm",
    "local_x_nm",
    "local_y_nm",
    "length_nm",
    "width_nm",
    "height_nm",
    "rotation_deg",
    "shape",
    "material",
    "substrate",
    "source_config_path",
    "dimer_center_x_nm",
    "dimer_pitch_nm",
    "supercell_period_nm",
]

SANITY_FIELDS = [
    "K",
    "six_dimers_present",
    "six_unique_target_bins_present",
    "supercell_period_nm",
    "supercell_period_matches_p180",
    "dimer_pitch_nm",
    "dimer_pitch_matches_p180",
    "all_source_anchors_early_pass",
    "pillar_count",
    "min_same_cell_gap_nm",
    "min_adjacent_dimer_gap_nm",
    "no_pillar_crosses_supercell_boundary",
    "boundary_crossing_intended_by_periodic_boundary",
    "no_overlap_detected",
    "no_steering_claim",
    "fdtd_run_performed",
]

NO_OVERCLAIM = (
    "This is a K=6 supercell dry-run/config generation step only. "
    "No K=6 FDTD has been run. No +15 deg beam steering has been verified. "
    "This prepares the input for later server-side FDTD validation. "
    "It is not a Micro-LED result."
)


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate P181 K=6 supercell dry-run config from P180 and P179 artifacts."
    )
    parser.add_argument("--p180-plan", type=Path, default=P180_PLAN_CSV)
    parser.add_argument("--p179-library", type=Path, default=P179_LIBRARY_CSV)
    parser.add_argument("--config-yaml", type=Path, default=CONFIG_YAML)
    parser.add_argument("--geometry-csv", type=Path, default=GEOMETRY_PLAN_CSV)
    parser.add_argument("--sanity-csv", type=Path, default=SANITY_CSV)
    parser.add_argument("--report", type=Path, default=REPORT_MD)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    p180_rows = read_csv_rows(args.p180_plan)
    p179_rows = read_csv_rows(args.p179_library)
    validate_p180_plan(p180_rows)

    placed_pillars, source_configs = build_geometry_plan(p180_rows)
    sanity = build_sanity_row(p180_rows, p179_rows, placed_pillars)
    config = build_supercell_config(p180_rows, p179_rows, placed_pillars, source_configs, sanity)

    write_yaml(config, args.config_yaml)
    write_csv_rows(placed_pillars, args.geometry_csv, GEOMETRY_FIELDS)
    write_csv_rows([sanity], args.sanity_csv, SANITY_FIELDS)
    write_report(args.report, args.config_yaml, args.geometry_csv, args.sanity_csv, p180_rows, sanity)

    print(f"config_yaml={args.config_yaml}")
    print(f"geometry_csv={args.geometry_csv}")
    print(f"sanity_csv={args.sanity_csv}")
    print(f"report={args.report}")
    print("status=stage10_k6_supercell_dryrun_config_only_no_fdtd")
    return 0


def validate_p180_plan(rows: Sequence[dict[str, str]]) -> None:
    if len(rows) != K:
        raise ValueError(f"P180 plan must contain K={K} rows")
    indices = [int(row["supercell_index"]) for row in rows]
    if indices != list(range(K)):
        raise ValueError(f"Unexpected P180 supercell indices: {indices}")
    bins = sorted(int(float(row["target_bin_deg"])) for row in rows)
    if bins != REQUIRED_BINS:
        raise ValueError(f"P180 plan must contain bins {REQUIRED_BINS}; got {bins}")


def build_geometry_plan(
    p180_rows: Sequence[dict[str, str]],
) -> tuple[list[dict[str, object]], dict[str, dict[str, object]]]:
    placed: list[dict[str, object]] = []
    source_configs: dict[str, dict[str, object]] = {}
    global_index = 0
    supercell_period = infer_supercell_period_nm(p180_rows)

    for row in p180_rows:
        config_path = resolve_repo_path(row["config_path"])
        config = read_yaml(config_path)
        candidate_id = row["candidate_id"]
        source_configs[candidate_id] = config
        geometry = config["geometry"]
        material = config.get("material", {})
        dimer_center_x = float(row["dimer_center_x_nm"])
        dimer_pitch = float(row["dimer_pitch_nm"])
        height = float(geometry["height_nm"])

        for pillar_name, pillar in extract_pillars(geometry):
            local_x = float(pillar.get("x_nm", local_x_from_frac(pillar, geometry)))
            local_y = float(pillar.get("y_nm", local_y_from_frac(pillar, geometry)))
            placed.append(
                {
                    "supercell_index": int(row["supercell_index"]),
                    "target_bin_deg": int(float(row["target_bin_deg"])),
                    "candidate_id": candidate_id,
                    "pillar_name": pillar_name,
                    "global_pillar_index": global_index,
                    "x_nm": dimer_center_x + local_x,
                    "y_nm": local_y,
                    "local_x_nm": local_x,
                    "local_y_nm": local_y,
                    "length_nm": float(pillar["length_nm"]),
                    "width_nm": float(pillar["width_nm"]),
                    "height_nm": height,
                    "rotation_deg": float(pillar.get("rotation_deg", 0.0)),
                    "shape": pillar.get("shape", "rectangle"),
                    "material": material.get("meta_material", ""),
                    "substrate": material.get("substrate", ""),
                    "source_config_path": relative_path(config_path),
                    "dimer_center_x_nm": dimer_center_x,
                    "dimer_pitch_nm": dimer_pitch,
                    "supercell_period_nm": supercell_period,
                }
            )
            global_index += 1
    return placed, source_configs


def extract_pillars(geometry: dict[str, object]) -> list[tuple[str, dict[str, object]]]:
    pillars: list[tuple[str, dict[str, object]]] = []
    for key in sorted(geometry):
        value = geometry[key]
        if key.startswith("nanopillar") and isinstance(value, dict):
            if "length_nm" in value and "width_nm" in value:
                pillars.append((key, value))
    if len(pillars) < 2:
        raise ValueError("Each source dimer config must contain at least nanopillar_1 and nanopillar_2")
    return pillars


def local_x_from_frac(pillar: dict[str, object], geometry: dict[str, object]) -> float:
    frac_x = pillar.get("frac_x")
    if frac_x is None:
        raise ValueError("Pillar must provide x_nm or frac_x")
    return (float(frac_x) - 0.5) * float(geometry["period_x_nm"])


def local_y_from_frac(pillar: dict[str, object], geometry: dict[str, object]) -> float:
    frac_y = pillar.get("frac_y")
    if frac_y is None:
        raise ValueError("Pillar must provide y_nm or frac_y")
    return (float(frac_y) - 0.5) * float(geometry["period_y_nm"])


def build_sanity_row(
    p180_rows: Sequence[dict[str, str]],
    p179_rows: Sequence[dict[str, str]],
    placed_pillars: Sequence[dict[str, object]],
) -> dict[str, object]:
    supercell_period = infer_supercell_period_nm(p180_rows)
    dimer_pitch = unique_float(p180_rows, "dimer_pitch_nm")
    same_cell_gap = min_gap(placed_pillars, same_dimer=True)
    adjacent_gap = min_adjacent_gap(placed_pillars)
    boundary_crossing = boundary_crossing_pillars(placed_pillars, supercell_period)
    overlaps = overlap_pairs(placed_pillars)
    p179_early = {row["candidate_id"]: parse_bool(row.get("early_pass")) for row in p179_rows}
    all_early = all(p179_early.get(row["candidate_id"], False) for row in p180_rows)

    return {
        "K": K,
        "six_dimers_present": sorted({int(row["supercell_index"]) for row in p180_rows}) == list(range(K)),
        "six_unique_target_bins_present": sorted({int(float(row["target_bin_deg"])) for row in p180_rows}) == REQUIRED_BINS,
        "supercell_period_nm": supercell_period,
        "supercell_period_matches_p180": all(
            math.isclose(float(pillar["supercell_period_nm"]), supercell_period, rel_tol=0.0, abs_tol=1.0e-9)
            for pillar in placed_pillars
        ),
        "dimer_pitch_nm": dimer_pitch,
        "dimer_pitch_matches_p180": all(
            math.isclose(float(row["dimer_pitch_nm"]), dimer_pitch, rel_tol=0.0, abs_tol=1.0e-9)
            for row in p180_rows
        ),
        "all_source_anchors_early_pass": all_early,
        "pillar_count": len(placed_pillars),
        "min_same_cell_gap_nm": same_cell_gap,
        "min_adjacent_dimer_gap_nm": adjacent_gap,
        "no_pillar_crosses_supercell_boundary": not boundary_crossing,
        "boundary_crossing_intended_by_periodic_boundary": False,
        "no_overlap_detected": not overlaps,
        "no_steering_claim": True,
        "fdtd_run_performed": False,
    }


def build_supercell_config(
    p180_rows: Sequence[dict[str, str]],
    p179_rows: Sequence[dict[str, str]],
    placed_pillars: Sequence[dict[str, object]],
    source_configs: dict[str, dict[str, object]],
    sanity: dict[str, object],
) -> dict[str, object]:
    first_config = source_configs[p180_rows[0]["candidate_id"]]
    return {
        "project": {
            "name": "blue_plane_wave_metasurface",
            "stage": "10_p181_k6_supercell_dryrun_config",
        },
        "boundary": {
            "dry_run_config_only": True,
            "no_fdtd_run_performed": True,
            "fdtd_run_performed": False,
            "not_steering_result": True,
            "no_plus15_steering_verified": True,
            "not_micro_led_result": True,
            "do_not_edit_runtime_yaml": True,
        },
        "target": dict(first_config.get("target", {})),
        "material": dict(first_config.get("material", {})),
        "simulation": dict(first_config.get("simulation", {})),
        "supercell": {
            "layout_mode": "manual_absolute_k6_phase_ramp_from_p179_anchors",
            "K": K,
            "wavelength_nm": first_config.get("target", {}).get("wavelength_nm", 633),
            "target_angle_deg_for_period_sizing_only": 15,
            "supercell_period_nm": sanity["supercell_period_nm"],
            "dimer_pitch_nm": sanity["dimer_pitch_nm"],
            "phase_order_bins_deg": [int(float(row["target_bin_deg"])) for row in p180_rows],
            "source_plan_csv": relative_path(P180_PLAN_CSV),
            "source_library_csv": relative_path(P179_LIBRARY_CSV),
            "notes": NO_OVERCLAIM,
        },
        "dimers": build_config_dimers(p180_rows, placed_pillars),
        "sanity": dict(sanity),
        "output": {
            "geometry_plan_csv": relative_path(GEOMETRY_PLAN_CSV),
            "sanity_csv": relative_path(SANITY_CSV),
            "report": relative_path(REPORT_MD),
            "result_dir": "outputs/apcd_k6_metagrating_633nm/p181_phase_ramp_supercell_dryrun",
        },
        "provenance": {
            "p180_plan_rows": len(p180_rows),
            "p179_library_rows": len(p179_rows),
            "source_anchor_configs": sorted({row["config_path"] for row in p180_rows}),
        },
    }


def build_config_dimers(
    p180_rows: Sequence[dict[str, str]],
    placed_pillars: Sequence[dict[str, object]],
) -> list[dict[str, object]]:
    dimers: list[dict[str, object]] = []
    for row in p180_rows:
        index = int(row["supercell_index"])
        dimer_pillars = [pillar for pillar in placed_pillars if int(pillar["supercell_index"]) == index]
        dimers.append(
            {
                "supercell_index": index,
                "target_bin_deg": int(float(row["target_bin_deg"])),
                "candidate_id": row["candidate_id"],
                "dimer_center_x_nm": float(row["dimer_center_x_nm"]),
                "dimer_pitch_nm": float(row["dimer_pitch_nm"]),
                "cumulative_target_phase_deg": float(row["cumulative_target_phase_deg"]),
                "source_config_path": row["config_path"],
                "pillars": [
                    {
                        key: pillar[key]
                        for key in (
                            "pillar_name",
                            "global_pillar_index",
                            "x_nm",
                            "y_nm",
                            "local_x_nm",
                            "local_y_nm",
                            "length_nm",
                            "width_nm",
                            "height_nm",
                            "rotation_deg",
                            "shape",
                        )
                    }
                    for pillar in dimer_pillars
                ],
            }
        )
    return dimers


def min_gap(pillars: Sequence[dict[str, object]], same_dimer: bool) -> float:
    distances: list[float] = []
    for index, first in enumerate(pillars):
        for second in pillars[index + 1 :]:
            same = int(first["supercell_index"]) == int(second["supercell_index"])
            if same != same_dimer:
                continue
            distances.append(polygon_gap_nm(first, second))
    return min(distances) if distances else float("nan")


def min_adjacent_gap(pillars: Sequence[dict[str, object]]) -> float:
    distances: list[float] = []
    for index, first in enumerate(pillars):
        for second in pillars[index + 1 :]:
            if abs(int(first["supercell_index"]) - int(second["supercell_index"])) == 1:
                distances.append(polygon_gap_nm(first, second))
    return min(distances) if distances else float("nan")


def overlap_pairs(pillars: Sequence[dict[str, object]]) -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    for index, first in enumerate(pillars):
        for second in pillars[index + 1 :]:
            if polygon_gap_nm(first, second) <= 0.0:
                pairs.append((int(first["global_pillar_index"]), int(second["global_pillar_index"])))
    return pairs


def boundary_crossing_pillars(
    pillars: Sequence[dict[str, object]],
    supercell_period_nm: float,
) -> list[int]:
    crossing: list[int] = []
    for pillar in pillars:
        xs = [point[0] for point in rectangle_polygon(pillar)]
        if min(xs) < 0.0 or max(xs) > supercell_period_nm:
            crossing.append(int(pillar["global_pillar_index"]))
    return crossing


def polygon_gap_nm(first: dict[str, object], second: dict[str, object]) -> float:
    first_poly = rectangle_polygon(first)
    second_poly = rectangle_polygon(second)
    if polygons_intersect(first_poly, second_poly):
        return 0.0
    return min(
        point_segment_distance(point, start, end)
        for point in first_poly
        for start, end in polygon_edges(second_poly)
    ) if first_poly and second_poly else float("nan")


def rectangle_polygon(pillar: dict[str, object]) -> list[tuple[float, float]]:
    cx = float(pillar["x_nm"])
    cy = float(pillar["y_nm"])
    half_length = float(pillar["length_nm"]) / 2.0
    half_width = float(pillar["width_nm"]) / 2.0
    theta = math.radians(float(pillar["rotation_deg"]))
    cos_t = math.cos(theta)
    sin_t = math.sin(theta)
    corners = [
        (-half_length, -half_width),
        (half_length, -half_width),
        (half_length, half_width),
        (-half_length, half_width),
    ]
    return [
        (cx + x * cos_t - y * sin_t, cy + x * sin_t + y * cos_t)
        for x, y in corners
    ]


def polygons_intersect(first: Sequence[tuple[float, float]], second: Sequence[tuple[float, float]]) -> bool:
    for polygon in (first, second):
        for start, end in polygon_edges(polygon):
            axis = normalize((-(end[1] - start[1]), end[0] - start[0]))
            if separated_on_axis(first, second, axis):
                return False
    return True


def separated_on_axis(
    first: Sequence[tuple[float, float]],
    second: Sequence[tuple[float, float]],
    axis: tuple[float, float],
) -> bool:
    first_proj = [dot(point, axis) for point in first]
    second_proj = [dot(point, axis) for point in second]
    return max(first_proj) < min(second_proj) or max(second_proj) < min(first_proj)


def polygon_edges(polygon: Sequence[tuple[float, float]]) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    return [(polygon[index], polygon[(index + 1) % len(polygon)]) for index in range(len(polygon))]


def point_segment_distance(
    point: tuple[float, float],
    start: tuple[float, float],
    end: tuple[float, float],
) -> float:
    px, py = point
    sx, sy = start
    ex, ey = end
    dx = ex - sx
    dy = ey - sy
    length_sq = dx * dx + dy * dy
    if length_sq == 0.0:
        return math.hypot(px - sx, py - sy)
    t = max(0.0, min(1.0, ((px - sx) * dx + (py - sy) * dy) / length_sq))
    nearest = (sx + t * dx, sy + t * dy)
    return math.hypot(px - nearest[0], py - nearest[1])


def dot(point: tuple[float, float], axis: tuple[float, float]) -> float:
    return point[0] * axis[0] + point[1] * axis[1]


def normalize(vector: tuple[float, float]) -> tuple[float, float]:
    length = math.hypot(vector[0], vector[1])
    if length == 0.0:
        return (0.0, 0.0)
    return (vector[0] / length, vector[1] / length)


def infer_supercell_period_nm(rows: Sequence[dict[str, str]]) -> float:
    last = max(rows, key=lambda row: int(row["supercell_index"]))
    return float(last["dimer_center_x_nm"]) + 0.5 * float(last["dimer_pitch_nm"])


def unique_float(rows: Sequence[dict[str, str]], key: str) -> float:
    values = {round(float(row[key]), 9) for row in rows}
    if len(values) != 1:
        raise ValueError(f"Expected one unique value for {key}, got {sorted(values)}")
    return float(next(iter(values)))


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def read_yaml(path: Path) -> dict[str, object]:
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def write_yaml(data: dict[str, object], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
    return path


def write_csv_rows(rows: Iterable[dict[str, object]], path: Path, fieldnames: Sequence[str]) -> Path:
    row_list = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fieldnames} for row in row_list)
    return path


def write_report(
    path: Path,
    config_yaml: Path,
    geometry_csv: Path,
    sanity_csv: Path,
    p180_rows: Sequence[dict[str, str]],
    sanity: dict[str, object],
) -> Path:
    lines = [
        "# P181 K=6 supercell dry-run config",
        "",
        "## Scope",
        "",
        NO_OVERCLAIM,
        "",
        "`K` means six dimers, not individual nanopillars.",
        "",
        "## Inputs",
        "",
        f"- P180 phase-ramp plan: `{relative_path(P180_PLAN_CSV)}`",
        f"- P179 frozen phase library: `{relative_path(P179_LIBRARY_CSV)}`",
        "",
        "## Assembly",
        "",
        "| index | target_bin_deg | candidate_id | source_config |",
        "| ---: | ---: | --- | --- |",
    ]
    for row in p180_rows:
        lines.append(
            f"| {row['supercell_index']} | {row['target_bin_deg']} | `{row['candidate_id']}` | `{row['config_path']}` |"
        )
    lines.extend(
        [
            "",
            "## Sanity",
            "",
            f"- K: {sanity['K']}",
            f"- six dimers present: {sanity['six_dimers_present']}",
            f"- six unique target bins present: {sanity['six_unique_target_bins_present']}",
            f"- supercell_period_nm: {sanity['supercell_period_nm']}",
            f"- dimer_pitch_nm: {sanity['dimer_pitch_nm']}",
            f"- all source anchors early-pass: {sanity['all_source_anchors_early_pass']}",
            f"- pillar_count: {sanity['pillar_count']}",
            f"- min_same_cell_gap_nm: {sanity['min_same_cell_gap_nm']}",
            f"- min_adjacent_dimer_gap_nm: {sanity['min_adjacent_dimer_gap_nm']}",
            f"- no pillar crosses supercell boundary: {sanity['no_pillar_crosses_supercell_boundary']}",
            f"- no overlap detected: {sanity['no_overlap_detected']}",
            f"- no steering claim: {sanity['no_steering_claim']}",
            f"- fdtd_run_performed: {sanity['fdtd_run_performed']}",
            "",
            "## Outputs",
            "",
            f"- dry-run config: `{relative_path(config_yaml)}`",
            f"- geometry plan CSV: `{relative_path(geometry_csv)}`",
            f"- sanity CSV: `{relative_path(sanity_csv)}`",
            "",
            "## Boundary",
            "",
            "This config is an assembly input for later server-side FDTD validation. It is not optical validation.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def parse_bool(value: object) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"true", "1", "yes", "pass"}


def resolve_repo_path(path_text: str) -> Path:
    path = Path(path_text)
    if not path.is_absolute():
        path = REPO_ROOT / path
    return path


def relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


if __name__ == "__main__":
    raise SystemExit(main())
