from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_candidate_selection import (
    SELECTED_BATCH_FIELDS,
    export_selected_batch_csv,
    load_candidate_pool,
    load_geometry_validation,
    select_first_fdtd_batch,
    summarize_selected_batch,
)


CANDIDATE_POOL = REPO_ROOT / "outputs" / "apcd_k6_active_learning" / "bounded_candidate_pool_v0.csv"
GEOMETRY_VALIDATION = (
    REPO_ROOT
    / "outputs"
    / "apcd_k6_active_learning"
    / "bounded_candidate_pool_v0_geometry_validation.csv"
)
SCRIPT_PATH = REPO_ROOT / "scripts" / "29_select_apcd_k6_first_fdtd_batch.py"
REPORT_PATH = REPO_ROOT / "reports" / "apcd_k6_first_fdtd_batch_selection_note.md"


def _selected_rows() -> list[dict[str, object]]:
    candidates = load_candidate_pool(CANDIDATE_POOL)
    validation = load_geometry_validation(GEOMETRY_VALIDATION)
    return select_first_fdtd_batch(candidates, validation, batch_size=8)


def test_selection_uses_only_geometry_pass_candidates() -> None:
    selected = _selected_rows()

    assert selected
    assert {row["geometry_pass"] for row in selected} == {"True"}
    assert {row["recommended_for_fdtd"] for row in selected} == {"True"}


def test_baseline_not_in_first_batch() -> None:
    selected = _selected_rows()

    assert "baseline" not in {row["candidate_id"] for row in selected}


def test_selected_count_is_6_to_10() -> None:
    selected = _selected_rows()

    assert 6 <= len(selected) <= 10


def test_candidate_ids_are_unique() -> None:
    selected = _selected_rows()
    ids = [row["candidate_id"] for row in selected]

    assert len(ids) == len(set(ids))


def test_selection_covers_multiple_candidate_families() -> None:
    selected = _selected_rows()
    summary = summarize_selected_batch(selected)

    assert len(summary["family_counts"]) >= 6
    assert summary["has_negative_internal_dx"] is True
    assert summary["has_positive_internal_dx"] is True
    assert summary["has_negative_internal_dy"] is True
    assert summary["has_positive_internal_dy"] is True


def test_status_is_selected_not_run() -> None:
    selected = _selected_rows()

    assert {row["status"] for row in selected} == {"selected_not_run"}


def test_output_csv_columns_are_complete(tmp_path: Path) -> None:
    selected = _selected_rows()
    output_csv = export_selected_batch_csv(selected, tmp_path / "first_fdtd_batch_v0.csv")

    with output_csv.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == SELECTED_BATCH_FIELDS
    assert len(loaded) == len(selected)


def test_cli_dry_run_writes_outputs_and_no_fsp(tmp_path: Path) -> None:
    output_csv = tmp_path / "first_fdtd_batch_v0.csv"
    summary_md = tmp_path / "first_fdtd_batch_v0_summary.md"
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

    assert "status=dry_run_selection_only_no_fdtd_no_lumapi_no_fsp_no_training_no_prediction" in completed.stdout
    assert "selected_count=8" in completed.stdout
    assert output_csv.is_file()
    assert summary_md.is_file()
    assert list(tmp_path.glob("*.fsp")) == []


def test_script_does_not_call_lumapi_or_fdtd_run() -> None:
    text = SCRIPT_PATH.read_text(encoding="utf-8")
    module_text = (REPO_ROOT / "src" / "metasurface" / "apcd_candidate_selection.py").read_text(
        encoding="utf-8"
    )

    assert "import lumapi" not in text
    assert "fdtd.run" not in text
    assert "fdtd.save" not in text
    assert "import lumapi" not in module_text
    assert "fdtd.run" not in module_text
    assert "fdtd.save" not in module_text


def test_report_states_rule_based_selection_boundaries() -> None:
    text = REPORT_PATH.read_text(encoding="utf-8")

    assert "09-P4" in text
    assert "No FDTD run was performed" in text
    assert "No model was trained" in text
    assert "No surrogate prediction was generated" in text
    assert "not a `+15 deg` steering result" in text
    assert "rule-based diversity selection" in text
