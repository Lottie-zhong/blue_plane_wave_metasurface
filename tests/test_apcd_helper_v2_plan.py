from __future__ import annotations

import csv
import subprocess
import sys
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts/63_generate_apcd_k6_v6_pilot_diagnosis_helper_v2_plan.py"
DIAGNOSIS = REPO_ROOT / "outputs/apcd_k6_active_learning/v6_pilot_failure_diagnosis.csv"
POOL = REPO_ROOT / "outputs/apcd_k6_active_learning/weak_helper_v2_candidate_pool_v7.csv"
VALIDATION = REPO_ROOT / "outputs/apcd_k6_active_learning/weak_helper_v2_candidate_pool_v7_geometry_validation.csv"
SELECTION = REPO_ROOT / "outputs/apcd_k6_active_learning/weak_helper_v2_fdtd_selection_v7.csv"
REPORT = REPO_ROOT / "reports/apcd_k6_v6_pilot_diagnosis_and_helper_v2_plan.md"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_v6_pilot_failure_diagnosis_rows_and_modes() -> None:
    rows = _rows(DIAGNOSIS)
    assert [row["candidate_id"] for row in rows] == [
        "ng_zero_rot_release_07",
        "ng_neg60_dxdy_release_08",
        "wh_zero_aux_phase_01",
    ]
    modes = {row["candidate_id"]: row["failure_mode"] for row in rows}
    assert modes["ng_zero_rot_release_07"] == "released_rotation_zero_failed_leakage_and_phase_far"
    assert modes["ng_neg60_dxdy_release_08"] == "released_dxdy_neg60_failed_leakage_and_phase_far"
    assert modes["wh_zero_aux_phase_01"] == "weak_helper_failed_leakage_ratio_and_insufficient_phase_shift"
    assert all("current_usable_phase_span=72.2413-118.0788 deg" in row["diagnosis"] for row in rows)


def test_helper_v2_pool_count_columns_families_and_helper_role() -> None:
    rows = _rows(POOL)
    assert len(rows) == 48
    assert len({row["candidate_id"] for row in rows}) == len(rows)
    required = {
        "candidate_id",
        "family",
        "target_bin_deg",
        "anchor_candidate",
        "helper_role",
        "p1_length_nm",
        "p2_length_nm",
        "p3_helper_length_nm",
        "p3_helper_width_nm",
        "p3_helper_rotation_deg",
        "p3_helper_frac_x",
        "p3_helper_frac_y",
        "expected_phase_direction",
        "design_rationale",
        "risk_level",
        "requires_fdtd",
        "status",
    }
    assert required.issubset(rows[0].keys())
    assert all(row["helper_role"] == "weak_auxiliary_phase_helper" for row in rows)
    assert all("not another APCD dimer" in row["notes"] for row in rows)
    assert Counter(row["family"] for row in rows) == {
        "helper_v2_weak_far_detour": 8,
        "helper_v2_medium_phase_delay": 8,
        "helper_v2_low_leakage_trim": 8,
        "helper_v2_zero_bridge": 8,
        "helper_v2_neg60_detour": 8,
        "helper_v2_pi_wrap_probe": 8,
    }


def test_helper_v2_geometry_validation_pass_rate_and_columns() -> None:
    rows = _rows(VALIDATION)
    assert len(rows) == 48
    required = {
        "candidate_id",
        "same_cell_min_gap_nm",
        "periodic_image_min_gap_nm",
        "helper_core_min_gap_nm",
        "no_pillar_overlap_pass",
        "same_cell_gap_pass",
        "periodic_gap_pass",
        "dimensions_bounds_pass",
        "helper_core_gap_pass",
        "duplicate_candidate_id_pass",
        "duplicate_geometry_pass",
        "overall_geometry_pass",
        "recommended_for_fdtd",
    }
    assert required.issubset(rows[0].keys())
    assert sum(row["overall_geometry_pass"] == "True" for row in rows) == 37
    assert all(row["duplicate_candidate_id_pass"] == "True" for row in rows)


def test_selected_not_run_rows_are_geometry_passing_and_cover_targets() -> None:
    selected = _rows(SELECTION)
    validation = {row["candidate_id"]: row for row in _rows(VALIDATION)}
    assert [row["candidate_id"] for row in selected] == [
        "wh2_zero_far_06",
        "wh2_neg60_detour_05",
        "wh2_pi_wrap_04",
        "wh2_lowleak_trim_03",
    ]
    assert len(selected) == 4
    assert {row["status"] for row in selected} == {"selected_not_run"}
    assert all(validation[row["candidate_id"]]["recommended_for_fdtd"] == "True" for row in selected)
    targets = {float(row["target_bin_deg"]) for row in selected}
    assert 0.0 in targets
    assert -60.0 in targets
    assert -180.0 in targets
    assert sum(row["risk_level"] == "high_risk" for row in selected) == 1
    assert [row["candidate_id"] for row in selected if row["next_round_priority"] == "top2_next_round"] == [
        "wh2_zero_far_06",
        "wh2_neg60_detour_05",
    ]


def test_dry_run_does_not_generate_yaml_fsp_or_call_lumapi() -> None:
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
    assert "no_fdtd_no_lumapi_no_fsp_no_yaml_no_training" in completed.stdout


def test_report_states_scope_boundaries() -> None:
    text = REPORT.read_text(encoding="utf-8")
    assert "No FDTD" in text
    assert "lumapi" in text
    assert "YAML generation" in text
    assert "K=7" in text
    assert "phase-ramp supercell" in text
    assert "TiO2/450 nm" in text
    assert "ML training" in text
    assert "+15 deg steering claim" in text
    assert "complete K=6 phase-state library claim" in text
