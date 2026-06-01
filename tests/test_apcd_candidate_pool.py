from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_candidate_pool import (
    ANCHOR_VARIANT_IDS,
    CANDIDATE_POOL_FIELDS,
    build_anchor_candidates_from_v0,
    build_baseline_candidate,
    build_candidate_pool,
    summarize_candidate_pool,
    validate_candidate_bounds,
)


DATASET_V0 = REPO_ROOT / "outputs" / "apcd_k6_active_learning" / "ml_ready_dataset_v0.csv"
SCRIPT_PATH = REPO_ROOT / "scripts" / "27_generate_apcd_k6_bounded_candidate_pool.py"
REPORT_PATH = REPO_ROOT / "reports" / "apcd_k6_bounded_candidate_pool_v0_note.md"


def test_candidate_pool_count_is_30_to_60() -> None:
    candidates = build_candidate_pool(DATASET_V0)

    assert 30 <= len(candidates) <= 60


def test_candidate_pool_contains_baseline_and_anchors() -> None:
    candidates = build_candidate_pool(DATASET_V0)
    ids = {row["candidate_id"] for row in candidates}

    assert "baseline" in ids
    for anchor in ANCHOR_VARIANT_IDS:
        assert anchor in ids


def test_candidate_ids_are_unique() -> None:
    candidates = build_candidate_pool(DATASET_V0)
    ids = [row["candidate_id"] for row in candidates]

    assert len(ids) == len(set(ids))


def test_all_candidates_are_within_bounds() -> None:
    candidates = build_candidate_pool(DATASET_V0)

    for candidate in candidates:
        assert validate_candidate_bounds(candidate) == []


def test_rotations_are_fixed() -> None:
    candidates = build_candidate_pool(DATASET_V0)

    assert {row["p1_rotation_deg"] for row in candidates} == {67.5}
    assert {row["p2_rotation_deg"] for row in candidates} == {112.5}


def test_no_beta_selective_pillar2_geometry() -> None:
    candidates = build_candidate_pool(DATASET_V0)

    for row in candidates:
        assert not (float(row["p2_length_nm"]) == 150.0 and float(row["p2_width_nm"]) == 85.0)


def test_anchor_candidates_are_read_from_v0() -> None:
    anchors = build_anchor_candidates_from_v0(DATASET_V0)
    by_id = {row["candidate_id"]: row for row in anchors}

    assert set(by_id) == set(ANCHOR_VARIANT_IDS)
    assert by_id["p1W_m5"]["p1_width_nm"] == 65
    assert by_id["p2W_p10"]["p2_width_nm"] == 160
    assert by_id["p1L_m10"]["p1_length_nm"] == 120


def test_baseline_candidate_has_expected_values() -> None:
    baseline = build_baseline_candidate()

    assert baseline["candidate_id"] == "baseline"
    assert baseline["p1_length_nm"] == 130
    assert baseline["p1_width_nm"] == 70
    assert baseline["p2_length_nm"] == 85
    assert baseline["p2_width_nm"] == 150
    assert baseline["requires_fdtd"] == "true"
    assert baseline["status"] == "not_evaluated"
    assert baseline["predicted_phase_bin"] == ""


def test_summary_reports_family_distribution_and_bounds() -> None:
    candidates = build_candidate_pool(DATASET_V0)
    summary = summarize_candidate_pool(candidates)

    assert summary["candidate_count"] == len(candidates)
    assert summary["bounds_ok"] is True
    assert summary["unique_candidate_ids"] is True
    assert set(["baseline", *ANCHOR_VARIANT_IDS]).issubset(set(summary["anchors_present"]))
    assert "p1w_p2w_combo" in summary["family_counts"]
    assert "lhs_like_mixed_combo" in summary["family_counts"]


def test_output_csv_columns_are_complete(tmp_path: Path) -> None:
    output_csv = tmp_path / "bounded_candidate_pool_v0.csv"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--dry-run",
            "--dataset-v0",
            str(DATASET_V0),
            "--output-csv",
            str(output_csv),
            "--summary-md",
            str(tmp_path / "summary.md"),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "status=dry_run_candidate_pool_only_no_fdtd_no_lumapi_no_fsp_no_training_no_prediction" in completed.stdout
    with output_csv.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    assert reader.fieldnames == CANDIDATE_POOL_FIELDS
    assert 30 <= len(rows) <= 60
    assert list(tmp_path.glob("*.fsp")) == []


def test_dry_run_script_does_not_call_lumapi_or_fdtd_run() -> None:
    text = SCRIPT_PATH.read_text(encoding="utf-8")
    module_text = (REPO_ROOT / "src" / "metasurface" / "apcd_candidate_pool.py").read_text(encoding="utf-8")

    assert "import lumapi" not in text
    assert "fdtd.run" not in text
    assert "fdtd.save" not in text
    assert "import lumapi" not in module_text
    assert "fdtd.run" not in module_text
    assert "fdtd.save" not in module_text


def test_report_states_scope_boundaries() -> None:
    text = REPORT_PATH.read_text(encoding="utf-8")

    assert "09-P2" in text
    assert "bounded candidate pool / DOE scaffold" in text
    assert "No FDTD run was performed" in text
    assert "No model was trained" in text
    assert "not a `+15 deg` steering result" in text
    assert "No surrogate prediction was generated" in text
