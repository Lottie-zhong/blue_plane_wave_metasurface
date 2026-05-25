from __future__ import annotations

import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.config import load_sweep_config
from metasurface.h_sweep import build_h_sweep_values


def test_load_plane_wave_h_sweep_config() -> None:
    config = load_sweep_config(REPO_ROOT / "configs" / "plane_wave_h_sweep.yaml")

    assert config.project.name == "blue_plane_wave_metasurface"
    assert config.target.wavelength_nm == 450
    assert config.target.incident_polarization == "LCP"
    assert config.target.output_polarization == "RCP"
    assert config.geometry.atom_period_nm == 220
    assert config.thickness_sweep.h_initial_nm == 350
    assert config.output.result_dir == Path("outputs/plane_wave_h_sweep")


def test_build_h_sweep_values_inclusive() -> None:
    config = load_sweep_config(REPO_ROOT / "configs" / "plane_wave_h_sweep.yaml")

    assert build_h_sweep_values(config) == [250, 275, 300, 325, 350, 375, 400, 425, 450]

