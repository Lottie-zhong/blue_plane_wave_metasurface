from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_next_phase_gap_candidates import (
    NEXT_PHASE_GAP_SELECTION_FIELDS,
    NEXT_PHASE_GAP_VALIDATION_FIELDS,
    build_next_phase_gap_candidate_pool,
    existing_geometry_rows_from_paths,
    select_next_phase_gap_fdtd_candidates,
    validate_next_phase_gap_candidate_pool,
    write_csv_rows,
)


EXISTING_GEOMETRY_INPUTS = [
    REPO_ROOT / "outputs/apcd_k6_active_learning/bounded_candidate_pool_v0.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/neighborhood_candidate_pool_v1.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/p1w_dx_fine_candidate_pool_v1.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/phase_gap_candidate_pool_v1.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/aggressive_phase_gap_candidate_pool_v1.csv",
]
VALIDATION_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/next_phase_gap_candidate_pool_v2_geometry_validation.csv"
SELECTION_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/next_phase_gap_fdtd_selection_v2.csv"
SELECTION_SUMMARY = REPO_ROOT / "outputs/apcd_k6_active_learning/next_phase_gap_fdtd_selection_v2_summary.md"
SCRIPT_49 = REPO_ROOT / "scripts/49_validate_apcd_k6_next_phase_gap_candidate_pool.py"
SCRIPT_50 = REPO_ROOT / "scripts/50_select_apcd_k6_next_phase_gap_fdtd_candidates.py"


def _pool() -> list[dict[str, object]]:
    return build_next_phase_gap_candidate_pool()


def _validation() -> list[dict[str, object]]:
    return validate_next_phase_gap_candidate_pool(_pool(), existing_geometry_rows_from_paths(EXISTING_GEOMETRY_INPUTS))


def test_validation_csv_columns_and_all_pass() -> None:
    rows = _validation()

    assert len(rows) == len(_pool())
    assert set(NEXT_PHASE_GAP_VALIDATION_FIELDS).issubset(rows[0].keys())
    assert sum(str(row["overall_geometry_pass"]) == "True" for row in rows) == 29
    assert sum(str(row["recommended_for_fdtd"]) == "True" for row in rows) == 29
    assert sum(str(row["duplicate_geometry_pass"]) != "True" for row in rows) == 9


def test_selection_count_policy_and_selected_not_run() -> None:
    selected = select_next_phase_gap_fdtd_candidates(_pool(), _validation())
    ids = [row["candidate_id"] for row in selected]
    targets = {float(row["target_bin_deg"]) for row in selected}
    families = {row["candidate_family"] for row in selected}
    risks = [str(row["risk_level"]) for row in selected]

    assert len(selected) == 4
    assert len(ids) == len(set(ids))
    assert ids == [
        "next_zero_rot_anchor_03",
        "next_rot_anchor_04",
        "next_mixed_bridge_03",
        "next_pi_mixed_bridge_03",
    ]
    assert {row["status"] for row in selected} == {"selected_not_run"}
    assert {str(row["geometry_pass"]) for row in selected} == {"True"}
    assert {str(row["recommended_for_fdtd"]) for row in selected} == {"True"}
    assert 0.0 in targets
    assert {-60.0, -120.0} & targets
    assert len(targets) >= 2
    assert len(families) > 1
    assert any("high" not in risk for risk in risks)


def test_selection_csv_columns_are_complete(tmp_path: Path) -> None:
    output = write_csv_rows(
        select_next_phase_gap_fdtd_candidates(_pool(), _validation()),
        tmp_path / "selection.csv",
        NEXT_PHASE_GAP_SELECTION_FIELDS,
    )

    with output.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == NEXT_PHASE_GAP_SELECTION_FIELDS
    assert len(loaded) == 4


def test_generated_validation_and_selection_outputs_exist() -> None:
    with VALIDATION_CSV.open("r", newline="", encoding="utf-8") as handle:
        validation_rows = list(csv.DictReader(handle))
    with SELECTION_CSV.open("r", newline="", encoding="utf-8") as handle:
        selection_rows = list(csv.DictReader(handle))

    assert len(validation_rows) == len(_pool())
    assert sum(row["overall_geometry_pass"] == "True" for row in validation_rows) == 29
    assert len(selection_rows) == 4
    assert SELECTION_SUMMARY.exists()


def test_dry_run_scripts_do_not_generate_fsp(tmp_path: Path) -> None:
    validation_run = subprocess.run(
        [sys.executable, str(SCRIPT_49), "--dry-run", "--validation", str(tmp_path / "validation.csv")],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    selection_run = subprocess.run(
        [sys.executable, str(SCRIPT_50), "--dry-run", "--selection", str(tmp_path / "selection.csv")],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "no_fdtd" in validation_run.stdout
    assert "no_lumapi" in validation_run.stdout
    assert "no_yaml" in selection_run.stdout
    assert list(tmp_path.rglob("*.fsp")) == []


def test_selection_summary_states_selection_only() -> None:
    text = SELECTION_SUMMARY.read_text(encoding="utf-8")

    assert "selected_not_run planning only" in text
    assert "No YAML config was generated" in text
    assert "No FDTD was run" in text
    assert "not a steering result" in text
