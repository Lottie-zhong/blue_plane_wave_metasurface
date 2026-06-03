from __future__ import annotations

import csv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"

import sys

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_focused_next_gap_candidates import (
    FOCUSED_NEXT_GAP_CANDIDATE_FIELDS,
    FOCUSED_NEXT_GAP_SELECTION_FIELDS,
    FOCUSED_NEXT_GAP_VALIDATION_FIELDS,
    build_focused_next_gap_candidate_pool,
    existing_geometry_rows_from_paths,
    select_focused_next_gap_fdtd_candidates,
    validate_focused_next_gap_candidate_pool,
    write_csv_rows,
)


POOL_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/focused_next_gap_candidate_pool_v3.csv"
VALIDATION_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/focused_next_gap_candidate_pool_v3_geometry_validation.csv"
SELECTION_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/focused_next_gap_fdtd_selection_v3.csv"
MODULE_PATH = REPO_ROOT / "src/metasurface/apcd_focused_next_gap_candidates.py"
SCRIPT_53 = REPO_ROOT / "scripts/53_generate_apcd_k6_focused_next_gap_candidate_pool.py"
SCRIPT_54 = REPO_ROOT / "scripts/54_validate_apcd_k6_focused_next_gap_candidate_pool.py"
SCRIPT_55 = REPO_ROOT / "scripts/55_select_apcd_k6_focused_next_gap_fdtd_candidates.py"
EXISTING_GEOMETRY_INPUTS = [
    REPO_ROOT / "outputs/apcd_k6_active_learning/bounded_candidate_pool_v0.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/neighborhood_candidate_pool_v1.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/p1w_dx_fine_candidate_pool_v1.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/phase_gap_candidate_pool_v1.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/aggressive_phase_gap_candidate_pool_v1.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/next_phase_gap_candidate_pool_v2.csv",
]


def _pool() -> list[dict[str, object]]:
    return build_focused_next_gap_candidate_pool()


def _validation() -> list[dict[str, object]]:
    return validate_focused_next_gap_candidate_pool(_pool(), existing_geometry_rows_from_paths(EXISTING_GEOMETRY_INPUTS))


def test_focused_pool_count_required_columns_and_metadata() -> None:
    rows = _pool()
    ids = [row["candidate_id"] for row in rows]
    families = {row["candidate_family"] for row in rows}
    targets = {float(row["target_bin_deg"]) for row in rows}

    assert 36 <= len(rows) <= 48
    assert len(rows) == 40
    assert len(ids) == len(set(ids))
    assert families == {"zero_bin_leakage_reduction", "negative_phase_redesign"}
    assert {0.0, -60.0, -120.0, -180.0}.issubset(targets)
    for row in rows:
        assert set(FOCUSED_NEXT_GAP_CANDIDATE_FIELDS).issubset(row.keys())
        assert row["target_bin_deg"] != ""
        assert row["candidate_family"] != ""
        assert str(row["design_rationale"]).strip()
        assert str(row["risk_level"]).strip()
        assert row["status"] == "not_evaluated"


def test_focused_pool_csv_columns_are_complete(tmp_path: Path) -> None:
    output = write_csv_rows(_pool(), tmp_path / "pool.csv", FOCUSED_NEXT_GAP_CANDIDATE_FIELDS)
    with output.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == FOCUSED_NEXT_GAP_CANDIDATE_FIELDS
    assert len(loaded) == len(_pool())


def test_geometry_validation_has_pass_fail_columns_and_all_current_candidates_pass() -> None:
    rows = _validation()

    assert len(rows) == len(_pool())
    assert set(FOCUSED_NEXT_GAP_VALIDATION_FIELDS).issubset(rows[0].keys())
    assert {str(row["overall_geometry_pass"]) for row in rows} == {"True"}
    assert {str(row["recommended_for_fdtd"]) for row in rows} == {"True"}


def test_selected_not_run_policy() -> None:
    selected = select_focused_next_gap_fdtd_candidates(_pool(), _validation())
    ids = [row["candidate_id"] for row in selected]
    targets = {float(row["target_bin_deg"]) for row in selected}
    families = {row["candidate_family"] for row in selected}
    risks = [str(row["risk_level"]) for row in selected]

    assert len(selected) == 4
    assert ids == [
        "focus_zero_leakred_07",
        "focus_neg60_geom_04",
        "focus_neg120_asym_03",
        "focus_pi_wrap_04",
    ]
    assert len(ids) == len(set(ids))
    assert {row["status"] for row in selected} == {"selected_not_run"}
    assert {str(row["geometry_pass"]) for row in selected} == {"True"}
    assert 0.0 in targets
    assert -60.0 in targets
    assert {-120.0, -180.0} & targets
    assert len(targets) >= 3
    assert len(families) > 1
    assert any("high" not in risk for risk in risks)


def test_selection_csv_columns_are_complete(tmp_path: Path) -> None:
    selected = select_focused_next_gap_fdtd_candidates(_pool(), _validation())
    output = write_csv_rows(selected, tmp_path / "selection.csv", FOCUSED_NEXT_GAP_SELECTION_FIELDS)
    with output.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == FOCUSED_NEXT_GAP_SELECTION_FIELDS
    assert len(loaded) == 4


def test_generated_outputs_exist_with_expected_counts() -> None:
    with POOL_CSV.open("r", newline="", encoding="utf-8") as handle:
        pool_rows = list(csv.DictReader(handle))
    with VALIDATION_CSV.open("r", newline="", encoding="utf-8") as handle:
        validation_rows = list(csv.DictReader(handle))
    with SELECTION_CSV.open("r", newline="", encoding="utf-8") as handle:
        selection_rows = list(csv.DictReader(handle))

    assert len(pool_rows) == 40
    assert len(validation_rows) == 40
    assert len(selection_rows) == 4


def test_code_does_not_call_lumapi_or_fdtd_run() -> None:
    combined = "\n".join(
        [
            MODULE_PATH.read_text(encoding="utf-8"),
            SCRIPT_53.read_text(encoding="utf-8"),
            SCRIPT_54.read_text(encoding="utf-8"),
            SCRIPT_55.read_text(encoding="utf-8"),
        ]
    )

    assert "import lumapi" not in combined
    assert "APCDSingleDimerRunner" not in combined
    assert "fdtd.run" not in combined
    assert "fdtd.save" not in combined
    assert ".fsp" in combined
