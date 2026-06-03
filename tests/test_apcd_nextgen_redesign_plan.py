from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts/61_generate_apcd_k6_v5_diagnosis_nextgen_plan.py"
DIAGNOSIS = REPO_ROOT / "outputs/apcd_k6_active_learning/accumulated_fdtd_diagnosis_v5.csv"
BOTTLENECK = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_span_bottleneck_analysis_v5.md"
POOL = REPO_ROOT / "outputs/apcd_k6_active_learning/nextgen_candidate_pool_v6.csv"
VALIDATION = REPO_ROOT / "outputs/apcd_k6_active_learning/nextgen_candidate_pool_v6_geometry_validation.csv"
SELECTION = REPO_ROOT / "outputs/apcd_k6_active_learning/nextgen_fdtd_selection_v6.csv"
REPORT = REPO_ROOT / "reports/apcd_k6_v5_diagnosis_and_nextgen_redesign_plan.md"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_accumulated_diagnosis_has_expected_failure_modes() -> None:
    rows = _rows(DIAGNOSIS)
    assert len(rows) == 27
    by_id = {row["candidate_id"]: row for row in rows}
    assert by_id["pl_pi_wrap_04"]["diagnosis_class"] == "phase_wrap_evidence_high_leakage"
    assert by_id["pl_neg60_focus_push_05"]["diagnosis_class"] == "early_pass_but_not_target"
    assert by_id["pl_neg120_aspect_03"]["diagnosis_class"] == "high_leakage_not_usable"
    assert by_id["next_rot_anchor_04"]["diagnosis_class"] == "negative_target_pulled_positive"
    usable = [row for row in rows if row["overall_early_pass"] == "True"]
    assert min(float(row["phase_deg"]) for row in usable) == 72.24132809604521
    assert max(float(row["phase_deg"]) for row in usable) == 118.07875127181353
    assert all(row["usable_phase_region"] == "usable_60_120_span" for row in usable)


def test_nextgen_pool_count_columns_and_families() -> None:
    rows = _rows(POOL)
    assert len(rows) == 60
    assert len({row["candidate_id"] for row in rows}) == 60
    required = {
        "candidate_id",
        "candidate_family",
        "target_bin_deg",
        "design_strategy",
        "p1_rotation_deg",
        "p2_rotation_deg",
        "internal_dx_nm",
        "internal_dy_nm",
        "requires_geometry_validation",
        "requires_fdtd",
        "status",
    }
    assert required.issubset(rows[0].keys())
    families = {row["candidate_family"] for row in rows}
    assert families == {
        "rotation_released_zero_bin",
        "rotation_released_neg60_dxdy",
        "controlled_swap_inversion_neg120",
        "pi_wrap_leakage_control",
        "expanded_internal_separation_negative_push",
        "height_period_future_knob_scout",
    }
    assert not any(row["p2_length_nm"] == "150" and row["p2_width_nm"] == "85" for row in rows)


def test_nextgen_geometry_validation_all_passes() -> None:
    rows = _rows(VALIDATION)
    assert len(rows) == 60
    assert sum(row["overall_geometry_pass"] == "True" for row in rows) == 60
    assert sum(row["recommended_for_fdtd"] == "True" for row in rows) == 60
    assert all(row["rotation_release_policy_pass"] == "True" for row in rows)


def test_nextgen_selection_rules() -> None:
    rows = _rows(SELECTION)
    assert len(rows) == 5
    assert [row["status"] for row in rows] == ["selected_not_run"] * 5
    assert [row["candidate_id"] for row in rows[:2]] == [
        "ng_zero_rot_release_07",
        "ng_neg60_dxdy_release_08",
    ]
    targets = {row["target_bin_deg"] for row in rows}
    assert {"0", "-60", "-120", "-180"}.issubset(targets)
    assert all(row["geometry_pass"] == "True" for row in rows)
    assert all(row["recommended_for_fdtd"] == "True" for row in rows)


def test_dry_run_does_not_call_fdtd_lumapi_or_generate_yaml_fsp() -> None:
    yaml_before = {path.name for path in (REPO_ROOT / "configs/apcd_k6_phase_state_candidates").glob("ng_*.yaml")}
    fsp_before = {path.name for path in REPO_ROOT.glob("*.fsp")}
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "--dry-run"],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    yaml_after = {path.name for path in (REPO_ROOT / "configs/apcd_k6_phase_state_candidates").glob("ng_*.yaml")}
    fsp_after = {path.name for path in REPO_ROOT.glob("*.fsp")}
    assert yaml_before == yaml_after
    assert fsp_before == fsp_after
    assert "no_fdtd_no_lumapi_no_fsp_no_yaml_no_training" in completed.stdout


def test_reports_state_scope_boundaries() -> None:
    report = REPORT.read_text(encoding="utf-8")
    bottleneck = BOTTLENECK.read_text(encoding="utf-8")
    for text in (report, bottleneck):
        assert "No FDTD" in text
        assert "lumapi" in text
        assert "phase-ramp supercell" in text
        assert "+15 deg steering" in text
        assert "complete K=6 phase-state library" in text or "K=6 phase-state library remains incomplete" in text
