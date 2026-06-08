from __future__ import annotations

import csv
import importlib.util
import math
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def p180():
    path = REPO_ROOT / "scripts/manual_p180_generate_k6_phase_ramp_plan.py"
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    module.main([])
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_p180_reads_p179_library(p180) -> None:
    library_rows = p180.read_phase_library(p180.P179_LIBRARY_CSV)

    assert len(library_rows) == 6
    assert sorted(int(float(row["bin_deg"])) for row in library_rows) == [-180, -120, -60, 0, 60, 120]


def test_p180_k6_plan_has_six_rows(p180) -> None:
    rows = read_csv(p180.PLAN_CSV)

    assert len(rows) == 6
    assert [int(row["supercell_index"]) for row in rows] == list(range(6))
    assert [int(float(row["target_bin_deg"])) for row in rows] == [0, 60, 120, -180, -120, -60]


def test_p180_phase_step_is_60_deg(p180) -> None:
    rows = read_csv(p180.PLAN_CSV)
    phases = [float(row["cumulative_target_phase_deg"]) for row in rows]

    assert phases == [0.0, 60.0, 120.0, 180.0, 240.0, 300.0]
    assert p180.EXPECTED_PHASE_STEP_DEG == pytest.approx(60.0)


def test_p180_target_angle_calculation_is_sane(p180) -> None:
    sanity = read_csv(p180.SANITY_CSV)[0]
    period = float(sanity["supercell_period_nm"])
    pitch = float(sanity["dimer_pitch_nm"])
    target_angle = math.degrees(math.asin(float(sanity["wavelength_nm"]) / period))

    assert int(sanity["K"]) == 6
    assert target_angle == pytest.approx(15.0)
    assert pitch == pytest.approx(period / 6.0)
    assert float(sanity["expected_phase_step_deg"]) == pytest.approx(60.0)


def test_p180_no_overclaim_wording_exists(p180) -> None:
    text = p180.REPORT_MD.read_text(encoding="utf-8")
    sanity = read_csv(p180.SANITY_CSV)[0]

    assert "This is a Stage 10 K=6 design plan only" in text
    assert "No K=6 FDTD has been run" in text
    assert "No +15 deg steering has been verified yet" in text
    assert "supercell assembly input for later FDTD" in text
    assert sanity["no_steering_claim"] == "True"
