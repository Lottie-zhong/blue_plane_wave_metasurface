from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_candidate_pool import build_baseline_candidate
from metasurface.apcd_candidate_validation import (
    FINE_VALIDATION_FIELDS,
    export_fine_candidate_validation_csv,
    read_candidate_pool_csv,
    summarize_fine_validation,
    validate_candidate_geometry,
    validate_fine_candidate_pool,
)


CANDIDATE_POOL = REPO_ROOT / "outputs" / "apcd_k6_active_learning" / "p1w_dx_fine_candidate_pool_v1.csv"
SCRIPT_PATH = REPO_ROOT / "scripts" / "36_validate_apcd_k6_p1w_dx_fine_candidate_pool_geometry.py"
REPORT_PATH = REPO_ROOT / "reports" / "apcd_k6_p1w_dx_fine_candidate_pool_geometry_validation_note.md"


def test_can_read_fine_candidate_pool_v1() -> None:
    candidates = read_candidate_pool_csv(CANDIDATE_POOL)

    assert len(candidates) == 20
    assert candidates[0]["candidate_id"] == "fine_p1w_dx_01"


def test_fine_validation_csv_columns_are_complete(tmp_path: Path) -> None:
    candidates = read_candidate_pool_csv(CANDIDATE_POOL)
    rows = validate_fine_candidate_pool(candidates)
    output_csv = export_fine_candidate_validation_csv(rows, tmp_path / "validation.csv")

    with output_csv.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == FINE_VALIDATION_FIELDS
    assert len(loaded) == 20
    assert "duplicate_geometry_pass" in loaded[0]


def test_fine_family_distribution_is_correct() -> None:
    candidates = read_candidate_pool_csv(CANDIDATE_POOL)
    rows = validate_fine_candidate_pool(candidates)
    summary = summarize_fine_validation(rows)

    assert summary["total"] == 20
    assert summary["family_counts"] == {
        "p1w_dx_fine_leakage_control": {"total": 16, "pass": 16, "fail": 0, "recommended": 16},
        "p1w_dx_p2w_leakage_trim": {"total": 4, "pass": 4, "fail": 0, "recommended": 4},
    }


def test_all_fine_parameters_in_bounds_and_rotations_fixed() -> None:
    candidates = read_candidate_pool_csv(CANDIDATE_POOL)
    rows = validate_fine_candidate_pool(candidates)

    assert {row["bounds_pass"] for row in rows} == {True}
    assert {row["rotation_policy_pass"] for row in rows} == {True}
    assert {row["duplicate_geometry_pass"] for row in rows} == {True}
    assert {row["overall_geometry_pass"] for row in rows} == {True}
    assert {row["recommended_for_fdtd"] for row in rows} == {True}


def test_beta_selective_pillar2_geometry_fails() -> None:
    candidate = dict(build_baseline_candidate())
    candidate["candidate_id"] = "beta_selective_case"
    candidate["p2_length_nm"] = 150
    candidate["p2_width_nm"] = 85
    row = validate_candidate_geometry(candidate)

    assert row["beta_selective_geometry_pass"] is False
    assert row["overall_geometry_pass"] is False


def test_obvious_overlap_structure_fails() -> None:
    candidate = dict(build_baseline_candidate())
    candidate["candidate_id"] = "overlap_case"
    candidate["p2_frac_x"] = candidate["p1_frac_x"]
    candidate["p2_frac_y"] = candidate["p1_frac_y"]
    row = validate_candidate_geometry(candidate)

    assert row["same_cell_gap_pass"] is False
    assert row["overall_geometry_pass"] is False


def test_periodic_gap_too_small_fails() -> None:
    candidate = dict(build_baseline_candidate())
    candidate["candidate_id"] = "periodic_gap_case"
    candidate["period_x_nm"] = 130
    row = validate_candidate_geometry(candidate)

    assert row["periodic_gap_pass"] is False
    assert row["overall_geometry_pass"] is False


def test_duplicate_existing_candidate_fails() -> None:
    candidate = dict(build_baseline_candidate())
    candidate.update(
        {
            "candidate_id": "duplicate_doe_p1w_dx_01",
            "candidate_family": "p1w_dx_fine_leakage_control",
            "p1_width_nm": 60,
            "internal_dx_nm": -30,
        }
    )
    rows = validate_fine_candidate_pool([candidate])

    assert rows[0]["duplicate_geometry_pass"] is False
    assert rows[0]["overall_geometry_pass"] is False
    assert rows[0]["recommended_for_fdtd"] is False
    assert "duplicates existing" in rows[0]["notes"]


def test_cli_dry_run_and_non_dry_run_do_not_generate_fsp(tmp_path: Path) -> None:
    dry_output = tmp_path / "dry_validation.csv"
    output = tmp_path / "validation.csv"
    dry = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--dry-run",
            "--candidate-pool",
            str(CANDIDATE_POOL),
            "--output-csv",
            str(dry_output),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--candidate-pool",
            str(CANDIDATE_POOL),
            "--output-csv",
            str(output),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "status=dry_run_p1w_dx_fine_geometry_validation_only_no_fdtd_no_lumapi_no_fsp_no_training" in dry.stdout
    assert "status=p1w_dx_fine_geometry_validation_only_no_fdtd_no_lumapi_no_fsp_no_training" in completed.stdout
    assert "candidate_count=20" in completed.stdout
    assert not dry_output.exists()
    assert output.is_file()
    assert list(tmp_path.glob("*.fsp")) == []


def test_script_does_not_call_lumapi_or_fdtd_run() -> None:
    script_text = SCRIPT_PATH.read_text(encoding="utf-8")
    module_text = (REPO_ROOT / "src" / "metasurface" / "apcd_candidate_validation.py").read_text(
        encoding="utf-8"
    )

    assert "import lumapi" not in script_text
    assert "fdtd.run" not in script_text
    assert "fdtd.save" not in script_text
    assert "import lumapi" not in module_text
    assert "fdtd.run" not in module_text
    assert "fdtd.save" not in module_text


def test_report_states_geometry_only_boundaries() -> None:
    text = REPORT_PATH.read_text(encoding="utf-8")

    assert "09-P11" in text
    assert "geometry / gap / sanity validation" in text
    assert "No FDTD run" in text
    assert "no lumapi call" in text
    assert "no model was trained" in text
    assert "no `.fsp` file was exported" in text
    assert "geometry only" in text
    assert "not a `+15 deg` steering result" in text
