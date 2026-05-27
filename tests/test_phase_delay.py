from __future__ import annotations

import csv
import math
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.phase_delay import compute_xy_phase_delay_from_files, wrap_phase_rad


def test_wrap_phase_rad() -> None:
    assert math.isclose(wrap_phase_rad(3 * math.pi), math.pi)
    assert math.isclose(wrap_phase_rad(-3 * math.pi), -math.pi)
    assert math.isclose(wrap_phase_rad(0.25), 0.25)


def test_compute_xy_phase_delay_from_files(tmp_path: Path) -> None:
    x_path = tmp_path / "x.csv"
    y_path = tmp_path / "y.csv"
    output_path = tmp_path / "phase_delay.csv"
    _write_single_summary(x_path, phase_rad="-2.5", transmission="0.84", status="ok")
    _write_single_summary(y_path, phase_rad="0.7", transmission="0.62", status="ok")

    written_path = compute_xy_phase_delay_from_files(x_path, y_path, output_path)

    with written_path.open("r", newline="", encoding="utf-8") as handle:
        row = next(csv.DictReader(handle))

    expected_delay = wrap_phase_rad(-2.5 - 0.7)
    assert row["status"] == "ok"
    assert math.isclose(float(row["phase_delay_rad"]), expected_delay)
    assert math.isclose(float(row["phase_delay_error_to_pi"]), abs(abs(expected_delay) - math.pi))
    assert row["transmission_x"] == "0.84"
    assert row["transmission_y"] == "0.62"


def _write_single_summary(path: Path, phase_rad: str, transmission: str, status: str) -> None:
    fieldnames = [
        "wavelength_nm",
        "period_nm",
        "length_nm",
        "width_nm",
        "height_nm",
        "rotation_deg",
        "incident_polarization",
        "transmission",
        "phase_rad",
        "farfield_peak",
        "farfield_shape",
        "status",
        "note",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(
            {
                "wavelength_nm": "450",
                "period_nm": "220",
                "length_nm": "160",
                "width_nm": "80",
                "height_nm": "350",
                "rotation_deg": "0",
                "incident_polarization": "x",
                "transmission": transmission,
                "phase_rad": phase_rad,
                "farfield_peak": "1",
                "farfield_shape": "1001x1001",
                "status": status,
                "note": "",
            }
        )
