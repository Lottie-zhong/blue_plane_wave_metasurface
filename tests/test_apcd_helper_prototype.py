from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts/64_run_apcd_k6_helper_prototype_batch.py"
POOL = REPO_ROOT / "outputs/apcd_k6_active_learning/helper_prototype_candidate_pool_v7.csv"
VALIDATION = REPO_ROOT / "outputs/apcd_k6_active_learning/helper_prototype_candidate_pool_v7_geometry_validation.csv"
RESULTS = REPO_ROOT / "outputs/apcd_k6_active_learning/helper_prototype_fdtd_results_v7.csv"
DATASET_V7 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v7.csv"
COVERAGE_V7 = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_coverage_v7.csv"
REPORT = REPO_ROOT / "reports/apcd_k6_helper_prototype_fdtd_v7_note.md"

VALID_IDS = ["h2_square_load_01", "h2_nearsquare_load_02", "h2_weak_aniso_03"]
ALL_IDS = [*VALID_IDS, "h2_phase_delay_04"]


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_helper_prototype_pool_has_four_fabrication_friendly_rows() -> None:
    rows = _rows(POOL)
    assert [row["candidate_id"] for row in rows] == ALL_IDS
    assert len(rows) == 4
    required = {
        "candidate_id",
        "family",
        "helper_role",
        "target_bin_deg",
        "helper_type",
        "p3_shape",
        "p3_length_nm",
        "p3_width_nm",
        "p3_rotation_deg",
        "p3_frac_x",
        "p3_frac_y",
        "p1_length_nm",
        "p1_width_nm",
        "p2_length_nm",
        "p2_width_nm",
        "period_x_nm",
        "period_y_nm",
        "height_nm",
    }
    assert required.issubset(rows[0].keys())
    assert all(row["family"] == "apcd_core_plus_helper_prototype" for row in rows)
    assert all(row["helper_role"] == "weak_auxiliary_phase_helper" for row in rows)
    assert {row["p3_shape"] for row in rows} <= {"square", "near-square rectangle", "rectangular nanofin"}
    assert all(row["p2_length_nm"] == "85" and row["p2_width_nm"] == "150" for row in rows)
    assert all(row["notes"].find("not another APCD dimer") >= 0 for row in rows)


def test_helper_prototype_geometry_validation_and_yaml_scope() -> None:
    rows = _rows(VALIDATION)
    assert len(rows) == 4
    assert sum(row["overall_geometry_pass"] == "True" for row in rows) == 3
    by_id = {row["candidate_id"]: row for row in rows}
    assert by_id["h2_phase_delay_04"]["recommended_for_fdtd"] == "False"
    assert float(by_id["h2_phase_delay_04"]["same_cell_min_gap_nm"]) < 50.0
    assert all(float(by_id[candidate_id]["same_cell_min_gap_nm"]) >= 50.0 for candidate_id in VALID_IDS)
    for candidate_id in VALID_IDS:
        assert (REPO_ROOT / f"configs/apcd_k6_phase_state_candidates/{candidate_id}.yaml").exists()
    assert not (REPO_ROOT / "configs/apcd_k6_phase_state_candidates/h2_phase_delay_04.yaml").exists()


def test_helper_prototype_yaml_configs_are_loadable_and_preserve_metadata() -> None:
    for candidate_id in VALID_IDS:
        path = REPO_ROOT / f"configs/apcd_k6_phase_state_candidates/{candidate_id}.yaml"
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data["candidate"]["variant_id"] == candidate_id
        assert data["candidate"]["helper_role"] == "weak_auxiliary_phase_helper"
        assert data["geometry"]["minimum_gap_nm"] == 50
        assert data["geometry"]["nanopillar_helper"]["role"] == "weak_auxiliary_phase_helper"
        assert data["boundary"]["not_random_helper_shape"] is True
        assert data["boundary"]["not_freeform_helper_shape"] is True
        assert data["boundary"]["not_phase_ramp_supercell"] is True


def test_helper_prototype_results_and_statuses() -> None:
    rows = _rows(RESULTS)
    assert [row["candidate_id"] for row in rows] == ALL_IDS
    required = {
        "candidate_id",
        "family",
        "helper_role",
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
    by_id = {row["candidate_id"]: row for row in rows}
    for candidate_id in VALID_IDS:
        row = by_id[candidate_id]
        assert row["run_status"] == "completed"
        assert row["status"] == "ok"
        assert row["early_pass"] == "True"
        assert row["target_bin_status"] == "usable_but_not_target"
        assert float(row["opposite_spin_leakage"]) <= 0.2
        assert float(row["conversion_to_leakage_ratio"]) >= 6.0
    assert by_id["h2_phase_delay_04"]["run_status"] == "not_run_geometry_failed"
    assert by_id["h2_phase_delay_04"]["target_bin_status"] == "not_run_geometry_failed"


def test_dataset_v7_and_coverage_v7_are_updated_without_library_claim() -> None:
    dataset = _rows(DATASET_V7)
    assert len(dataset) == 33
    ids = {row["variant_id"] for row in dataset}
    assert set(VALID_IDS).issubset(ids)
    assert "h2_phase_delay_04" not in ids
    coverage = {float(row["phase_bin_deg"]): row["coverage_status"] for row in _rows(COVERAGE_V7)}
    assert coverage == {
        0.0: "evidence_only",
        60.0: "early_covered",
        120.0: "strong_covered",
        -180.0: "evidence_only",
        -120.0: "open_gap",
        -60.0: "open_gap",
    }


def test_dry_run_does_not_generate_fsp_or_extra_yaml() -> None:
    yaml_before = {path.name for path in (REPO_ROOT / "configs/apcd_k6_phase_state_candidates").glob("h2_*.yaml")}
    fsp_before = {path.name for path in REPO_ROOT.glob("*.fsp")}
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--dry-run"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    yaml_after = {path.name for path in (REPO_ROOT / "configs/apcd_k6_phase_state_candidates").glob("h2_*.yaml")}
    fsp_after = {path.name for path in REPO_ROOT.glob("*.fsp")}
    assert yaml_before == yaml_after
    assert fsp_before == fsp_after
    assert "no_fdtd_no_lumapi_no_fsp" in completed.stdout


def test_report_states_scope_and_no_unsupported_claims() -> None:
    text = REPORT.read_text(encoding="utf-8")
    assert "No full 48-row helper v2 pool" in text
    assert "K=7" in text
    assert "phase-ramp supercell" in text
    assert "TiO2/450 nm" in text
    assert "ML/DenseNet/cVAE training" in text
    assert "random/freeform helper shape" in text
    assert "+15 deg steering claim" in text
    assert "complete K=6 phase-state library claim" in text
    assert "does not close the remaining major target gaps" in text
