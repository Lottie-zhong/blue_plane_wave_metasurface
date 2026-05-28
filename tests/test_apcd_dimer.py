from __future__ import annotations

import csv
import math
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_dimer import (
    APCD_DIMER_RESULT_FIELDS,
    APCDSingleDimerRunner,
    run_apcd_single_dimer_lumerical,
    run_apcd_single_dimer_setup_only,
    write_apcd_single_dimer_results,
    write_apcd_single_dimer_summary,
)
from metasurface.config import RuntimeConfig, load_apcd_single_dimer_config


def test_load_apcd_single_dimer_config() -> None:
    config = load_apcd_single_dimer_config(REPO_ROOT / "configs" / "apcd_single_dimer_633nm.yaml")

    assert config.project.stage == "gate1_single_apcd_dimer_633nm"
    assert config.target.wavelength_nm == 633
    assert config.material.substrate == "Al2O3"
    assert config.material.meta_material == "c-Si"
    assert config.geometry.period_x_nm == 340
    assert config.geometry.period_y_nm == 340
    assert config.geometry.height_nm == 300
    assert config.geometry.nanopillar_1.length_nm == 130
    assert config.geometry.nanopillar_1.width_nm == 70
    assert config.geometry.nanopillar_1.rotation_deg == 45
    assert config.geometry.nanopillar_2.length_nm == 150
    assert config.geometry.nanopillar_2.width_nm == 85
    assert config.geometry.nanopillar_2.rotation_deg == -45


def test_apcd_single_dimer_dry_run_does_not_import_lumapi(tmp_path: Path) -> None:
    sys.modules.pop("lumapi", None)
    config = load_apcd_single_dimer_config(REPO_ROOT / "configs" / "apcd_single_dimer_633nm.yaml")

    row = APCDSingleDimerRunner.from_runtime_file(config=config, runtime_path=None, dry_run=True).run()
    results_path = write_apcd_single_dimer_results(row, tmp_path / "results.csv")
    summary_path = write_apcd_single_dimer_summary(row, tmp_path / "summary.md")

    assert "lumapi" not in sys.modules
    assert row["status"] == "dry_run"
    assert row["gate_pass"] == ""
    with results_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded_rows = list(reader)
    assert reader.fieldnames == APCD_DIMER_RESULT_FIELDS
    assert loaded_rows[0]["wavelength_nm"] == "633"
    assert "Acceptance criteria" in summary_path.read_text(encoding="utf-8")


def test_apcd_single_dimer_lumerical_extracts_circular_matrix() -> None:
    config = load_apcd_single_dimer_config(REPO_ROOT / "configs" / "apcd_single_dimer_633nm.yaml")
    runtime = RuntimeConfig(mode="test", enable_lumerical=True, lumapi_python_api_dir="", hide_gui=True)
    lumapi = _FakeLumapi()

    row = run_apcd_single_dimer_lumerical(config=config, runtime=runtime, lumapi=lumapi)

    assert row["status"] == "ok"
    assert math.isclose(float(row["target_conversion"]), 1.0)
    assert math.isclose(float(row["opposite_spin_leakage"]), 0.0)
    assert float(row["spin_ER_dB"]) > 8
    assert row["gate_pass"] is True
    assert math.isclose(float(row["total_transmission"]), 0.5)
    assert len(lumapi.fdtds) == 2
    assert lumapi.fdtds[0].source_phases == [0, 90]
    assert lumapi.fdtds[1].source_phases == [0, -90]
    assert lumapi.fdtds[0].rotations == [45, -45]


def test_apcd_single_dimer_setup_only_saves_fsp_without_run(tmp_path: Path) -> None:
    config = load_apcd_single_dimer_config(REPO_ROOT / "configs" / "apcd_single_dimer_633nm.yaml")
    runtime = RuntimeConfig(mode="test", enable_lumerical=True, lumapi_python_api_dir="", hide_gui=True)
    lumapi = _FakeLumapi()
    fsp_output = tmp_path / "apcd_single_dimer_633nm_setup.fsp"

    row = run_apcd_single_dimer_setup_only(
        config=config,
        runtime=runtime,
        lumapi=lumapi,
        fsp_output=fsp_output,
    )

    assert row["status"] == "setup_only"
    assert "solver was not run" in str(row["note"])
    assert lumapi.fdtds[0].saved_path == str(fsp_output)
    assert lumapi.fdtds[0].run_called is False
    assert lumapi.fdtds[0].getdata_called is False
    assert lumapi.fdtds[0].source_phases == [0, 90]


class _FakeLumapi:
    def __init__(self) -> None:
        self.fdtds: list[_FakeFDTD] = []

    def FDTD(self, hide: bool) -> "_FakeFDTD":
        fdtd = _FakeFDTD()
        fdtd.hide = hide
        self.fdtds.append(fdtd)
        return fdtd


class _FakeFDTD:
    def __init__(self) -> None:
        self.hide = False
        self.run_called = False
        self.getdata_called = False
        self.saved_path = ""
        self.source_phases: list[float] = []
        self.rotations: list[float] = []
        self._current_object = ""

    def switchtolayout(self) -> None:
        pass

    def deleteall(self) -> None:
        pass

    def addfdtd(self) -> None:
        self._current_object = "fdtd"

    def addrect(self) -> None:
        self._current_object = "rect"

    def addplane(self) -> None:
        self._current_object = "plane"

    def addpower(self) -> None:
        self._current_object = "power"

    def addprofile(self) -> None:
        self._current_object = "profile"

    def set(self, name: str, value: object) -> None:
        if self._current_object == "rect" and name == "rotation 1":
            self.rotations.append(float(value))
        if self._current_object == "plane" and name == "phase":
            self.source_phases.append(float(value))

    def run(self) -> None:
        self.run_called = True

    def save(self, path: str) -> None:
        self.saved_path = path

    def transmission(self, _name: str) -> float:
        return 0.9 if self.source_phases == [0, 90] else 0.1

    def getdata(self, _name: str, data_name: str) -> object:
        self.getdata_called = True
        if self.source_phases == [0, 90]:
            if data_name == "Ex":
                return [[1 / math.sqrt(2)]]
            if data_name == "Ey":
                return [[-1j / math.sqrt(2)]]
        return [[0j]]

    def close(self) -> None:
        pass
