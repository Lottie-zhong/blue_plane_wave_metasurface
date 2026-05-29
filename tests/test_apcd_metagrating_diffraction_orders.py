from __future__ import annotations

import csv
import math
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_diffraction import (
    APCD_DIFFRACTION_ORDER_FIELDS,
    build_expected_order_table,
    expected_order_angle_deg,
    extract_fdtd_grating_orders,
    normalize_order_efficiency,
    write_diffraction_dry_run_outputs,
)


def test_k6_k7_expected_target_angles_are_15_deg() -> None:
    for K in (6, 7):
        rows = build_expected_order_table(K)
        plus = next(row for row in rows if row["order_n"] == 1)
        minus = next(row for row in rows if row["order_n"] == -1)
        zero = next(row for row in rows if row["order_n"] == 0)

        assert math.isclose(float(plus["expected_theta_deg"]), 15.0, abs_tol=1e-12)
        assert math.isclose(float(minus["expected_theta_deg"]), -15.0, abs_tol=1e-12)
        assert math.isclose(abs(float(plus["expected_theta_deg"])), abs(float(minus["expected_theta_deg"])))
        assert math.isclose(float(zero["expected_theta_deg"]), 0.0)


def test_expected_order_angle_deg_uses_grating_equation() -> None:
    period = 633 / math.sin(math.radians(15))

    assert math.isclose(expected_order_angle_deg(1, 633, period), 15.0, abs_tol=1e-12)
    assert math.isclose(expected_order_angle_deg(-1, 633, period), -15.0, abs_tol=1e-12)
    assert math.isclose(expected_order_angle_deg(0, 633, period), 0.0)


def test_source_normalized_efficiency_is_fraction_times_transmission() -> None:
    assert normalize_order_efficiency(0.25, 0.8) == 0.2


def test_dry_run_outputs_schema_and_plan(tmp_path: Path) -> None:
    schema_path, plan_path, rows = write_diffraction_dry_run_outputs(K=6, output_dir=tmp_path)

    assert schema_path.exists()
    assert plan_path.exists()
    assert len(rows) == 3
    with schema_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded_rows = list(reader)

    assert reader.fieldnames == APCD_DIFFRACTION_ORDER_FIELDS
    assert len(loaded_rows) == 3
    text = plan_path.read_text(encoding="utf-8")
    assert "not an optical result" in text
    assert "no FDTD run was performed" in text
    assert "Current structure remains a scaffold only" in text
    assert "Do not use `grating()` alone" in text


def test_fake_fdtd_extraction_calls_grating_commands_without_run() -> None:
    fdtd = _FakeFDTD()
    rows = extract_fdtd_grating_orders(fdtd, monitor_name="T", K=6)

    assert fdtd.run_called is False
    assert fdtd.calls == [
        "gratingn:T",
        "gratingm:T",
        "gratingu1:T",
        "gratingu2:T",
        "grating:T",
        "transmission:T",
        "gratingvector:T",
    ]
    assert len(rows) == 3
    assert rows[1]["order_efficiency_source_norm"] == 0.2
    assert rows[1]["Ex_order_complex_real"] == 1.0
    assert rows[1]["Ey_order_complex_imag"] == -1.0
    assert rows[1]["Ez_order_complex_real"] == 0.0


def test_script_dry_run_writes_repo_outputs() -> None:
    script = REPO_ROOT / "scripts" / "17_extract_apcd_metagrating_diffraction_orders.py"
    script_text = script.read_text(encoding="utf-8")
    assert "lumapi" not in script_text
    assert "fdtd.run" not in script_text

    completed = subprocess.run(
        [sys.executable, str(script), "--K", "7", "--dry-run"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "K=7" in completed.stdout
    assert "expected_plus1_theta_deg=15.0" in completed.stdout
    assert (
        REPO_ROOT / "outputs" / "apcd_k7_metagrating_633nm" / "diffraction_order_schema.csv"
    ).exists()
    assert (
        REPO_ROOT / "outputs" / "apcd_k7_metagrating_633nm" / "diffraction_order_extraction_plan.md"
    ).exists()


class _FakeFDTD:
    def __init__(self) -> None:
        self.calls: list[str] = []
        self.run_called = False

    def run(self) -> None:
        self.run_called = True

    def gratingn(self, monitor_name: str) -> list[int]:
        self.calls.append(f"gratingn:{monitor_name}")
        return [-1, 1, 0]

    def gratingm(self, monitor_name: str) -> list[int]:
        self.calls.append(f"gratingm:{monitor_name}")
        return [0, 0, 0]

    def gratingu1(self, monitor_name: str) -> list[float]:
        self.calls.append(f"gratingu1:{monitor_name}")
        return [-0.2588190451, 0.2588190451, 0.0]

    def gratingu2(self, monitor_name: str) -> list[float]:
        self.calls.append(f"gratingu2:{monitor_name}")
        return [0.0, 0.0, 0.0]

    def grating(self, monitor_name: str) -> list[float]:
        self.calls.append(f"grating:{monitor_name}")
        return [0.1, 0.25, 0.65]

    def transmission(self, monitor_name: str) -> float:
        self.calls.append(f"transmission:{monitor_name}")
        return 0.8

    def gratingvector(self, monitor_name: str) -> list[list[complex]]:
        self.calls.append(f"gratingvector:{monitor_name}")
        return [
            [0.0 + 0.0j, 0.0 + 0.0j, 0.0 + 0.0j],
            [1.0 + 0.5j, 0.0 - 1.0j, 0.0 + 0.0j],
            [0.2 + 0.0j, 0.3 + 0.0j, 0.0 + 0.0j],
        ]
