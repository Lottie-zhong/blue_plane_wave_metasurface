from __future__ import annotations

import csv
import importlib.util
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "24_summarize_apcd_k6_candidate_subset.py"


def _load_script_module():
    spec = importlib.util.spec_from_file_location("candidate_subset_summary", SCRIPT_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load candidate subset summary script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_result(path: Path, variant: str, t_alpha: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "target_conversion",
        "opposite_spin_leakage",
        "conversion_to_leakage_ratio",
        "PD",
        "total_transmission",
        "t_alpha_star_from_alpha",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerow(
            {
                "target_conversion": "0.9",
                "opposite_spin_leakage": "0.1",
                "conversion_to_leakage_ratio": "9",
                "PD": "0.8",
                "total_transmission": "0.5",
                "t_alpha_star_from_alpha": t_alpha,
            }
        )


def test_parse_complex_and_phase_deg() -> None:
    module = _load_script_module()
    value = module.parse_complex_text("-0.4347133268511511+0.8684071668544278j")

    assert abs(value.real + 0.4347133268511511) < 1e-15
    assert abs(module.phase_deg(value) - 116.59195034600026) < 1e-12


def test_phase_shift_wrap() -> None:
    module = _load_script_module()

    assert module.wrap_phase_shift_deg(-179, 179) == 2
    assert module.wrap_phase_shift_deg(179, -179) == -2


def test_missing_results_does_not_crash(tmp_path: Path) -> None:
    module = _load_script_module()
    row = module.summarize_variant(
        variant_id="missing",
        changed_parameter="pillar_1_length_nm",
        delta_nm=5,
        results_root=tmp_path,
    )

    assert row["variant_id"] == "missing"
    assert str(row["notes"]).startswith("missing results.csv")
    assert row["overall_early_pass"] == ""


def test_summary_csv_columns_are_complete(tmp_path: Path) -> None:
    module = _load_script_module()
    results_root = tmp_path / "results"
    _write_result(results_root / "baseline" / "results.csv", "baseline", "-0.35675399032712+0.9142415295978351j")
    rows = module.build_subset_summary_rows(results_root)
    output_csv = module.write_summary_csv(rows, tmp_path / "summary.csv")

    with output_csv.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded = list(reader)

    assert reader.fieldnames == module.SUMMARY_FIELDS
    assert len(loaded) == 7
    assert loaded[0]["variant_id"] == "p1L_m10"
    assert loaded[-2]["variant_id"] == "p1W_m5"
    assert loaded[-1]["variant_id"] == "p1W_p5"


def test_report_and_csv_writer_outputs_files(tmp_path: Path) -> None:
    module = _load_script_module()
    results_root = tmp_path / "results"
    _write_result(results_root / "baseline" / "results.csv", "baseline", "-0.35675399032712+0.9142415295978351j")
    rows = module.build_subset_summary_rows(results_root)
    report = module.write_length_width_trend_report(rows, tmp_path / "report.md")

    text = report.read_text(encoding="utf-8")
    assert "No new FDTD run was performed" in text
    assert "not proof of `+15 deg` steering" in text
    assert "P1 Width Trend" in text
    assert "Do not launch all 13 candidates as a batch" in text


def test_p1_width_rows_enter_summary_and_phase_shift_is_correct(tmp_path: Path) -> None:
    module = _load_script_module()
    results_root = tmp_path / "results"
    _write_result(results_root / "p1W_m5" / "results.csv", "p1W_m5", "-0.2561991699338597+0.9353368486510016j")
    _write_result(results_root / "p1W_p5" / "results.csv", "p1W_p5", "-0.4576269847268101+0.8578247085066996j")

    rows = module.build_subset_summary_rows(results_root)
    p1w_m5 = next(row for row in rows if row["variant_id"] == "p1W_m5")
    p1w_p5 = next(row for row in rows if row["variant_id"] == "p1W_p5")

    assert p1w_m5["changed_parameter"] == "pillar_1_width_nm"
    assert abs(p1w_m5["phase_shift_vs_baseline_deg"] - (-5.998417282378824)) < 1e-12
    assert abs(p1w_p5["phase_shift_vs_baseline_deg"] - 6.762100361623993) < 1e-12


def test_script_does_not_call_lumapi_or_fdtd_run() -> None:
    text = SCRIPT_PATH.read_text(encoding="utf-8")

    assert "lumapi" not in text
    assert "fdtd.run" not in text
    assert ".fsp" not in text
