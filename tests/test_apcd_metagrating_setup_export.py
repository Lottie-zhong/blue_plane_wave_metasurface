from __future__ import annotations

import csv
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_metagrating import (
    export_apcd_metagrating_setup_only,
    read_apcd_metagrating_geometry_csv,
    validate_apcd_metagrating_geometry_rows,
    write_apcd_metagrating_gui_checklist,
    write_apcd_metagrating_setup_summary,
)
from metasurface.config import RuntimeConfig, load_apcd_single_dimer_config


def _config():
    return load_apcd_single_dimer_config(REPO_ROOT / "configs" / "apcd_fig2_elliptical_633nm_alpha_pass.yaml")


def _rows_for_k(K: int):
    return read_apcd_metagrating_geometry_csv(
        REPO_ROOT / "outputs" / f"apcd_k{K}_metagrating_633nm" / "geometry.csv"
    )


def test_k6_setup_export_uses_12_pillars_and_does_not_run(tmp_path: Path) -> None:
    rows = _rows_for_k(6)
    runtime = RuntimeConfig(mode="test", enable_lumerical=True, lumapi_python_api_dir="", hide_gui=True)
    lumapi = _FakeLumapi()
    fsp_output = tmp_path / "apcd_k6_metagrating_633nm_setup.fsp"

    row = export_apcd_metagrating_setup_only(_config(), rows, runtime, lumapi, fsp_output)

    assert row["status"] == "setup_only"
    assert row["nanopillar_count"] == 12
    assert row["fdtd_run_called"] is False
    assert lumapi.fdtd.run_called is False
    assert lumapi.fdtd.saved_path == str(fsp_output)
    assert lumapi.fdtd.addrect_count == 13
    assert lumapi.fdtd.addplane_count == 1
    assert "T" in lumapi.fdtd.object_names
    assert "T_fields" in lumapi.fdtd.object_names


def test_k7_setup_export_uses_14_pillars_and_does_not_run(tmp_path: Path) -> None:
    rows = _rows_for_k(7)
    runtime = RuntimeConfig(mode="test", enable_lumerical=True, lumapi_python_api_dir="", hide_gui=True)
    lumapi = _FakeLumapi()
    fsp_output = tmp_path / "apcd_k7_metagrating_633nm_setup.fsp"

    row = export_apcd_metagrating_setup_only(_config(), rows, runtime, lumapi, fsp_output)

    assert row["status"] == "setup_only"
    assert row["nanopillar_count"] == 14
    assert lumapi.fdtd.run_called is False
    assert lumapi.fdtd.saved_path == str(fsp_output)
    assert lumapi.fdtd.addrect_count == 15
    assert lumapi.fdtd.addplane_count == 1


def test_setup_summary_and_gui_checklist_are_written(tmp_path: Path) -> None:
    rows = _rows_for_k(6)
    runtime = RuntimeConfig(mode="test", enable_lumerical=True, lumapi_python_api_dir="", hide_gui=True)
    row = export_apcd_metagrating_setup_only(
        _config(),
        rows,
        runtime,
        _FakeLumapi(),
        tmp_path / "apcd_k6_metagrating_633nm_setup.fsp",
    )

    summary_path = write_apcd_metagrating_setup_summary(row, tmp_path / "geometry.csv", tmp_path / "setup_summary.md")
    checklist_path = write_apcd_metagrating_gui_checklist(row, tmp_path / "gui_inspection_checklist.md")

    summary_text = summary_path.read_text(encoding="utf-8")
    checklist_text = checklist_path.read_text(encoding="utf-8")
    assert "This is not an FDTD result" in summary_text
    assert "FDTD was not run" in summary_text
    assert "t_{alpha*<-alpha} phase-gradient" in summary_text
    assert "2K = 12 nanopillars" in checklist_text
    assert "pillar 2 is 85 x 150 nm, not 150 x 85 nm" in checklist_text


def test_setup_export_rejects_wrong_pillar_count() -> None:
    rows = _rows_for_k(6)[:-1]

    try:
        validate_apcd_metagrating_geometry_rows(rows, 6)
    except ValueError as exc:
        assert "12 nanopillars" in str(exc)
    else:
        raise AssertionError("Expected wrong pillar count to fail validation")


def test_setup_export_rejects_original_beta_selective_pillar_2(tmp_path: Path) -> None:
    rows = _rows_for_k(6)
    rows[1] = dict(rows[1])
    rows[1]["length_nm"] = 150.0
    rows[1]["width_nm"] = 85.0

    try:
        validate_apcd_metagrating_geometry_rows(rows, 6)
    except ValueError as exc:
        assert "original beta-selective pillar 2" in str(exc)
    else:
        raise AssertionError("Expected original beta-selective pillar 2 to fail validation")


def test_geometry_csv_pillar_2_is_not_original_beta_selective() -> None:
    for K in (6, 7):
        rows = _rows_for_k(K)
        pillar_2_rows = [row for row in rows if row["pillar_index_in_dimer"] == 2]
        assert len(pillar_2_rows) == K
        assert all(row["length_nm"] == 85.0 and row["width_nm"] == 150.0 for row in pillar_2_rows)
        assert not any(row["length_nm"] == 150.0 and row["width_nm"] == 85.0 for row in pillar_2_rows)


def test_output_geometry_csv_files_have_expected_counts() -> None:
    for K, expected_count in ((6, 12), (7, 14)):
        csv_path = REPO_ROOT / "outputs" / f"apcd_k{K}_metagrating_633nm" / "geometry.csv"
        with csv_path.open("r", newline="", encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        assert len(rows) == expected_count


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
        self.addrect_count = 0
        self.addplane_count = 0
        self.object_names: list[str] = []
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

    def addprofile(self) -> None:
        self._current_object = "profile"

    def set(self, name: str, value: object) -> None:
        if name == "name":
            self.object_names.append(str(value))

    def save(self, path: str) -> None:
        self.saved_path = path
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(b"fake fsp")

    def run(self) -> None:
        self.run_called = True

    def close(self) -> None:
        pass
