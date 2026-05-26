from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType
from typing import Optional, Union

from metasurface.config import NanofinSingleConfig, RuntimeConfig, load_runtime_config
from metasurface.lumapi_runner import import_lumapi


SINGLE_NANOFIN_FIELDS = [
    "wavelength_nm",
    "period_nm",
    "length_nm",
    "width_nm",
    "height_nm",
    "rotation_deg",
    "incident_polarization",
    "transmission",
    "phase_rad",
    "status",
    "note",
]


@dataclass(frozen=True)
class SingleNanofinRunner:
    config: NanofinSingleConfig
    dry_run: bool = False
    runtime: Optional[RuntimeConfig] = None
    setup_only: bool = False
    fsp_output: Optional[Path] = None

    @classmethod
    def from_runtime_file(
        cls,
        config: NanofinSingleConfig,
        runtime_path: Optional[Union[str, Path]],
        dry_run: bool,
        setup_only: bool = False,
        fsp_output: Optional[Union[str, Path]] = None,
    ) -> "SingleNanofinRunner":
        runtime = None if dry_run or runtime_path is None else load_runtime_config(runtime_path)
        output_path = None if fsp_output is None else Path(fsp_output)
        return cls(
            config=config,
            dry_run=dry_run,
            runtime=runtime,
            setup_only=setup_only,
            fsp_output=output_path,
        )

    def run(self) -> list[dict[str, object]]:
        if self.dry_run:
            return [build_single_nanofin_dry_run_row(self.config)]

        if self.runtime is None:
            raise ValueError("A runtime config is required when dry_run is False")
        if not self.runtime.enable_lumerical:
            raise RuntimeError("runtime.enable_lumerical is false; use --dry-run or update runtime.yaml")

        lumapi = import_lumapi(self.runtime)
        return [
            run_single_nanofin_lumerical(
                self.config,
                self.runtime,
                lumapi,
                setup_only=self.setup_only,
                fsp_output=self.fsp_output,
            )
        ]


def build_single_nanofin_dry_run_row(config: NanofinSingleConfig) -> dict[str, object]:
    geometry = config.geometry
    return {
        "wavelength_nm": config.target.wavelength_nm,
        "period_nm": geometry.period_nm,
        "length_nm": geometry.length_nm,
        "width_nm": geometry.width_nm,
        "height_nm": geometry.height_nm,
        "rotation_deg": geometry.rotation_deg,
        "incident_polarization": config.target.incident_polarization,
        "transmission": "",
        "phase_rad": "",
        "status": "dry_run",
        "note": "single nanofin setup only; lumapi was not imported",
    }


def run_single_nanofin_lumerical(
    config: NanofinSingleConfig,
    runtime: RuntimeConfig,
    lumapi: ModuleType,
    setup_only: bool = False,
    fsp_output: Optional[Path] = None,
) -> dict[str, object]:
    geometry = config.geometry
    note = ""
    transmission: object = ""
    phase_rad: object = ""
    status = "error"

    fdtd = None
    try:
        fdtd = lumapi.FDTD(hide=runtime.hide_gui)
        _build_single_nanofin_model(fdtd, config)
        if setup_only:
            if fsp_output is not None:
                fsp_output.parent.mkdir(parents=True, exist_ok=True)
                fdtd.save(str(fsp_output))
                note = f"model saved to {fsp_output}; solver was not run"
            else:
                note = "model built; solver was not run"
            status = "setup_only"
        else:
            fdtd.run()
            transmission = _safe_float(fdtd.transmission("T"))
            phase_rad = _extract_center_phase_rad(fdtd, "phase_monitor", config.target.incident_polarization)
            status = "ok"
    except Exception as exc:  # Lumerical exceptions vary by installation.
        note = f"{type(exc).__name__}: {exc}"
    finally:
        if fdtd is not None:
            try:
                fdtd.close()
            except Exception:
                pass

    return {
        "wavelength_nm": config.target.wavelength_nm,
        "period_nm": geometry.period_nm,
        "length_nm": geometry.length_nm,
        "width_nm": geometry.width_nm,
        "height_nm": geometry.height_nm,
        "rotation_deg": geometry.rotation_deg,
        "incident_polarization": config.target.incident_polarization,
        "transmission": transmission,
        "phase_rad": phase_rad,
        "status": status,
        "note": note,
    }


def _build_single_nanofin_model(fdtd: object, config: NanofinSingleConfig) -> None:
    geometry = config.geometry
    nm = 1e-9
    period = geometry.period_nm * nm
    length = geometry.length_nm * nm
    width = geometry.width_nm * nm
    height = geometry.height_nm * nm
    wavelength = config.target.wavelength_nm * nm

    z_min = -500 * nm
    z_max = height + 700 * nm
    source_z = -250 * nm
    monitor_z = height + 350 * nm

    fdtd.switchtolayout()
    fdtd.deleteall()

    fdtd.addfdtd()
    fdtd.set("dimension", "3D")
    fdtd.set("x span", period)
    fdtd.set("y span", period)
    fdtd.set("z min", z_min)
    fdtd.set("z max", z_max)
    fdtd.set("x min bc", "Periodic")
    fdtd.set("x max bc", "Periodic")
    fdtd.set("y min bc", "Periodic")
    fdtd.set("y max bc", "Periodic")
    fdtd.set("z min bc", "PML")
    fdtd.set("z max bc", "PML")
    fdtd.set("mesh accuracy", 2)
    fdtd.set("simulation time", 1000e-15)

    fdtd.addrect()
    fdtd.set("name", "nanofin")
    fdtd.set("x span", length)
    fdtd.set("y span", width)
    fdtd.set("z min", 0)
    fdtd.set("z max", height)
    if geometry.rotation_deg:
        fdtd.set("first axis", "z")
        fdtd.set("rotation 1", geometry.rotation_deg)
    _set_nanofin_material(fdtd, config)

    fdtd.addplane()
    fdtd.set("name", "source")
    fdtd.set("injection axis", "z")
    fdtd.set("direction", "Forward")
    fdtd.set("x span", period)
    fdtd.set("y span", period)
    fdtd.set("z", source_z)
    fdtd.set("wavelength start", wavelength)
    fdtd.set("wavelength stop", wavelength)
    fdtd.set("polarization angle", _polarization_angle_deg(config.target.incident_polarization))

    fdtd.addpower()
    fdtd.set("name", "T")
    fdtd.set("monitor type", "2D Z-normal")
    fdtd.set("x span", period)
    fdtd.set("y span", period)
    fdtd.set("z", monitor_z)

    fdtd.addprofile()
    fdtd.set("name", "phase_monitor")
    fdtd.set("monitor type", "2D Z-normal")
    fdtd.set("x span", period)
    fdtd.set("y span", period)
    fdtd.set("z", monitor_z)


def _polarization_angle_deg(polarization: str) -> float:
    normalized = polarization.lower()
    if normalized in {"x", "x_pol", "x-polarized"}:
        return 0.0
    if normalized in {"y", "y_pol", "y-polarized"}:
        return 90.0
    raise ValueError(f"Unsupported single-nanofin polarization: {polarization}")


def _set_nanofin_material(fdtd: object, config: NanofinSingleConfig) -> None:
    if config.material.metasurface_index is not None:
        fdtd.set("material", "<Object defined dielectric>")
        fdtd.set("index", config.material.metasurface_index)
        return
    fdtd.set("material", config.material.metasurface)


def _extract_center_phase_rad(fdtd: object, monitor_name: str, polarization: str) -> float:
    import numpy as np

    result = fdtd.getresult(monitor_name, "E")
    key = "Ex" if _polarization_angle_deg(polarization) == 0 else "Ey"
    field = np.asarray(result[key]).squeeze()
    center = tuple(axis_size // 2 for axis_size in field.shape)
    return float(np.angle(field[center]))


def _safe_float(value: object) -> object:
    import numpy as np

    try:
        if hasattr(value, "item"):
            return value.item()
        array = np.asarray(value).squeeze()
        if array.size == 1:
            return float(array.item())
        return float(np.mean(array))
    except Exception:
        return value


def write_single_nanofin_summary(rows: list[dict[str, object]], output_path: Union[str, Path]) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SINGLE_NANOFIN_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    return path
