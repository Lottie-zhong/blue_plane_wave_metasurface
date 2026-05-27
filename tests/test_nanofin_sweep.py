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
    XY_SWEEP_RESULT_FIELDS,
    build_xy_sweep_plan_rows,
    collect_xy_sweep_result_rows,
    filter_xy_sweep_rows,
    load_xy_sweep_config,
    write_xy_case_configs,
    write_xy_sweep_plan,
    write_xy_sweep_results,
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


def test_filter_xy_sweep_rows_by_case_id() -> None:
    config = load_xy_sweep_config(REPO_ROOT / "configs" / "nanofin_xy_sweep.yaml")
    rows = build_xy_sweep_plan_rows(config)

    selected = filter_xy_sweep_rows(rows, case_ids=["L160_W80_H350_R0", "L200_W120_H350_R0"])

    assert [row["case_id"] for row in selected] == ["L160_W80_H350_R0", "L200_W120_H350_R0"]


def test_filter_xy_sweep_rows_rejects_missing_case_id() -> None:
    config = load_xy_sweep_config(REPO_ROOT / "configs" / "nanofin_xy_sweep.yaml")
    rows = build_xy_sweep_plan_rows(config)

    try:
        filter_xy_sweep_rows(rows, case_ids=["missing"])
    except ValueError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("Expected missing case_id to raise ValueError")


def test_collect_xy_sweep_result_rows_sorts_completed_cases(tmp_path: Path) -> None:
    config = load_xy_sweep_config(REPO_ROOT / "configs" / "nanofin_xy_sweep.yaml")
    rows = build_xy_sweep_plan_rows(config)[:2]
    rows[0]["phase_delay_summary"] = tmp_path / "worse.csv"
    rows[1]["phase_delay_summary"] = tmp_path / "better.csv"
    _write_phase_delay(rows[0]["phase_delay_summary"], phase_delay="0.5", error="2.64")
    _write_phase_delay(rows[1]["phase_delay_summary"], phase_delay="3.0", error="0.14")

    result_rows = collect_xy_sweep_result_rows(rows)
    output_path = write_xy_sweep_results(result_rows, tmp_path / "results.csv")

    with output_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded_rows = list(reader)

    assert reader.fieldnames == XY_SWEEP_RESULT_FIELDS
    assert loaded_rows[0]["case_id"] == rows[1]["case_id"]
    assert loaded_rows[0]["phase_delay_error_to_pi"] == "0.14"


def test_collect_xy_sweep_result_rows_marks_missing_cases(tmp_path: Path) -> None:
    config = load_xy_sweep_config(REPO_ROOT / "configs" / "nanofin_xy_sweep.yaml")
    rows = build_xy_sweep_plan_rows(config)[:1]
    rows[0]["phase_delay_summary"] = tmp_path / "missing.csv"

    result_rows = collect_xy_sweep_result_rows(rows)

    assert result_rows[0]["status"] == "missing"
    assert result_rows[0]["note"] == "phase delay summary missing"


def _write_phase_delay(path: Path, phase_delay: str, error: str) -> None:
    fieldnames = [
        "phase_x_rad",
        "phase_y_rad",
        "phase_delay_rad",
        "phase_delay_error_to_pi",
        "transmission_x",
        "transmission_y",
        "status_x",
        "status_y",
        "status",
        "note",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "phase_x_rad": "1",
                "phase_y_rad": "0",
                "phase_delay_rad": phase_delay,
                "phase_delay_error_to_pi": error,
                "transmission_x": "0.9",
                "transmission_y": "0.8",
                "status_x": "ok",
                "status_y": "ok",
                "status": "ok",
                "note": "",
            }
        )
