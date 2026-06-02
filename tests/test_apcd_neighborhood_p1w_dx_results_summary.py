from __future__ import annotations

import csv
import importlib.util
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "34_summarize_apcd_k6_neighborhood_p1w_dx_results.py"
REPORT_PATH = REPO_ROOT / "reports" / "apcd_k6_neighborhood_p1w_dx_fdtd_result_note.md"


def _load_summary_module():
    spec = importlib.util.spec_from_file_location("p1w_dx_results_summary", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_early_pass_flags_are_correct() -> None:
    module = _load_summary_module()
    rows = {row["candidate_id"]: row for row in module.build_result_summary_rows()}

    assert rows["nhood_p1w_dx_05"]["overall_early_pass"] is True
    assert rows["nhood_p1w_dx_05"]["early_leakage_pass"] is True
    assert rows["nhood_p1w_dx_05"]["early_ratio_pass"] is True

    assert rows["nhood_p1w_dx_02"]["overall_early_pass"] is False
    assert rows["nhood_p1w_dx_02"]["early_target_pass"] is True
    assert rows["nhood_p1w_dx_02"]["early_leakage_pass"] is False
    assert rows["nhood_p1w_dx_02"]["early_ratio_pass"] is False


def test_inside_90_100_deg_region_flags_are_correct() -> None:
    module = _load_summary_module()
    rows = {row["candidate_id"]: row for row in module.build_result_summary_rows()}

    assert rows["nhood_p1w_dx_05"]["inside_90_100_deg_region"] is False
    assert rows["nhood_p1w_dx_02"]["inside_90_100_deg_region"] is True


def test_phase_below_doe_p1w_dx_01_flags_are_correct() -> None:
    module = _load_summary_module()
    rows = {row["candidate_id"]: row for row in module.build_result_summary_rows()}

    assert rows["nhood_p1w_dx_05"]["phase_below_doe_p1w_dx_01"] is False
    assert rows["nhood_p1w_dx_02"]["phase_below_doe_p1w_dx_01"] is True


def test_priority_classification_is_correct() -> None:
    module = _load_summary_module()
    rows = {row["candidate_id"]: row for row in module.build_result_summary_rows()}

    assert rows["nhood_p1w_dx_05"]["priority"] == "low_leakage_conservative_reference"
    assert rows["nhood_p1w_dx_02"]["priority"] == "lower_phase_high_leakage_boundary"


def test_output_csv_columns_are_complete(tmp_path: Path) -> None:
    module = _load_summary_module()
    rows = module.build_result_summary_rows()
    output_csv = module.export_result_summary_csv(rows, tmp_path / "summary.csv")

    with output_csv.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == module.RESULT_FIELDS
    assert len(loaded) == 2
    assert {row["candidate_id"] for row in loaded} == {"nhood_p1w_dx_05", "nhood_p1w_dx_02"}


def test_cli_dry_run_does_not_generate_fsp(tmp_path: Path) -> None:
    output_csv = tmp_path / "neighborhood_p1w_dx_fdtd_results_v1.csv"
    completed = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--dry-run", "--output-csv", str(output_csv)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "status=summary_only_no_fdtd_no_lumapi_no_fsp_no_training" in completed.stdout
    assert "row_count=2" in completed.stdout
    assert output_csv.is_file()
    assert list(tmp_path.glob("*.fsp")) == []


def test_script_does_not_call_lumapi_or_fdtd_run_or_save() -> None:
    text = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "import lumapi" not in text
    assert "fdtd.run" not in text
    assert "fdtd.save" not in text


def test_report_states_result_boundaries() -> None:
    text = REPORT_PATH.read_text(encoding="utf-8")

    assert "09-P9" in text
    assert "Only two neighborhood candidates were run" in text
    assert "did not run `nhood_lhs_leakred_06`" in text
    assert "did not run the 24-row" in text
    assert "No model was trained" in text
    assert "steering claim" in text
    assert "no new phase state" in text
