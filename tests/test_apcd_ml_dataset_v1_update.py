from __future__ import annotations

import csv
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_phase_gap_candidates import (
    build_geometry_lookup,
    build_ml_dataset_v1,
    overall_early_pass,
    parse_complex_text,
    read_csv_fieldnames,
    read_csv_rows,
    write_csv_rows,
)


V0_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v0.csv"
SUMMARY_PATHS = [
    REPO_ROOT / "outputs/apcd_k6_active_learning/first_fdtd_batch_v0_results_summary.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/neighborhood_p1w_dx_fdtd_results_v1.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/p1w_dx_fine_fdtd_results_v1.csv",
]
POOL_PATHS = [
    REPO_ROOT / "outputs/apcd_k6_active_learning/bounded_candidate_pool_v0.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/neighborhood_candidate_pool_v1.csv",
    REPO_ROOT / "outputs/apcd_k6_active_learning/p1w_dx_fine_candidate_pool_v1.csv",
]
OUTPUT_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v1.csv"
SCRIPT_PATH = REPO_ROOT / "scripts/38_update_apcd_k6_ml_dataset_v1.py"


def _dataset_rows() -> list[dict[str, object]]:
    return build_ml_dataset_v1(
        read_csv_rows(V0_CSV),
        SUMMARY_PATHS,
        build_geometry_lookup(POOL_PATHS),
        read_csv_fieldnames(V0_CSV),
    )


def test_dataset_v1_sample_count_and_expected_ids() -> None:
    rows = _dataset_rows()
    ids = {str(row["variant_id"]) for row in rows}

    assert len(rows) == 17
    assert {"fine_p1w_dx_08", "fine_p1w_dx_03"}.issubset(ids)
    assert {"doe_p1w_p2w_02", "doe_p1w_dx_01", "doe_lhs_like_01"}.issubset(ids)


def test_dataset_v1_complex_real_imag_are_preserved() -> None:
    row = next(row for row in _dataset_rows() if row["variant_id"] == "fine_p1w_dx_08")
    value = parse_complex_text("-0.1499102881279542+0.9301319830907702j")

    assert float(row["t_alpha_star_from_alpha_real"]) == value.real
    assert float(row["t_alpha_star_from_alpha_imag"]) == value.imag
    assert float(row["t_alpha_star_from_alpha_abs"]) == abs(value)


def test_dataset_v1_geometry_and_early_pass_stats() -> None:
    rows = _dataset_rows()
    fine = next(row for row in rows if row["variant_id"] == "fine_p1w_dx_03")
    early_count = sum(1 for row in rows if str(row["overall_early_pass"]) == "True")

    assert fine["p1_width_nm"] == "56"
    assert fine["internal_dx_nm"] == "-33"
    assert early_count == 12
    assert overall_early_pass(0.9341050748265248, 0.147484033031872, 6.333601377847639)


def test_dataset_v1_output_columns_align_schema(tmp_path: Path) -> None:
    rows = _dataset_rows()
    columns = read_csv_fieldnames(V0_CSV)
    output = write_csv_rows(rows, tmp_path / "dataset.csv", columns)

    with output.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == columns
    assert len(loaded) == 17


def test_dataset_v1_script_has_no_lumapi_fdtd_run_or_fsp_generation() -> None:
    text = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "import lumapi" not in text
    assert "fdtd.run" not in text
    assert "fdtd.save" not in text
    assert ".fsp" not in text
