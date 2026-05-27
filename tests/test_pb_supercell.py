from __future__ import annotations

import csv
import math
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.config import RuntimeConfig, load_pb_supercell_config
from metasurface.pb_supercell import (
    PB_SUPERCELL_FIELDS,
    PBSupercellRunner,
    run_pb_supercell_lumerical,
    write_pb_supercell_summary,
)


def test_load_pb_supercell_config() -> None:
    config = load_pb_supercell_config(REPO_ROOT / "configs" / "pb_supercell_L205_W70_H450.yaml")

    assert config.project.stage == "p3_pb_supercell_L205_W70_H450"
    assert config.target.incident_polarization == "LCP"
    assert config.target.output_polarization == "RCP"
    assert config.target.target_order == "+1"
    assert config.geometry.atoms == 8
    assert config.geometry.atom_period_nm == 220
    assert config.geometry.length_nm == 205
    assert config.geometry.width_nm == 70
    assert config.geometry.height_nm == 450
    assert config.geometry.rotation_step_deg == 22.5


def test_pb_supercell_dry_run_does_not_import_lumapi(tmp_path: Path) -> None:
    sys.modules.pop("lumapi", None)
    config = load_pb_supercell_config(REPO_ROOT / "configs" / "pb_supercell_L205_W70_H450.yaml")

    rows = PBSupercellRunner.from_runtime_file(config=config, runtime_path=None, dry_run=True).run()
    written_path = write_pb_supercell_summary(rows, tmp_path / "pb_supercell_summary.csv")

    assert "lumapi" not in sys.modules
    assert rows[0]["status"] == "dry_run"
    assert rows[0]["supercell_period_nm"] == 1760
    assert math.isclose(rows[0]["target_angle_deg"], math.degrees(math.asin(450 / 1760)))

    with written_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded_rows = list(reader)

    assert reader.fieldnames == PB_SUPERCELL_FIELDS
    assert loaded_rows[0]["target_order"] == "+1"


def test_pb_supercell_setup_only_builds_rotated_atoms_and_circular_sources(tmp_path: Path) -> None:
    config = load_pb_supercell_config(REPO_ROOT / "configs" / "pb_supercell_L205_W70_H450.yaml")
    runtime = RuntimeConfig(mode="test", enable_lumerical=True, lumapi_python_api_dir="", hide_gui=True)
    fsp_output = tmp_path / "pb_supercell.fsp"
    lumapi = _FakeLumapi()

    row = run_pb_supercell_lumerical(
        config=config,
        runtime=runtime,
        lumapi=lumapi,
        setup_only=True,
        fsp_output=fsp_output,
    )

    assert row["status"] == "setup_only"
    assert lumapi.fdtd.run_called is False
    assert lumapi.fdtd.saved_path == str(fsp_output)
    assert lumapi.fdtd.addrect_count == 8
    assert lumapi.fdtd.addplane_count == 2
    assert lumapi.fdtd.rotations == [index * 22.5 for index in range(8)]
    assert lumapi.fdtd.source_phases == [0, 90]
    assert lumapi.fdtd.source_amplitudes == [0.7071067811865475, 0.7071067811865475]
    assert "farfieldfilter(1);" in lumapi.fdtd.eval_commands


def test_pb_supercell_extracts_plus_one_total_order_efficiency(tmp_path: Path) -> None:
    config = load_pb_supercell_config(REPO_ROOT / "configs" / "pb_supercell_L205_W70_H450.yaml")
    runtime = RuntimeConfig(mode="test", enable_lumerical=True, lumapi_python_api_dir="", hide_gui=True)
    lumapi = _FakeLumapi()

    row = run_pb_supercell_lumerical(
        config=config,
        runtime=runtime,
        lumapi=lumapi,
        load_fsp=tmp_path / "solved_pb_supercell.fsp",
        extract_only=True,
    )

    assert row["status"] == "ok"
    assert row["transmission"] == 0.8
    assert row["order_efficiency_total"] == 0.4
    assert math.isclose(row["order_efficiency_rcp_estimate"], 0.4)
    assert row["order_efficiency_lcp_estimate"] == 0.0
    assert "gratingpolar Etheta +/- i*Ephi" in str(row["note"])


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
        self.addrect_count = 0
        self.addplane_count = 0
        self.rotations: list[float] = []
        self.source_phases: list[float] = []
        self.source_amplitudes: list[float] = []
        self.eval_commands: list[str] = []
        self._current_object = ""

    def switchtolayout(self) -> None:
        pass

    def deleteall(self) -> None:
        pass

    def addfdtd(self) -> None:
        self._current_object = "fdtd"

    def addrect(self) -> None:
        self.addrect_count += 1
        self._current_object = "rect"

    def addplane(self) -> None:
        self.addplane_count += 1
        self._current_object = "plane"

    def addpower(self) -> None:
        self._current_object = "power"

    def set(self, name: str, value: object) -> None:
        if self._current_object == "rect" and name == "rotation 1":
            self.rotations.append(float(value))
        if self._current_object == "plane" and name == "phase":
            self.source_phases.append(float(value))
        if self._current_object == "plane" and name == "amplitude":
            self.source_amplitudes.append(float(value))

    def eval(self, command: str) -> None:
        self.eval_commands.append(command)

    def save(self, path: str) -> None:
        self.saved_path = path

    def load(self, path: str) -> None:
        self.loaded_path = path

    def run(self) -> None:
        self.run_called = True

    def transmission(self, _name: str) -> float:
        return 0.8

    def grating(self, _name: str) -> list[float]:
        return [0.1, 0.5, 0.4]

    def gratingn(self, _name: str) -> list[int]:
        return [-1, 1, 0]

    def gratingm(self, _name: str) -> list[int]:
        return 0

    def gratingpolar(self, _name: str) -> list[list[list[complex]]]:
        return [
            [[0j, 0j, 0j]],
            [[0j, 0.5 + 0j, -0.5j]],
            [[0j, 0j, 0j]],
        ]

    def close(self) -> None:
        pass
