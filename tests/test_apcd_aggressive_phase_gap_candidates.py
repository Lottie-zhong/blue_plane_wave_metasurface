from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_aggressive_phase_gap_candidates import (
    AGGRESSIVE_PHASE_GAP_CANDIDATE_FIELDS,
    AGGRESSIVE_PHASE_GAP_SELECTION_FIELDS,
    AGGRESSIVE_PHASE_GAP_VALIDATION_FIELDS,
    build_aggressive_phase_gap_candidate_pool,
    existing_geometry_rows_from_paths,
    select_aggressive_phase_gap_fdtd_candidates,
    validate_aggressive_phase_gap_candidate_pool,
    write_csv_rows,
)


EXISTING_GEOMETRY_INPUTS = [
    REPO_ROOT / "outputs/apcd_k6_active_learning/bounded_candidate_pool_v0.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/neighborhood_candidate_pool_v1.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/p1w_dx_fine_candidate_pool_v1.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/phase_gap_candidate_pool_v1.csv",
]
POOL_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/aggressive_phase_gap_candidate_pool_v1.csv"
VALIDATION_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/aggressive_phase_gap_candidate_pool_v1_geometry_validation.csv"
SELECTION_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/aggressive_phase_gap_fdtd_selection_v1.csv"
REPORT_PATH = REPO_ROOT / "reports/apcd_k6_aggressive_phase_gap_candidate_pool_v1_note.md"
MODULE_PATH = REPO_ROOT / "src/metasurface/apcd_aggressive_phase_gap_candidates.py"
SCRIPT_43 = REPO_ROOT / "scripts/43_generate_apcd_k6_aggressive_phase_gap_candidate_pool.py"
SCRIPT_44 = REPO_ROOT / "scripts/44_validate_and_select_apcd_k6_aggressive_phase_gap_candidates.py"


def _pool() -> list[dict[str, object]]:
    return build_aggressive_phase_gap_candidate_pool()


def _validation() -> list[dict[str, object]]:
    return validate_aggressive_phase_gap_candidate_pool(_pool(), existing_geometry_rows_from_paths(EXISTING_GEOMETRY_INPUTS))


def test_candidate_count_families_and_unique_ids() -> None:
    rows = _pool()
    ids = [row["candidate_id"] for row in rows]
    families = {row["candidate_family"] for row in rows}

    assert 24 <= len(rows) <= 36
    assert len(ids) == len(set(ids))
    assert families == {
        "lhs_like_retention_high_dy",
        "lhs_like_leakage_control_p1w",
        "lhs_like_p2w_trim",
        "lhs_to_fine_bridge_aggressive",
        "dy_sweep_near_lhs",
        "mixed_aggressive_but_safe",
    }


def test_candidate_csv_columns_are_complete(tmp_path: Path) -> None:
    output = write_csv_rows(_pool(), tmp_path / "pool.csv", AGGRESSIVE_PHASE_GAP_CANDIDATE_FIELDS)

    with output.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == AGGRESSIVE_PHASE_GAP_CANDIDATE_FIELDS
    assert len(loaded) == len(_pool())


def test_all_candidates_obey_bounds_and_rotation_policy() -> None:
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


def test_geometry_validation_columns_and_pass_count() -> None:
    rows = _validation()

    assert len(rows) == 32
    assert sum(str(row["overall_geometry_pass"]) == "True" for row in rows) == 32
    assert sum(str(row["recommended_for_fdtd"]) == "True" for row in rows) == 32
    assert set(AGGRESSIVE_PHASE_GAP_VALIDATION_FIELDS).issubset(rows[0].keys())


def test_selected_not_run_count_and_policy() -> None:
    selected = select_aggressive_phase_gap_fdtd_candidates(_pool(), _validation())
    ids = [row["candidate_id"] for row in selected]
    families = [row["candidate_family"] for row in selected]

    assert len(selected) == 3
    assert ids == ["aggr_lhs_retention_dy_05", "aggr_p1w_leakctrl_04", "aggr_bridge_lhs_fine_05"]
    assert len(ids) == len(set(ids))
    assert "lhs_like_retention_high_dy" in families
    assert "lhs_like_leakage_control_p1w" in families
    assert "lhs_to_fine_bridge_aggressive" in families
    assert {row["status"] for row in selected} == {"selected_not_run"}
    assert {str(row["geometry_pass"]) for row in selected} == {"True"}
    assert {str(row["recommended_for_fdtd"]) for row in selected} == {"True"}


def test_selection_csv_columns_are_complete(tmp_path: Path) -> None:
    selected = select_aggressive_phase_gap_fdtd_candidates(_pool(), _validation())
    output = write_csv_rows(selected, tmp_path / "selection.csv", AGGRESSIVE_PHASE_GAP_SELECTION_FIELDS)

    with output.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == AGGRESSIVE_PHASE_GAP_SELECTION_FIELDS
    assert len(loaded) == 3


def test_generated_outputs_exist_with_expected_counts() -> None:
    assert len(list(csv.DictReader(POOL_CSV.open("r", newline="", encoding="utf-8")))) == 32
    assert len(list(csv.DictReader(VALIDATION_CSV.open("r", newline="", encoding="utf-8")))) == 32
    assert len(list(csv.DictReader(SELECTION_CSV.open("r", newline="", encoding="utf-8")))) == 3


def test_dry_run_scripts_do_not_generate_fsp(tmp_path: Path) -> None:
    pool_run = subprocess.run(
        [sys.executable, str(SCRIPT_43), "--dry-run", "--output", str(tmp_path / "pool.csv")],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    validation_run = subprocess.run(
        [sys.executable, str(SCRIPT_44), "--dry-run", "--pool", str(POOL_CSV)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "no_fdtd" in pool_run.stdout
    assert "no_lumapi" in pool_run.stdout
    assert "no_fsp" in validation_run.stdout
    assert list(tmp_path.glob("*.fsp")) == []


def test_code_does_not_call_lumapi_or_fdtd_run() -> None:
    combined = "\n".join(
        [
            MODULE_PATH.read_text(encoding="utf-8"),
            SCRIPT_43.read_text(encoding="utf-8"),
            SCRIPT_44.read_text(encoding="utf-8"),
        ]
    )

    assert "import lumapi" not in combined
    assert "fdtd.run" not in combined
    assert "fdtd.save" not in combined


def test_report_states_no_fdtd_no_training_no_steering() -> None:
    text = REPORT_PATH.read_text(encoding="utf-8")

    assert "09-P17" in text
    assert "No FDTD was run" in text
    assert "No lumapi call was made" in text
    assert "No `.fsp` file was generated" in text
    assert "No model was trained" in text
    assert "not a steering result" in text
    assert "K=6 phase-state library is still incomplete" in text
