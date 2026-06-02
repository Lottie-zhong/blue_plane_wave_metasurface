from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_neighborhood_selection import (
    NEIGHBORHOOD_SELECTION_FIELDS,
    export_neighborhood_fdtd_selection_csv,
    load_neighborhood_candidate_pool,
    load_neighborhood_geometry_validation,
    select_neighborhood_fdtd_candidates,
    summarize_neighborhood_fdtd_selection,
)


CANDIDATE_POOL = REPO_ROOT / "outputs" / "apcd_k6_active_learning" / "neighborhood_candidate_pool_v1.csv"
GEOMETRY_VALIDATION = (
    REPO_ROOT / "outputs" / "apcd_k6_active_learning" / "neighborhood_candidate_pool_v1_geometry_validation.csv"
)
SCRIPT_PATH = REPO_ROOT / "scripts" / "33_select_apcd_k6_neighborhood_fdtd_candidates.py"
REPORT_PATH = REPO_ROOT / "reports" / "apcd_k6_neighborhood_fdtd_selection_v1_note.md"


def _selected_rows() -> list[dict[str, object]]:
    candidates = load_neighborhood_candidate_pool(CANDIDATE_POOL)
    validation = load_neighborhood_geometry_validation(GEOMETRY_VALIDATION)
    return select_neighborhood_fdtd_candidates(candidates, validation)


def test_selection_uses_only_geometry_pass_recommended_candidates() -> None:
    selected = _selected_rows()

    assert {row["geometry_pass"] for row in selected} == {"True"}
    assert {row["recommended_for_fdtd"] for row in selected} == {"True"}


def test_selected_count_is_2_to_4() -> None:
    selected = _selected_rows()

    assert 2 <= len(selected) <= 4


def test_selection_includes_p1w_dx_neighborhood() -> None:
    selected = _selected_rows()

    assert any(row["candidate_family"] == "p1w_dx_neighborhood" for row in selected)


def test_lhs_like_leakage_reduction_count_is_at_most_one() -> None:
    selected = _selected_rows()
    summary = summarize_neighborhood_fdtd_selection(selected)

    assert summary["lhs_like_leakage_reduction_count"] <= 1


def test_candidate_ids_are_unique_and_expected() -> None:
    selected = _selected_rows()
    ids = [row["candidate_id"] for row in selected]

    assert ids == ["nhood_p1w_dx_05", "nhood_p1w_dx_02", "nhood_lhs_leakred_06"]
    assert len(ids) == len(set(ids))


def test_status_is_selected_not_run() -> None:
    selected = _selected_rows()

    assert {row["status"] for row in selected} == {"selected_not_run"}


def test_output_csv_columns_are_complete(tmp_path: Path) -> None:
    selected = _selected_rows()
    output_csv = export_neighborhood_fdtd_selection_csv(selected, tmp_path / "selection.csv")

    with output_csv.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == NEIGHBORHOOD_SELECTION_FIELDS
    assert len(loaded) == len(selected)


def test_cli_dry_run_does_not_write_outputs_or_generate_fsp(tmp_path: Path) -> None:
    output_csv = tmp_path / "selection.csv"
    summary_md = tmp_path / "selection.md"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--dry-run",
            "--candidate-pool",
            str(CANDIDATE_POOL),
            "--geometry-validation",
            str(GEOMETRY_VALIDATION),
            "--output-csv",
            str(output_csv),
            "--summary-md",
            str(summary_md),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "status=neighborhood_fdtd_selection_only_no_fdtd_no_lumapi_no_fsp_no_training_no_prediction" in completed.stdout
    assert "selected_count=3" in completed.stdout
    assert "dry_run=true; no output files written" in completed.stdout
    assert not output_csv.exists()
    assert not summary_md.exists()
    assert list(tmp_path.glob("*.fsp")) == []


def test_script_does_not_call_lumapi_or_fdtd_run() -> None:
    script_text = SCRIPT_PATH.read_text(encoding="utf-8")
    module_text = (REPO_ROOT / "src" / "metasurface" / "apcd_neighborhood_selection.py").read_text(
        encoding="utf-8"
    )

    assert "import lumapi" not in script_text
    assert "fdtd.run" not in script_text
    assert "fdtd.save" not in script_text
    assert "import lumapi" not in module_text
    assert "fdtd.run" not in module_text
    assert "fdtd.save" not in module_text


def test_report_states_selection_only_boundaries() -> None:
    text = REPORT_PATH.read_text(encoding="utf-8")

    assert "09-P8" in text
    assert "only selects 2-4 neighborhood FDTD candidates" in text
    assert "No FDTD run was" in text
    assert "no lumapi call" in text
    assert "no model was trained" in text
    assert "no `.fsp` file was exported" in text
    assert "selection only" in text
    assert "not a `+15 deg` steering result" in text
