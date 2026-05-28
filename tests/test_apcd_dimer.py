from __future__ import annotations

import csv
import math
import sys
from dataclasses import replace
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_dimer import (
    APCD_DIMER_RESULT_FIELDS,
    APCDSingleDimerRunner,
    apcd_alpha_beta_basis,
    jones_matrix_alpha_beta_basis,
    jones_matrix_linear_basis,
    run_apcd_single_dimer_lumerical,
    run_apcd_single_dimer_setup_only,
    transform_linear_jones_to_alpha_beta,
    validate_apcd_single_dimer_geometry,
    write_apcd_single_dimer_results,
    write_apcd_single_dimer_summary,
    write_jones_matrix_alpha_beta_basis_npy,
    write_jones_matrix_linear_basis_npy,
)
from metasurface.config import RuntimeConfig, load_apcd_single_dimer_config


def test_load_apcd_single_dimer_config() -> None:
    config = load_apcd_single_dimer_config(REPO_ROOT / "configs" / "apcd_single_dimer_633nm.yaml")

    assert config.project.stage == "legacy_single_apcd_dimer_633nm_fractional_layout"
    assert config.target.wavelength_nm == 633
    assert config.target.target_polarization_type == "elliptical"
    assert config.target.psi_deg == 112.5
    assert config.target.chi_deg == 22.5
    assert config.material.substrate == "Al2O3"
    assert config.material.meta_material == "c-Si"
    assert config.geometry.layout_mode == "apcd_fractional"
    assert config.geometry.period_x_nm == 340
    assert config.geometry.period_y_nm == 340
    assert config.geometry.height_nm == 300
    assert config.geometry.minimum_gap_nm == 5
    assert config.geometry.nanopillar_1.length_nm == 130
    assert config.geometry.nanopillar_1.width_nm == 70
    assert config.geometry.nanopillar_1.frac_x == 0.75
    assert config.geometry.nanopillar_1.frac_y == 0.75
    assert config.geometry.nanopillar_1.x_nm == 85
    assert config.geometry.nanopillar_1.y_nm == 85
    assert config.geometry.nanopillar_1.rotation_deg == 67.5
    assert config.geometry.nanopillar_2.length_nm == 150
    assert config.geometry.nanopillar_2.width_nm == 85
    assert config.geometry.nanopillar_2.frac_x == 0.25
    assert config.geometry.nanopillar_2.frac_y == 0.25
    assert config.geometry.nanopillar_2.x_nm == -85
    assert config.geometry.nanopillar_2.y_nm == -85
    assert config.geometry.nanopillar_2.rotation_deg == 112.5


def test_apcd_single_dimer_yaml_uses_fractional_centers() -> None:
    config_path = REPO_ROOT / "configs" / "apcd_single_dimer_633nm.yaml"
    config_text = config_path.read_text(encoding="utf-8")
    raw_config = yaml.safe_load(config_text)

    assert "x_nm: -55" not in config_text
    assert "x_nm: 55" not in config_text
    assert raw_config["geometry"]["layout_mode"] == "apcd_fractional"
    assert "x_nm" not in raw_config["geometry"]["nanopillar_1"]
    assert "y_nm" not in raw_config["geometry"]["nanopillar_1"]
    assert "x_nm" not in raw_config["geometry"]["nanopillar_2"]
    assert "y_nm" not in raw_config["geometry"]["nanopillar_2"]
    assert raw_config["geometry"]["nanopillar_1"]["frac_x"] == 0.75
    assert raw_config["geometry"]["nanopillar_1"]["frac_y"] == 0.75
    assert raw_config["geometry"]["nanopillar_2"]["frac_x"] == 0.25
    assert raw_config["geometry"]["nanopillar_2"]["frac_y"] == 0.25


def test_apcd_fig2_elliptical_baseline_matches_paper_layout() -> None:
    config = load_apcd_single_dimer_config(REPO_ROOT / "configs" / "apcd_fig2_elliptical_633nm.yaml")

    assert config.project.stage == "phase1_apcd_fig2_elliptical_633nm"
    assert config.target.wavelength_nm == 633
    assert config.target.output_basis == "alpha_beta"
    assert config.target.target_polarization_type == "elliptical"
    assert config.target.psi_deg == 112.5
    assert config.target.chi_deg == 22.5
    assert config.material.meta_material == "c-Si"
    assert config.material.substrate == "Al2O3"
    assert config.geometry.layout_mode == "apcd_fractional"
    assert config.geometry.period_x_nm == 340
    assert config.geometry.period_y_nm == 340
    assert config.geometry.height_nm == 300
    assert config.geometry.nanopillar_1.length_nm == 130
    assert config.geometry.nanopillar_1.width_nm == 70
    assert config.geometry.nanopillar_1.x_nm == 85
    assert config.geometry.nanopillar_1.y_nm == 85
    assert config.geometry.nanopillar_1.rotation_deg == 67.5
    assert config.geometry.nanopillar_2.length_nm == 150
    assert config.geometry.nanopillar_2.width_nm == 85
    assert config.geometry.nanopillar_2.x_nm == -85
    assert config.geometry.nanopillar_2.y_nm == -85
    assert config.geometry.nanopillar_2.rotation_deg == 112.5


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
    assert float(loaded_rows[0]["wavelength_nm"]) == 633
    assert "periodic APCD unit cell" in summary_path.read_text(encoding="utf-8")


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
    assert lumapi.fdtds[0].rotations == [67.5, 112.5]


def test_apcd_fig2_lumerical_extracts_linear_and_alpha_beta_matrices() -> None:
    config = load_apcd_single_dimer_config(REPO_ROOT / "configs" / "apcd_fig2_elliptical_633nm.yaml")
    runtime = RuntimeConfig(mode="test", enable_lumerical=True, lumapi_python_api_dir="", hide_gui=True)
    lumapi = _FakeLumapi()

    row = run_apcd_single_dimer_lumerical(config=config, runtime=runtime, lumapi=lumapi)

    assert row["status"] == "ok"
    assert len(lumapi.fdtds) == 2
    assert lumapi.fdtds[0].events.index("run") < lumapi.fdtds[0].events.index("getdata:T_fields:Ex")
    assert lumapi.fdtds[1].events.index("run") < lumapi.fdtds[1].events.index("getdata:T_fields:Ex")
    run_index = lumapi.fdtds[0].events.index("run")
    ex_index = lumapi.fdtds[0].events.index("getdata:T_fields:Ex")
    assert "switchtolayout" not in lumapi.fdtds[0].events[run_index:ex_index]
    assert lumapi.fdtds[0].transmission_called is False
    assert lumapi.fdtds[1].transmission_called is False
    assert lumapi.fdtds[0].source_angles == [0]
    assert lumapi.fdtds[1].source_angles == [90]
    assert lumapi.fdtds[0].source_phases == [0]
    assert lumapi.fdtds[1].source_phases == [0]
    assert row["spin_ER_dB"] == ""
    assert row["T_R_from_L"] == ""
    assert row["t_xx"] == "0.8+0j"
    assert row["t_xy"] == "0.2+0j"
    assert row["t_yx"] == "0+0.1j"
    assert row["t_yy"] == "0.7+0j"
    expected_linear = [[0.8 + 0j, 0.2 + 0j], [0 + 0.1j, 0.7 + 0j]]
    expected_alpha_beta = transform_linear_jones_to_alpha_beta(
        expected_linear,
        psi_deg=112.5,
        chi_deg=22.5,
    )
    assert jones_matrix_linear_basis(row) == expected_linear
    for row_index in range(2):
        for column_index in range(2):
            assert abs(
                jones_matrix_alpha_beta_basis(row)[row_index][column_index]
                - expected_alpha_beta[row_index][column_index]
            ) < 1e-12
    assert float(row["T_alpha"]) >= 0
    assert float(row["T_beta"]) >= 0
    assert -1 <= float(row["PD"]) <= 1


def test_apcd_fig2_results_fields_include_paper_metrics(tmp_path: Path) -> None:
    config = load_apcd_single_dimer_config(REPO_ROOT / "configs" / "apcd_fig2_elliptical_633nm.yaml")
    runtime = RuntimeConfig(mode="test", enable_lumerical=True, lumapi_python_api_dir="", hide_gui=True)
    row = run_apcd_single_dimer_lumerical(config=config, runtime=runtime, lumapi=_FakeLumapi())

    results_path = write_apcd_single_dimer_results(row, tmp_path / "results.csv")

    with results_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded_rows = list(reader)
    for field in (
        "t_alpha_star_from_alpha",
        "t_beta_star_from_alpha",
        "t_alpha_star_from_beta",
        "t_beta_star_from_beta",
        "T_alpha",
        "T_beta",
        "PD",
    ):
        assert field in reader.fieldnames
        assert loaded_rows[0][field] != ""


def test_apcd_fig2_writes_required_jones_npy_files(tmp_path: Path) -> None:
    config = load_apcd_single_dimer_config(REPO_ROOT / "configs" / "apcd_fig2_elliptical_633nm.yaml")
    runtime = RuntimeConfig(mode="test", enable_lumerical=True, lumapi_python_api_dir="", hide_gui=True)
    row = run_apcd_single_dimer_lumerical(config=config, runtime=runtime, lumapi=_FakeLumapi())

    linear_path = write_jones_matrix_linear_basis_npy(row, tmp_path / "jones_matrix_linear_basis.npy")
    alpha_beta_path = write_jones_matrix_alpha_beta_basis_npy(row, tmp_path / "jones_matrix_alpha_beta_basis.npy")

    assert linear_path.exists()
    assert alpha_beta_path.exists()


def test_apcd_fig2_successful_fake_run_writes_required_outputs(tmp_path: Path) -> None:
    config = load_apcd_single_dimer_config(REPO_ROOT / "configs" / "apcd_fig2_elliptical_633nm.yaml")
    runtime = RuntimeConfig(mode="test", enable_lumerical=True, lumapi_python_api_dir="", hide_gui=True)
    row = run_apcd_single_dimer_lumerical(config=config, runtime=runtime, lumapi=_FakeLumapi())

    results_path = write_apcd_single_dimer_results(row, tmp_path / "results.csv")
    summary_path = write_apcd_single_dimer_summary(row, tmp_path / "summary.md")
    linear_path = write_jones_matrix_linear_basis_npy(row, tmp_path / "jones_matrix_linear_basis.npy")
    alpha_beta_path = write_jones_matrix_alpha_beta_basis_npy(row, tmp_path / "jones_matrix_alpha_beta_basis.npy")

    assert results_path.exists()
    assert summary_path.exists()
    assert linear_path.exists()
    assert alpha_beta_path.exists()


def test_apcd_fig2_missing_field_data_writes_diagnostic_summary_and_debug_fsp(tmp_path: Path) -> None:
    config = load_apcd_single_dimer_config(REPO_ROOT / "configs" / "apcd_fig2_elliptical_633nm.yaml")
    config = replace(config, output=replace(config.output, result_dir=tmp_path))
    runtime = RuntimeConfig(mode="test", enable_lumerical=True, lumapi_python_api_dir="", hide_gui=True)
    lumapi = _MissingFieldLumapi()

    row = run_apcd_single_dimer_lumerical(config=config, runtime=runtime, lumapi=lumapi)
    summary_path = write_apcd_single_dimer_summary(row, tmp_path / "summary.md")

    assert row["status"] == "error"
    assert "T_fields" in str(row["_diagnostics"])
    assert row["_debug_fsp_path"] == tmp_path / "debug_after_run_X.fsp"
    assert lumapi.fdtds[0].saved_path == str(tmp_path / "debug_after_run_X.fsp")
    save_index = lumapi.fdtds[0].events.index(f"save:{tmp_path / 'debug_after_run_X.fsp'}")
    assert "switchtolayout" not in lumapi.fdtds[0].events[lumapi.fdtds[0].events.index("run"):save_index]
    summary_text = summary_path.read_text(encoding="utf-8")
    assert "Run diagnostics" in summary_text
    assert "debug_after_run_X.fsp" in summary_text
    assert "T_fields_Ex_probe" in summary_text


def test_apcd_fig2_getdata_failure_uses_getresult_fallback() -> None:
    config = load_apcd_single_dimer_config(REPO_ROOT / "configs" / "apcd_fig2_elliptical_633nm.yaml")
    runtime = RuntimeConfig(mode="test", enable_lumerical=True, lumapi_python_api_dir="", hide_gui=True)
    lumapi = _GetDataFailsGetResultSucceedsLumapi()

    row = run_apcd_single_dimer_lumerical(config=config, runtime=runtime, lumapi=lumapi)

    assert row["status"] == "ok"
    assert row["t_xx"] == "0.8+0j"
    assert any(event == "getresult:T_fields:E" for event in lumapi.fdtds[0].events)
    assert "fallback succeeded" in str(row["_diagnostics"])


def test_alpha_beta_transform_for_ideal_apcd_projector() -> None:
    config = load_apcd_single_dimer_config(REPO_ROOT / "configs" / "apcd_fig2_elliptical_633nm.yaml")
    basis = apcd_alpha_beta_basis(psi_deg=config.target.psi_deg, chi_deg=config.target.chi_deg)
    alpha = basis["alpha"]
    alpha_star = basis["alpha_star"]
    ideal_linear = [
        [alpha_star[0] * alpha[0].conjugate(), alpha_star[0] * alpha[1].conjugate()],
        [alpha_star[1] * alpha[0].conjugate(), alpha_star[1] * alpha[1].conjugate()],
    ]
    transformed = transform_linear_jones_to_alpha_beta(
        ideal_linear,
        psi_deg=config.target.psi_deg,
        chi_deg=config.target.chi_deg,
    )
    assert abs(transformed[0][0] - 1) < 1e-12
    assert abs(transformed[1][0]) < 1e-12
    assert abs(transformed[0][1]) < 1e-12
    assert abs(transformed[1][1]) < 1e-12


def test_apcd_single_dimer_geometry_validation_estimates_gap() -> None:
    config = load_apcd_single_dimer_config(REPO_ROOT / "configs" / "apcd_fig2_elliptical_633nm.yaml")

    validation = validate_apcd_single_dimer_geometry(config)

    assert validation.minimum_gap_nm > config.geometry.minimum_gap_nm
    assert validation.same_cell_min_gap_nm > config.geometry.minimum_gap_nm
    assert validation.periodic_image_min_gap_nm > config.geometry.minimum_gap_nm
    assert validation.nearest_pair_description
    assert validation.passed is True


def test_apcd_single_dimer_geometry_validation_rejects_overlap() -> None:
    config = load_apcd_single_dimer_config(REPO_ROOT / "configs" / "apcd_single_dimer_633nm.yaml")
    invalid_geometry = replace(
        config.geometry,
        layout_mode="manual_absolute",
        nanopillar_1=replace(config.geometry.nanopillar_1, x_nm=0, y_nm=0),
        nanopillar_2=replace(config.geometry.nanopillar_2, x_nm=0, y_nm=0),
    )
    invalid_config = replace(config, geometry=invalid_geometry)

    try:
        validate_apcd_single_dimer_geometry(invalid_config)
    except ValueError as exc:
        assert "overlaps" in str(exc)
    else:
        raise AssertionError("Expected overlapping APCD geometry to be rejected")


def test_apcd_single_dimer_geometry_validation_rejects_periodic_overlap() -> None:
    config = load_apcd_single_dimer_config(REPO_ROOT / "configs" / "apcd_fig2_elliptical_633nm.yaml")
    periodic_overlap_geometry = replace(
        config.geometry,
        layout_mode="manual_absolute",
        nanopillar_1=replace(
            config.geometry.nanopillar_1,
            length_nm=100,
            width_nm=50,
            x_nm=160,
            y_nm=0,
            rotation_deg=0,
        ),
        nanopillar_2=replace(
            config.geometry.nanopillar_2,
            length_nm=100,
            width_nm=50,
            x_nm=-160,
            y_nm=0,
            rotation_deg=0,
        ),
    )
    invalid_config = replace(config, geometry=periodic_overlap_geometry)

    try:
        validate_apcd_single_dimer_geometry(invalid_config)
    except ValueError as exc:
        assert "periodic image" in str(exc)
    else:
        raise AssertionError("Expected periodic-image overlap to be rejected")


def test_apcd_single_dimer_setup_only_saves_fsp_without_run(tmp_path: Path) -> None:
    config = load_apcd_single_dimer_config(REPO_ROOT / "configs" / "apcd_fig2_elliptical_633nm.yaml")
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
    assert lumapi.fdtds[0].source_angles == [0]
    assert lumapi.fdtds[0].source_phases == [0]


def test_apcd_single_dimer_setup_only_does_not_save_invalid_geometry(tmp_path: Path) -> None:
    config = load_apcd_single_dimer_config(REPO_ROOT / "configs" / "apcd_single_dimer_633nm.yaml")
    invalid_geometry = replace(
        config.geometry,
        layout_mode="manual_absolute",
        nanopillar_1=replace(config.geometry.nanopillar_1, x_nm=0, y_nm=0),
        nanopillar_2=replace(config.geometry.nanopillar_2, x_nm=0, y_nm=0),
    )
    invalid_config = replace(config, geometry=invalid_geometry)
    runtime = RuntimeConfig(mode="test", enable_lumerical=True, lumapi_python_api_dir="", hide_gui=True)
    lumapi = _FakeLumapi()

    row = run_apcd_single_dimer_setup_only(
        config=invalid_config,
        runtime=runtime,
        lumapi=lumapi,
        fsp_output=tmp_path / "invalid.fsp",
    )

    assert row["status"] == "error"
    assert "overlaps" in str(row["note"])
    assert lumapi.fdtds[0].saved_path == ""
    assert lumapi.fdtds[0].run_called is False


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
        self.transmission_called = False
        self.saved_path = ""
        self.source_phases: list[float] = []
        self.source_angles: list[float] = []
        self.rotations: list[float] = []
        self.events: list[str] = []
        self._current_object = ""

    def switchtolayout(self) -> None:
        self.events.append("switchtolayout")

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
        if self._current_object == "plane" and name == "polarization angle":
            self.source_angles.append(float(value))
        if self._current_object == "plane" and name == "phase":
            self.source_phases.append(float(value))

    def run(self) -> None:
        self.events.append("run")
        self.run_called = True

    def save(self, path: str) -> None:
        self.events.append(f"save:{path}")
        self.saved_path = path

    def getresult(self, name: str, result_name: str) -> object:
        self.events.append(f"getresult:{name}:{result_name}")
        if name == "T_fields" and result_name == "E":
            if self.source_angles == [0]:
                return {"Ex": [[0.8 + 0j]], "Ey": [[0 + 0.1j]]}
            if self.source_angles == [90]:
                return {"Ex": [[0.2 + 0j]], "Ey": [[0.7 + 0j]]}
        return {"name": name, "result": result_name}

    def transmission(self, _name: str) -> float:
        self.events.append(f"transmission:{_name}")
        self.transmission_called = True
        if self.source_angles == [0]:
            return 0.64
        if self.source_angles == [90]:
            return 0.49
        return 0.9 if self.source_phases == [0, 90] else 0.1

    def getdata(self, _name: str, data_name: str) -> object:
        self.events.append(f"getdata:{_name}:{data_name}")
        self.getdata_called = True
        if self.source_angles == [0]:
            if data_name == "Ex":
                return [[0.8 + 0j]]
            if data_name == "Ey":
                return [[0 + 0.1j]]
        if self.source_angles == [90]:
            if data_name == "Ex":
                return [[0.2 + 0j]]
            if data_name == "Ey":
                return [[0.7 + 0j]]
        if self.source_phases == [0, 90]:
            if data_name == "Ex":
                return [[1 / math.sqrt(2)]]
            if data_name == "Ey":
                return [[-1j / math.sqrt(2)]]
        return [[0j]]

    def close(self) -> None:
        pass


class _MissingFieldLumapi:
    def __init__(self) -> None:
        self.fdtds: list[_MissingFieldFDTD] = []

    def FDTD(self, hide: bool) -> "_MissingFieldFDTD":
        fdtd = _MissingFieldFDTD()
        fdtd.hide = hide
        self.fdtds.append(fdtd)
        return fdtd


class _MissingFieldFDTD(_FakeFDTD):
    def getdata(self, _name: str, data_name: str) -> object:
        self.events.append(f"getdata:{_name}:{data_name}")
        self.getdata_called = True
        raise RuntimeError(f"missing monitor data: {_name}.{data_name}")

    def getresult(self, name: str, result_name: str) -> object:
        self.events.append(f"getresult:{name}:{result_name}")
        raise RuntimeError(f"missing result data: {name}.{result_name}")


class _GetDataFailsGetResultSucceedsLumapi:
    def __init__(self) -> None:
        self.fdtds: list[_GetDataFailsGetResultSucceedsFDTD] = []

    def FDTD(self, hide: bool) -> "_GetDataFailsGetResultSucceedsFDTD":
        fdtd = _GetDataFailsGetResultSucceedsFDTD()
        fdtd.hide = hide
        self.fdtds.append(fdtd)
        return fdtd


class _GetDataFailsGetResultSucceedsFDTD(_FakeFDTD):
    def getdata(self, _name: str, data_name: str) -> object:
        self.events.append(f"getdata:{_name}:{data_name}")
        self.getdata_called = True
        raise RuntimeError(f"getdata unavailable: {_name}.{data_name}")
