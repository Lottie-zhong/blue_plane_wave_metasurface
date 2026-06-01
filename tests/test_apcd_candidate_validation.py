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
    VALIDATION_FIELDS,
    export_candidate_validation_csv,
    estimate_periodic_image_gap_nm,
    estimate_same_cell_gap_nm,
    read_candidate_pool_csv,
    rectangle_corners_nm,
    validate_candidate_geometry,
    validate_candidate_pool,
)


CANDIDATE_POOL = REPO_ROOT / "outputs" / "apcd_k6_active_learning" / "bounded_candidate_pool_v0.csv"
SCRIPT_PATH = REPO_ROOT / "scripts" / "28_validate_apcd_k6_candidate_pool_geometry.py"
REPORT_PATH = REPO_ROOT / "reports" / "apcd_k6_candidate_pool_geometry_validation_note.md"


def test_rectangle_corners_returns_four_points() -> None:
    corners = rectangle_corners_nm(100, 50, 45, 0, 0)

    assert len(corners) == 4
    assert all(len(point) == 2 for point in corners)


def test_baseline_geometry_gap_validation_passes() -> None:
    baseline = build_baseline_candidate()
    row = validate_candidate_geometry(baseline)

    assert estimate_same_cell_gap_nm(baseline) >= 5
    assert estimate_periodic_image_gap_nm(baseline) >= 5
    assert row["same_cell_gap_pass"] is True
    assert row["periodic_gap_pass"] is True
    assert row["overall_geometry_pass"] is True
    assert row["recommended_for_fdtd"] is True


def test_obvious_overlap_structure_fails_same_cell_gap() -> None:
    candidate = dict(build_baseline_candidate())
    candidate["candidate_id"] = "overlap_case"
    candidate["p2_frac_x"] = candidate["p1_frac_x"]
    candidate["p2_frac_y"] = candidate["p1_frac_y"]
    row = validate_candidate_geometry(candidate)

    assert row["same_cell_min_gap_nm"] == 0
    assert row["same_cell_gap_pass"] is False
    assert row["overall_geometry_pass"] is False


def test_periodic_image_gap_too_small_fails() -> None:
    candidate = dict(build_baseline_candidate())
    candidate["candidate_id"] = "periodic_gap_case"
    candidate["period_x_nm"] = 130
    row = validate_candidate_geometry(candidate)

    assert row["periodic_image_min_gap_nm"] < 5
    assert row["periodic_gap_pass"] is False
    assert row["overall_geometry_pass"] is False


def test_beta_selective_pillar2_geometry_fails() -> None:
    candidate = dict(build_baseline_candidate())
    candidate["candidate_id"] = "beta_selective_case"
    candidate["p2_length_nm"] = 150
    candidate["p2_width_nm"] = 85
    row = validate_candidate_geometry(candidate)

    assert row["beta_selective_geometry_pass"] is False
    assert row["overall_geometry_pass"] is False
    assert "beta-selective" in row["notes"]


def test_rotation_policy_change_fails() -> None:
    candidate = dict(build_baseline_candidate())
    candidate["candidate_id"] = "rotation_changed_case"
    candidate["p1_rotation_deg"] = 70
    row = validate_candidate_geometry(candidate)

    assert row["rotation_policy_pass"] is False
    assert row["overall_geometry_pass"] is False


def test_validation_csv_columns_are_complete(tmp_path: Path) -> None:
    candidates = read_candidate_pool_csv(CANDIDATE_POOL)
    rows = validate_candidate_pool(candidates)
    output_csv = export_candidate_validation_csv(rows, tmp_path / "validation.csv")

    with output_csv.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == VALIDATION_FIELDS
    assert len(loaded) == 52


def test_pool_validation_passes_baseline_and_anchors() -> None:
    candidates = read_candidate_pool_csv(CANDIDATE_POOL)
    rows = validate_candidate_pool(candidates)
    by_id = {row["candidate_id"]: row for row in rows}

    for candidate_id in ["baseline", "p1W_m5", "p2W_p10", "p1L_m10", "p1L_m5", "p1L_p5"]:
        assert by_id[candidate_id]["overall_geometry_pass"] is True
        assert by_id[candidate_id]["recommended_for_fdtd"] is True


def test_script_dry_run_and_non_dry_run_do_not_generate_fsp(tmp_path: Path) -> None:
    dry = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--dry-run",
            "--candidate-pool",
            str(CANDIDATE_POOL),
            "--output-csv",
            str(tmp_path / "dry_validation.csv"),
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
            str(tmp_path / "validation.csv"),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "status=dry_run_geometry_validation_plan_only_no_fdtd_no_lumapi_no_fsp_no_training" in dry.stdout
    assert "status=geometry_validation_only_no_fdtd_no_lumapi_no_fsp_no_training" in completed.stdout
    assert not (tmp_path / "dry_validation.csv").exists()
    assert (tmp_path / "validation.csv").is_file()
    assert list(tmp_path.glob("*.fsp")) == []


def test_script_does_not_call_lumapi_or_fdtd_run() -> None:
    text = SCRIPT_PATH.read_text(encoding="utf-8")
    module_text = (REPO_ROOT / "src" / "metasurface" / "apcd_candidate_validation.py").read_text(
        encoding="utf-8"
    )

    assert "import lumapi" not in text
    assert "fdtd.run" not in text
    assert "fdtd.save" not in text
    assert "import lumapi" not in module_text
    assert "fdtd.run" not in module_text
    assert "fdtd.save" not in module_text


def test_report_states_validation_scope_boundaries() -> None:
    text = REPORT_PATH.read_text(encoding="utf-8")

    assert "09-P3" in text
    assert "geometry / gap / sanity validation" in text
    assert "No FDTD run was performed" in text
    assert "No model was trained" in text
    assert "No `.fsp` file was exported" in text
    assert "not a `+15 deg` steering result" in text
    assert "does not say anything about target-channel phase" in text
