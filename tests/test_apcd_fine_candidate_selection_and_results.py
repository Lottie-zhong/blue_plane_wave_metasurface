from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_fine_candidate_selection import (
    FINE_RESULT_FIELDS,
    FINE_SELECTION_FIELDS,
    explicit_result_row,
    export_fine_fdtd_selection_csv,
    export_fine_result_csv,
    load_fine_candidate_pool,
    load_fine_geometry_validation,
    select_fine_fdtd_candidates,
)


CANDIDATE_POOL = REPO_ROOT / "outputs" / "apcd_k6_active_learning" / "p1w_dx_fine_candidate_pool_v1.csv"
GEOMETRY_VALIDATION = (
    REPO_ROOT / "outputs" / "apcd_k6_active_learning" / "p1w_dx_fine_candidate_pool_v1_geometry_validation.csv"
)
SCRIPT_PATH = REPO_ROOT / "scripts" / "37_select_and_run_apcd_k6_p1w_dx_fine_candidates.py"
REPORT_PATH = REPO_ROOT / "reports" / "apcd_k6_p1w_dx_fine_fdtd_selection_and_result_note.md"


def _selected_rows() -> list[dict[str, object]]:
    candidates = load_fine_candidate_pool(CANDIDATE_POOL)
    validation = load_fine_geometry_validation(GEOMETRY_VALIDATION)
    return select_fine_fdtd_candidates(candidates, validation)


def test_selection_uses_only_geometry_pass_recommended_candidates() -> None:
    selected = _selected_rows()

    assert {row["geometry_pass"] for row in selected} == {"True"}
    assert {row["recommended_for_fdtd"] for row in selected} == {"True"}


def test_selected_count_and_top2_run_flags() -> None:
    selected = _selected_rows()

    assert 2 <= len(selected) <= 3
    assert [row["will_run_now"] for row in selected] == [True, True, False]
    assert [row["status"] for row in selected] == [
        "selected_for_run",
        "selected_for_run",
        "selected_backup_not_run",
    ]


def test_selection_family_policy_and_unique_ids() -> None:
    selected = _selected_rows()
    ids = [row["candidate_id"] for row in selected]
    families = [row["candidate_family"] for row in selected]

    assert ids == ["fine_p1w_dx_08", "fine_p1w_dx_03", "fine_p1w_dx_p2w_trim_02"]
    assert len(ids) == len(set(ids))
    assert families.count("p1w_dx_fine_leakage_control") >= 2
    assert families.count("p1w_dx_p2w_leakage_trim") <= 1


def test_selection_csv_columns_are_complete(tmp_path: Path) -> None:
    selected = _selected_rows()
    output_csv = export_fine_fdtd_selection_csv(selected, tmp_path / "selection.csv")

    with output_csv.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == FINE_SELECTION_FIELDS
    assert len(loaded) == len(selected)


def test_result_flags_for_top2_are_correct() -> None:
    rows = [
        explicit_result_row(
            candidate_id="fine_p1w_dx_08",
            candidate_family="p1w_dx_fine_leakage_control",
            status="ok",
            target_conversion=0.9371572161476376,
            opposite_spin_leakage=0.12853745775102376,
            conversion_to_leakage_ratio=7.290926960424362,
            pd=0.758772449746472,
            total_transmission=0.5328473369493308,
            t_alpha_star_from_alpha="-0.1499102881279542+0.9301319830907702j",
        ),
        explicit_result_row(
            candidate_id="fine_p1w_dx_03",
            candidate_family="p1w_dx_fine_leakage_control",
            status="ok",
            target_conversion=0.9341050748265248,
            opposite_spin_leakage=0.147484033031872,
            conversion_to_leakage_ratio=6.333601377847639,
            pd=0.727282695506685,
            total_transmission=0.5407945539291984,
            t_alpha_star_from_alpha="-0.1396641194544862+0.9289431891822021j",
        ),
    ]

    assert {row["overall_early_pass"] for row in rows} == {True}
    assert {row["inside_90_100_deg_region"] for row in rows} == {True}
    assert {row["phase_below_doe_p1w_dx_01"] for row in rows} == {True}
    assert {row["priority"] for row in rows} == {"usable_phase_candidate"}


def test_result_csv_columns_are_complete(tmp_path: Path) -> None:
    rows = [
        explicit_result_row(
            candidate_id="fine_p1w_dx_08",
            candidate_family="p1w_dx_fine_leakage_control",
            status="ok",
            target_conversion=0.9371572161476376,
            opposite_spin_leakage=0.12853745775102376,
            conversion_to_leakage_ratio=7.290926960424362,
            pd=0.758772449746472,
            total_transmission=0.5328473369493308,
            t_alpha_star_from_alpha="-0.1499102881279542+0.9301319830907702j",
        )
    ]
    output_csv = export_fine_result_csv(rows, tmp_path / "results.csv")

    with output_csv.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == FINE_RESULT_FIELDS
    assert len(loaded) == 1


def test_cli_select_only_does_not_generate_fsp(tmp_path: Path) -> None:
    selection_csv = tmp_path / "selection.csv"
    selection_summary = tmp_path / "selection.md"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--select-only",
            "--candidate-pool",
            str(CANDIDATE_POOL),
            "--geometry-validation",
            str(GEOMETRY_VALIDATION),
            "--selection-csv",
            str(selection_csv),
            "--selection-summary",
            str(selection_summary),
            "--config-dir",
            str(tmp_path / "configs"),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "status=p1w_dx_fine_selection_only_no_fdtd_no_lumapi_no_fsp_no_training_no_prediction" in completed.stdout
    assert "mode=select_only; no configs written" in completed.stdout
    assert selection_csv.is_file()
    assert selection_summary.is_file()
    assert list(tmp_path.glob("*.fsp")) == []


def test_unit_paths_do_not_call_lumapi_or_fdtd_run() -> None:
    script_text = SCRIPT_PATH.read_text(encoding="utf-8")
    module_text = (REPO_ROOT / "src" / "metasurface" / "apcd_fine_candidate_selection.py").read_text(
        encoding="utf-8"
    )

    assert "import lumapi" not in script_text
    assert "fdtd.run" not in script_text
    assert "fdtd.save" not in script_text
    assert "import lumapi" not in module_text
    assert "fdtd.run" not in module_text
    assert "fdtd.save" not in module_text


def test_report_states_no_full_pool_no_training_no_steering() -> None:
    text = REPORT_PATH.read_text(encoding="utf-8")

    assert "09-P12" in text
    assert "did not run the 20-row fine pool" in text
    assert "did not train a model" in text
    assert "does not make a steering claim" in text
    assert "backup candidate" in text
    assert "not run" in text
