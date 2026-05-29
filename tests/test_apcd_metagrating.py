from __future__ import annotations

import csv
import math
import subprocess
import sys
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_metagrating import (
    APCD_METAGRATING_GEOMETRY_FIELDS,
    build_apcd_k_dimer_metagrating_geometry,
    calculate_supercell_period_nm,
    write_apcd_metagrating_dry_run_outputs,
)
from metasurface.config import load_apcd_single_dimer_config


def _alpha_pass_config():
    return load_apcd_single_dimer_config(REPO_ROOT / "configs" / "apcd_fig2_elliptical_633nm_alpha_pass.yaml")


def test_k6_geometry_has_12_nanopillars_and_expected_pitch() -> None:
    config = _alpha_pass_config()
    rows = build_apcd_k_dimer_metagrating_geometry(config, K=6)
    expected_period = 633 / math.sin(math.radians(15))

    assert len(rows) == 12
    assert math.isclose(rows[0]["supercell_period_nm"], expected_period)
    assert math.isclose(rows[0]["dimer_pitch_nm"], expected_period / 6)
    assert len({row["global_pillar_index"] for row in rows}) == 12
    assert Counter(row["dimer_index"] for row in rows) == Counter({index: 2 for index in range(6)})


def test_k7_geometry_has_14_nanopillars_and_expected_pitch() -> None:
    config = _alpha_pass_config()
    rows = build_apcd_k_dimer_metagrating_geometry(config, K=7)
    expected_period = calculate_supercell_period_nm(633, 15)

    assert len(rows) == 14
    assert math.isclose(rows[0]["supercell_period_nm"], expected_period)
    assert math.isclose(rows[0]["dimer_pitch_nm"], expected_period / 7)
    assert len({row["global_pillar_index"] for row in rows}) == 14
    assert Counter(row["dimer_index"] for row in rows) == Counter({index: 2 for index in range(7)})


def test_metagrating_inherits_alpha_pass_dimer_geometry() -> None:
    config = _alpha_pass_config()
    rows = build_apcd_k_dimer_metagrating_geometry(config, K=7)

    pillar_1_rows = [row for row in rows if row["pillar_index_in_dimer"] == 1]
    pillar_2_rows = [row for row in rows if row["pillar_index_in_dimer"] == 2]

    assert all(row["length_nm"] == 130 for row in pillar_1_rows)
    assert all(row["width_nm"] == 70 for row in pillar_1_rows)
    assert all(row["rotation_deg"] == 67.5 for row in pillar_1_rows)
    assert all(row["frac_x"] == 0.75 for row in pillar_1_rows)
    assert all(row["frac_y"] == 0.75 for row in pillar_1_rows)

    assert all(row["length_nm"] == 85 for row in pillar_2_rows)
    assert all(row["width_nm"] == 150 for row in pillar_2_rows)
    assert all(row["rotation_deg"] == 112.5 for row in pillar_2_rows)
    assert all(row["frac_x"] == 0.25 for row in pillar_2_rows)
    assert all(row["frac_y"] == 0.25 for row in pillar_2_rows)
    assert not any(row["length_nm"] == 150 and row["width_nm"] == 85 for row in pillar_2_rows)


def test_local_fractional_coordinates_are_applied_inside_each_dimer_cell() -> None:
    config = _alpha_pass_config()
    rows = build_apcd_k_dimer_metagrating_geometry(config, K=6)
    pitch = rows[0]["dimer_pitch_nm"]
    period = rows[0]["supercell_period_nm"]

    first_pillar_1 = rows[0]
    first_pillar_2 = rows[1]
    first_center = -0.5 * period + 0.5 * pitch

    assert math.isclose(first_pillar_1["x_nm"], first_center + 0.25 * pitch)
    assert math.isclose(first_pillar_2["x_nm"], first_center - 0.25 * pitch)
    assert math.isclose(first_pillar_1["y_nm"], 85.0)
    assert math.isclose(first_pillar_2["y_nm"], -85.0)


def test_dry_run_outputs_write_csv_and_summary(tmp_path: Path) -> None:
    config = _alpha_pass_config()
    csv_path, summary_path, rows = write_apcd_metagrating_dry_run_outputs(
        config=config,
        K=6,
        output_dir=tmp_path / "apcd_k6_metagrating_633nm",
    )

    assert csv_path.exists()
    assert summary_path.exists()
    assert len(rows) == 12

    with csv_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded_rows = list(reader)

    assert reader.fieldnames == APCD_METAGRATING_GEOMETRY_FIELDS
    assert len(loaded_rows) == 12
    assert loaded_rows[0]["K"] == "6"
    assert "dry-run geometry definition only" in summary_path.read_text(encoding="utf-8")


def test_cli_all_dry_run_writes_k6_and_k7_outputs(tmp_path: Path) -> None:
    script_path = REPO_ROOT / "scripts" / "14_build_apcd_k_dimer_metagrating.py"
    completed = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "--all",
            "--dry-run",
            "--output-root",
            str(tmp_path),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "K=6" in completed.stdout
    assert "K=7" in completed.stdout
    assert (tmp_path / "apcd_k6_metagrating_633nm" / "geometry.csv").exists()
    assert (tmp_path / "apcd_k6_metagrating_633nm" / "geometry_summary.md").exists()
    assert (tmp_path / "apcd_k7_metagrating_633nm" / "geometry.csv").exists()
    assert (tmp_path / "apcd_k7_metagrating_633nm" / "geometry_summary.md").exists()
