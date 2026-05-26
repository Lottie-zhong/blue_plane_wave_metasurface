from __future__ import annotations

import csv
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.config import RuntimeConfig, load_nanofin_single_config
from metasurface.nanofin_single import (
    SINGLE_NANOFIN_FIELDS,
    SingleNanofinRunner,
    run_single_nanofin_lumerical,
    write_single_nanofin_summary,
)


def test_load_nanofin_single_config() -> None:
    config = load_nanofin_single_config(REPO_ROOT / "configs" / "nanofin_single.yaml")

    assert config.project.stage == "p1_single_nanofin"
    assert config.target.wavelength_nm == 450
    assert config.target.incident_polarization == "x"
    assert config.material.metasurface == "TiO2"
    assert config.material.metasurface_index == 2.5
    assert config.geometry.period_nm == 220
    assert config.geometry.length_nm == 160
    assert config.geometry.width_nm == 80
    assert config.geometry.height_nm == 350
    assert config.far_field.projection_direction == "auto"
    assert config.far_field.material_index == "auto"
    assert config.far_field.far_field_filter == 1
    assert config.far_field.resolution_2d == 1001
    assert config.far_field.resolution_3d == 1001
    assert config.far_field.assume_structure_is_periodic is False
    assert config.far_field.override_near_field_mesh is False


def test_nanofin_single_dry_run_does_not_import_lumapi(tmp_path: Path) -> None:
    sys.modules.pop("lumapi", None)
    config = load_nanofin_single_config(REPO_ROOT / "configs" / "nanofin_single.yaml")

    rows = SingleNanofinRunner.from_runtime_file(config=config, runtime_path=None, dry_run=True).run()
    written_path = write_single_nanofin_summary(rows, tmp_path / "single_nanofin_summary.csv")

    assert "lumapi" not in sys.modules
    assert len(rows) == 1
    assert rows[0]["status"] == "dry_run"
    assert rows[0]["height_nm"] == 350

    with written_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded_rows = list(reader)

    assert reader.fieldnames == SINGLE_NANOFIN_FIELDS
    assert loaded_rows[0]["period_nm"] == "220"
    assert loaded_rows[0]["transmission"] == ""
    assert loaded_rows[0]["farfield_peak"] == ""


def test_nanofin_setup_only_saves_model_without_run(tmp_path: Path) -> None:
    config = load_nanofin_single_config(REPO_ROOT / "configs" / "nanofin_single.yaml")
    runtime = RuntimeConfig(mode="test", enable_lumerical=True, lumapi_python_api_dir="", hide_gui=True)
    fsp_output = tmp_path / "single_nanofin.fsp"
    lumapi = _FakeLumapi()

    row = run_single_nanofin_lumerical(
        config=config,
        runtime=runtime,
        lumapi=lumapi,
        setup_only=True,
        fsp_output=fsp_output,
    )

    assert row["status"] == "setup_only"
    assert "solver was not run" in str(row["note"])
    assert lumapi.fdtd.run_called is False
    assert lumapi.fdtd.saved_path == str(fsp_output)
    assert "farfieldfilter(1);" in lumapi.fdtd.eval_commands
    assert 'farfieldsettings("far field filter",1);' in lumapi.fdtd.eval_commands
    assert 'farfieldsettings("override near field mesh",0);' in lumapi.fdtd.eval_commands
    assert 'farfieldsettings("near field samples per wavelength",4);' in lumapi.fdtd.eval_commands


def test_nanofin_extract_only_loads_fsp_without_run(tmp_path: Path) -> None:
    config = load_nanofin_single_config(REPO_ROOT / "configs" / "nanofin_single.yaml")
    runtime = RuntimeConfig(mode="test", enable_lumerical=True, lumapi_python_api_dir="", hide_gui=True)
    fsp_input = tmp_path / "solved_single_nanofin.fsp"
    lumapi = _FakeLumapi()

    row = run_single_nanofin_lumerical(
        config=config,
        runtime=runtime,
        lumapi=lumapi,
        load_fsp=fsp_input,
        extract_only=True,
    )

    assert row["status"] == "ok"
    assert row["transmission"] == 0.75
    assert row["phase_rad"] == 0.0
    assert row["farfield_peak"] == 3.0
    assert row["farfield_shape"] == "2x2"
    assert lumapi.fdtd.loaded_path == str(fsp_input)
    assert lumapi.fdtd.run_called is False
    assert lumapi.fdtd.farfield_args == ("T", 1, 1001, 1001, 1, 1, 1, 0, 1)


class _FakeLumapi:
    def __init__(self) -> None:
        self.fdtd = _FakeFDTD()

    def FDTD(self, hide: bool) -> "_FakeFDTD":
        self.fdtd.hide = hide
        return self.fdtd


class _FakeFDTD:
    def __init__(self) -> None:
        self.hide = False
        self.run_called = False
        self.saved_path = ""
        self.loaded_path = ""
        self.farfield_args: tuple[object, ...] = ()
        self.eval_commands: list[str] = []

    def switchtolayout(self) -> None:
        pass

    def deleteall(self) -> None:
        pass

    def addfdtd(self) -> None:
        pass

    def addrect(self) -> None:
        pass

    def addplane(self) -> None:
        pass

    def addpower(self) -> None:
        pass

    def addprofile(self) -> None:
        pass

    def set(self, _name: str, _value: object) -> None:
        pass

    def eval(self, command: str) -> None:
        self.eval_commands.append(command)

    def save(self, path: str) -> None:
        self.saved_path = path

    def load(self, path: str) -> None:
        self.loaded_path = path

    def run(self) -> None:
        self.run_called = True

    def transmission(self, _name: str) -> float:
        return 0.75

    def getdata(self, _name: str, data_name: str) -> object:
        if data_name == "Ex":
            return [[1 + 0j]]
        if data_name == "Ey":
            return [[0 + 1j]]
        raise KeyError(data_name)

    def farfield3d(self, *args: object) -> list[list[float]]:
        self.farfield_args = args
        return [[1.0, float("nan")], [3.0, 0.5]]

    def close(self) -> None:
        pass
