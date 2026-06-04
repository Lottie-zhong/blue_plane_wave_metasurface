from __future__ import annotations

import csv
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts/69_summarize_apcd_lower_transition_result.py"


@pytest.fixture(scope="module")
def summarizer_module():
    spec = importlib.util.spec_from_file_location("apcd_lower_transition_summarizer", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_circular_phase_and_bin_logic(summarizer_module) -> None:
    assert summarizer_module.phase_deg_from_complex("-1+0j") == pytest.approx(-180.0)
    assert summarizer_module.phase_deg_from_complex("0+1j") == pytest.approx(90.0)

    nearest, error = summarizer_module.nearest_phase_bin(179.0, summarizer_module.TARGET_BINS_DEG)
    assert nearest == -180.0
    assert error == pytest.approx(1.0)

    nearest, error = summarizer_module.nearest_phase_bin(-2.0, summarizer_module.REMAINING_MISSING_BINS_DEG)
    assert nearest == 0.0
    assert error == pytest.approx(2.0)


def test_early_and_near_pass_logic(summarizer_module) -> None:
    assert summarizer_module.early_pass(0.5, 0.2, 6.0) is True
    assert summarizer_module.near_pass(0.5, 0.25, 3.0) is True
    assert summarizer_module.near_pass(0.7, 0.1, 8.0) is False
    assert summarizer_module.early_pass(0.49, 0.1, 8.0) is False
    assert summarizer_module.near_pass(0.5, 0.26, 8.0) is False


def test_opens_missing_bin_logic(summarizer_module) -> None:
    assert summarizer_module.opens_missing_bin(60.0, True) is True
    assert summarizer_module.opens_missing_bin(0.0, True) is True
    assert summarizer_module.opens_missing_bin(-60.0, True) is True
    assert summarizer_module.opens_missing_bin(-120.0, True) is False
    assert summarizer_module.opens_missing_bin(60.0, False) is False


def test_summarize_raw_result_computes_required_metrics(summarizer_module, tmp_path: Path) -> None:
    raw_result = tmp_path / "results.csv"
    raw = {
        "status": "ok",
        "t_alpha_star_from_alpha": "0.5+0.8660254037844386j",
        "target_conversion": "0.82",
        "opposite_spin_leakage": "0.1",
        "conversion_to_leakage_ratio": "8.2",
        "PD": "0.75",
    }

    row = summarizer_module.summarize_raw_result(
        candidate_id="cpk_mbin_lower_transition_01",
        raw=raw,
        result_path=raw_result,
        coverage_base=tmp_path / "coverage.csv",
        stage_label="09-P73",
    )

    assert row["phase_deg"] == pytest.approx(60.0)
    assert row["nearest_target_bin_deg"] == 60
    assert row["best_remaining_missing_bin_deg"] == 60
    assert row["target_conversion"] == pytest.approx(0.82)
    assert row["opposite_spin_leakage"] == pytest.approx(0.1)
    assert row["conversion_to_leakage_ratio"] == pytest.approx(8.2)
    assert row["PD"] == pytest.approx(0.75)
    assert row["early_pass"] is True
    assert row["near_pass"] is False
    assert row["opens_missing_bin"] is True


def test_missing_results_csv_exits_cleanly_without_summary(summarizer_module, monkeypatch, capsys, tmp_path: Path) -> None:
    missing_result = tmp_path / "missing" / "results.csv"
    summary_csv = tmp_path / "summary.csv"
    report_md = tmp_path / "summary.md"

    monkeypatch.setattr(summarizer_module, "candidate_result_path", lambda _candidate_id: missing_result)
    monkeypatch.setattr(summarizer_module, "output_paths", lambda _stage_label, _candidate_id: (summary_csv, report_md))
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(SCRIPT_PATH),
            "--candidate-id",
            "cpk_mbin_lower_transition_01",
            "--coverage-base",
            str(tmp_path / "coverage.csv"),
            "--stage-label",
            "09-P73",
        ],
    )

    assert summarizer_module.main() == 0
    captured = capsys.readouterr()
    assert "Real FDTD result missing; run this candidate on the server first." in captured.out
    assert not summary_csv.exists()
    assert not report_md.exists()


def test_write_summary_outputs_are_small_committed_artifacts(summarizer_module, tmp_path: Path) -> None:
    row = {
        "candidate_id": "cpk_mbin_lower_transition_01",
        "stage_label": "09-P73",
        "status": "ok",
        "phase_deg": 60.0,
        "nearest_target_bin_deg": 60,
        "phase_error_to_bin_deg": 0.0,
        "best_remaining_missing_bin_deg": 60,
        "phase_error_to_best_missing_bin_deg": 0.0,
        "target_conversion": 0.8,
        "opposite_spin_leakage": 0.1,
        "conversion_to_leakage_ratio": 8.0,
        "PD": 0.7,
        "early_pass": True,
        "near_pass": False,
        "opens_missing_bin": True,
        "source_result_csv": "outputs/apcd_k6_metagrating_633nm/phase_state_candidates/cpk_mbin_lower_transition_01/results.csv",
        "source_coverage_csv": "outputs/apcd_k6_active_learning/combined_phase_knob_phase_state_coverage_p69.csv",
        "notes": "test row",
    }
    summary_csv = tmp_path / "summary.csv"
    report_md = tmp_path / "summary.md"

    summarizer_module.write_csv_rows([row], summary_csv, summarizer_module.RESULT_FIELDS)
    summarizer_module.write_report(report_md, row)

    with summary_csv.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["candidate_id"] == "cpk_mbin_lower_transition_01"
    assert "Do not commit the raw candidate `results.csv`" in report_md.read_text(encoding="utf-8")


def test_no_raw_results_fsp_pre_run_or_npy_files_are_tracked() -> None:
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=REPO_ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    tracked = completed.stdout.splitlines()
    forbidden = [
        path
        for path in tracked
        if path.endswith("/results.csv")
        or path.endswith("/summary.md")
        or path.endswith(".fsp")
        or path.endswith(".npy")
        or "/pre_run" in path
    ]
    assert forbidden == []
