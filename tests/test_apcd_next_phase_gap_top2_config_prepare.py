from __future__ import annotations

import csv
import importlib.util
import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/51_prepare_apcd_k6_next_phase_gap_top2_configs.py"
CONFIG_DIR = REPO_ROOT / "configs/apcd_k6_phase_state_candidates"
POOL_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/next_phase_gap_candidate_pool_v2.csv"

SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.config import load_apcd_single_dimer_config


spec = importlib.util.spec_from_file_location("next_top2_prepare", SCRIPT_PATH)
next_top2_prepare = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(next_top2_prepare)


TOP2_IDS = ["next_zero_rot_anchor_03", "next_rot_anchor_04"]
SKIPPED_IDS = ["next_mixed_bridge_03", "next_pi_mixed_bridge_03"]


def _pool_rows_by_id() -> dict[str, dict[str, str]]:
    with POOL_CSV.open("r", newline="", encoding="utf-8") as handle:
        return {row["candidate_id"]: row for row in csv.DictReader(handle)}


def _yaml_data(candidate_id: str) -> dict[str, object]:
    return yaml.safe_load((CONFIG_DIR / f"{candidate_id}.yaml").read_text(encoding="utf-8"))


def test_top2_yaml_files_are_generated_and_skipped_configs_are_absent() -> None:
    for candidate_id in TOP2_IDS:
        assert (CONFIG_DIR / f"{candidate_id}.yaml").exists()
    for candidate_id in SKIPPED_IDS:
        assert not (CONFIG_DIR / f"{candidate_id}.yaml").exists()


def test_candidate_id_and_metadata_are_preserved() -> None:
    pool_by_id = _pool_rows_by_id()
    for candidate_id in TOP2_IDS:
        data = _yaml_data(candidate_id)
        expected = pool_by_id[candidate_id]

        assert data["candidate"]["variant_id"] == candidate_id
        assert data["candidate"]["candidate_type"] == expected["candidate_family"]
        assert data["candidate"]["target_bin_deg"] == int(float(expected["target_bin_deg"]))
        assert data["candidate"]["source_stage"] == expected["source_stage"]
        assert data["candidate"]["anchor_candidate"] == expected["anchor_candidate"]
        assert data["candidate"]["source_pool_csv"] == "outputs/apcd_k6_active_learning/next_phase_gap_candidate_pool_v2.csv"
        assert data["candidate"]["source_selection_csv"] == "outputs/apcd_k6_active_learning/next_phase_gap_fdtd_selection_v2.csv"
        assert data["boundary"]["no_fdtd_run_in_09_p22"] is True
        assert data["boundary"]["no_fsp_export_in_09_p22"] is True


def test_yaml_geometry_matches_candidate_pool_and_config_loader_accepts_it() -> None:
    pool_by_id = _pool_rows_by_id()
    for candidate_id in TOP2_IDS:
        config_path = CONFIG_DIR / f"{candidate_id}.yaml"
        config = load_apcd_single_dimer_config(config_path)
        expected = pool_by_id[candidate_id]

        assert config.geometry.nanopillar_1.length_nm == float(expected["p1_length_nm"])
        assert config.geometry.nanopillar_1.width_nm == float(expected["p1_width_nm"])
        assert config.geometry.nanopillar_2.length_nm == float(expected["p2_length_nm"])
        assert config.geometry.nanopillar_2.width_nm == float(expected["p2_width_nm"])
        assert config.geometry.nanopillar_1.rotation_deg == float(expected["p1_rotation_deg"])
        assert config.geometry.nanopillar_2.rotation_deg == float(expected["p2_rotation_deg"])
        assert config.output.result_dir.as_posix().endswith(f"/{candidate_id}")


def test_prepare_script_dry_run_writes_only_top2_and_no_fsp_or_results(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--dry-run",
            "--config-dir",
            str(tmp_path / "configs"),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "dry_run_validation_pass=True" in completed.stdout
    assert "no_fdtd" in completed.stdout
    assert "no_lumapi" in completed.stdout
    assert "no_fsp" in completed.stdout
    assert sorted(path.name for path in (tmp_path / "configs").glob("*.yaml")) == [
        "next_rot_anchor_04.yaml",
        "next_zero_rot_anchor_03.yaml",
    ]
    assert list(tmp_path.rglob("*.fsp")) == []
    assert list(tmp_path.rglob("results.csv")) == []
    assert list(tmp_path.rglob("pre_run_X.fsp")) == []
    assert list(tmp_path.rglob("pre_run_Y.fsp")) == []


def test_validate_top2_configs_returns_pass_rows() -> None:
    rows = next_top2_prepare.top2_candidate_rows(
        next_top2_prepare.read_csv_rows(next_top2_prepare.DEFAULT_SELECTION_CSV),
        next_top2_prepare.read_csv_rows(next_top2_prepare.DEFAULT_POOL_CSV),
    )
    validation = next_top2_prepare.validate_top2_configs(
        [CONFIG_DIR / f"{candidate_id}.yaml" for candidate_id in TOP2_IDS],
        rows,
    )

    assert [row["candidate_id"] for row in validation] == TOP2_IDS
    assert {row["validation_pass"] for row in validation} == {True}


def test_script_does_not_call_lumapi_fdtd_run_or_export_fsp() -> None:
    text = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "import lumapi" not in text
    assert "APCDSingleDimerRunner" not in text
    assert "fdtd.run" not in text
    assert "fdtd.save" not in text
    assert "setup_only" not in text
