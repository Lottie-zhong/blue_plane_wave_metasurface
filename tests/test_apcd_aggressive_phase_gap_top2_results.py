from __future__ import annotations

import csv
import importlib.util
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/45_run_and_summarize_apcd_k6_aggressive_phase_gap_top2.py"
SELECTION_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/aggressive_phase_gap_fdtd_selection_v1.csv"
RESULT_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/aggressive_phase_gap_top2_fdtd_results_v1.csv"
REPORT_PATH = REPO_ROOT / "reports/apcd_k6_aggressive_phase_gap_top2_fdtd_result_note.md"

spec = importlib.util.spec_from_file_location("aggressive_top2", SCRIPT_PATH)
aggressive_top2 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(aggressive_top2)


def test_top2_config_generation_writes_only_top2(tmp_path: Path) -> None:
    rows = aggressive_top2.load_selection_rows(SELECTION_CSV)
    written = aggressive_top2.write_top2_configs(rows, tmp_path)

    assert sorted(path.name for path in written) == [
        "aggr_lhs_retention_dy_05.yaml",
        "aggr_p1w_leakctrl_04.yaml",
    ]
    assert not (tmp_path / "aggr_bridge_lhs_fine_05.yaml").exists()


def test_result_flags_show_new_usable_60_90_candidates() -> None:
    lhs = aggressive_top2.result_row_from_values(
        candidate_id="aggr_lhs_retention_dy_05",
        candidate_family="lhs_like_retention_high_dy",
        status="ok",
        target_conversion=0.8570222822237621,
        opposite_spin_leakage=0.1028870531101224,
        conversion_to_leakage_ratio=8.329738837977422,
        pd=0.785631727240723,
        total_transmission=0.47995466766694245,
        t_alpha_star_from_alpha="0.2683524894267085+0.8378961424762233j",
    )
    p1w = aggressive_top2.result_row_from_values(
        candidate_id="aggr_p1w_leakctrl_04",
        candidate_family="lhs_like_leakage_control_p1w",
        status="ok",
        target_conversion=0.8718902349705875,
        opposite_spin_leakage=0.09911912635679705,
        conversion_to_leakage_ratio=8.796387407857752,
        pd=0.7958431086149413,
        total_transmission=0.4855046806636925,
        t_alpha_star_from_alpha="0.1371896062263708+0.8798337055076977j",
    )

    assert lhs["overall_early_pass"] is True
    assert p1w["overall_early_pass"] is True
    assert lhs["inside_60_90_deg_region"] is True
    assert p1w["inside_60_90_deg_region"] is True
    assert lhs["near_60_deg_bin"] is True
    assert p1w["near_90_100_deg_region"] is False
    assert lhs["priority"] == "usable_60_90_phase_candidate"
    assert p1w["priority"] == "usable_60_90_phase_candidate"


def test_result_csv_columns_are_complete() -> None:
    with RESULT_CSV.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert reader.fieldnames == aggressive_top2.AGGRESSIVE_PHASE_GAP_RESULT_FIELDS
    assert [row["candidate_id"] for row in rows] == ["aggr_lhs_retention_dy_05", "aggr_p1w_leakctrl_04"]
    assert {row["priority"] for row in rows} == {"usable_60_90_phase_candidate"}


def test_script_write_configs_does_not_generate_fsp_or_third_config(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--write-configs",
            "--config-dir",
            str(tmp_path / "configs"),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "config_generation_only_no_fdtd_no_lumapi_no_fsp_no_training_not_steering_result" in completed.stdout
    assert list(tmp_path.glob("*.fsp")) == []
    assert not (tmp_path / "configs" / "aggr_bridge_lhs_fine_05.yaml").exists()


def test_script_does_not_call_lumapi_or_fdtd_run() -> None:
    text = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "import lumapi" not in text
    assert "fdtd.run" not in text
    assert "fdtd.save" not in text


def test_report_states_scope_and_no_steering_or_library_claim() -> None:
    text = REPORT_PATH.read_text(encoding="utf-8")

    assert "09-P18" in text
    assert "did not run `aggr_bridge_lhs_fine_05`" in text
    assert "No model was trained" in text
    assert "K=7 was not used" in text
    assert "No phase-ramp supercell" in text
    assert "not a steering result" in text
    assert "does not support a +15 deg steering claim" in text
    assert "K=6 phase-state library is still incomplete" in text
    assert "new usable 60-90 deg single-dimer phase candidates" in text
