from __future__ import annotations

import csv
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"

import sys

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_phase_lowering_candidates import (
    PHASE_LOWERING_CANDIDATE_FIELDS,
    PHASE_LOWERING_SELECTION_FIELDS,
    PHASE_LOWERING_VALIDATION_FIELDS,
    build_phase_lowering_candidate_pool,
    existing_geometry_rows_from_paths,
    select_phase_lowering_fdtd_candidates,
    validate_phase_lowering_candidate_pool,
    write_csv_rows,
)


POOL_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_lowering_candidate_pool_v4.csv"
VALIDATION_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_lowering_candidate_pool_v4_geometry_validation.csv"
SELECTION_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_lowering_fdtd_selection_v4.csv"
MODULE_PATH = REPO_ROOT / "src/metasurface/apcd_phase_lowering_candidates.py"
SCRIPT_57 = REPO_ROOT / "scripts/57_generate_apcd_k6_phase_lowering_candidate_pool.py"
SCRIPT_58 = REPO_ROOT / "scripts/58_validate_apcd_k6_phase_lowering_candidate_pool.py"
SCRIPT_59 = REPO_ROOT / "scripts/59_select_apcd_k6_phase_lowering_fdtd_candidates.py"
EXISTING_GEOMETRY_INPUTS = [
    REPO_ROOT / "outputs/apcd_k6_active_learning/bounded_candidate_pool_v0.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/neighborhood_candidate_pool_v1.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/p1w_dx_fine_candidate_pool_v1.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/phase_gap_candidate_pool_v1.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/aggressive_phase_gap_candidate_pool_v1.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/next_phase_gap_candidate_pool_v2.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/focused_next_gap_candidate_pool_v3.csv",
]


def _pool() -> list[dict[str, object]]:
    return build_phase_lowering_candidate_pool()


def _validation() -> list[dict[str, object]]:
    return validate_phase_lowering_candidate_pool(_pool(), existing_geometry_rows_from_paths(EXISTING_GEOMETRY_INPUTS))


def test_phase_lowering_pool_count_columns_and_metadata() -> None:
    rows = _pool()
    ids = [row["candidate_id"] for row in rows]
    families = {row["candidate_family"] for row in rows}
    targets = {float(row["target_bin_deg"]) for row in rows}

    assert 36 <= len(rows) <= 48
    assert len(rows) == 42
    assert len(ids) == len(set(ids))
    assert families == {
        "neg60_phase_lowering_from_focus_anchor",
        "zero_bridge_from_focus_anchor",
        "pi_wrap_from_focus_anchor",
        "coupled_dx_dy_phase_push",
        "aspect_ratio_inversion_probe",
        "mixed_negative_phase_safe_probe",
    }
    assert {0.0, -60.0, -120.0, -180.0}.issubset(targets)
    for row in rows:
        assert set(PHASE_LOWERING_CANDIDATE_FIELDS).issubset(row.keys())
        assert row["target_bin_deg"] != ""
        assert row["candidate_family"] != ""
        assert str(row["design_rationale"]).strip()
        assert str(row["risk_level"]).strip()
        assert str(row["expected_phase_direction"]).strip()
        assert row["requires_fdtd"] == "true"
        assert row["status"] == "not_evaluated"


def test_candidate_csv_columns_are_complete(tmp_path: Path) -> None:
    output = write_csv_rows(_pool(), tmp_path / "pool.csv", PHASE_LOWERING_CANDIDATE_FIELDS)
    with output.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == PHASE_LOWERING_CANDIDATE_FIELDS
    assert len(loaded) == len(_pool())


def test_geometry_validation_columns_and_pass_counts() -> None:
    rows = _validation()

    assert len(rows) == len(_pool())
    assert set(PHASE_LOWERING_VALIDATION_FIELDS).issubset(rows[0].keys())
    assert {str(row["overall_geometry_pass"]) for row in rows} == {"True"}
    assert {str(row["recommended_for_fdtd"]) for row in rows} == {"True"}


def test_selected_not_run_policy() -> None:
    selected = select_phase_lowering_fdtd_candidates(_pool(), _validation())
    ids = [row["candidate_id"] for row in selected]
    targets = {float(row["target_bin_deg"]) for row in selected}
    families = {row["candidate_family"] for row in selected}
    risks = [str(row["risk_level"]) for row in selected]
    anchors = " ".join(row["anchor_candidate"] for row in selected)

    assert len(selected) == 4
    assert ids == [
        "pl_zero_bridge_04",
        "pl_neg60_focus_push_05",
        "pl_neg120_aspect_03",
        "pl_pi_wrap_04",
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
    assert "focus_neg60_geom_04" in anchors


def test_selection_csv_columns_are_complete(tmp_path: Path) -> None:
    selected = select_phase_lowering_fdtd_candidates(_pool(), _validation())
    output = write_csv_rows(selected, tmp_path / "selection.csv", PHASE_LOWERING_SELECTION_FIELDS)
    with output.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == PHASE_LOWERING_SELECTION_FIELDS
    assert len(loaded) == 4


def test_generated_outputs_exist_with_expected_counts() -> None:
    with POOL_CSV.open("r", newline="", encoding="utf-8") as handle:
        pool_rows = list(csv.DictReader(handle))
    with VALIDATION_CSV.open("r", newline="", encoding="utf-8") as handle:
        validation_rows = list(csv.DictReader(handle))
    with SELECTION_CSV.open("r", newline="", encoding="utf-8") as handle:
        selection_rows = list(csv.DictReader(handle))

    assert len(pool_rows) == 42
    assert len(validation_rows) == 42
    assert len(selection_rows) == 4


def test_code_does_not_call_lumapi_or_fdtd_run() -> None:
    combined = "\n".join(
        [
            MODULE_PATH.read_text(encoding="utf-8"),
            SCRIPT_57.read_text(encoding="utf-8"),
            SCRIPT_58.read_text(encoding="utf-8"),
            SCRIPT_59.read_text(encoding="utf-8"),
        ]
    )

    assert "import lumapi" not in combined
    assert "APCDSingleDimerRunner" not in combined
    assert "fdtd.run" not in combined
    assert "fdtd.save" not in combined
    assert "setup_only" not in combined
