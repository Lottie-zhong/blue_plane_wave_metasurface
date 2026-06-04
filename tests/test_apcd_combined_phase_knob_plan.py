from __future__ import annotations

import csv
import subprocess
import sys
from collections import Counter
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts/66_generate_apcd_k6_combined_phase_knob_plan.py"
DIAGNOSIS = REPO_ROOT / "outputs/apcd_k6_active_learning/helper_plateau_diagnosis_v8.csv"
POOL = REPO_ROOT / "outputs/apcd_k6_active_learning/combined_phase_knob_candidate_pool_v9.csv"
VALIDATION = REPO_ROOT / "outputs/apcd_k6_active_learning/combined_phase_knob_candidate_pool_v9_geometry_validation.csv"
SELECTION = REPO_ROOT / "outputs/apcd_k6_active_learning/combined_phase_knob_fdtd_selection_v9.csv"
REPORT = REPO_ROOT / "reports/apcd_k6_helper_plateau_and_combined_phase_knob_plan.md"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_helper_plateau_diagnosis_captures_120_132_plateau() -> None:
    rows = _rows(DIAGNOSIS)
    assert len(rows) == 7
    assert {row["helper_group"] for row in rows} == {
        "square_or_nearsquare_loading",
        "weak_anisotropic_helper",
        "phase_delay_helper",
    }
    assert max(float(row["phase_deg"]) for row in rows) == 131.6649840315141
    plateau_rows = [row for row in rows if row["diagnosis_class"] == "low_leakage_phase_plateau_120_132"]
    assert len(plateau_rows) >= 5
    assert all(row["early_pass"] == "True" for row in rows)


def test_combined_phase_knob_pool_count_columns_and_families() -> None:
    rows = _rows(POOL)
    assert len(rows) == 45
    assert len({row["candidate_id"] for row in rows}) == 45
    required = {
        "candidate_id",
        "family",
        "target_bin_deg",
        "anchor_candidate",
        "helper_role",
        "p1_rotation_deg",
        "p2_rotation_deg",
        "p3_length_nm",
        "p3_width_nm",
        "p3_rotation_deg",
        "height_nm",
        "period_x_nm",
        "period_y_nm",
        "expected_phase_direction",
        "design_rationale",
        "risk_level",
        "requires_fdtd",
        "status",
    }
    assert required.issubset(rows[0].keys())
    assert Counter(row["family"] for row in rows) == {
        "helper_plus_released_rotation": 9,
        "helper_plus_height_propagation": 9,
        "helper_plus_period_phase": 9,
        "helper_position_phase_scout": 9,
        "strong_but_safe_phase_delay_helper": 9,
    }
    assert all(row["helper_role"] == "weak_auxiliary_phase_helper" for row in rows)
    assert all(row["p2_length_nm"] == "85" and row["p2_width_nm"] == "150" for row in rows)


def test_combined_phase_knob_geometry_validation() -> None:
    rows = _rows(VALIDATION)
    assert len(rows) == 45
    assert sum(row["overall_geometry_pass"] == "True" for row in rows) == 33
    assert all(row["duplicate_candidate_id_pass"] == "True" for row in rows)
    assert all(row["helper_role_pass"] == "True" for row in rows)
    assert all(row["helper_not_apcd_dimer_pass"] == "True" for row in rows)
    for row in rows:
        if row["overall_geometry_pass"] == "True":
            threshold = float(row["minimum_gap_nm_threshold"])
            assert float(row["same_cell_min_gap_nm"]) >= threshold
            assert float(row["periodic_image_min_gap_nm"]) >= threshold
            assert float(row["helper_core_min_gap_nm"]) >= threshold


def test_combined_phase_knob_selection_rules() -> None:
    rows = _rows(SELECTION)
    assert [row["candidate_id"] for row in rows] == [
        "cpk_rot_release_02",
        "cpk_height_prop_05",
        "cpk_period_phase_04",
        "cpk_position_scout_01",
        "cpk_strong_delay_07",
    ]
    assert len(rows) == 5
    families = {row["family"] for row in rows}
    assert "helper_plus_released_rotation" in families
    assert "helper_plus_height_propagation" in families
    assert "helper_plus_period_phase" in families
    assert {"helper_position_phase_scout", "strong_but_safe_phase_delay_helper"} <= families
    assert sum(float(row["target_bin_deg"]) == -180.0 for row in rows) >= 2
    assert sum(row["risk_level"] == "high_risk" for row in rows) == 1
    assert [row["candidate_id"] for row in rows if row["next_round_priority"] == "top2_next_run"] == [
        "cpk_rot_release_02",
        "cpk_height_prop_05",
    ]


def test_combined_phase_knob_dry_run_no_yaml_fsp_lumapi() -> None:
    yaml_before = {path.name for path in (REPO_ROOT / "configs/apcd_k6_phase_state_candidates").glob("cpk_*.yaml")}
    fsp_before = {path.name for path in REPO_ROOT.glob("*.fsp")}
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--dry-run"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    yaml_after = {path.name for path in (REPO_ROOT / "configs/apcd_k6_phase_state_candidates").glob("cpk_*.yaml")}
    fsp_after = {path.name for path in REPO_ROOT.glob("*.fsp")}
    assert yaml_before == yaml_after == set()
    assert fsp_before == fsp_after
    assert "no_fdtd_no_lumapi_no_fsp_no_yaml_no_training" in completed.stdout


def test_combined_phase_knob_report_scope_and_top2() -> None:
    text = REPORT.read_text(encoding="utf-8")
    assert "low-leakage plateau around 120-132 deg" in text
    assert "0 deg, -60 deg, -120 deg, and -180 deg are still not covered" in text
    assert "height and period are propagation/material phase scouts" in text
    assert "Recommended next run top-2: `cpk_rot_release_02` and `cpk_height_prop_05`" in text
    assert "No FDTD" in text
    assert "lumapi" in text
    assert "YAML generation" in text
    assert "K=7" in text
    assert "phase-ramp supercell" in text
    assert "TiO2/450 nm" in text
    assert "ML/DenseNet/cVAE training" in text
    assert "random/freeform helper" in text
    assert "+15 deg steering claim" in text
    assert "complete K=6 phase-state library claim" in text
