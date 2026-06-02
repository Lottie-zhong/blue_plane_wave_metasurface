from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_fine_neighborhood_candidates import (
    EXISTING_REFERENCE_GEOMETRIES,
    FINE_CANDIDATE_FIELDS,
    build_fine_candidate_pool,
    export_fine_candidate_pool,
    load_p1w_dx_reference_results,
    summarize_fine_candidate_pool,
    validate_fine_candidate_bounds,
)


RESULTS_CSV = REPO_ROOT / "outputs" / "apcd_k6_active_learning" / "neighborhood_p1w_dx_fdtd_results_v1.csv"
SCRIPT_PATH = REPO_ROOT / "scripts" / "35_generate_apcd_k6_p1w_dx_fine_candidate_pool.py"
REPORT_PATH = REPO_ROOT / "reports" / "apcd_k6_p1w_dx_fine_candidate_pool_v1_note.md"


def test_load_p1w_dx_reference_results() -> None:
    rows = load_p1w_dx_reference_results(RESULTS_CSV)

    assert set(rows) == {"nhood_p1w_dx_05", "nhood_p1w_dx_02"}
    assert rows["nhood_p1w_dx_05"]["overall_early_pass"] == "True"
    assert rows["nhood_p1w_dx_02"]["inside_90_100_deg_region"] == "True"


def test_fine_candidate_count_is_12_to_20() -> None:
    candidates = build_fine_candidate_pool()

    assert 12 <= len(candidates) <= 20


def test_candidate_ids_are_unique() -> None:
    candidates = build_fine_candidate_pool()
    ids = [row["candidate_id"] for row in candidates]

    assert len(ids) == len(set(ids))


def test_family_distribution_includes_required_family() -> None:
    candidates = build_fine_candidate_pool()
    summary = summarize_fine_candidate_pool(candidates)

    assert summary["family_counts"] == {
        "p1w_dx_fine_leakage_control": 16,
        "p1w_dx_p2w_leakage_trim": 4,
    }


def test_p1_width_and_internal_dx_are_concentrated() -> None:
    candidates = build_fine_candidate_pool()
    p1_widths = {float(row["p1_width_nm"]) for row in candidates}
    internal_dx_values = {float(row["internal_dx_nm"]) for row in candidates}

    assert min(p1_widths) >= 55
    assert max(p1_widths) <= 60
    assert {56.0, 57.0, 58.0, 59.0}.issubset(p1_widths)
    assert min(internal_dx_values) >= -35
    assert max(internal_dx_values) <= -30
    assert {-31.0, -32.0, -33.0, -34.0}.issubset(internal_dx_values)


def test_all_parameters_in_bounds_and_rotations_fixed() -> None:
    candidates = build_fine_candidate_pool()

    for candidate in candidates:
        assert validate_fine_candidate_bounds(candidate, strict=False) == []
        assert candidate["p1_rotation_deg"] == 67.5
        assert candidate["p2_rotation_deg"] == 112.5


def test_no_beta_selective_p2_geometry() -> None:
    candidates = build_fine_candidate_pool()

    for candidate in candidates:
        assert not (candidate["p2_length_nm"] == 150 and candidate["p2_width_nm"] == 85)


def test_no_duplicate_existing_reference_geometries() -> None:
    candidates = build_fine_candidate_pool()
    keys = {
        (
            float(row["p1_length_nm"]),
            float(row["p1_width_nm"]),
            float(row["p2_length_nm"]),
            float(row["p2_width_nm"]),
            float(row["internal_dx_nm"]),
            float(row["internal_dy_nm"]),
        )
        for row in candidates
    }

    assert keys.isdisjoint(EXISTING_REFERENCE_GEOMETRIES)


def test_output_csv_columns_are_complete(tmp_path: Path) -> None:
    candidates = build_fine_candidate_pool()
    output_csv = export_fine_candidate_pool(candidates, tmp_path / "fine_pool.csv")

    with output_csv.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == FINE_CANDIDATE_FIELDS
    assert len(loaded) == len(candidates)
    assert {row["status"] for row in loaded} == {"not_evaluated"}
    assert {row["requires_fdtd"] for row in loaded} == {"true"}
    assert {row["requires_geometry_validation"] for row in loaded} == {"true"}


def test_cli_dry_run_does_not_write_outputs_or_generate_fsp(tmp_path: Path) -> None:
    output_csv = tmp_path / "fine_pool.csv"
    summary_md = tmp_path / "fine_pool.md"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--dry-run",
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

    assert "status=p1w_dx_fine_candidate_pool_only_no_fdtd_no_lumapi_no_fsp_no_training_no_prediction" in completed.stdout
    assert "candidate_count=20" in completed.stdout
    assert "dry_run=true; no output files written" in completed.stdout
    assert not output_csv.exists()
    assert not summary_md.exists()
    assert list(tmp_path.glob("*.fsp")) == []


def test_script_does_not_call_lumapi_or_fdtd_run() -> None:
    script_text = SCRIPT_PATH.read_text(encoding="utf-8")
    module_text = (REPO_ROOT / "src" / "metasurface" / "apcd_fine_neighborhood_candidates.py").read_text(
        encoding="utf-8"
    )

    assert "import lumapi" not in script_text
    assert "fdtd.run" not in script_text
    assert "fdtd.save" not in script_text
    assert "import lumapi" not in module_text
    assert "fdtd.run" not in module_text
    assert "fdtd.save" not in module_text


def test_report_states_candidate_pool_only_boundaries() -> None:
    text = REPORT_PATH.read_text(encoding="utf-8")

    assert "09-P10" in text
    assert "only generates a p1w_dx fine neighborhood candidate pool" in text
    assert "No FDTD run" in text
    assert "no lumapi call" in text
    assert "no model was trained" in text
    assert "no `.fsp` file was exported" in text
    assert "candidate pool only" in text
    assert "not a `+15 deg` steering result" in text
