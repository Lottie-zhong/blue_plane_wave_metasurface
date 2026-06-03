from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_focused_next_gap_candidates import angular_distance_deg


DATASET_V2 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v2.csv"
DATASET_V3 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v3.csv"
COVERAGE_V3 = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_coverage_v3.csv"
REPORT = REPO_ROOT / "reports/apcd_k6_focused_next_gap_redesign_v3_note.md"
SCRIPT_53 = REPO_ROOT / "scripts/53_generate_apcd_k6_focused_next_gap_candidate_pool.py"
SCRIPT_55 = REPO_ROOT / "scripts/55_select_apcd_k6_focused_next_gap_fdtd_candidates.py"


def _rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_dataset_v3_adds_p23_rows_without_duplicates() -> None:
    v2 = _rows(DATASET_V2)
    v3 = _rows(DATASET_V3)
    ids = [row["variant_id"] for row in v3]
    by_id = {row["variant_id"]: row for row in v3}

    assert len(v3) == len(v2) + 2
    assert len(ids) == len(set(ids))
    assert {"next_zero_rot_anchor_03", "next_rot_anchor_04"}.issubset(by_id)
    assert by_id["next_zero_rot_anchor_03"]["overall_early_pass"] == "False"
    assert by_id["next_zero_rot_anchor_03"]["target_bin_status"] == "evidence_only"
    assert by_id["next_zero_rot_anchor_03"]["phase_region"] == "target_bin_evidence_only"
    assert by_id["next_rot_anchor_04"]["overall_early_pass"] == "False"
    assert by_id["next_rot_anchor_04"]["target_bin_status"] == "open_gap"
    assert by_id["next_rot_anchor_04"]["phase_region"] == "target_bin_open_gap"


def test_coverage_v3_statuses_match_expected_gap_state() -> None:
    coverage = {float(row["phase_bin_deg"]): row for row in _rows(COVERAGE_V3)}

    assert coverage[60.0]["coverage_status"] == "early_covered"
    assert coverage[120.0]["coverage_status"] == "strong_covered"
    assert coverage[0.0]["coverage_status"] == "evidence_only"
    assert coverage[0.0]["nearest_candidate_evidence_only"] == "next_zero_rot_anchor_03"
    assert coverage[-60.0]["coverage_status"] == "open_gap"
    assert coverage[-120.0]["coverage_status"] == "open_gap"
    assert coverage[-180.0]["coverage_status"] == "open_gap"


def test_wrapped_distance_for_zero_evidence() -> None:
    assert abs(angular_distance_deg(20.788972844777305, 0.0) - 20.788972844777305) < 1e-12
    assert angular_distance_deg(179.0, -179.0) == 2.0


def test_dry_run_scripts_do_not_generate_fsp(tmp_path: Path) -> None:
    generate = subprocess.run(
        [sys.executable, str(SCRIPT_53), "--dry-run", "--pool", str(tmp_path / "pool.csv")],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    select = subprocess.run(
        [sys.executable, str(SCRIPT_55), "--dry-run", "--selection", str(tmp_path / "selection.csv")],
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


def test_report_states_boundaries_and_interpretation() -> None:
    text = REPORT.read_text(encoding="utf-8")

    assert "0 deg gap" in text
    assert "evidence_only rather than usable" in text
    assert "-60 deg bin remains open_gap" in text
    assert "rotation-assisted hypothesis" in text
    assert "No K=7" in text
    assert "no phase-ramp supercell" in text
    assert "no `.fsp`" in text
    assert "+15 deg steering" in text
