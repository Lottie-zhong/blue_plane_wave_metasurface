from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts/82_generate_apcd_p196_h320_zero_scout.py"
SUMMARY_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/p196_h320_zero_bin_mechanism_scout_candidates.csv"
VALIDATION_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/p196_h320_zero_bin_mechanism_scout_geometry_validation.csv"
REPORT_MD = REPO_ROOT / "reports/p196_h320_zero_bin_mechanism_scout.md"
CONFIG_DIR = REPO_ROOT / "configs/apcd_k6_phase_state_candidates"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_p196_summary_pool_count_columns_and_groups() -> None:
    rows = _rows(SUMMARY_CSV)
    assert len(rows) == 12
    assert len({row["candidate_id"] for row in rows}) == 12
    required = {
        "candidate_id",
        "group",
        "base_anchor",
        "geometry_changes",
        "expected_mechanism",
        "status",
        "config_path",
    }
    assert required.issubset(rows[0])
    assert {row["height_nm"] for row in rows} == {"320"}
    assert {row["target_bin_deg"] for row in rows} == {"0"}
    assert {row["status"] for row in rows} == {"not_evaluated"}
    assert {
        "dimer_gap_coupling_offset",
        "mild_notch_slot_perturbation",
        "weak_scalar_helper",
        "balanced_p1_p2_geometry_compensation",
    }.issubset({row["group"] for row in rows})


def test_p196_configs_exist_and_keep_fixed_height_boundary() -> None:
    rows = _rows(SUMMARY_CSV)
    for row in rows:
        config_path = CONFIG_DIR / f"{row['candidate_id']}.yaml"
        assert config_path.exists()
        with config_path.open("r", encoding="utf-8") as handle:
            config = yaml.safe_load(handle)
        assert config["candidate"]["variant_id"] == row["candidate_id"]
        assert config["geometry"]["height_nm"] == 320
        assert config["candidate"]["target_bins_deg"] == "0"
        assert config["boundary"]["not_mixed_height"] is True
        assert config["boundary"]["no_fdtd_run_by_generator"] is True
        assert config["boundary"]["not_phase_ramp_supercell"] is True


def test_p196_geometry_validation_passes_for_small_pool() -> None:
    rows = _rows(VALIDATION_CSV)
    assert len(rows) == 12
    assert all(row["overall_geometry_pass"] == "True" for row in rows)
    assert all(row["recommended_for_fdtd"] == "True" for row in rows)
    assert all(float(row["same_cell_min_gap_nm"]) >= 5.0 for row in rows)
    assert all(float(row["periodic_image_min_gap_nm"]) >= 5.0 for row in rows)
    assert all(row["boundary_pass"] == "True" for row in rows)
    assert all(row["duplicate_candidate_id_pass"] == "True" for row in rows)
    assert all(row["duplicate_geometry_pass"] == "True" for row in rows)


def test_p196_dry_run_no_fdtd_lumapi_fsp_or_extra_configs(tmp_path) -> None:
    config_dir = tmp_path / "configs"
    before = set(config_dir.glob("*.yaml"))
    fsp_before = set(REPO_ROOT.glob("**/*p196*.fsp"))
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--dry-run",
            "--config-dir",
            str(config_dir),
            "--summary-csv",
            str(tmp_path / "summary.csv"),
            "--validation-csv",
            str(tmp_path / "validation.csv"),
            "--report",
            str(tmp_path / "report.md"),
        ],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    after = set(config_dir.glob("*.yaml"))
    fsp_after = set(REPO_ROOT.glob("**/*p196*.fsp"))
    assert before == after
    assert fsp_before == fsp_after
    assert "no_fdtd_no_lumapi_no_fsp_no_k6_phase_ramp" in completed.stdout
    assert not (tmp_path / "summary.csv").exists()
    assert not (tmp_path / "report.md").exists()


def test_p196_report_scope() -> None:
    text = REPORT_MD.read_text(encoding="utf-8")
    assert "Stage 09 fixed-height h320" in text
    assert "does not run FDTD" in text
    assert "does not call lumapi" in text
    assert "does not export `.fsp`" in text
    assert "does not enter K6 phase-ramp supercell" in text
    assert "does not claim steering" in text
