from __future__ import annotations

import csv
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_active_learning import (
    ML_INPUT_COLUMNS,
    ML_OUTPUT_LABEL_COLUMNS,
    build_candidate_parameter_schema,
    build_ml_dataset_schema,
    phase_bin_targets,
    phase_error_to_bins,
    rank_candidates_by_active_learning_score,
    score_candidate_for_phase_bin,
    validate_candidate_bounds,
    wrap_phase_deg,
)


SCRIPT_PATH = REPO_ROOT / "scripts" / "25_define_apcd_k6_active_learning_scaffold.py"
REPORT_PATH = REPO_ROOT / "reports" / "apcd_k6_small_data_active_learning_plan.md"


def test_phase_bin_targets_k6_minus180_convention() -> None:
    assert phase_bin_targets(k=6, convention="[-180,180)") == [0.0, 60.0, 120.0, -180.0, -120.0, -60.0]


def test_phase_wrap_is_correct() -> None:
    assert wrap_phase_deg(180) == -180
    assert wrap_phase_deg(181) == -179
    assert wrap_phase_deg(-181) == 179
    assert wrap_phase_deg(360, convention="[0,360)") == 0
    assert wrap_phase_deg(-60, convention="[0,360)") == 300


def test_phase_error_to_nearest_bin_is_correct() -> None:
    result = phase_error_to_bins(179, phase_bin_targets(k=6))

    assert result["nearest_bin_index"] == 3
    assert result["nearest_target_deg"] == -180.0
    assert result["abs_error_deg"] == 1.0


def test_schema_columns_are_complete() -> None:
    schema = build_ml_dataset_schema()
    columns = [row["column_name"] for row in schema]

    assert columns == ML_INPUT_COLUMNS + ML_OUTPUT_LABEL_COLUMNS
    assert {"t_alpha_star_from_alpha_real", "t_alpha_star_from_alpha_imag", "phase_deg"}.issubset(columns)
    assert "source_result_csv" in columns


def test_candidate_parameter_schema_contains_requested_bounds() -> None:
    rows = {row["parameter_name"]: row for row in build_candidate_parameter_schema()}

    assert rows["p1_length_nm"]["min_value"] == 110.0
    assert rows["p1_length_nm"]["max_value"] == 150.0
    assert rows["p1_width_nm"]["min_value"] == 55.0
    assert rows["p1_width_nm"]["max_value"] == 90.0
    assert rows["p2_length_nm"]["min_value"] == 70.0
    assert rows["p2_length_nm"]["max_value"] == 105.0
    assert rows["p2_width_nm"]["min_value"] == 130.0
    assert rows["p2_width_nm"]["max_value"] == 170.0
    assert rows["internal_dx_nm"]["min_value"] == -40.0
    assert rows["internal_dx_nm"]["max_value"] == 40.0
    assert rows["p1_rotation_deg"]["step_or_sampling"] == "fixed"
    assert rows["p2_rotation_deg"]["step_or_sampling"] == "fixed"


def test_candidate_bounds_validation_passes_and_fails() -> None:
    candidate = {
        row["parameter_name"]: row["baseline_value"]
        for row in build_candidate_parameter_schema()
    }

    assert validate_candidate_bounds(candidate) == []

    invalid = dict(candidate)
    invalid["p1_length_nm"] = 151
    with pytest.raises(ValueError, match="p1_length_nm"):
        validate_candidate_bounds(invalid)
    assert validate_candidate_bounds(invalid, strict=False) == ["p1_length_nm: 151 outside [110, 150]"]

    invalid_rotation = dict(candidate)
    invalid_rotation["p1_rotation_deg"] = 70
    with pytest.raises(ValueError, match="p1_rotation_deg"):
        validate_candidate_bounds(invalid_rotation)


def test_score_prefers_near_phase_high_target_and_low_leakage() -> None:
    good = score_candidate_for_phase_bin(
        phase_deg=61,
        target_phase_deg=60,
        target_conversion=0.9,
        opposite_spin_leakage=0.02,
        conversion_to_leakage_ratio=45,
        PD=0.8,
    )
    bad = score_candidate_for_phase_bin(
        phase_deg=100,
        target_phase_deg=60,
        target_conversion=0.4,
        opposite_spin_leakage=0.4,
        conversion_to_leakage_ratio=1,
        PD=0.1,
    )

    assert good["phase_error_deg"] == 1
    assert good["active_learning_score"] > bad["active_learning_score"]


def test_rank_candidates_selects_per_phase_bin() -> None:
    candidates = [
        {"variant_id": "near_zero", "phase_deg": 2, "target_conversion": 0.8, "opposite_spin_leakage": 0.05},
        {"variant_id": "near_sixty", "phase_deg": 59, "target_conversion": 0.8, "opposite_spin_leakage": 0.05},
        {"variant_id": "low_quality", "phase_deg": 60, "target_conversion": 0.1, "opposite_spin_leakage": 0.9},
    ]

    rows = rank_candidates_by_active_learning_score(candidates, targets=[0.0, 60.0], per_bin=1)

    assert [row["variant_id"] for row in rows] == ["near_zero", "near_sixty"]
    assert [row["phase_bin_index"] for row in rows] == [0, 1]


def test_active_learning_code_does_not_call_lumapi_or_fdtd_run() -> None:
    text = (REPO_ROOT / "src" / "metasurface" / "apcd_active_learning.py").read_text(encoding="utf-8")

    assert "import lumapi" not in text
    assert "fdtd.run" not in text
    assert "fdtd.save" not in text


def test_dry_run_writes_scaffold_outputs_and_no_fsp(tmp_path: Path) -> None:
    output_dir = tmp_path / "active_learning"
    completed = subprocess.run(
        [sys.executable, str(SCRIPT_PATH), "--dry-run", "--output-dir", str(output_dir)],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "status=dry_run_active_learning_scaffold_only_no_training_no_fdtd_no_fsp_not_steering_result" in completed.stdout
    expected = [
        "ml_ready_dataset_schema.csv",
        "candidate_parameter_schema.csv",
        "phase_bin_targets.csv",
        "active_learning_scoring_rules.md",
    ]
    for name in expected:
        assert (output_dir / name).is_file()
    assert list(output_dir.glob("*.fsp")) == []

    with (output_dir / "phase_bin_targets.csv").open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [float(row["phase_target_deg"]) for row in rows] == [0.0, 60.0, 120.0, -180.0, -120.0, -60.0]


def test_report_states_no_training_no_fdtd_no_steering_result() -> None:
    text = REPORT_PATH.read_text(encoding="utf-8")

    assert "09_small_data_active_learning_surrogate" in text
    assert "No model training was performed" in text
    assert "No FDTD run was performed" in text
    assert "No `.fsp` file was generated" in text
    assert "not a `+15 deg` steering result" in text
    assert "Random Forest" in text
    assert "XGBoost / LightGBM" in text
    assert "Gaussian Process" in text
    assert "DenseNet" in text
    assert "cVAE" in text
