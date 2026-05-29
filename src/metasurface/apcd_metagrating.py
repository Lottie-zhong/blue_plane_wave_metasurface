from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Iterable

from metasurface.config import APCDSingleDimerConfig


APCD_METAGRATING_GEOMETRY_FIELDS = [
    "K",
    "dimer_index",
    "pillar_index_in_dimer",
    "global_pillar_index",
    "x_nm",
    "y_nm",
    "length_nm",
    "width_nm",
    "height_nm",
    "rotation_deg",
    "frac_x",
    "frac_y",
    "dimer_pitch_nm",
    "supercell_period_nm",
    "wavelength_nm",
    "target_angle_deg",
]


def calculate_supercell_period_nm(wavelength_nm: float, target_angle_deg: float) -> float:
    sin_theta = math.sin(math.radians(target_angle_deg))
    if sin_theta <= 0:
        raise ValueError("target_angle_deg must give a positive first-order grating period")
    return wavelength_nm / sin_theta


def build_apcd_k_dimer_metagrating_geometry(
    config: APCDSingleDimerConfig,
    K: int,
    target_angle_deg: float = 15.0,
) -> list[dict[str, float | int]]:
    if K <= 0:
        raise ValueError("K must be positive")

    geometry = config.geometry
    wavelength_nm = float(config.target.wavelength_nm)
    supercell_period_nm = calculate_supercell_period_nm(wavelength_nm, target_angle_deg)
    dimer_pitch_nm = supercell_period_nm / K
    local_period_y_nm = float(geometry.period_y_nm)

    pillars = [geometry.nanopillar_1, geometry.nanopillar_2]
    rows: list[dict[str, float | int]] = []

    global_pillar_index = 0
    for dimer_index in range(K):
        dimer_cell_x_start_nm = -0.5 * supercell_period_nm + dimer_index * dimer_pitch_nm
        dimer_center_x_nm = dimer_cell_x_start_nm + 0.5 * dimer_pitch_nm

        for pillar_index_in_dimer, pillar in enumerate(pillars, start=1):
            if pillar.frac_x is None or pillar.frac_y is None:
                raise ValueError("APCD metagrating requires fractional pillar coordinates")

            x_local_nm = (pillar.frac_x - 0.5) * dimer_pitch_nm
            y_local_nm = (pillar.frac_y - 0.5) * local_period_y_nm
            rows.append(
                {
                    "K": K,
                    "dimer_index": dimer_index,
                    "pillar_index_in_dimer": pillar_index_in_dimer,
                    "global_pillar_index": global_pillar_index,
                    "x_nm": dimer_center_x_nm + x_local_nm,
                    "y_nm": y_local_nm,
                    "length_nm": float(pillar.length_nm),
                    "width_nm": float(pillar.width_nm),
                    "height_nm": float(geometry.height_nm),
                    "rotation_deg": float(pillar.rotation_deg),
                    "frac_x": float(pillar.frac_x),
                    "frac_y": float(pillar.frac_y),
                    "dimer_pitch_nm": dimer_pitch_nm,
                    "supercell_period_nm": supercell_period_nm,
                    "wavelength_nm": wavelength_nm,
                    "target_angle_deg": float(target_angle_deg),
                }
            )
            global_pillar_index += 1

    return rows


def validate_alpha_pass_dimer_source(config: APCDSingleDimerConfig) -> None:
    geometry = config.geometry
    p1 = geometry.nanopillar_1
    p2 = geometry.nanopillar_2

    expected = [
        (p1.length_nm, 130.0, "nanopillar_1.length_nm"),
        (p1.width_nm, 70.0, "nanopillar_1.width_nm"),
        (p1.frac_x, 0.75, "nanopillar_1.frac_x"),
        (p1.frac_y, 0.75, "nanopillar_1.frac_y"),
        (p1.rotation_deg, 67.5, "nanopillar_1.rotation_deg"),
        (p2.length_nm, 85.0, "nanopillar_2.length_nm"),
        (p2.width_nm, 150.0, "nanopillar_2.width_nm"),
        (p2.frac_x, 0.25, "nanopillar_2.frac_x"),
        (p2.frac_y, 0.25, "nanopillar_2.frac_y"),
        (p2.rotation_deg, 112.5, "nanopillar_2.rotation_deg"),
    ]
    for observed, target, name in expected:
        if observed is None or not math.isclose(float(observed), target, rel_tol=0.0, abs_tol=1e-9):
            raise ValueError(f"{name} must be {target} for the validated alpha-pass dimer")


def write_apcd_metagrating_geometry_csv(rows: Iterable[dict[str, object]], path: Path) -> Path:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=APCD_METAGRATING_GEOMETRY_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_apcd_metagrating_geometry_summary(
    rows: list[dict[str, float | int]],
    config: APCDSingleDimerConfig,
    path: Path,
) -> Path:
    if not rows:
        raise ValueError("Cannot write a geometry summary without rows")

    first = rows[0]
    K = int(first["K"])
    nanopillar_count = len(rows)
    p1 = config.geometry.nanopillar_1
    p2 = config.geometry.nanopillar_2

    lines = [
        f"# APCD K={K} Dimer Metagrating Geometry Dry Run",
        "",
        "- status: dry_run_geometry",
        f"- K: {K}",
        f"- dimer_count: {K}",
        f"- nanopillar_count: {nanopillar_count}",
        f"- wavelength_nm: {first['wavelength_nm']}",
        f"- target_angle_deg: {first['target_angle_deg']}",
        f"- supercell_period_nm: {first['supercell_period_nm']}",
        f"- dimer_pitch_nm: {first['dimer_pitch_nm']}",
        "- K_definition: K is the number of APCD dimers, not the number of individual nanopillars.",
        "- total_nanopillars: 2K",
        "",
        "Alpha-pass dimer source geometry:",
        "",
        (
            f"- nanopillar_1: length_nm={p1.length_nm}, width_nm={p1.width_nm}, "
            f"frac=({p1.frac_x}, {p1.frac_y}), rotation_deg={p1.rotation_deg}"
        ),
        (
            f"- nanopillar_2: length_nm={p2.length_nm}, width_nm={p2.width_nm}, "
            f"frac=({p2.frac_x}, {p2.frac_y}), rotation_deg={p2.rotation_deg}"
        ),
        "- pillar_2_switched_length_width: True",
        "- source_config: configs/apcd_fig2_elliptical_633nm_alpha_pass.yaml",
        "",
        "Scope note:",
        "",
        "- This file is a dry-run geometry definition only.",
        "- This is not an FDTD result.",
        "- This is not an .fsp export.",
        "- This is not a far-field or diffraction-order result.",
        "- No lumapi call is required to generate this file.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_apcd_metagrating_dry_run_outputs(
    config: APCDSingleDimerConfig,
    K: int,
    output_dir: Path,
    target_angle_deg: float = 15.0,
) -> tuple[Path, Path, list[dict[str, float | int]]]:
    validate_alpha_pass_dimer_source(config)
    rows = build_apcd_k_dimer_metagrating_geometry(config, K=K, target_angle_deg=target_angle_deg)
    csv_path = write_apcd_metagrating_geometry_csv(rows, output_dir / "geometry.csv")
    summary_path = write_apcd_metagrating_geometry_summary(rows, config, output_dir / "geometry_summary.md")
    return csv_path, summary_path, rows
