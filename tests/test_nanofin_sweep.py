from __future__ import annotations

import csv
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.nanofin_sweep import (
    XY_SWEEP_PLAN_FIELDS,
    build_xy_sweep_plan_rows,
    load_xy_sweep_config,
    write_xy_case_configs,
    write_xy_sweep_plan,
)


def test_build_xy_sweep_plan_rows() -> None:
    config = load_xy_sweep_config(REPO_ROOT / "configs" / "nanofin_xy_sweep.yaml")

    rows = build_xy_sweep_plan_rows(config)

    assert len(rows) == 20
    assert rows[0]["case_id"] == "L120_W60_H350_R0"
    assert rows[0]["x_config"] == Path("outputs/nanofin_xy_sweep/L120_W60_H350_R0/L120_W60_H350_R0_x.yaml")
    assert rows[-1]["case_id"] == "L200_W120_H350_R0"
    assert {row["status"] for row in rows} == {"planned"}


def test_write_xy_sweep_plan_and_case_configs(tmp_path: Path) -> None:
    config = load_xy_sweep_config(REPO_ROOT / "configs" / "nanofin_xy_sweep.yaml")
    rows = build_xy_sweep_plan_rows(config)[:1]
    rows[0]["x_config"] = tmp_path / "case_x.yaml"
    rows[0]["y_config"] = tmp_path / "case_y.yaml"
    output_path = tmp_path / "xy_sweep_plan.csv"

    written_path = write_xy_sweep_plan(rows, output_path)
    write_xy_case_configs(config, rows)

    with written_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded_rows = list(reader)

    assert reader.fieldnames == XY_SWEEP_PLAN_FIELDS
    assert loaded_rows[0]["case_id"] == "L120_W60_H350_R0"
    assert (tmp_path / "case_x.yaml").exists()
    assert (tmp_path / "case_y.yaml").exists()
    assert "incident_polarization: x" in (tmp_path / "case_x.yaml").read_text(encoding="utf-8")
    assert "incident_polarization: y" in (tmp_path / "case_y.yaml").read_text(encoding="utf-8")
    assert "length_nm: 120" in (tmp_path / "case_x.yaml").read_text(encoding="utf-8")
    assert "width_nm: 60" in (tmp_path / "case_y.yaml").read_text(encoding="utf-8")
