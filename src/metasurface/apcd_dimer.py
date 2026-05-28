from __future__ import annotations

import cmath
import csv
import math
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Optional, Union

from metasurface.config import (
    APCDDimerMaterialConfig,
    APCDNanopillarConfig,
    APCDSingleDimerConfig,
    RuntimeConfig,
    load_runtime_config,
)
from metasurface.lumapi_runner import import_lumapi


APCD_DIMER_RESULT_FIELDS = [
    "wavelength_nm",
    "period_x_nm",
    "period_y_nm",
    "height_nm",
    "transmission_lcp",
    "transmission_rcp",
    "total_transmission",
    "T_R_from_L",
    "T_L_from_L",
    "T_R_from_R",
    "T_L_from_R",
    "target_conversion",
    "opposite_spin_leakage",
    "conversion_to_leakage_ratio",
    "spin_ER_dB",
    "gate_pass",
    "status",
    "note",
]


@dataclass(frozen=True)
class APCDGeometryValidation:
    minimum_gap_nm: float
    minimum_allowed_gap_nm: float
    closest_pair: str


@dataclass(frozen=True)
class APCDSingleDimerRunner:
    config: APCDSingleDimerConfig
    dry_run: bool = False
    runtime: Optional[RuntimeConfig] = None
    setup_only: bool = False
    fsp_output: Optional[Path] = None

    @classmethod
    def from_runtime_file(
        cls,
        config: APCDSingleDimerConfig,
        runtime_path: Optional[Union[str, Path]],
        dry_run: bool,
        setup_only: bool = False,
        fsp_output: Optional[Union[str, Path]] = None,
    ) -> "APCDSingleDimerRunner":
        runtime = None if dry_run or runtime_path is None else load_runtime_config(runtime_path)
        output_path = None if fsp_output is None else Path(fsp_output)
        return cls(
            config=config,
            dry_run=dry_run,
            runtime=runtime,
            setup_only=setup_only,
            fsp_output=output_path,
        )

    def run(self) -> dict[str, object]:
        if self.dry_run:
            return build_apcd_single_dimer_dry_run_row(self.config)

        if self.runtime is None:
            raise ValueError("A runtime config is required when dry_run is False")
        if not self.runtime.enable_lumerical:
            raise RuntimeError("runtime.enable_lumerical is false; use --dry-run or update runtime.yaml")

        lumapi = import_lumapi(self.runtime)
        if self.setup_only:
            output_path = self.fsp_output or self.config.output.result_dir / "apcd_single_dimer_633nm_setup.fsp"
            return run_apcd_single_dimer_setup_only(self.config, self.runtime, lumapi, output_path)
        return run_apcd_single_dimer_lumerical(self.config, self.runtime, lumapi)


def build_apcd_single_dimer_dry_run_row(config: APCDSingleDimerConfig) -> dict[str, object]:
    return _result_row(
        config=config,
        matrix={},
        target_conversion="",
        opposite_spin_leakage="",
        ratio="",
        spin_er_db="",
        gate_pass="",
        status="dry_run",
        note="single APCD dimer setup only; lumapi was not imported",
    )


def run_apcd_single_dimer_lumerical(
    config: APCDSingleDimerConfig,
    runtime: RuntimeConfig,
    lumapi: ModuleType,
) -> dict[str, object]:
    try:
        matrix = {
            "L": _run_one_incidence(config, runtime, lumapi, incident_polarization="LCP"),
            "R": _run_one_incidence(config, runtime, lumapi, incident_polarization="RCP"),
        }
        target_conversion = abs(matrix["L"]["R"]) ** 2
        opposite_spin_leakage = abs(matrix["R"]["R"]) ** 2 + abs(matrix["R"]["L"]) ** 2
        ratio = (target_conversion + config.target.eps) / (opposite_spin_leakage + config.target.eps)
        spin_er_db = 10 * math.log10(ratio)
        gate_pass = (
            spin_er_db > config.target.spin_er_threshold_db
            or ratio > config.target.conversion_to_leakage_threshold
        )
        return _result_row(
            config=config,
            matrix=matrix,
            target_conversion=target_conversion,
            opposite_spin_leakage=opposite_spin_leakage,
            ratio=ratio,
            spin_er_db=spin_er_db,
            gate_pass=gate_pass,
            status="ok",
            note="Circular basis convention: R=(Ex+iEy)/sqrt(2), L=(Ex-iEy)/sqrt(2)",
        )
    except Exception as exc:
        return _result_row(
            config=config,
            matrix={},
            target_conversion="",
            opposite_spin_leakage="",
            ratio="",
            spin_er_db="",
            gate_pass=False,
            status="error",
            note=f"{type(exc).__name__}: {exc}",
        )


def run_apcd_single_dimer_setup_only(
    config: APCDSingleDimerConfig,
    runtime: RuntimeConfig,
    lumapi: ModuleType,
    fsp_output: Union[str, Path],
) -> dict[str, object]:
    fdtd = None
    output_path = Path(fsp_output)
    try:
        fdtd = lumapi.FDTD(hide=runtime.hide_gui)
        _build_apcd_single_dimer_model(fdtd, config, incident_polarization="LCP")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        fdtd.save(str(output_path))
        return _result_row(
            config=config,
            matrix={},
            target_conversion="",
            opposite_spin_leakage="",
            ratio="",
            spin_er_db="",
            gate_pass="",
            status="setup_only",
            note=f"model saved to {output_path}; solver was not run",
        )
    except Exception as exc:
        return _result_row(
            config=config,
            matrix={},
            target_conversion="",
            opposite_spin_leakage="",
            ratio="",
            spin_er_db="",
            gate_pass=False,
            status="error",
            note=f"{type(exc).__name__}: {exc}",
        )
    finally:
        if fdtd is not None:
            try:
                fdtd.close()
            except Exception:
                pass


def _run_one_incidence(
    config: APCDSingleDimerConfig,
    runtime: RuntimeConfig,
    lumapi: ModuleType,
    incident_polarization: str,
) -> dict[str, complex]:
    fdtd = None
    try:
        fdtd = lumapi.FDTD(hide=runtime.hide_gui)
        _build_apcd_single_dimer_model(fdtd, config, incident_polarization)
        fdtd.run()
        transmission = _safe_float(fdtd.transmission("T"))
        ex = _center_value(_squeeze(fdtd.getdata("T_fields", "Ex")))
        ey = _center_value(_squeeze(fdtd.getdata("T_fields", "Ey")))
        e_r = (ex + 1j * ey) / math.sqrt(2)
        e_l = (ex - 1j * ey) / math.sqrt(2)
        return {"R": e_r, "L": e_l, "transmission": transmission}
    finally:
        if fdtd is not None:
            try:
                fdtd.close()
            except Exception:
                pass


def _build_apcd_single_dimer_model(
    fdtd: object,
    config: APCDSingleDimerConfig,
    incident_polarization: str,
) -> None:
    validate_apcd_single_dimer_geometry(config)

    nm = 1e-9
    geometry = config.geometry
    simulation = config.simulation
    period_x = geometry.period_x_nm * nm
    period_y = geometry.period_y_nm * nm
    height = geometry.height_nm * nm
    substrate_thickness = simulation.substrate_thickness_nm * nm
    wavelength = config.target.wavelength_nm * nm

    z_min = -substrate_thickness
    z_max = height + simulation.z_padding_above_nm * nm
    source_z = -simulation.source_offset_nm * nm
    monitor_z = height + simulation.monitor_offset_nm * nm

    fdtd.switchtolayout()
    fdtd.deleteall()

    fdtd.addfdtd()
    fdtd.set("dimension", "3D")
    fdtd.set("x span", period_x)
    fdtd.set("y span", period_y)
    fdtd.set("z min", z_min)
    fdtd.set("z max", z_max)
    fdtd.set("x min bc", "Periodic")
    fdtd.set("x max bc", "Periodic")
    fdtd.set("y min bc", "Periodic")
    fdtd.set("y max bc", "Periodic")
    fdtd.set("z min bc", "PML")
    fdtd.set("z max bc", "PML")
    fdtd.set("mesh accuracy", simulation.mesh_accuracy)
    fdtd.set("simulation time", simulation.simulation_time_fs * 1e-15)

    fdtd.addrect()
    fdtd.set("name", "substrate")
    fdtd.set("x span", period_x)
    fdtd.set("y span", period_y)
    fdtd.set("z min", z_min)
    fdtd.set("z max", 0)
    _set_material(fdtd, config.material, is_substrate=True)

    _add_nanopillar(fdtd, config, config.geometry.nanopillar_1, "nanopillar_1")
    _add_nanopillar(fdtd, config, config.geometry.nanopillar_2, "nanopillar_2")
    _add_circular_plane_wave_sources(fdtd, config, incident_polarization, period_x, period_y, source_z, wavelength)

    fdtd.addpower()
    fdtd.set("name", "T")
    fdtd.set("monitor type", "2D Z-normal")
    fdtd.set("x span", period_x)
    fdtd.set("y span", period_y)
    fdtd.set("z", monitor_z)

    fdtd.addprofile()
    fdtd.set("name", "T_fields")
    fdtd.set("monitor type", "2D Z-normal")
    fdtd.set("x span", period_x)
    fdtd.set("y span", period_y)
    fdtd.set("z", monitor_z)


def _add_nanopillar(
    fdtd: object,
    config: APCDSingleDimerConfig,
    pillar: APCDNanopillarConfig,
    name: str,
) -> None:
    nm = 1e-9
    fdtd.addrect()
    fdtd.set("name", name)
    fdtd.set("x", pillar.x_nm * nm)
    fdtd.set("y", pillar.y_nm * nm)
    fdtd.set("x span", pillar.length_nm * nm)
    fdtd.set("y span", pillar.width_nm * nm)
    fdtd.set("z min", 0)
    fdtd.set("z max", config.geometry.height_nm * nm)
    fdtd.set("first axis", "z")
    fdtd.set("rotation 1", pillar.rotation_deg)
    _set_material(fdtd, config.material, is_substrate=False)


def validate_apcd_single_dimer_geometry(config: APCDSingleDimerConfig) -> APCDGeometryValidation:
    geometry = config.geometry
    pillar_1 = geometry.nanopillar_1
    pillar_2 = geometry.nanopillar_2
    polygon_1 = _rotated_rectangle_corners_nm(pillar_1)
    polygon_2 = _rotated_rectangle_corners_nm(pillar_2)

    direct_gap_nm = _polygon_gap_nm(polygon_1, polygon_2)
    minimum_gap_nm = direct_gap_nm
    closest_pair = "nanopillar_1 to nanopillar_2"

    for x_shift in (-geometry.period_x_nm, 0, geometry.period_x_nm):
        for y_shift in (-geometry.period_y_nm, 0, geometry.period_y_nm):
            if x_shift == 0 and y_shift == 0:
                continue
            shifted_2 = [(x + x_shift, y + y_shift) for x, y in polygon_2]
            periodic_gap_nm = _polygon_gap_nm(polygon_1, shifted_2)
            if periodic_gap_nm < minimum_gap_nm:
                minimum_gap_nm = periodic_gap_nm
                closest_pair = f"nanopillar_1 to nanopillar_2 periodic image ({x_shift:g}, {y_shift:g}) nm"

    if minimum_gap_nm <= 0:
        raise ValueError(f"APCD dimer geometry overlaps: {closest_pair}")
    if minimum_gap_nm < geometry.minimum_gap_nm:
        raise ValueError(
            "APCD dimer geometry gap is too small: "
            f"{minimum_gap_nm:.3g} nm < {geometry.minimum_gap_nm:.3g} nm ({closest_pair})"
        )

    return APCDGeometryValidation(
        minimum_gap_nm=minimum_gap_nm,
        minimum_allowed_gap_nm=geometry.minimum_gap_nm,
        closest_pair=closest_pair,
    )


def _rotated_rectangle_corners_nm(pillar: APCDNanopillarConfig) -> list[tuple[float, float]]:
    angle = math.radians(pillar.rotation_deg)
    cos_angle = math.cos(angle)
    sin_angle = math.sin(angle)
    half_length = pillar.length_nm / 2
    half_width = pillar.width_nm / 2
    corners = []
    for local_x, local_y in (
        (-half_length, -half_width),
        (half_length, -half_width),
        (half_length, half_width),
        (-half_length, half_width),
    ):
        corners.append(
            (
                pillar.x_nm + local_x * cos_angle - local_y * sin_angle,
                pillar.y_nm + local_x * sin_angle + local_y * cos_angle,
            )
        )
    return corners


def _polygon_gap_nm(polygon_1: list[tuple[float, float]], polygon_2: list[tuple[float, float]]) -> float:
    if _polygons_overlap(polygon_1, polygon_2):
        return 0.0

    minimum = math.inf
    for index_1, point_1 in enumerate(polygon_1):
        next_1 = polygon_1[(index_1 + 1) % len(polygon_1)]
        for index_2, point_2 in enumerate(polygon_2):
            next_2 = polygon_2[(index_2 + 1) % len(polygon_2)]
            minimum = min(minimum, _segment_distance_nm(point_1, next_1, point_2, next_2))
    return float(minimum)


def _polygons_overlap(polygon_1: list[tuple[float, float]], polygon_2: list[tuple[float, float]]) -> bool:
    for polygon in (polygon_1, polygon_2):
        for index, point in enumerate(polygon):
            next_point = polygon[(index + 1) % len(polygon)]
            edge = (next_point[0] - point[0], next_point[1] - point[1])
            axis = (-edge[1], edge[0])
            axis_length = math.hypot(axis[0], axis[1])
            normalized_axis = (axis[0] / axis_length, axis[1] / axis_length)
            projection_1 = [_dot(point_1, normalized_axis) for point_1 in polygon_1]
            projection_2 = [_dot(point_2, normalized_axis) for point_2 in polygon_2]
            if max(projection_1) < min(projection_2) or max(projection_2) < min(projection_1):
                return False
    return True


def _segment_distance_nm(
    point_1: tuple[float, float],
    point_2: tuple[float, float],
    point_3: tuple[float, float],
    point_4: tuple[float, float],
) -> float:
    if _segments_intersect(point_1, point_2, point_3, point_4):
        return 0.0
    return min(
        _point_segment_distance_nm(point_1, point_3, point_4),
        _point_segment_distance_nm(point_2, point_3, point_4),
        _point_segment_distance_nm(point_3, point_1, point_2),
        _point_segment_distance_nm(point_4, point_1, point_2),
    )


def _segments_intersect(
    point_1: tuple[float, float],
    point_2: tuple[float, float],
    point_3: tuple[float, float],
    point_4: tuple[float, float],
) -> bool:
    orientation_1 = _orientation(point_1, point_2, point_3)
    orientation_2 = _orientation(point_1, point_2, point_4)
    orientation_3 = _orientation(point_3, point_4, point_1)
    orientation_4 = _orientation(point_3, point_4, point_2)
    return orientation_1 * orientation_2 <= 0 and orientation_3 * orientation_4 <= 0


def _point_segment_distance_nm(
    point: tuple[float, float],
    segment_start: tuple[float, float],
    segment_end: tuple[float, float],
) -> float:
    segment = (segment_end[0] - segment_start[0], segment_end[1] - segment_start[1])
    segment_length_sq = _dot(segment, segment)
    if segment_length_sq == 0:
        return math.hypot(point[0] - segment_start[0], point[1] - segment_start[1])
    offset = (point[0] - segment_start[0], point[1] - segment_start[1])
    t = max(0.0, min(1.0, _dot(offset, segment) / segment_length_sq))
    closest = (segment_start[0] + t * segment[0], segment_start[1] + t * segment[1])
    return math.hypot(point[0] - closest[0], point[1] - closest[1])


def _orientation(
    point_1: tuple[float, float],
    point_2: tuple[float, float],
    point_3: tuple[float, float],
) -> float:
    return (point_2[0] - point_1[0]) * (point_3[1] - point_1[1]) - (
        point_2[1] - point_1[1]
    ) * (point_3[0] - point_1[0])


def _dot(point_1: tuple[float, float], point_2: tuple[float, float]) -> float:
    return point_1[0] * point_2[0] + point_1[1] * point_2[1]


def _add_circular_plane_wave_sources(
    fdtd: object,
    config: APCDSingleDimerConfig,
    incident_polarization: str,
    x_span: float,
    y_span: float,
    z: float,
    wavelength: float,
) -> None:
    normalized = incident_polarization.lower()
    if normalized not in {"lcp", "rcp"}:
        raise ValueError(f"Unsupported incident polarization: {incident_polarization}")
    y_phase_deg = 90 if normalized == "lcp" else -90
    amplitude = 1 / math.sqrt(2)
    for name, polarization_angle, phase in (
        ("source_x", 0, 0),
        ("source_y", 90, y_phase_deg),
    ):
        fdtd.addplane()
        fdtd.set("name", name)
        fdtd.set("injection axis", "z")
        fdtd.set("direction", "Forward")
        fdtd.set("x span", x_span)
        fdtd.set("y span", y_span)
        fdtd.set("z", z)
        fdtd.set("wavelength start", wavelength)
        fdtd.set("wavelength stop", wavelength)
        fdtd.set("polarization angle", polarization_angle)
        fdtd.set("phase", phase)
        fdtd.set("amplitude", amplitude)


def _set_material(fdtd: object, material: APCDDimerMaterialConfig, is_substrate: bool) -> None:
    material_name = material.substrate_material_lumerical if is_substrate else material.meta_material_lumerical
    material_index = material.substrate_index if is_substrate else material.meta_index
    fdtd.set("material", material_name)
    if material_name == "<Object defined dielectric>" and material_index is not None:
        fdtd.set("index", material_index)


def _result_row(
    config: APCDSingleDimerConfig,
    matrix: dict[str, dict[str, complex]],
    target_conversion: object,
    opposite_spin_leakage: object,
    ratio: object,
    spin_er_db: object,
    gate_pass: object,
    status: str,
    note: str,
) -> dict[str, object]:
    return {
        "wavelength_nm": config.target.wavelength_nm,
        "period_x_nm": config.geometry.period_x_nm,
        "period_y_nm": config.geometry.period_y_nm,
        "height_nm": config.geometry.height_nm,
        "transmission_lcp": matrix.get("L", {}).get("transmission", ""),
        "transmission_rcp": matrix.get("R", {}).get("transmission", ""),
        "total_transmission": _mean_transmission(matrix),
        "T_R_from_L": _complex_text(matrix.get("L", {}).get("R", "")),
        "T_L_from_L": _complex_text(matrix.get("L", {}).get("L", "")),
        "T_R_from_R": _complex_text(matrix.get("R", {}).get("R", "")),
        "T_L_from_R": _complex_text(matrix.get("R", {}).get("L", "")),
        "target_conversion": target_conversion,
        "opposite_spin_leakage": opposite_spin_leakage,
        "conversion_to_leakage_ratio": ratio,
        "spin_ER_dB": spin_er_db,
        "gate_pass": gate_pass,
        "status": status,
        "note": note,
    }


def jones_matrix_circular_basis(row: dict[str, object]) -> list[list[complex]]:
    return [
        [_parse_complex(row["T_R_from_L"]), _parse_complex(row["T_R_from_R"])],
        [_parse_complex(row["T_L_from_L"]), _parse_complex(row["T_L_from_R"])],
    ]


def write_apcd_single_dimer_results(row: dict[str, object], output_path: Union[str, Path]) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=APCD_DIMER_RESULT_FIELDS)
        writer.writeheader()
        writer.writerow(row)
    return path


def write_apcd_single_dimer_summary(row: dict[str, object], output_path: Union[str, Path]) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# APCD Single Dimer 633 nm Gate 1 Summary",
        "",
        f"- status: {row['status']}",
        f"- target_conversion: {row['target_conversion']}",
        f"- opposite_spin_leakage: {row['opposite_spin_leakage']}",
        f"- conversion_to_leakage_ratio: {row['conversion_to_leakage_ratio']}",
        f"- spin_ER_dB: {row['spin_ER_dB']}",
        f"- total_transmission: {row['total_transmission']}",
        f"- gate_pass: {row['gate_pass']}",
        f"- note: {row['note']}",
        "",
        "Acceptance criteria:",
        "",
        "- spin_ER_dB > 8 dB; or",
        "- target_conversion / opposite_spin_leakage > 6.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_jones_matrix_npy(row: dict[str, object], output_path: Union[str, Path]) -> Path:
    import numpy as np

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    matrix = np.array(jones_matrix_circular_basis(row), dtype=np.complex128)
    np.save(path, matrix)
    return path


def _complex_text(value: object) -> str:
    if value == "":
        return ""
    number = complex(value)  # type: ignore[arg-type]
    return f"{number.real:.16g}{number.imag:+.16g}j"


def _mean_transmission(matrix: dict[str, dict[str, object]]) -> object:
    transmissions = [
        float(values["transmission"])
        for values in matrix.values()
        if values.get("transmission", "") != ""
    ]
    if not transmissions:
        return ""
    return sum(transmissions) / len(transmissions)


def _safe_float(value: object) -> object:
    try:
        if hasattr(value, "item"):
            return value.item()
        return float(value)
    except Exception:
        return value


def _parse_complex(value: object) -> complex:
    if value == "":
        return 0 + 0j
    return complex(str(value))


def _squeeze(value: object) -> object:
    if hasattr(value, "squeeze"):
        return value.squeeze()
    while isinstance(value, (list, tuple)) and len(value) == 1:
        value = value[0]
    return value


def _shape_of(value: object) -> tuple[int, ...]:
    if hasattr(value, "shape"):
        return tuple(int(size) for size in value.shape if int(size) != 1)
    if isinstance(value, (list, tuple)):
        if not value:
            return (0,)
        return (len(value),) + _shape_of(value[0])
    return ()


def _center_value(value: object) -> complex:
    squeezed = _squeeze(value)
    shape = _shape_of(squeezed)
    if not shape:
        return complex(squeezed)  # type: ignore[arg-type]
    current = squeezed
    for axis_size in shape:
        current = current[axis_size // 2]  # type: ignore[index]
    return complex(current)  # type: ignore[arg-type]
