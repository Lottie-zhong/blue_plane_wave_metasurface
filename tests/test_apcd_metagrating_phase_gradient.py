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

from metasurface.apcd_metagrating import (
    build_phase_gradient_requirements,
    normalized_structure_factor,
    read_apcd_metagrating_geometry_csv,
    write_phase_gradient_outputs,
)


def _geometry_rows(K: int):
    return read_apcd_metagrating_geometry_csv(
        REPO_ROOT / "outputs" / f"apcd_k{K}_metagrating_633nm" / "geometry.csv"
    )


def test_k6_phase_step_is_60_deg() -> None:
    rows = build_phase_gradient_requirements(_geometry_rows(6))

    assert len(rows) == 6
    assert math.isclose(rows[1]["plus_ramp_phase_deg"] - rows[0]["plus_ramp_phase_deg"], 60.0)


def test_k7_phase_step_is_360_over_7_deg() -> None:
    rows = build_phase_gradient_requirements(_geometry_rows(7))

    assert len(rows) == 7
    assert math.isclose(
        rows[1]["plus_ramp_phase_deg"] - rows[0]["plus_ramp_phase_deg"],
        360 / 7,
    )


def test_uniform_first_order_structure_factors_are_near_zero() -> None:
    for K in (6, 7):
        phases = [0.0] * K
        assert abs(normalized_structure_factor(phases, order_m=1)) < 1e-12
        assert abs(normalized_structure_factor(phases, order_m=-1)) < 1e-12


def test_plus_and_minus_ramps_enhance_opposite_first_order_signs() -> None:
    for K in (6, 7):
        rows = build_phase_gradient_requirements(_geometry_rows(K))
        plus = [float(row["plus_ramp_phase_rad"]) for row in rows]
        minus = [float(row["minus_ramp_phase_rad"]) for row in rows]

        assert math.isclose(abs(normalized_structure_factor(plus, order_m=1)), 1.0, abs_tol=1e-12)
        assert abs(normalized_structure_factor(plus, order_m=-1)) < 1e-12
        assert math.isclose(abs(normalized_structure_factor(minus, order_m=-1)), 1.0, abs_tol=1e-12)
        assert abs(normalized_structure_factor(minus, order_m=1)) < 1e-12


def test_phase_gradient_outputs_write_csv_and_markdown(tmp_path: Path) -> None:
    csv_path, md_path, rows = write_phase_gradient_outputs(
        geometry_csv=REPO_ROOT / "outputs" / "apcd_k6_metagrating_633nm" / "geometry.csv",
        requirements_csv=tmp_path / "phase_gradient_requirements.csv",
        sanity_check_md=tmp_path / "phase_gradient_sanity_check.md",
    )

    assert csv_path.exists()
    assert md_path.exists()
    assert len(rows) == 6
    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        loaded_rows = list(csv.DictReader(handle))
    assert len(loaded_rows) == 6
    assert loaded_rows[0]["uniform_phase_rad"] == "0.0"
    text = md_path.read_text(encoding="utf-8")
    assert "current uniform scaffold alone should not be claimed" in text
    assert "Sign Convention Caveat" in text
    assert "t_{alpha*<-alpha}" in text


def test_phase_gradient_script_does_not_use_lumapi_or_fdtd_run(tmp_path: Path) -> None:
    sys.modules.pop("lumapi", None)
    script_path = REPO_ROOT / "scripts" / "16_analyze_apcd_k_dimer_phase_gradient_requirements.py"
    script_text = script_path.read_text(encoding="utf-8")

    assert "lumapi" not in script_text
    assert "fdtd.run" not in script_text

    completed = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--K",
            "6",
            "--output-root",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    assert completed.returncode != 0
    assert "No such file" in completed.stderr or "cannot find" in completed.stderr.lower()
    assert "lumapi" not in sys.modules


def test_phase_gradient_script_writes_repo_outputs() -> None:
    script_path = REPO_ROOT / "scripts" / "16_analyze_apcd_k_dimer_phase_gradient_requirements.py"
    completed = subprocess.run(
        [sys.executable, str(script_path), "--K", "7"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "K=7" in completed.stdout
    assert "phase_step_deg=51.42857142857143" in completed.stdout
    assert (
        REPO_ROOT / "outputs" / "apcd_k7_metagrating_633nm" / "phase_gradient_requirements.csv"
    ).exists()
    assert (
        REPO_ROOT / "outputs" / "apcd_k7_metagrating_633nm" / "phase_gradient_sanity_check.md"
    ).exists()
