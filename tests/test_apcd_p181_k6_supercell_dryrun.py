from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def p181():
    path = REPO_ROOT / "scripts/manual_p181_generate_k6_supercell_dryrun_config.py"
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


def test_p181_reads_p180_plan(p181) -> None:
    rows = p181.read_csv_rows(p181.P180_PLAN_CSV)

    assert len(rows) == 6
    assert [int(row["supercell_index"]) for row in rows] == list(range(6))


def test_p181_generated_config_has_k6_dimers(p181) -> None:
    config = yaml.safe_load(p181.CONFIG_YAML.read_text(encoding="utf-8"))

    assert config["supercell"]["K"] == 6
    assert len(config["dimers"]) == 6
    assert config["boundary"]["fdtd_run_performed"] is False


def test_p181_six_bins_are_present(p181) -> None:
    config = yaml.safe_load(p181.CONFIG_YAML.read_text(encoding="utf-8"))

    assert sorted(dimer["target_bin_deg"] for dimer in config["dimers"]) == [-180, -120, -60, 0, 60, 120]


def test_p181_no_overclaim_wording_exists(p181) -> None:
    text = p181.REPORT_MD.read_text(encoding="utf-8")

    assert "K=6 supercell dry-run/config generation step only" in text
    assert "No K=6 FDTD has been run" in text
    assert "No +15 deg beam steering has been verified" in text
    assert "later server-side FDTD validation" in text


def test_p181_dry_run_flag_is_false_for_fdtd(p181) -> None:
    sanity = read_csv(p181.SANITY_CSV)[0]

    assert sanity["fdtd_run_performed"] == "False"
    assert sanity["no_steering_claim"] == "True"


def test_p181_min_gap_sanity_is_present(p181) -> None:
    sanity = read_csv(p181.SANITY_CSV)[0]

    assert float(sanity["min_same_cell_gap_nm"]) > 0.0
    assert float(sanity["min_adjacent_dimer_gap_nm"]) > 0.0
    assert sanity["no_overlap_detected"] == "True"
