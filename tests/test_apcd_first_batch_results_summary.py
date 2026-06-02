from __future__ import annotations

import csv
import importlib.util
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "30_summarize_apcd_k6_first_fdtd_batch_results.py"
REPORT_PATH = REPO_ROOT / "reports" / "apcd_k6_first_fdtd_batch_v0_result_note.md"


def _load_summary_module():
    spec = importlib.util.spec_from_file_location("apcd_first_batch_summary", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_early_pass_flags_are_correct() -> None:
    module = _load_summary_module()
    rows = {row["candidate_id"]: row for row in module.build_result_summary_rows()}

    assert rows["doe_p1w_dx_01"]["overall_early_pass"] is True
    assert rows["doe_p1w_dx_01"]["early_target_pass"] is True
    assert rows["doe_p1w_dx_01"]["early_leakage_pass"] is True
    assert rows["doe_p1w_dx_01"]["early_ratio_pass"] is True

    assert rows["doe_p1w_p2w_02"]["overall_early_pass"] is False
    assert rows["doe_p1w_p2w_02"]["early_target_pass"] is True
    assert rows["doe_p1w_p2w_02"]["early_leakage_pass"] is False
    assert rows["doe_p1w_p2w_02"]["early_ratio_pass"] is False

    assert rows["doe_lhs_like_01"]["overall_early_pass"] is False
    assert rows["doe_lhs_like_01"]["early_leakage_pass"] is False
    assert rows["doe_lhs_like_01"]["early_ratio_pass"] is False


def test_phase_outside_v0_range_flags_are_correct() -> None:
    module = _load_summary_module()
    rows = {row["candidate_id"]: row for row in module.build_result_summary_rows()}

    assert rows["doe_p1w_p2w_02"]["phase_outside_v0_range"] is False
    assert rows["doe_p1w_dx_01"]["phase_outside_v0_range"] is True
    assert rows["doe_lhs_like_01"]["phase_outside_v0_range"] is True


def test_priority_classification_is_correct() -> None:
    module = _load_summary_module()
    rows = {row["candidate_id"]: row for row in module.build_result_summary_rows()}

    assert rows["doe_p1w_dx_01"]["priority"] == "high_priority_neighborhood"
    assert rows["doe_lhs_like_01"]["priority"] == "phase_coverage_evidence_high_leakage"
    assert rows["doe_p1w_p2w_02"]["priority"] == "record_not_priority"


def test_output_csv_columns_are_complete(tmp_path: Path) -> None:
    module = _load_summary_module()
    rows = module.build_result_summary_rows()
    output_csv = module.export_result_summary_csv(rows, tmp_path / "summary.csv")

    with output_csv.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == module.RESULT_SUMMARY_FIELDS
    assert len(loaded) == 3
    assert {row["candidate_id"] for row in loaded} == {
        "doe_p1w_p2w_02",
        "doe_p1w_dx_01",
        "doe_lhs_like_01",
    }


def test_cli_dry_run_does_not_generate_fsp(tmp_path: Path) -> None:
    output_csv = tmp_path / "first_fdtd_batch_v0_results_summary.csv"
    completed = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--dry-run", "--output-csv", str(output_csv)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "status=summary_only_no_fdtd_no_lumapi_no_fsp_no_training" in completed.stdout
    assert "row_count=3" in completed.stdout
    assert output_csv.is_file()
    assert list(tmp_path.glob("*.fsp")) == []


def test_script_does_not_call_lumapi_or_fdtd_run_or_save() -> None:
    text = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "import lumapi" not in text
    assert "fdtd.run" not in text
    assert "fdtd.save" not in text


def test_report_states_result_boundaries() -> None:
    text = REPORT_PATH.read_text(encoding="utf-8")

    assert "09-P5" in text
    assert "did not run all 8" in text
    assert "did not run the 52-row" in text
    assert "No model was trained" in text
    assert "not a `+15 deg` steering proof" in text
    assert "doe_p1w_dx_01" in text
    assert "doe_lhs_like_01" in text
