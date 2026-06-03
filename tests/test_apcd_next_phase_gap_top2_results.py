from __future__ import annotations

import csv
import importlib.util
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/52_run_and_summarize_apcd_k6_next_phase_gap_top2.py"
RESULT_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/next_phase_gap_top2_fdtd_results_v2.csv"
SUMMARY_MD = REPO_ROOT / "outputs/apcd_k6_active_learning/next_phase_gap_top2_fdtd_results_v2_summary.md"
REPORT_MD = REPO_ROOT / "reports/apcd_k6_next_phase_gap_top2_fdtd_result_note.md"

spec = importlib.util.spec_from_file_location("next_phase_gap_top2_results", SCRIPT_PATH)
next_top2 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(next_top2)


def _result_rows() -> list[dict[str, str]]:
    with RESULT_CSV.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_result_csv_contains_only_top2_candidates() -> None:
    rows = _result_rows()
    ids = [row["candidate_id"] for row in rows]

    assert ids == ["next_zero_rot_anchor_03", "next_rot_anchor_04"]
    assert "next_mixed_bridge_03" not in ids
    assert "next_pi_mixed_bridge_03" not in ids


def test_required_metric_columns_exist() -> None:
    with RESULT_CSV.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames

    assert fieldnames == next_top2.NEXT_PHASE_GAP_TOP2_RESULT_FIELDS
    for column in (
        "phase_deg",
        "phase_error_to_target_deg",
        "target_conversion",
        "opposite_spin_leakage",
        "conversion_to_leakage_ratio",
        "PD",
        "total_transmission",
        "t_alpha_star_from_alpha",
        "phase_shift_vs_baseline_deg",
        "early_pass",
        "target_bin_pass",
        "target_bin_status",
    ):
        assert column in fieldnames


def test_phase_error_uses_wrapped_angular_distance() -> None:
    assert next_top2.angular_distance_deg(179.0, -179.0) == 2.0
    assert next_top2.angular_distance_deg(157.83382648796396, -60.0) == 142.16617351203604

    rows = {row["candidate_id"]: row for row in _result_rows()}
    assert abs(float(rows["next_zero_rot_anchor_03"]["phase_error_to_target_deg"]) - 20.788972844777305) < 1e-12
    assert abs(float(rows["next_rot_anchor_04"]["phase_error_to_target_deg"]) - 142.16617351203604) < 1e-12


def test_early_pass_thresholds_and_target_bin_status() -> None:
    evidence = next_top2.result_row_from_values(
        candidate_id="evidence",
        target_bin_deg=0.0,
        candidate_family="unit",
        status="ok",
        target_conversion=0.7,
        opposite_spin_leakage=0.5,
        conversion_to_leakage_ratio=1.0,
        PD=0.0,
        total_transmission=0.1,
        t_alpha_star_from_alpha="1+0j",
    )
    strong = next_top2.result_row_from_values(
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
    near = next_top2.result_row_from_values(
        candidate_id="near",
        target_bin_deg=0.0,
        candidate_family="unit",
        status="ok",
        target_conversion=0.7,
        opposite_spin_leakage=0.1,
        conversion_to_leakage_ratio=7.0,
        PD=0.0,
        total_transmission=0.1,
        t_alpha_star_from_alpha="0.8660254037844386+0.5j",
    )

    assert evidence["early_pass"] is False
    assert evidence["target_bin_status"] == "evidence_only"
    assert strong["early_pass"] is True
    assert strong["target_bin_status"] == "strong_covered"
    assert near["target_bin_status"] == "near_but_not_covered"

    rows = {row["candidate_id"]: row for row in _result_rows()}
    assert rows["next_zero_rot_anchor_03"]["early_pass"] == "False"
    assert rows["next_zero_rot_anchor_03"]["target_bin_status"] == "evidence_only"
    assert rows["next_rot_anchor_04"]["early_pass"] == "False"
    assert rows["next_rot_anchor_04"]["target_bin_status"] == "open_gap"


def test_script_does_not_call_lumapi_or_fdtd_run() -> None:
    text = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "import lumapi" not in text
    assert "APCDSingleDimerRunner" not in text
    assert "fdtd.run" not in text
    assert "fdtd.save" not in text


def test_summary_and_report_state_boundaries() -> None:
    text = SUMMARY_MD.read_text(encoding="utf-8") + "\n" + REPORT_MD.read_text(encoding="utf-8")

    assert "09-P23" in text
    assert "next_mixed_bridge_03" in text
    assert "next_pi_mixed_bridge_03" in text
    assert "were not run" in text
    assert "full 38-row next candidate pool was not run" in text
    assert "not a +15 deg steering result" in text
    assert "does not complete the K=6 phase-state library" in text
    assert "No raw `results.csv`, `.fsp`, `pre_run_X.fsp`, or `pre_run_Y.fsp`" in text
