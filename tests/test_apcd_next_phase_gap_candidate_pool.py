from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_next_phase_gap_candidates import (
    NEXT_PHASE_GAP_CANDIDATE_FIELDS,
    build_next_phase_gap_candidate_pool,
    summarize_next_candidate_pool,
    write_csv_rows,
)


POOL_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/next_phase_gap_candidate_pool_v2.csv"
SUMMARY_MD = REPO_ROOT / "outputs/apcd_k6_active_learning/next_phase_gap_candidate_pool_v2_summary.md"
MODULE_PATH = REPO_ROOT / "src/metasurface/apcd_next_phase_gap_candidates.py"
SCRIPT_48 = REPO_ROOT / "scripts/48_generate_apcd_k6_next_phase_gap_candidate_pool.py"


def _pool() -> list[dict[str, object]]:
    return build_next_phase_gap_candidate_pool()


def test_candidate_count_targets_and_unique_ids() -> None:
    rows = _pool()
    ids = [row["candidate_id"] for row in rows]
    summary = summarize_next_candidate_pool(rows)
    target_counts = {float(key): value for key, value in summary["target_bin_counts"].items()}

    assert 36 <= len(rows) <= 48
    assert len(ids) == len(set(ids))
    for target in (0.0, -60.0, -120.0, -180.0):
        assert target_counts[target] >= 4


def test_candidate_columns_and_flags(tmp_path: Path) -> None:
    output = write_csv_rows(_pool(), tmp_path / "pool.csv", NEXT_PHASE_GAP_CANDIDATE_FIELDS)
    with output.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == NEXT_PHASE_GAP_CANDIDATE_FIELDS
    assert len(loaded) == len(_pool())
    assert {row["status"] for row in loaded} == {"not_evaluated"}
    assert {row["requires_fdtd"] for row in loaded} == {"true"}
    assert {row["requires_geometry_validation"] for row in loaded} == {"true"}


def test_all_candidates_obey_bounds_and_do_not_use_beta_selective_geometry() -> None:
    for row in _pool():
        assert 110 <= float(row["p1_length_nm"]) <= 150
        assert 55 <= float(row["p1_width_nm"]) <= 90
        assert 70 <= float(row["p2_length_nm"]) <= 105
        assert 130 <= float(row["p2_width_nm"]) <= 170
        assert -40 <= float(row["internal_dx_nm"]) <= 40
        assert -40 <= float(row["internal_dy_nm"]) <= 40
        assert 0 <= float(row["p1_rotation_deg"]) < 180
        assert 0 <= float(row["p2_rotation_deg"]) < 180
        assert not (float(row["p2_length_nm"]) == 150.0 and float(row["p2_width_nm"]) == 85.0)


def test_generated_pool_output_has_expected_count() -> None:
    with POOL_CSV.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    assert len(rows) == len(_pool())
    assert SUMMARY_MD.exists()


def test_dry_run_does_not_generate_fsp(tmp_path: Path) -> None:
    completed = subprocess.run(
        [sys.executable, str(SCRIPT_48), "--dry-run", "--output", str(tmp_path / "pool.csv")],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "no_fdtd" in completed.stdout
    assert "no_lumapi" in completed.stdout
    assert "no_fsp" in completed.stdout
    assert list(tmp_path.rglob("*.fsp")) == []


def test_module_and_script_do_not_call_lumapi_or_fdtd_run() -> None:
    combined = "\n".join([MODULE_PATH.read_text(encoding="utf-8"), SCRIPT_48.read_text(encoding="utf-8")])

    assert "import lumapi" not in combined
    assert "fdtd.run" not in combined
    assert "fdtd.save" not in combined
