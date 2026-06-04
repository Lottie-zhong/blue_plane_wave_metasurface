from __future__ import annotations

import csv
import subprocess
import sys
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts/67_generate_apcd_k6_v10_refinement_plan.py"
POOL = REPO_ROOT / "outputs/apcd_k6_active_learning/combined_phase_knob_v10_refinement_pool.csv"
VALIDATION = REPO_ROOT / "outputs/apcd_k6_active_learning/combined_phase_knob_v10_refinement_pool_geometry_validation.csv"
SELECTION = REPO_ROOT / "outputs/apcd_k6_active_learning/combined_phase_knob_v10_refinement_fdtd_selection.csv"
REPORT = REPO_ROOT / "reports/combined_phase_knob_v10_refinement_plan.md"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_v10_refinement_pool_count_columns_families_and_anchor() -> None:
    rows = _rows(POOL)
    assert len(rows) == 26
    assert len({row["candidate_id"] for row in rows}) == 26
    assert Counter(row["family"] for row in rows) == {
        "height_transition_sweep": 6,
        "weak_helper_leakage_recovery": 5,
        "helper_position_gap_recovery": 5,
        "helper_rotation_recovery": 5,
        "conservative_height_comparison": 5,
    }
    assert all(row["anchor_candidate"] == "cpk_height_prop_05" for row in rows)
    assert all(row["target_bin_deg"] == "-120" for row in rows)
    assert all(row["helper_role"] == "weak_auxiliary_phase_helper" for row in rows)
    assert all(row["p2_length_nm"] == "85" and row["p2_width_nm"] == "150" for row in rows)


def test_v10_refinement_candidate_id_stability() -> None:
    rows = _rows(POOL)
    assert [row["candidate_id"] for row in rows[:6]] == [
        "cpk_refine_htrans_01",
        "cpk_refine_htrans_02",
        "cpk_refine_htrans_03",
        "cpk_refine_htrans_04",
        "cpk_refine_htrans_05",
        "cpk_refine_htrans_06",
    ]


def test_v10_refinement_geometry_validation_min_gap_50_nm() -> None:
    rows = _rows(VALIDATION)
    assert len(rows) == 26
    assert sum(row["overall_geometry_pass"] == "True" for row in rows) == 26
    assert all(row["duplicate_candidate_id_pass"] == "True" for row in rows)
    assert all(row["duplicate_geometry_pass"] == "True" for row in rows)
    assert all(row["helper_role_pass"] == "True" for row in rows)
    assert all(row["helper_not_apcd_dimer_pass"] == "True" for row in rows)
    for row in rows:
        assert float(row["same_cell_min_gap_nm"]) >= 50.0
        assert float(row["periodic_image_min_gap_nm"]) >= 50.0
        assert float(row["helper_core_min_gap_nm"]) >= 50.0


def test_v10_refinement_selection_rules() -> None:
    rows = _rows(SELECTION)
    assert [row["candidate_id"] for row in rows] == [
        "cpk_refine_htrans_04",
        "cpk_refine_weak_helper_03",
        "cpk_refine_pos_gap_01",
        "cpk_refine_helper_rot_04",
        "cpk_refine_htrans_05",
        "cpk_refine_conservative_03",
    ]
    assert [row["candidate_id"] for row in rows if row["next_round_priority"] == "top2_next_run"] == [
        "cpk_refine_htrans_04",
        "cpk_refine_weak_helper_03",
    ]


def test_v10_refinement_dry_run_no_yaml_fsp_lumapi() -> None:
    yaml_before = {
        path.name
        for path in (REPO_ROOT / "configs/apcd_k6_phase_state_candidates").glob("cpk_refine_*.yaml")
    }
    fsp_before = {path.name for path in REPO_ROOT.glob("**/*v10*.fsp")}

    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--dry-run"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )

    yaml_after = {
        path.name
        for path in (REPO_ROOT / "configs/apcd_k6_phase_state_candidates").glob("cpk_refine_*.yaml")
    }
    fsp_after = {path.name for path in REPO_ROOT.glob("**/*v10*.fsp")}

    assert yaml_before == yaml_after == set()
    assert fsp_before == fsp_after
    assert "09_P54_P56_v10_refinement_planning_only" in completed.stdout
    assert "no_fdtd_no_lumapi_no_fsp_no_yaml_no_training" in completed.stdout


def test_v10_refinement_report_scope_and_naming() -> None:
    text = REPORT.read_text(encoding="utf-8")
    assert "09-P54/P56 combined phase-knob v10 refinement planning" in text
    assert "`v10 refinement pool` is only the candidate-pool version" in text
    assert "`cpk_height_prop_05` is the key negative-phase anchor" in text
    assert "phase = -109.64 deg" in text
    assert "Recommended first manual FDTD candidates after review: `cpk_refine_htrans_04` and `cpk_refine_weak_helper_03`" in text
    assert "no K=6 phase-ramp supercell" in text
    assert "no +15 deg steering claim" in text
    assert "no complete K=6 phase-state library claim" in text
    assert "stage 10" not in text.lower()
    assert "task 10" not in text.lower()
