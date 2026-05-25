from __future__ import annotations

import csv
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.config import load_sweep_config
from metasurface.h_sweep import SUMMARY_FIELDS, write_h_sweep_summary
from metasurface.lumapi_runner import SweepRunner


def test_dry_run_does_not_import_lumapi() -> None:
    sys.modules.pop("lumapi", None)
    config = load_sweep_config(REPO_ROOT / "configs" / "plane_wave_h_sweep.yaml")

    rows = SweepRunner.from_runtime_file(config=config, runtime_path=None, dry_run=True).run()

    assert "lumapi" not in sys.modules
    assert len(rows) == 9
    assert rows[0]["h_nm"] == 250
    assert rows[-1]["h_nm"] == 450
    assert {row["status"] for row in rows} == {"dry_run"}


def test_write_h_sweep_summary_csv(tmp_path: Path) -> None:
    config = load_sweep_config(REPO_ROOT / "configs" / "plane_wave_h_sweep.yaml")
    rows = SweepRunner.from_runtime_file(config=config, runtime_path=None, dry_run=True).run()
    output_path = tmp_path / "h_sweep_summary.csv"

    written_path = write_h_sweep_summary(rows, output_path)

    with written_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded_rows = list(reader)

    assert reader.fieldnames == SUMMARY_FIELDS
    assert len(loaded_rows) == 9
    assert loaded_rows[0]["h_nm"] == "250"
    assert loaded_rows[0]["wavelength_nm"] == "450"
    assert loaded_rows[0]["rcp_plus1_efficiency"] == ""
    assert loaded_rows[0]["note"] == "dry-run only; lumapi was not imported"

