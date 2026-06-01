from __future__ import annotations

import csv
import importlib.util
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "26_collect_apcd_k6_ml_dataset_v0.py"
SCHEMA_CSV = REPO_ROOT / "outputs" / "apcd_k6_active_learning" / "ml_ready_dataset_schema.csv"
CONFIG_INDEX_CSV = (
    REPO_ROOT
    / "outputs"
    / "apcd_k6_metagrating_633nm"
    / "phase_state_candidate_config_index.csv"
)
RESULTS_ROOT = REPO_ROOT / "outputs" / "apcd_k6_metagrating_633nm" / "phase_state_candidates"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("apcd_ml_dataset_collection", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load APCD ML dataset collection script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _schema_columns() -> list[str]:
    with SCHEMA_CSV.open("r", newline="", encoding="utf-8") as handle:
        return [row["column_name"] for row in csv.DictReader(handle)]


def test_parse_complex_t_alpha_star_from_alpha() -> None:
    module = _load_script_module()
    value = module.parse_complex_text("-0.35675399032712+0.9142415295978351j")

    assert abs(value.real + 0.35675399032712) < 1e-15
    assert abs(value.imag - 0.9142415295978351) < 1e-15


def test_candidate_config_geometry_is_read_from_yaml() -> None:
    module = _load_script_module()
    index_rows = module.read_candidate_config_index(CONFIG_INDEX_CSV)
    baseline = next(row for row in index_rows if row["variant_id"] == "baseline")
    row = module.candidate_input_row(baseline)

    assert row["p1_length_nm"] == 130
    assert row["p1_width_nm"] == 70
    assert row["p2_length_nm"] == 85
    assert row["p2_width_nm"] == 150
    assert row["p1_frac_x"] == 0.75
    assert row["p2_frac_y"] == 0.25
    assert row["p1_rotation_deg"] == 67.5
    assert row["p2_rotation_deg"] == 112.5
    assert row["material"] == "c-Si"
    assert row["substrate"] == "Al2O3"


def test_phase_deg_computation_is_correct() -> None:
    module = _load_script_module()
    value = module.parse_complex_text("-0.35675399032712+0.9142415295978351j")

    assert abs(module.phase_deg(value) - 111.31665091018952) < 1e-12


def test_phase_shift_wrap_is_correct() -> None:
    module = _load_script_module()

    assert module.phase_shift_vs_baseline_deg(-179, 179) == 2
    assert module.phase_shift_vs_baseline_deg(179, -179) == -2


def test_early_pass_computation_is_correct() -> None:
    module = _load_script_module()

    assert module.overall_early_pass(
        target_conversion=0.5,
        opposite_spin_leakage=0.2,
        conversion_to_leakage_ratio=6,
    )
    assert not module.overall_early_pass(
        target_conversion=0.49,
        opposite_spin_leakage=0.2,
        conversion_to_leakage_ratio=6,
    )
    assert not module.overall_early_pass(
        target_conversion=0.8,
        opposite_spin_leakage=0.21,
        conversion_to_leakage_ratio=6,
    )
    assert not module.overall_early_pass(
        target_conversion=0.8,
        opposite_spin_leakage=0.1,
        conversion_to_leakage_ratio=5.99,
    )


def test_missing_results_do_not_crash(tmp_path: Path) -> None:
    module = _load_script_module()
    rows, included, missing, columns = module.collect_ml_dataset_v0(
        schema_csv=SCHEMA_CSV,
        config_index_csv=CONFIG_INDEX_CSV,
        results_root=tmp_path / "missing_results",
    )

    assert rows == []
    assert included == []
    assert "baseline" in missing
    assert columns == _schema_columns()


def test_dataset_columns_align_to_schema(tmp_path: Path) -> None:
    module = _load_script_module()
    dataset_path, report_path, rows, included, missing = module.write_outputs(
        schema_csv=SCHEMA_CSV,
        config_index_csv=CONFIG_INDEX_CSV,
        results_root=RESULTS_ROOT,
        output_csv=tmp_path / "ml_ready_dataset_v0.csv",
        collection_report=tmp_path / "collection_report.md",
    )

    with dataset_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == _schema_columns()
    assert len(loaded) == len(rows)
    assert included == [
        "baseline",
        "p1L_m10",
        "p1L_m5",
        "p1L_p5",
        "p1L_p10",
        "p1W_m5",
        "p1W_p5",
        "p2W_m10",
        "p2W_m5",
        "p2W_p10",
    ]
    assert missing == ["p2L_m5", "p2L_p5", "p2W_p5"]
    assert report_path.is_file()


def test_baseline_dataset_row_values_are_correct() -> None:
    module = _load_script_module()
    index_rows = module.read_candidate_config_index(CONFIG_INDEX_CSV)
    baseline = next(row for row in index_rows if row["variant_id"] == "baseline")
    row = module.build_dataset_row(baseline, RESULTS_ROOT / "baseline" / "results.csv")

    assert row["variant_id"] == "baseline"
    assert abs(row["t_alpha_star_from_alpha_real"] + 0.35675399032712) < 1e-15
    assert abs(row["t_alpha_star_from_alpha_imag"] - 0.9142415295978351) < 1e-15
    assert abs(row["phase_deg"] - 111.31665091018952) < 1e-12
    assert abs(row["phase_shift_vs_baseline_deg"]) < 1e-12
    assert row["overall_early_pass"] is True
    assert row["source_result_csv"] == "outputs/apcd_k6_metagrating_633nm/phase_state_candidates/baseline/results.csv"


def test_script_does_not_call_lumapi_or_fdtd_run() -> None:
    text = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "import lumapi" not in text
    assert "fdtd.run" not in text
    assert "fdtd.save" not in text


def test_cli_writes_dataset_report_and_no_fsp(tmp_path: Path) -> None:
    dataset_path = tmp_path / "ml_ready_dataset_v0.csv"
    report_path = tmp_path / "ml_ready_dataset_v0_collection_report.md"
    completed = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--schema-csv",
            str(SCHEMA_CSV),
            "--config-index",
            str(CONFIG_INDEX_CSV),
            "--results-root",
            str(RESULTS_ROOT),
            "--output-csv",
            str(dataset_path),
            "--collection-report",
            str(report_path),
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "status=collection_only_no_fdtd_no_lumapi_no_fsp_no_training_no_new_candidates" in completed.stdout
    assert "rows=10" in completed.stdout
    assert dataset_path.is_file()
    assert report_path.is_file()
    assert list(tmp_path.glob("*.fsp")) == []
