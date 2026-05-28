from __future__ import annotations

from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Union

import yaml


@dataclass(frozen=True)
class ProjectConfig:
    name: str
    stage: str


@dataclass(frozen=True)
class TargetConfig:
    wavelength_nm: float
    incident_wave: str
    incident_polarization: str
    output_polarization: str
    deflection_angle_deg: float
    target_order: str


@dataclass(frozen=True)
class MaterialConfig:
    metasurface: str
    metasurface_index: float | None = None


@dataclass(frozen=True)
class GeometryConfig:
    supercell_atoms: int
    atom_period_nm: float
    supercell_period_um: float


@dataclass(frozen=True)
class NanofinGeometryConfig:
    period_nm: float
    length_nm: float
    width_nm: float
    height_nm: float
    rotation_deg: float


@dataclass(frozen=True)
class PBSupercellGeometryConfig:
    atom_period_nm: float
    atoms: int
    length_nm: float
    width_nm: float
    height_nm: float
    rotation_start_deg: float
    rotation_step_deg: float


@dataclass(frozen=True)
class APCDNanopillarConfig:
    length_nm: float
    width_nm: float
    x_nm: float
    y_nm: float
    rotation_deg: float


@dataclass(frozen=True)
class APCDDimerGeometryConfig:
    period_x_nm: float
    period_y_nm: float
    height_nm: float
    nanopillar_1: APCDNanopillarConfig
    nanopillar_2: APCDNanopillarConfig
    dimer_center_distance_um: float | None = None
    minimum_gap_nm: float = 5.0


@dataclass(frozen=True)
class APCDDimerMaterialConfig:
    substrate: str
    meta_material: str
    substrate_material_lumerical: str
    meta_material_lumerical: str
    substrate_index: float | None = None
    meta_index: float | None = None


@dataclass(frozen=True)
class APCDDimerTargetConfig:
    wavelength_nm: float
    incident_wave: str
    output_basis: str
    eps: float
    spin_er_threshold_db: float
    conversion_to_leakage_threshold: float


@dataclass(frozen=True)
class APCDDimerSimulationConfig:
    substrate_thickness_nm: float
    source_offset_nm: float
    monitor_offset_nm: float
    z_padding_above_nm: float
    mesh_accuracy: int
    simulation_time_fs: float


@dataclass(frozen=True)
class FarFieldConfig:
    projection_direction: str
    material_index: str
    far_field_filter: int
    resolution_2d: int
    resolution_3d: int
    assume_structure_is_periodic: bool
    illumination: str
    override_near_field_mesh: bool
    near_field_samples_per_wavelength: int


@dataclass(frozen=True)
class PhaseDesignConfig:
    method: str
    phase_step_rad: float
    rotation_step_deg: float


@dataclass(frozen=True)
class ThicknessSweepConfig:
    h_min_nm: int
    h_max_nm: int
    h_step_nm: int
    h_initial_nm: int


@dataclass(frozen=True)
class OutputConfig:
    result_dir: Path


@dataclass(frozen=True)
class RuntimeConfig:
    mode: str
    enable_lumerical: bool
    lumapi_python_api_dir: str
    hide_gui: bool


@dataclass(frozen=True)
class PlaneWaveSweepConfig:
    project: ProjectConfig
    target: TargetConfig
    material: MaterialConfig
    geometry: GeometryConfig
    phase_design: PhaseDesignConfig
    thickness_sweep: ThicknessSweepConfig
    output: OutputConfig


@dataclass(frozen=True)
class NanofinSingleConfig:
    project: ProjectConfig
    target: TargetConfig
    material: MaterialConfig
    geometry: NanofinGeometryConfig
    far_field: FarFieldConfig
    output: OutputConfig


@dataclass(frozen=True)
class PBSupercellConfig:
    project: ProjectConfig
    target: TargetConfig
    material: MaterialConfig
    geometry: PBSupercellGeometryConfig
    far_field: FarFieldConfig
    output: OutputConfig


@dataclass(frozen=True)
class APCDSingleDimerConfig:
    project: ProjectConfig
    target: APCDDimerTargetConfig
    material: APCDDimerMaterialConfig
    geometry: APCDDimerGeometryConfig
    simulation: APCDDimerSimulationConfig
    output: OutputConfig


def load_sweep_config(path: Union[str, Path]) -> PlaneWaveSweepConfig:
    data = _read_yaml_mapping(path)
    return PlaneWaveSweepConfig(
        project=ProjectConfig(**_required_mapping(data, "project")),
        target=TargetConfig(**_required_mapping(data, "target")),
        material=MaterialConfig(**_required_mapping(data, "material")),
        geometry=GeometryConfig(**_required_mapping(data, "geometry")),
        phase_design=PhaseDesignConfig(**_required_mapping(data, "phase_design")),
        thickness_sweep=ThicknessSweepConfig(**_required_mapping(data, "thickness_sweep")),
        output=OutputConfig(result_dir=Path(_required_mapping(data, "output")["result_dir"])),
    )


def load_nanofin_single_config(path: Union[str, Path]) -> NanofinSingleConfig:
    data = _read_yaml_mapping(path)
    return NanofinSingleConfig(
        project=ProjectConfig(**_required_mapping(data, "project")),
        target=TargetConfig(**_required_mapping(data, "target")),
        material=MaterialConfig(**_required_mapping(data, "material")),
        geometry=NanofinGeometryConfig(**_required_mapping(data, "geometry")),
        far_field=FarFieldConfig(**_required_mapping(data, "far_field")),
        output=OutputConfig(result_dir=Path(_required_mapping(data, "output")["result_dir"])),
    )


def load_pb_supercell_config(path: Union[str, Path]) -> PBSupercellConfig:
    data = _read_yaml_mapping(path)
    return PBSupercellConfig(
        project=ProjectConfig(**_required_mapping(data, "project")),
        target=TargetConfig(**_required_mapping(data, "target")),
        material=MaterialConfig(**_required_mapping(data, "material")),
        geometry=PBSupercellGeometryConfig(**_required_mapping(data, "geometry")),
        far_field=FarFieldConfig(**_required_mapping(data, "far_field")),
        output=OutputConfig(result_dir=Path(_required_mapping(data, "output")["result_dir"])),
    )


def load_apcd_single_dimer_config(path: Union[str, Path]) -> APCDSingleDimerConfig:
    data = _read_yaml_mapping(path)
    geometry_data = _required_mapping(data, "geometry")
    nanopillar_1 = APCDNanopillarConfig(**_required_mapping(geometry_data, "nanopillar_1"))
    nanopillar_2 = APCDNanopillarConfig(**_required_mapping(geometry_data, "nanopillar_2"))
    dimer_center_distance_um = geometry_data.get("dimer_center_distance_um")
    if dimer_center_distance_um is not None:
        half_distance_nm = float(dimer_center_distance_um) * 1000 / 2
        nanopillar_1 = replace(nanopillar_1, x_nm=-half_distance_nm)
        nanopillar_2 = replace(nanopillar_2, x_nm=half_distance_nm)
    geometry = APCDDimerGeometryConfig(
        period_x_nm=float(geometry_data["period_x_nm"]),
        period_y_nm=float(geometry_data["period_y_nm"]),
        height_nm=float(geometry_data["height_nm"]),
        nanopillar_1=nanopillar_1,
        nanopillar_2=nanopillar_2,
        dimer_center_distance_um=(
            None if dimer_center_distance_um is None else float(dimer_center_distance_um)
        ),
        minimum_gap_nm=float(geometry_data.get("minimum_gap_nm", 5.0)),
    )
    return APCDSingleDimerConfig(
        project=ProjectConfig(**_required_mapping(data, "project")),
        target=APCDDimerTargetConfig(**_required_mapping(data, "target")),
        material=APCDDimerMaterialConfig(**_required_mapping(data, "material")),
        geometry=geometry,
        simulation=APCDDimerSimulationConfig(**_required_mapping(data, "simulation")),
        output=OutputConfig(result_dir=Path(_required_mapping(data, "output")["result_dir"])),
    )


def load_runtime_config(path: Union[str, Path]) -> RuntimeConfig:
    data = _read_yaml_mapping(path)
    runtime = _required_mapping(data, "runtime")
    lumapi = _required_mapping(data, "lumapi")
    return RuntimeConfig(
        mode=str(runtime.get("mode", "")),
        enable_lumerical=bool(runtime.get("enable_lumerical", False)),
        lumapi_python_api_dir=str(lumapi.get("python_api_dir", "")),
        hide_gui=bool(lumapi.get("hide_gui", True)),
    )


def _read_yaml_mapping(path: Union[str, Path]) -> dict[str, Any]:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Config file must contain a YAML mapping: {config_path}")
    return data


def _required_mapping(data: dict[str, Any], key: str) -> dict[str, Any]:
    value = data.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"Missing required mapping section: {key}")
    return value
