from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts/62_run_apcd_k6_nextgen_phase_knob_pilot.py"
WEAK_POOL = REPO_ROOT / "outputs/apcd_k6_active_learning/weak_helper_candidate_pool_v6.csv"
WEAK_VALIDATION = REPO_ROOT / "outputs/apcd_k6_active_learning/weak_helper_candidate_pool_v6_geometry_validation.csv"
RESULTS = REPO_ROOT / "outputs/apcd_k6_active_learning/nextgen_phase_knob_pilot_fdtd_results_v6.csv"
DATASET_V6 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v6.csv"
COVERAGE_V6 = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_coverage_v6.csv"
REPORT = REPO_ROOT / "reports/apcd_k6_nextgen_phase_knob_pilot_fdtd_v6_note.md"

PILOT_IDS = ["ng_zero_rot_release_07", "ng_neg60_dxdy_release_08", "wh_zero_aux_phase_01"]


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_weak_helper_mini_pool_generated_and_validated() -> None:
    rows = _rows(WEAK_POOL)
    validation = _rows(WEAK_VALIDATION)
    assert len(rows) == 10
    assert len(validation) == 10
    assert all(row["candidate_family"] == "apcd_core_plus_weak_helper" for row in rows)
    assert all(row["helper_role"] == "weak_auxiliary_phase_helper" for row in rows)
    assert sum(row["overall_geometry_pass"] == "True" for row in validation) == 4
    assert any(row["candidate_id"] == "wh_zero_aux_phase_01" and row["recommended_for_fdtd"] == "True" for row in validation)


def test_pilot_yaml_configs_include_helper_only_for_helper_candidate() -> None:
    for candidate_id in PILOT_IDS:
        path = REPO_ROOT / f"configs/apcd_k6_phase_state_candidates/{candidate_id}.yaml"
        assert path.exists()
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data["candidate"]["variant_id"] == candidate_id
        assert data["boundary"]["not_phase_ramp_supercell"] is True
        if candidate_id.startswith("wh_"):
            assert data["candidate"]["helper_role"] == "weak_auxiliary_phase_helper"
            assert data["geometry"]["nanopillar_helper"]["role"] == "weak_auxiliary_phase_helper"
        else:
            assert "nanopillar_helper" not in data["geometry"]


def test_pilot_results_contain_only_three_completed_candidates() -> None:
    rows = _rows(RESULTS)
    assert [row["candidate_id"] for row in rows] == PILOT_IDS
    assert {row["run_status"] for row in rows} == {"completed"}
    required = {
        "candidate_id",
        "family",
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
        "notes",
    }
    assert required.issubset(rows[0].keys())
    assert all(row["target_bin_status"] == "open_gap" for row in rows)
    assert all(row["early_pass"] == "False" for row in rows)


def test_dataset_v6_and_coverage_v6_are_updated() -> None:
    dataset = _rows(DATASET_V6)
    assert len(dataset) == 30
    ids = {row["variant_id"] for row in dataset}
    assert set(PILOT_IDS).issubset(ids)
    coverage = {float(row["phase_bin_deg"]): row["coverage_status"] for row in _rows(COVERAGE_V6)}
    assert coverage[0.0] == "evidence_only"
    assert coverage[60.0] == "early_covered"
    assert coverage[120.0] == "strong_covered"
    assert coverage[-180.0] == "evidence_only"
    assert coverage[-120.0] == "open_gap"
    assert coverage[-60.0] == "open_gap"


def test_dry_run_does_not_generate_extra_yaml_or_fsp() -> None:
    yaml_before = {path.name for path in (REPO_ROOT / "configs/apcd_k6_phase_state_candidates").glob("*.yaml")}
    fsp_before = {path.name for path in REPO_ROOT.glob("*.fsp")}
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--dry-run"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    yaml_after = {path.name for path in (REPO_ROOT / "configs/apcd_k6_phase_state_candidates").glob("*.yaml")}
    fsp_after = {path.name for path in REPO_ROOT.glob("*.fsp")}
    assert yaml_before == yaml_after
    assert fsp_before == fsp_after
    assert "config_validation_only_no_fdtd_no_lumapi_no_fsp" in completed.stdout


def test_report_states_scope_boundaries() -> None:
    text = REPORT.read_text(encoding="utf-8")
    assert "No full 60-row nextgen pool" in text
    assert "K=7" in text
    assert "phase-ramp supercell" in text
    assert "+15 deg steering claim" in text
    assert "complete K=6 phase-state library claim" in text
