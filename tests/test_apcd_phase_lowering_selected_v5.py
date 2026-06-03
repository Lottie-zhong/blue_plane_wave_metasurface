from __future__ import annotations

import csv
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest
import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/60_run_and_summarize_apcd_k6_phase_lowering_selected.py"
RESULT_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_lowering_selected_fdtd_results_v4.csv"
DATASET_V5 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v5.csv"
COVERAGE_V5 = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_coverage_v5.csv"
REPORT = REPO_ROOT / "reports/apcd_k6_phase_lowering_selected_fdtd_and_coverage_v5_note.md"

SELECTED_IDS = ["pl_zero_bridge_04", "pl_neg60_focus_push_05", "pl_neg120_aspect_03", "pl_pi_wrap_04"]


@pytest.fixture(scope="module")
def p29_module():
    spec = importlib.util.spec_from_file_location("p29_phase_lowering_selected", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_selected_yaml_configs_exist_and_match_ids() -> None:
    for candidate_id in SELECTED_IDS:
        path = REPO_ROOT / f"configs/apcd_k6_phase_state_candidates/{candidate_id}.yaml"
        assert path.exists()
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data["candidate"]["variant_id"] == candidate_id
        assert data["candidate"]["source_stage"] == "09-P29/P32"
        assert data["boundary"]["not_phase_ramp_supercell"] is True
        assert data["boundary"]["not_steering_result"] is True


def test_results_csv_contains_required_metrics_and_only_selected_candidates() -> None:
    rows = _rows(RESULT_CSV)
    assert [row["candidate_id"] for row in rows] == SELECTED_IDS
    required = {
        "candidate_id",
        "target_bin_deg",
        "phase_deg",
        "phase_error_to_target_deg",
        "target_conversion",
        "opposite_spin_leakage",
        "conversion_to_leakage_ratio",
        "PD",
        "total_transmission",
        "t_alpha_star_from_alpha",
        "early_pass",
        "target_bin_status",
        "run_status",
    }
    assert required.issubset(rows[0].keys())
    assert {row["run_status"] for row in rows} == {"completed"}


def test_phase_error_and_early_pass_rules(p29_module) -> None:
    rows = {row["candidate_id"]: row for row in _rows(RESULT_CSV)}
    pi_row = rows["pl_pi_wrap_04"]
    assert float(pi_row["phase_error_to_target_deg"]) == pytest.approx(
        p29_module.angular_distance_deg(float(pi_row["phase_deg"]), -180.0)
    )
    assert pi_row["early_target_pass"] == "True"
    assert pi_row["early_leakage_pass"] == "False"
    assert pi_row["early_ratio_pass"] == "False"
    assert pi_row["early_pass"] == "False"
    assert pi_row["target_bin_status"] == "evidence_only"

    neg60 = rows["pl_neg60_focus_push_05"]
    assert neg60["early_pass"] == "True"
    assert neg60["target_bin_status"] == "open_gap"


def test_dataset_v5_and_coverage_v5_are_updated() -> None:
    dataset_rows = _rows(DATASET_V5)
    assert len(dataset_rows) == 27
    ids = {row["variant_id"] for row in dataset_rows}
    assert set(SELECTED_IDS).issubset(ids)

    coverage = {float(row["phase_bin_deg"]): row["coverage_status"] for row in _rows(COVERAGE_V5)}
    assert coverage[0.0] == "evidence_only"
    assert coverage[60.0] == "early_covered"
    assert coverage[120.0] == "strong_covered"
    assert coverage[-60.0] == "open_gap"
    assert coverage[-120.0] == "open_gap"
    assert coverage[-180.0] == "evidence_only"


def test_dry_run_does_not_call_fdtd_lumapi_or_generate_fsp() -> None:
    before = {path.name for path in REPO_ROOT.glob("*.fsp")}
    completed = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--dry-run"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    after = {path.name for path in REPO_ROOT.glob("*.fsp")}
    assert before == after
    assert "dry_run_validation_pass=True" in completed.stdout
    assert "no_fdtd_no_lumapi_no_fsp" in completed.stdout


def test_report_states_scope_boundaries() -> None:
    text = REPORT.read_text(encoding="utf-8")
    assert "No full 42-row pool" in text
    assert "No full 42-row pool, old pool, K=7" in text
    assert "+15 deg steering claim" in text
    assert "complete K=6 phase-state library claim" in text
