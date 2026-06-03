from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_phase_lowering_candidates import angular_distance_deg


DATASET_V3 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v3.csv"
DATASET_V4 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v4.csv"
COVERAGE_V4 = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_coverage_v4.csv"
REPORT = REPO_ROOT / "reports/apcd_k6_phase_lowering_redesign_v4_note.md"
SCRIPT_57 = REPO_ROOT / "scripts/57_generate_apcd_k6_phase_lowering_candidate_pool.py"
SCRIPT_59 = REPO_ROOT / "scripts/59_select_apcd_k6_phase_lowering_fdtd_candidates.py"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_dataset_v4_adds_p26_rows_without_duplicates() -> None:
    v3 = _rows(DATASET_V3)
    v4 = _rows(DATASET_V4)
    ids = [row["variant_id"] for row in v4]
    by_id = {row["variant_id"]: row for row in v4}

    assert len(v4) == len(v3) + 2
    assert len(ids) == len(set(ids))
    assert {"focus_zero_leakred_07", "focus_neg60_geom_04"}.issubset(by_id)
    assert by_id["focus_zero_leakred_07"]["overall_early_pass"] == "False"
    assert by_id["focus_zero_leakred_07"]["phase_region"] == "target_bin_evidence_only"
    assert by_id["focus_zero_leakred_07"]["target_bin_status"] == "evidence_only"
    assert by_id["focus_neg60_geom_04"]["overall_early_pass"] == "True"
    assert by_id["focus_neg60_geom_04"]["phase_region"] == "usable_but_not_target"
    assert by_id["focus_neg60_geom_04"]["target_bin_status"] == "open_gap"


def test_phase_coverage_v4_contains_expected_bins_and_statuses() -> None:
    coverage = {float(row["phase_bin_deg"]): row for row in _rows(COVERAGE_V4)}

    assert set(coverage) == {0.0, 60.0, 120.0, -180.0, -120.0, -60.0}
    assert coverage[0.0]["coverage_status"] == "evidence_only"
    assert coverage[60.0]["coverage_status"] == "early_covered"
    assert coverage[120.0]["coverage_status"] == "strong_covered"
    assert coverage[-60.0]["coverage_status"] == "open_gap"
    assert coverage[-120.0]["coverage_status"] == "open_gap"
    assert coverage[-180.0]["coverage_status"] == "open_gap"


def test_wrapped_angular_distance() -> None:
    assert angular_distance_deg(179.0, -179.0) == 2.0
    assert abs(angular_distance_deg(30.534894730576525, 0.0) - 30.534894730576525) < 1e-12


def test_dry_run_scripts_do_not_generate_fsp(tmp_path: Path) -> None:
    generate = subprocess.run(
        [sys.executable, str(SCRIPT_57), "--dry-run", "--pool", str(tmp_path / "pool.csv")],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    select = subprocess.run(
        [sys.executable, str(SCRIPT_59), "--dry-run", "--selection", str(tmp_path / "selection.csv")],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "no_fdtd" in generate.stdout
    assert "no_lumapi" in generate.stdout
    assert "no_fsp" in generate.stdout
    assert "no_yaml" in select.stdout
    assert list(tmp_path.rglob("*.fsp")) == []


def test_report_states_phase_lowering_boundaries() -> None:
    text = REPORT.read_text(encoding="utf-8")

    assert "did not fill 0 deg" in text
    assert "high-quality positive-phase candidate" in text
    assert "phase-lowering candidate pool" in text
    assert "No FDTD" in text
    assert "no lumapi" in text
    assert "no `.fsp`" in text
    assert "no +15 deg steering claim" in text
