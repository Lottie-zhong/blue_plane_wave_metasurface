from __future__ import annotations

from dataclasses import dataclass
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
