from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def load_script(name: str):
    path = REPO_ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[path.stem] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def p164():
    return load_script("manual_p164_build_zero_stage_database.py")


@pytest.fixture(scope="module")
def p165():
    return load_script("manual_p165_generate_zero_cliff_recovery_candidates.py")


@pytest.fixture(scope="module")
def p166():
    return load_script("manual_p166_summarize_zero_cliff_recovery.py")


def test_p164_phase_bin_and_zero_open_logic(p164, tmp_path) -> None:
    result_csv = tmp_path / "results.csv"
    raw = {
        "phase_deg": "20.13",
        "target_conversion": "0.61",
        "opposite_spin_leakage": "0.10",
        "conversion_to_leakage_ratio": "6.2",
        "PD": "0.5",
        "status": "complete",
    }

    row = p164.summarize_result_row("cpk_zero_example", "unit", result_csv, raw)

    assert row["phase_deg"] == pytest.approx(20.13)
    assert row["nearest_bin"] == 0
    assert row["phase_error_deg"] == pytest.approx(20.13)
    assert row["early_pass"] is True
    assert row["opens_0"] is True


def test_p164_complex_phase_and_selectivity_failure(p164, tmp_path) -> None:
    result_csv = tmp_path / "results.csv"
    raw = {
        "t_alpha_star_from_alpha": "0.5+0.8660254037844386j",
        "target_conversion": "0.61",
        "opposite_spin_leakage": "0.10",
        "conversion_to_leakage_ratio": "4.63",
        "PD": "0.5",
    }

    row = p164.summarize_result_row("cpk_zero_example", "unit", result_csv, raw)

    assert row["phase_deg"] == pytest.approx(60.0)
    assert row["nearest_bin"] == 60
    assert row["early_pass"] is False
    assert row["opens_0"] is False


def test_p165_candidate_specs_include_requested_groups(p165) -> None:
    no_notch = p165.build_candidate_specs(notch_supported=False)
    with_notch = p165.build_candidate_specs(notch_supported=True)

    assert len(no_notch) == 9
    assert len(with_notch) == 12
    assert [spec.height_nm for spec in no_notch[:6]] == [232.49, 232.48, 232.47, 232.46, 232.45, 232.44]
    assert "cpk_zero_l60_lhs_h232p49_p1geom120x58_01" in {spec.candidate_id for spec in with_notch}
    assert "cpk_zero_l60_lhs_h232p4_p1geom121x58_01" in {spec.candidate_id for spec in with_notch}
    assert any(spec.p1_shape == "notched_rectangle" for spec in with_notch)


def test_p165_generated_config_keeps_yaml_only_stage_boundary(p165) -> None:
    spec = p165.CandidateSpec(
        candidate_id="cpk_zero_unit",
        group="A",
        family="ultra_fine_height_scan",
        height_nm=232.49,
        p1_length_nm=120,
        p1_width_nm=58,
        rationale="unit",
    )
    anchor = {
        "project": {"name": "blue_plane_wave_metasurface", "stage": "old"},
        "geometry": {
            "period_x_nm": 340,
            "period_y_nm": 340,
            "height_nm": 300,
            "nanopillar_1": {"length_nm": 115, "width_nm": 55, "rotation_deg": 67.5},
            "nanopillar_2": {"length_nm": 75, "width_nm": 135, "rotation_deg": 112.5},
        },
        "output": {"result_dir": "old"},
    }

    config = p165.build_candidate_config(anchor, spec)

    assert config["project"]["stage"] == "09_p165_zero_cliff_recovery_candidate_yaml_only"
    assert config["geometry"]["height_nm"] == pytest.approx(232.49)
    assert config["geometry"]["nanopillar_1"]["length_nm"] == 120
    assert config["geometry"]["nanopillar_1"]["width_nm"] == 58
    assert config["boundary"]["no_fdtd_run_by_generator"] is True
    assert "cpk_zero_unit" in config["output"]["result_dir"]


def test_p166_missing_results_do_not_crash(p166, tmp_path) -> None:
    plan = [
        {
            "candidate_id": "cpk_zero_missing",
            "group": "A",
            "family": "ultra_fine_height_scan",
        }
    ]

    rows = p166.summarize_plan_results(plan, tmp_path)
    decisions = p166.build_decision_rows(rows)

    assert rows[0]["result_status"] == "missing_result"
    assert rows[0]["early_pass"] is False
    assert rows[0]["opens_0"] is False
    assert any(row["decision_key"] == "next_action" for row in decisions)
