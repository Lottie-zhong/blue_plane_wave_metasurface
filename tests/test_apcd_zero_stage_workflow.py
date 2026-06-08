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


@pytest.fixture(scope="module")
def p169():
    return load_script("manual_p169_generate_integer_zero_recovery_candidates.py")


@pytest.fixture(scope="module")
def p170():
    return load_script("manual_p170_summarize_integer_zero_recovery.py")


@pytest.fixture(scope="module")
def p173():
    return load_script("manual_p173_generate_fixed_h233_resonance_phase_candidates.py")


@pytest.fixture(scope="module")
def p174():
    return load_script("manual_p174_summarize_fixed_h233_resonance_phase.py")


@pytest.fixture(scope="module")
def p176():
    return load_script("manual_p176_generate_h232_zero_coupled_recovery_candidates.py")


@pytest.fixture(scope="module")
def p177():
    return load_script("manual_p177_summarize_h232_zero_coupled_recovery.py")


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


def test_p169_candidate_specs_are_integer_and_include_requested_names(p169) -> None:
    no_notch = p169.build_candidate_specs(notch_supported=False)
    with_notch = p169.build_candidate_specs(notch_supported=True)
    requested = {
        "cpk_zero_l60_lhs_h232_p1geom121x58_01",
        "cpk_zero_l60_lhs_h232_p1geom120x57_01",
        "cpk_zero_l60_lhs_h232_p1geom119x58_01",
        "cpk_zero_l60_lhs_h232_p1geom120x59_01",
        "cpk_zero_l60_lhs_h232_p1geom118x58_01",
        "cpk_zero_l60_lhs_h232_p1geom122x58_01",
        "cpk_zero_l60_lhs_h232_p1geom120x58_notch_p1_right4_01",
        "cpk_zero_l60_lhs_h232_p1geom120x58_notch_p1_left4_01",
        "cpk_zero_l60_lhs_h232_p1geom120x58_notch_p1_right6_01",
    }

    assert len(no_notch) == 6
    assert len(with_notch) == 9
    assert requested == {spec.candidate_id for spec in with_notch}
    for spec in with_notch:
        assert isinstance(spec.p1_length_nm, int)
        assert isinstance(spec.p1_width_nm, int)
        if spec.p1_notch_depth_nm is not None:
            assert isinstance(spec.p1_notch_depth_nm, int)
        if spec.p1_notch_width_nm is not None:
            assert isinstance(spec.p1_notch_width_nm, int)


def test_p169_generated_config_fixes_integer_height_and_stage_boundary(p169) -> None:
    spec = p169.CandidateSpec(
        candidate_id="cpk_zero_integer_unit",
        group="integer_p1_minor_compensation",
        family="integer_p1_length_width_compensation",
        p1_length_nm=121,
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

    config = p169.build_candidate_config(anchor, spec)
    row = p169.plan_row(spec, Path("configs/apcd_k6_phase_state_candidates/cpk_zero_integer_unit.yaml"))
    p169.assert_integer_geometry([row])

    assert config["project"]["stage"] == "09_p169_integer_zero_recovery_candidate_yaml_only"
    assert config["geometry"]["height_nm"] == 232
    assert isinstance(config["geometry"]["height_nm"], int)
    assert config["geometry"]["nanopillar_1"]["length_nm"] == 121
    assert config["boundary"]["integer_nm_official_geometry"] is True
    assert config["boundary"]["sub_nm_height_diagnostic_only"] is True
    assert "cpk_zero_integer_unit" in config["output"]["result_dir"]


def test_p170_missing_results_do_not_crash(p170, tmp_path) -> None:
    plan = [
        {
            "candidate_id": "cpk_zero_integer_missing",
            "group": "integer_p1_minor_compensation",
            "family": "integer_p1_length_width_compensation",
        }
    ]

    rows = p170.summarize_plan_results(plan, tmp_path)
    decisions = p170.build_decision_rows(rows)

    assert rows[0]["result_status"] == "missing_result"
    assert rows[0]["early_pass"] is False
    assert rows[0]["opens_0"] is False
    assert any(row["decision_key"] == "official_height_nm" and row["decision_value"] == 232 for row in decisions)


def test_p173_candidate_specs_are_fixed_h233_integer_and_limited(p173) -> None:
    no_notch = p173.build_candidate_specs(notch_supported=False)
    with_notch = p173.build_candidate_specs(notch_supported=True)
    requested_core = {
        "cpk_zero_l60_h233_p1geom120x58_p2geom74x135_01",
        "cpk_zero_l60_h233_p1geom120x58_p2geom76x135_01",
        "cpk_zero_l60_h233_p1geom120x58_p2geom75x134_01",
        "cpk_zero_l60_h233_p1geom120x58_p2geom75x136_01",
        "cpk_zero_l60_h233_p1geom120x58_p2geom74x134_01",
        "cpk_zero_l60_h233_p1geom120x58_p2geom76x136_01",
        "cpk_zero_l60_h233_p1geom119x58_01",
        "cpk_zero_l60_h233_p1geom118x58_01",
        "cpk_zero_l60_h233_p1geom120x57_01",
    }

    assert len(no_notch) == 9
    assert len(with_notch) == 12
    assert len(with_notch) <= 12
    assert requested_core.issubset({spec.candidate_id for spec in with_notch})
    assert any(spec.p1_shape == "notched_rectangle" for spec in with_notch)
    assert any(spec.p2_shape == "notched_rectangle" for spec in with_notch)
    for spec in with_notch:
        assert isinstance(spec.p1_length_nm, int)
        assert isinstance(spec.p1_width_nm, int)
        assert isinstance(spec.p2_length_nm, int)
        assert isinstance(spec.p2_width_nm, int)
        if spec.p1_notch_depth_nm is not None:
            assert isinstance(spec.p1_notch_depth_nm, int)
        if spec.p2_notch_depth_nm is not None:
            assert isinstance(spec.p2_notch_depth_nm, int)


def test_p173_generated_config_fixes_h233_and_p2_geometry(p173) -> None:
    spec = p173.CandidateSpec(
        candidate_id="cpk_zero_h233_unit",
        group="A",
        family="p2_dynamic_resonance_phase_scan",
        p1_length_nm=120,
        p1_width_nm=58,
        p2_length_nm=74,
        p2_width_nm=134,
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

    config = p173.build_candidate_config(anchor, spec)
    row = p173.plan_row(spec, Path("configs/apcd_k6_phase_state_candidates/cpk_zero_h233_unit.yaml"))
    p173.assert_integer_geometry([row])

    assert config["project"]["stage"] == "09_p173_fixed_h233_resonance_phase_candidate_yaml_only"
    assert config["geometry"]["height_nm"] == 233
    assert isinstance(config["geometry"]["height_nm"], int)
    assert config["geometry"]["nanopillar_1"]["length_nm"] == 120
    assert config["geometry"]["nanopillar_1"]["width_nm"] == 58
    assert config["geometry"]["nanopillar_2"]["length_nm"] == 74
    assert config["geometry"]["nanopillar_2"]["width_nm"] == 134
    assert config["boundary"]["fixed_height_nm"] == 233
    assert config["boundary"]["no_fdtd_run_by_generator"] is True


def test_p174_missing_results_do_not_crash_and_defer_decision(p174, tmp_path) -> None:
    plan = [
        {
            "candidate_id": "cpk_zero_h233_missing",
            "group": "A",
            "family": "p2_dynamic_resonance_phase_scan",
        }
    ]

    rows = p174.summarize_plan_results(plan, tmp_path)
    decisions = p174.build_decision_rows(rows)

    assert rows[0]["result_status"] == "missing_result"
    assert rows[0]["early_pass"] is False
    assert rows[0]["opens_0"] is False
    assert any(row["decision_key"] == "official_height_nm" and row["decision_value"] == 233 for row in decisions)
    assert any(
        row["decision_key"] == "final_decision" and row["decision_value"] == "run_missing_real_fdtd_on_server"
        for row in decisions
    )


def test_p174_decision_logic_opens_and_continue(p174) -> None:
    opened = [
        {
            "candidate_id": "cpk_open",
            "result_status": "ok",
            "opens_0": True,
            "early_pass": True,
            "err_to_30_boundary": 20.0,
            "err_to_0": 10.0,
        }
    ]
    continued = [
        {
            "candidate_id": "cpk_continue",
            "result_status": "ok",
            "opens_0": False,
            "early_pass": True,
            "err_to_30_boundary": 3.0,
            "err_to_0": 33.0,
        }
    ]

    opened_decisions = p174.build_decision_rows(opened)
    continued_decisions = p174.build_decision_rows(continued)

    assert any(row["decision_key"] == "final_decision" and row["decision_value"] == "0_bin_opened" for row in opened_decisions)
    assert any(
        row["decision_key"] == "final_decision"
        and row["decision_value"] == "continue_fixed_h233_resonance_scan"
        for row in continued_decisions
    )


def test_p176_candidate_generation_is_deterministic_integer_and_fixed_h232(p176) -> None:
    specs = p176.build_candidate_specs()
    expected = [
        "cpk_zero_l60_h232_p1geom120x58_p2geom75x136_01",
        "cpk_zero_l60_h232_p1geom120x58_p2geom76x136_01",
        "cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01",
        "cpk_zero_l60_h232_p1geom120x58_p2geom77x137_01",
        "cpk_zero_l60_h232_p1geom120x58_p2geom74x136_01",
        "cpk_zero_l60_h232_p1geom119x58_p2geom76x136_01",
    ]

    assert [spec.candidate_id for spec in specs] == expected
    for spec in specs:
        assert isinstance(spec.p1_length_nm, int)
        assert isinstance(spec.p1_width_nm, int)
        assert isinstance(spec.p2_length_nm, int)
        assert isinstance(spec.p2_width_nm, int)


def test_p176_generated_config_validates_min_gap_and_no_overclaim(p176) -> None:
    anchor = {
        "project": {"name": "blue_plane_wave_metasurface", "stage": "old"},
        "candidate": {"variant_id": "anchor"},
        "geometry": {
            "layout_mode": "manual_absolute",
            "period_x_nm": 340,
            "period_y_nm": 340,
            "height_nm": 300,
            "minimum_gap_nm": 5,
            "nanopillar_1": {
                "length_nm": 115,
                "width_nm": 55,
                "rotation_deg": 67.5,
                "x_nm": 65,
                "y_nm": 101,
                "frac_x": 0.75,
                "frac_y": 0.75,
            },
            "nanopillar_2": {
                "length_nm": 75,
                "width_nm": 135,
                "rotation_deg": 112.5,
                "x_nm": -65,
                "y_nm": -101,
                "frac_x": 0.25,
                "frac_y": 0.25,
            },
        },
        "output": {"result_dir": "old"},
    }
    rows = []
    for spec in p176.build_candidate_specs():
        config = p176.build_candidate_config(anchor, spec)
        gap = p176.validate_min_gap(config)
        row = p176.plan_row(spec, config, Path(f"configs/{spec.candidate_id}.yaml"), gap)
        rows.append(row)

        assert config["project"]["stage"] == "09_p176_h232_zero_coupled_recovery_candidate_yaml_only"
        assert config["geometry"]["height_nm"] == 232
        assert config["geometry"]["minimum_gap_nm"] == 50
        assert config["boundary"]["fixed_height_nm"] == 232
        assert config["boundary"]["minimum_gap_nm_threshold"] == 50.0
        assert config["boundary"]["no_notch_in_p176_batch"] is True
        assert "not K=6 phase-ramp" in config["candidate"]["notes"]
        assert "not steering" in config["candidate"]["notes"]
        assert "not a Micro-LED result" in config["candidate"]["notes"]
        assert "not_steering_result" in config["boundary"]
        assert gap["same_cell_min_gap_nm"] >= 50.0
        assert gap["periodic_image_min_gap_nm"] >= 50.0

    p176.assert_integer_geometry(rows)
    assert all(row["geometry_pass"] is True for row in rows)


def test_p177_missing_results_do_not_crash_and_defer_decision(p177, tmp_path) -> None:
    plan = [
        {
            "candidate_id": "cpk_zero_h232_missing",
            "group": "p2_size_up_selection_recovery",
            "family": "h232_zero_coupled_p2_size_width_recovery",
        }
    ]

    rows = p177.summarize_plan_results(plan, tmp_path)
    decisions = p177.build_decision_rows(rows)

    assert rows[0]["result_status"] == "missing_result"
    assert rows[0]["early_pass"] is False
    assert rows[0]["opens_0"] is False
    assert any(
        row["decision_key"] == "final_decision" and row["decision_value"] == "run_missing_real_fdtd_on_server"
        for row in decisions
    )


def test_p177_decision_logic_opens_continue_and_shift(p177) -> None:
    opened = [
        {
            "candidate_id": "cpk_open",
            "result_status": "ok",
            "nearest_bin": 0,
            "opens_0": True,
            "early_pass": True,
            "leakage": 0.18,
        }
    ]
    continued = [
        {
            "candidate_id": "cpk_continue",
            "result_status": "ok",
            "nearest_bin": 0,
            "opens_0": False,
            "early_pass": False,
            "leakage": 0.15,
        }
    ]
    shifted = [
        {
            "candidate_id": "cpk_shift",
            "result_status": "ok",
            "nearest_bin": 60,
            "opens_0": False,
            "early_pass": False,
            "leakage": 0.25,
        }
    ]

    opened_decisions = p177.build_decision_rows(opened)
    continued_decisions = p177.build_decision_rows(continued)
    shifted_decisions = p177.build_decision_rows(shifted)

    assert any(row["decision_key"] == "final_decision" and row["decision_value"] == "0_bin_opened" for row in opened_decisions)
    assert any(
        row["decision_key"] == "final_decision" and row["decision_value"] == "continue_coupled_recovery"
        for row in continued_decisions
    )
    assert any(
        row["decision_key"] == "final_decision" and row["decision_value"] == "mechanism_shift_needed"
        for row in shifted_decisions
    )
