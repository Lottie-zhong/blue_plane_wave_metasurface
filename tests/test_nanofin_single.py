from __future__ import annotations

import csv
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.config import load_nanofin_single_config
from metasurface.nanofin_single import (
    SINGLE_NANOFIN_FIELDS,
    SingleNanofinRunner,
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
