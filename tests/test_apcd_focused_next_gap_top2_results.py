from __future__ import annotations

import csv
import importlib.util
import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/56_run_and_summarize_apcd_k6_focused_next_gap_top2.py"
CONFIG_DIR = REPO_ROOT / "configs/apcd_k6_phase_state_candidates"
POOL_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/focused_next_gap_candidate_pool_v3.csv"
RESULT_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/focused_next_gap_top2_fdtd_results_v3.csv"
SUMMARY_MD = REPO_ROOT / "outputs/apcd_k6_active_learning/focused_next_gap_top2_fdtd_results_v3_summary.md"
REPORT_MD = REPO_ROOT / "reports/apcd_k6_focused_next_gap_top2_fdtd_result_note.md"
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.config import load_apcd_single_dimer_config


spec = importlib.util.spec_from_file_location("focused_top2", SCRIPT_PATH)
focused_top2 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(focused_top2)

TOP2_IDS = ["focus_zero_leakred_07", "focus_neg60_geom_04"]
SKIPPED_IDS = ["focus_neg120_asym_03", "focus_pi_wrap_04"]


def _pool_rows_by_id() -> dict[str, dict[str, str]]:
    with POOL_CSV.open("r", newline="", encoding="utf-8") as handle:
        return {row["candidate_id"]: row for row in csv.DictReader(handle)}


def _result_rows() -> list[dict[str, str]]:
    with RESULT_CSV.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_only_top2_yaml_configs_are_generated() -> None:
    for candidate_id in TOP2_IDS:
        assert (CONFIG_DIR / f"{candidate_id}.yaml").exists()
    for candidate_id in SKIPPED_IDS:
        assert not (CONFIG_DIR / f"{candidate_id}.yaml").exists()


def test_yaml_metadata_and_geometry_match_pool() -> None:
    pool_by_id = _pool_rows_by_id()
    for candidate_id in TOP2_IDS:
        data = yaml.safe_load((CONFIG_DIR / f"{candidate_id}.yaml").read_text(encoding="utf-8"))
        config = load_apcd_single_dimer_config(CONFIG_DIR / f"{candidate_id}.yaml")
        expected = pool_by_id[candidate_id]

        assert data["candidate"]["variant_id"] == candidate_id
        assert data["candidate"]["candidate_type"] == expected["candidate_family"]
        assert data["candidate"]["target_bin_deg"] == int(float(expected["target_bin_deg"]))
        assert data["candidate"]["source_stage"] == expected["source_stage"]
        assert data["candidate"]["anchor_candidate"] == expected["anchor_candidate"]
        assert data["candidate"]["risk_level"] == expected["risk_level"]
        assert data["candidate"]["design_rationale"] == expected["design_rationale"]
        assert config.geometry.nanopillar_1.length_nm == float(expected["p1_length_nm"])
        assert config.geometry.nanopillar_1.width_nm == float(expected["p1_width_nm"])
        assert config.geometry.nanopillar_2.length_nm == float(expected["p2_length_nm"])
        assert config.geometry.nanopillar_2.width_nm == float(expected["p2_width_nm"])


def test_result_csv_contains_only_top2_and_required_columns() -> None:
    rows = _result_rows()
    ids = [row["candidate_id"] for row in rows]

    assert ids == TOP2_IDS
    for skipped in SKIPPED_IDS:
        assert skipped not in ids
    with RESULT_CSV.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == focused_top2.FOCUSED_NEXT_GAP_TOP2_RESULT_FIELDS


def test_wrapped_phase_error_and_statuses() -> None:
    rows = {row["candidate_id"]: row for row in _result_rows()}

    assert focused_top2.angular_distance_deg(179.0, -179.0) == 2.0
    assert abs(float(rows["focus_zero_leakred_07"]["phase_error_to_target_deg"]) - 30.534894730576525) < 1e-12
    assert abs(float(rows["focus_neg60_geom_04"]["phase_error_to_target_deg"]) - 143.13394588891055) < 1e-12
    assert rows["focus_zero_leakred_07"]["early_pass"] == "False"
    assert rows["focus_zero_leakred_07"]["target_bin_status"] == "evidence_only"
    assert rows["focus_neg60_geom_04"]["early_pass"] == "True"
    assert rows["focus_neg60_geom_04"]["target_bin_status"] == "open_gap"


def test_early_pass_and_target_bin_status_helpers() -> None:
    strong = focused_top2.result_row_from_values(
        candidate_id="strong",
        target_bin_deg=0.0,
        candidate_family="unit",
        status="ok",
        target_conversion=0.7,
        opposite_spin_leakage=0.1,
        conversion_to_leakage_ratio=7.0,
        PD=0.0,
        total_transmission=0.1,
        t_alpha_star_from_alpha="1+0j",
    )
    evidence = focused_top2.result_row_from_values(
        candidate_id="evidence",
        target_bin_deg=0.0,
        candidate_family="unit",
        status="ok",
        target_conversion=0.7,
        opposite_spin_leakage=0.4,
        conversion_to_leakage_ratio=1.0,
        PD=0.0,
        total_transmission=0.1,
        t_alpha_star_from_alpha="1+0j",
    )
    open_gap = focused_top2.result_row_from_values(
        candidate_id="usable_not_target",
        target_bin_deg=-60.0,
        candidate_family="unit",
        status="ok",
        target_conversion=0.7,
        opposite_spin_leakage=0.1,
        conversion_to_leakage_ratio=7.0,
        PD=0.0,
        total_transmission=0.1,
        t_alpha_star_from_alpha="1+0j",
    )

    assert strong["early_pass"] is True
    assert strong["target_bin_status"] == "strong_covered"
    assert evidence["early_pass"] is False
    assert evidence["target_bin_status"] == "evidence_only"
    assert open_gap["early_pass"] is True
    assert open_gap["target_bin_status"] == "open_gap"


def test_config_dry_run_writes_only_top2_and_no_fsp_or_results(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--write-configs",
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
    assert sorted(path.name for path in (tmp_path / "configs").glob("*.yaml")) == [
        "focus_neg60_geom_04.yaml",
        "focus_zero_leakred_07.yaml",
    ]
    assert list(tmp_path.rglob("*.fsp")) == []
    assert list(tmp_path.rglob("results.csv")) == []
    assert list(tmp_path.rglob("pre_run_X.fsp")) == []
    assert list(tmp_path.rglob("pre_run_Y.fsp")) == []


def test_script_and_report_boundaries() -> None:
    script = SCRIPT_PATH.read_text(encoding="utf-8")
    text = SUMMARY_MD.read_text(encoding="utf-8") + "\n" + REPORT_MD.read_text(encoding="utf-8")

    assert "import lumapi" not in script
    assert "APCDSingleDimerRunner" not in script
    assert "fdtd.run" not in script
    assert "fdtd.save" not in script
    assert "focus_neg120_asym_03" in text
    assert "focus_pi_wrap_04" in text
    assert "full 40-row focused pool" in text
    assert "not a +15 deg steering result" in text
    assert "does not complete the K=6 phase-state library" in text
    assert "No raw `results.csv`, `.fsp`, `pre_run_X.fsp`, or `pre_run_Y.fsp`" in text
