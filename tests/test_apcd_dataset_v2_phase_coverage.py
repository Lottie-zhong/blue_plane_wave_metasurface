from __future__ import annotations

import csv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"

import sys

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_next_phase_gap_candidates import angular_distance_deg
from metasurface.apcd_active_learning import wrap_phase_deg


DATASET_V1 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v1.csv"
DATASET_V2 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v2.csv"
COVERAGE_V2 = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_coverage_v2.csv"
ANALYSIS_V2 = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_gap_analysis_v2.md"
READINESS_V2 = REPO_ROOT / "outputs/apcd_k6_active_learning/k6_phase_state_readiness_v2.md"
REPORT_V2 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v2_collection_report.md"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_dataset_v2_adds_two_p18_rows_and_phase_region() -> None:
    v1 = _rows(DATASET_V1)
    v2 = _rows(DATASET_V2)
    ids = {row["variant_id"] for row in v2}

    assert len(v2) == len(v1) + 2
    assert len(ids) == len(v2)
    assert {"aggr_lhs_retention_dy_05", "aggr_p1w_leakctrl_04"}.issubset(ids)
    assert "phase_region" in v2[0]

    p18 = {row["variant_id"]: row for row in v2 if row["variant_id"].startswith("aggr_")}
    assert p18["aggr_lhs_retention_dy_05"]["phase_region"] == "60_90_usable"
    assert p18["aggr_p1w_leakctrl_04"]["phase_region"] == "60_90_usable"


def test_phase_wrap_and_angular_distance() -> None:
    assert wrap_phase_deg(180.0) == -180.0
    assert wrap_phase_deg(181.0) == -179.0
    assert angular_distance_deg(179.0, -179.0) == 2.0
    assert angular_distance_deg(72.24132809604521, 60.0) < 13.0


def test_phase_coverage_v2_has_expected_bins_and_60_bin_status() -> None:
    coverage = _rows(COVERAGE_V2)
    by_bin = {float(row["phase_bin_deg"]): row for row in coverage}

    assert set(by_bin) == {0.0, 60.0, 120.0, -180.0, -120.0, -60.0}
    assert by_bin[60.0]["coverage_status"] == "early_covered"
    assert by_bin[60.0]["nearest_candidate_early_pass"] == "aggr_lhs_retention_dy_05"
    assert by_bin[120.0]["coverage_status"] == "strong_covered"
    assert {by_bin[target]["coverage_status"] for target in (0.0, -60.0, -120.0, -180.0)} == {"open_gap"}


def test_reports_state_no_fdtd_training_steering_or_complete_library() -> None:
    combined = "\n".join(
        [
            REPORT_V2.read_text(encoding="utf-8"),
            ANALYSIS_V2.read_text(encoding="utf-8"),
            READINESS_V2.read_text(encoding="utf-8"),
        ]
    )

    assert "No FDTD was run" in combined
    assert "No lumapi" in combined or "No lumapi call was made" in combined
    assert "No model was trained" in combined
    assert "not a steering result" in combined
    assert "not ready for K=6 phase-ramp supercell assembly" in combined
