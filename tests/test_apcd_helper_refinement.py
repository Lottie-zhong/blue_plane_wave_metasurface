from __future__ import annotations

import csv
import subprocess
import sys
from collections import Counter
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts/65_run_apcd_k6_helper_refinement_batch.py"
POOL = REPO_ROOT / "outputs/apcd_k6_active_learning/helper_refinement_candidate_pool_v8.csv"
VALIDATION = REPO_ROOT / "outputs/apcd_k6_active_learning/helper_refinement_candidate_pool_v8_geometry_validation.csv"
SELECTION = REPO_ROOT / "outputs/apcd_k6_active_learning/helper_refinement_fdtd_selection_v8.csv"
RESULTS = REPO_ROOT / "outputs/apcd_k6_active_learning/helper_refinement_fdtd_results_v8.csv"
DATASET_V8 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v8.csv"
COVERAGE_V8 = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_coverage_v8.csv"
REPORT = REPO_ROOT / "reports/apcd_k6_helper_refinement_fdtd_v8_note.md"

SELECTED_IDS = ["hr_aniso_push_05", "hr_aniso_push_08", "hr_phase_delay_03", "hr_lowleak_control_02"]


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_helper_refinement_pool_count_families_and_columns() -> None:
    rows = _rows(POOL)
    assert len(rows) == 16
    assert len({row["candidate_id"] for row in rows}) == 16
    required = {
        "candidate_id",
        "family",
        "target_bin_deg",
        "helper_role",
        "p3_length_nm",
        "p3_width_nm",
        "p3_rotation_deg",
        "p3_frac_x",
        "p3_frac_y",
        "expected_phase_direction",
        "design_rationale",
        "risk_level",
        "requires_fdtd",
        "status",
    }
    assert required.issubset(rows[0].keys())
    assert Counter(row["family"] for row in rows) == {
        "aniso_helper_phase_push": 8,
        "phase_delay_gap_fixed": 5,
        "lowleak_anchor_control": 3,
    }
    assert all(row["helper_role"] == "weak_auxiliary_phase_helper" for row in rows)
    assert all(row["p2_length_nm"] == "85" and row["p2_width_nm"] == "150" for row in rows)


def test_helper_refinement_geometry_validation_all_passes() -> None:
    rows = _rows(VALIDATION)
    assert len(rows) == 16
    assert sum(row["overall_geometry_pass"] == "True" for row in rows) == 16
    assert all(row["duplicate_candidate_id_pass"] == "True" for row in rows)
    assert all(row["duplicate_geometry_pass"] == "True" for row in rows)
    for row in rows:
        threshold = float(row["minimum_gap_nm_threshold"])
        assert float(row["same_cell_min_gap_nm"]) >= threshold
        assert float(row["periodic_image_min_gap_nm"]) >= threshold
        assert float(row["helper_core_min_gap_nm"]) >= threshold


def test_helper_refinement_selection_and_yaml_configs() -> None:
    rows = _rows(SELECTION)
    assert [row["candidate_id"] for row in rows] == SELECTED_IDS
    assert len(rows) == 4
    assert Counter(row["family"] for row in rows) == {
        "aniso_helper_phase_push": 2,
        "phase_delay_gap_fixed": 1,
        "lowleak_anchor_control": 1,
    }
    assert {row["status"] for row in rows} == {"selected_for_run"}
    for candidate_id in SELECTED_IDS:
        path = REPO_ROOT / f"configs/apcd_k6_phase_state_candidates/{candidate_id}.yaml"
        assert path.exists()
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        assert data["candidate"]["variant_id"] == candidate_id
        assert data["candidate"]["helper_role"] == "weak_auxiliary_phase_helper"
        assert data["geometry"]["nanopillar_helper"]["role"] == "weak_auxiliary_phase_helper"
        assert data["boundary"]["not_phase_ramp_supercell"] is True
        assert data["boundary"]["not_random_helper_shape"] is True
        assert data["boundary"]["not_freeform_helper_shape"] is True


def test_helper_refinement_results_are_top4_only_and_early_pass() -> None:
    rows = _rows(RESULTS)
    assert [row["candidate_id"] for row in rows] == SELECTED_IDS
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
    assert all(row["run_status"] == "completed" and row["status"] == "ok" for row in rows)
    assert all(row["early_pass"] == "True" for row in rows)
    assert all(float(row["opposite_spin_leakage"]) <= 0.2 for row in rows)
    assert all(float(row["conversion_to_leakage_ratio"]) >= 6.0 for row in rows)
    assert {row["target_bin_status"] for row in rows} == {"usable_but_not_target", "strong_covered"}
    assert max(float(row["phase_deg"]) for row in rows) > 131.0
    assert max(float(row["phase_deg"]) for row in rows) < 150.0


def test_dataset_v8_and_coverage_v8() -> None:
    dataset = _rows(DATASET_V8)
    assert len(dataset) == 37
    ids = {row["variant_id"] for row in dataset}
    assert set(SELECTED_IDS).issubset(ids)
    coverage = {float(row["phase_bin_deg"]): row["coverage_status"] for row in _rows(COVERAGE_V8)}
    assert coverage == {
        0.0: "evidence_only",
        60.0: "early_covered",
        120.0: "strong_covered",
        -180.0: "evidence_only",
        -120.0: "open_gap",
        -60.0: "open_gap",
    }


def test_helper_refinement_dry_run_does_not_generate_fsp_or_extra_yaml() -> None:
    yaml_before = {path.name for path in (REPO_ROOT / "configs/apcd_k6_phase_state_candidates").glob("hr_*.yaml")}
    fsp_before = {path.name for path in REPO_ROOT.glob("*.fsp")}
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--dry-run"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    yaml_after = {path.name for path in (REPO_ROOT / "configs/apcd_k6_phase_state_candidates").glob("hr_*.yaml")}
    fsp_after = {path.name for path in REPO_ROOT.glob("*.fsp")}
    assert yaml_before == yaml_after
    assert fsp_before == fsp_after
    assert "no_fdtd_no_lumapi_no_fsp" in completed.stdout


def test_helper_refinement_report_boundaries_and_interpretation() -> None:
    text = REPORT.read_text(encoding="utf-8")
    assert "Square/near-square helpers stayed low leakage" in text
    assert "h2_weak_aniso_03" in text
    assert "h2_phase_delay_04" in text
    assert "failed geometry only" in text
    assert "did not reach the 150-180 deg / pi-near region" in text
    assert "No full helper v2 pool" in text
    assert "full helper refinement pool" in text
    assert "K=7" in text
    assert "phase-ramp supercell" in text
    assert "TiO2/450 nm" in text
    assert "ML/DenseNet/cVAE training" in text
    assert "random/freeform helper" in text
    assert "+15 deg steering claim" in text
    assert "complete K=6 phase-state library claim" in text
