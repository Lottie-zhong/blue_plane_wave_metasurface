from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_phase_gap_candidates import (
    PHASE_GAP_CANDIDATE_FIELDS,
    PHASE_GAP_SELECTION_FIELDS,
    PHASE_GAP_VALIDATION_FIELDS,
    build_phase_gap_candidate_pool,
    existing_geometry_rows_from_paths,
    select_phase_gap_fdtd_candidates,
    validate_phase_gap_candidate_pool,
    write_csv_rows,
)


EXISTING_GEOMETRY_INPUTS = [
    REPO_ROOT / "outputs/apcd_k6_active_learning/bounded_candidate_pool_v0.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/neighborhood_candidate_pool_v1.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/p1w_dx_fine_candidate_pool_v1.csv",
]
POOL_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_gap_candidate_pool_v1.csv"
VALIDATION_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_gap_candidate_pool_v1_geometry_validation.csv"
SELECTION_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_gap_fdtd_selection_v1.csv"
DECISION_REPORT = REPO_ROOT / "reports/apcd_k6_phase_gap_driven_next_candidate_decision.md"
POOL_SCRIPT = REPO_ROOT / "scripts/40_generate_apcd_k6_phase_gap_candidate_pool.py"
VALIDATE_SCRIPT = REPO_ROOT / "scripts/41_validate_and_select_apcd_k6_phase_gap_candidates.py"
MODULE_PATH = REPO_ROOT / "src/metasurface/apcd_phase_gap_candidates.py"


def _pool() -> list[dict[str, object]]:
    return build_phase_gap_candidate_pool()


def _validation() -> list[dict[str, object]]:
    return validate_phase_gap_candidate_pool(_pool(), existing_geometry_rows_from_paths(EXISTING_GEOMETRY_INPUTS))


def test_phase_gap_candidate_pool_count_families_and_unique_ids() -> None:
    rows = _pool()
    ids = [row["candidate_id"] for row in rows]
    families = {row["candidate_family"] for row in rows}

    assert 18 <= len(rows) <= 30
    assert len(ids) == len(set(ids))
    assert families == {
        "gap_60_90_lhs_leakage_reduced",
        "gap_60_90_bridge_from_p1w_dx",
        "gap_60_90_p1w_dx_extended",
        "gap_60_90_p2w_trim",
    }


def test_phase_gap_candidates_obey_bounds_rotations_and_beta_policy() -> None:
    for row in _pool():
        assert 110 <= float(row["p1_length_nm"]) <= 150
        assert 55 <= float(row["p1_width_nm"]) <= 90
        assert 70 <= float(row["p2_length_nm"]) <= 105
        assert 130 <= float(row["p2_width_nm"]) <= 170
        assert -40 <= float(row["internal_dx_nm"]) <= 40
        assert -40 <= float(row["internal_dy_nm"]) <= 40
        assert float(row["p1_rotation_deg"]) == 67.5
        assert float(row["p2_rotation_deg"]) == 112.5
        assert not (float(row["p2_length_nm"]) == 150.0 and float(row["p2_width_nm"]) == 85.0)


def test_candidate_pool_csv_columns_are_complete(tmp_path: Path) -> None:
    output = write_csv_rows(_pool(), tmp_path / "pool.csv", PHASE_GAP_CANDIDATE_FIELDS)

    with output.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == PHASE_GAP_CANDIDATE_FIELDS
    assert len(loaded) == len(_pool())


def test_geometry_validation_columns_and_counts() -> None:
    rows = _validation()

    assert len(rows) == 24
    assert sum(1 for row in rows if str(row["overall_geometry_pass"]) == "True") == 24
    assert sum(1 for row in rows if str(row["recommended_for_fdtd"]) == "True") == 24
    assert {field for field in PHASE_GAP_VALIDATION_FIELDS}.issubset(rows[0].keys())


def test_selected_count_policy_and_selected_ids() -> None:
    selected = select_phase_gap_fdtd_candidates(_pool(), _validation())
    ids = [row["candidate_id"] for row in selected]
    families = [row["candidate_family"] for row in selected]

    assert 2 <= len(selected) <= 4
    assert ids == ["gap_bridge_03", "gap_lhs_leakred_06", "gap_p2w_trim_03"]
    assert len(ids) == len(set(ids))
    assert "gap_60_90_bridge_from_p1w_dx" in families
    assert "gap_60_90_lhs_leakage_reduced" in families
    assert {row["status"] for row in selected} == {"selected_not_run"}


def test_selection_csv_columns_are_complete(tmp_path: Path) -> None:
    selected = select_phase_gap_fdtd_candidates(_pool(), _validation())
    output = write_csv_rows(selected, tmp_path / "selection.csv", PHASE_GAP_SELECTION_FIELDS)

    with output.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == PHASE_GAP_SELECTION_FIELDS
    assert len(loaded) == len(selected)


def test_generated_outputs_exist_with_expected_counts() -> None:
    assert len(list(csv.DictReader(POOL_CSV.open("r", newline="", encoding="utf-8")))) == 24
    assert len(list(csv.DictReader(VALIDATION_CSV.open("r", newline="", encoding="utf-8")))) == 24
    assert len(list(csv.DictReader(SELECTION_CSV.open("r", newline="", encoding="utf-8")))) == 3


def test_dry_run_scripts_do_not_generate_fsp(tmp_path: Path) -> None:
    pool_run = subprocess.run(
        [sys.executable, str(POOL_SCRIPT), "--dry-run", "--output", str(tmp_path / "pool.csv")],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    validation_run = subprocess.run(
        [sys.executable, str(VALIDATE_SCRIPT), "--dry-run", "--pool", str(POOL_CSV)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "no_fdtd" in pool_run.stdout
    assert "no_fdtd" in validation_run.stdout
    assert list(tmp_path.glob("*.fsp")) == []


def test_no_lumapi_fdtd_run_or_fsp_export_in_phase_gap_code() -> None:
    combined = "\n".join(
        [
            MODULE_PATH.read_text(encoding="utf-8"),
            POOL_SCRIPT.read_text(encoding="utf-8"),
            VALIDATE_SCRIPT.read_text(encoding="utf-8"),
        ]
    )

    assert "import lumapi" not in combined
    assert "fdtd.run" not in combined
    assert "fdtd.save" not in combined


def test_decision_report_states_no_fdtd_no_training_no_steering() -> None:
    text = DECISION_REPORT.read_text(encoding="utf-8")

    assert "No new FDTD was run" in text
    assert "No model was trained" in text
    assert "not a steering result" in text
    assert "60-90 deg" in text
    assert "K=7" in text
