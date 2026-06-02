from __future__ import annotations

import csv
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_phase_gap_candidates import (
    PHASE_COVERAGE_FIELDS,
    analyze_phase_coverage,
    read_csv_rows,
    read_phase_targets,
    write_csv_rows,
)


DATASET_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v1.csv"
TARGETS_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_bin_targets.csv"
COVERAGE_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_coverage_v1.csv"
REPORT_PATH = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_gap_analysis_v1.md"
SCRIPT_PATH = REPO_ROOT / "scripts/39_analyze_apcd_k6_phase_coverage_v1.py"


def _coverage_rows() -> list[dict[str, object]]:
    return analyze_phase_coverage(read_csv_rows(DATASET_CSV), read_phase_targets(TARGETS_CSV))


def test_phase_bin_nearest_candidates_are_correct() -> None:
    rows = {float(row["phase_bin_deg"]): row for row in _coverage_rows()}

    assert rows[60.0]["nearest_candidate_all"] == "doe_lhs_like_01"
    assert float(rows[60.0]["nearest_error_all"]) < 1.0
    assert rows[120.0]["nearest_candidate_early_pass"] == "p1W_p5"
    assert float(rows[120.0]["nearest_error_early_pass"]) < 2.0


def test_phase_gap_analysis_marks_missing_bins() -> None:
    rows = {float(row["phase_bin_deg"]): row for row in _coverage_rows()}

    assert rows[60.0]["bin_status"] == "high_leakage_only"
    assert rows[120.0]["bin_status"] == "covered_candidate"
    assert rows[0.0]["bin_status"] == "missing"
    assert rows[-60.0]["bin_status"] == "missing"
    assert rows[-120.0]["bin_status"] == "missing"


def test_phase_coverage_csv_columns_are_complete(tmp_path: Path) -> None:
    output = write_csv_rows(_coverage_rows(), tmp_path / "coverage.csv", PHASE_COVERAGE_FIELDS)

    with output.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == PHASE_COVERAGE_FIELDS
    assert len(loaded) == 6


def test_generated_phase_coverage_output_exists_and_has_expected_rows() -> None:
    rows = read_csv_rows(COVERAGE_CSV)

    assert len(rows) == 6
    assert {row["bin_status"] for row in rows}.issuperset({"missing", "covered_candidate", "high_leakage_only"})


def test_phase_gap_report_states_scope_and_no_steering() -> None:
    text = REPORT_PATH.read_text(encoding="utf-8")

    assert "No FDTD was run" in text
    assert "No model was trained" in text
    assert "not a steering result" in text
    assert "98-99 deg region" in text
    assert "K=6 phase-state library is still incomplete" in text


def test_phase_coverage_script_does_not_call_lumapi_or_fdtd_run() -> None:
    text = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "import lumapi" not in text
    assert "fdtd.run" not in text
    assert "fdtd.save" not in text
    assert ".fsp" not in text
