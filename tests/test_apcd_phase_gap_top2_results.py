from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/42_run_and_summarize_apcd_k6_phase_gap_top2.py"
RESULT_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_gap_fdtd_results_v1.csv"
REPORT_PATH = REPO_ROOT / "reports/apcd_k6_phase_gap_top2_fdtd_result_note.md"

if str(SCRIPT_PATH.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT_PATH.parent))

import importlib.util

spec = importlib.util.spec_from_file_location("phase_gap_top2", SCRIPT_PATH)
phase_gap_top2 = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(phase_gap_top2)


def test_top2_config_generation_writes_only_top2(tmp_path: Path) -> None:
    rows = phase_gap_top2.load_selection_rows(
        REPO_ROOT / "outputs/apcd_k6_active_learning/phase_gap_fdtd_selection_v1.csv"
    )
    written = phase_gap_top2.write_top2_configs(rows, tmp_path)

    assert sorted(path.name for path in written) == ["gap_bridge_03.yaml", "gap_lhs_leakred_06.yaml"]
    assert not (tmp_path / "gap_p2w_trim_03.yaml").exists()


def test_result_flags_are_correct_for_gap_top2() -> None:
    bridge = phase_gap_top2.result_row_from_values(
        candidate_id="gap_bridge_03",
        candidate_family="gap_60_90_bridge_from_p1w_dx",
        status="ok",
        target_conversion=0.9258332341737782,
        opposite_spin_leakage=0.09474297037776827,
        conversion_to_leakage_ratio=9.772052010544263,
        pd=0.8143343535629332,
        total_transmission=0.5102881022757734,
        t_alpha_star_from_alpha="-0.1108542881061453+0.938070764351445j",
    )
    lhs = phase_gap_top2.result_row_from_values(
        candidate_id="gap_lhs_leakred_06",
        candidate_family="gap_60_90_lhs_leakage_reduced",
        status="ok",
        target_conversion=0.9232330695542147,
        opposite_spin_leakage=0.07493963746730173,
        conversion_to_leakage_ratio=12.31968956275946,
        pd=0.8498463503548566,
        total_transmission=0.49908635351075814,
        t_alpha_star_from_alpha="-0.104267142440902+0.9413392076511971j",
    )

    assert bridge["overall_early_pass"] is True
    assert lhs["overall_early_pass"] is True
    assert bridge["inside_60_90_deg_region"] is False
    assert lhs["inside_60_90_deg_region"] is False
    assert bridge["near_90_100_deg_region"] is True
    assert lhs["near_90_100_deg_region"] is True
    assert bridge["priority"] == "early_pass_outside_60_90"
    assert lhs["priority"] == "early_pass_outside_60_90"


def test_phase_gap_result_csv_columns_are_complete() -> None:
    with RESULT_CSV.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert reader.fieldnames == phase_gap_top2.PHASE_GAP_RESULT_FIELDS
    assert [row["candidate_id"] for row in rows] == ["gap_bridge_03", "gap_lhs_leakred_06"]


def test_script_write_configs_dry_path_does_not_generate_fsp(tmp_path: Path) -> None:
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
    assert not (tmp_path / "configs" / "gap_p2w_trim_03.yaml").exists()


def test_script_does_not_call_lumapi_or_fdtd_run() -> None:
    text = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "import lumapi" not in text
    assert "fdtd.run" not in text
    assert "fdtd.save" not in text


def test_report_states_scope_and_no_steering_claim() -> None:
    text = REPORT_PATH.read_text(encoding="utf-8")

    assert "09-P16" in text
    assert "only ran" in text
    assert "gap_p2w_trim_03" in text
    assert "did not run the 24-row phase-gap pool" in text
    assert "No model was trained" in text
    assert "K=7 was not used" in text
    assert "No phase-ramp supercell" in text
    assert "not a steering result" in text
    assert "No new 60-90 deg usable phase candidate" in text
