from __future__ import annotations

import csv
import math
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_phase_states import (
    APCD_PHASE_STATE_LIBRARY_FIELDS,
    build_k6_detour_displacement_targets,
    build_k6_phase_targets,
    build_phase_state_schema_rows,
    compute_phase_state_metrics,
    detour_phase_deg,
    displacement_for_phase_deg,
    evaluate_phase_state_pass_fail,
    phase_error_deg,
    summarize_phase_generation_options,
    wrap_phase_deg,
    write_phase_state_dry_run_outputs,
)


K6_SUPERCELL_PERIOD_NM = 2445.724192163921


def test_k6_plus_ramp_targets() -> None:
    assert build_k6_phase_targets("plus") == [0, 60, 120, 180, 240, 300]


def test_k6_minus_ramp_targets() -> None:
    assert build_k6_phase_targets("minus") == [0, -60, -120, -180, -240, -300]


def test_phase_wrap_conventions() -> None:
    assert wrap_phase_deg(180) == -180
    assert wrap_phase_deg(181) == -179
    assert wrap_phase_deg(-181) == 179
    assert wrap_phase_deg(360) == 0
    assert wrap_phase_deg(-60, convention="0_360") == 300


def test_detour_phase_zero_displacement_returns_zero() -> None:
    assert detour_phase_deg(
        order_m=1,
        displacement_nm=0,
        supercell_period_nm=K6_SUPERCELL_PERIOD_NM,
    ) == 0


def test_displacement_for_60_deg_is_lambda_over_6_for_order_one() -> None:
    displacement = displacement_for_phase_deg(
        phase_deg=60,
        order_m=1,
        supercell_period_nm=K6_SUPERCELL_PERIOD_NM,
    )

    assert math.isclose(displacement, K6_SUPERCELL_PERIOD_NM / 6)


def test_k6_detour_plus_displacement_targets_are_monotonic() -> None:
    rows = build_k6_detour_displacement_targets(
        "plus",
        supercell_period_nm=K6_SUPERCELL_PERIOD_NM,
        order_m=1,
    )
    displacements = [float(row["dimer_dx_nm"]) for row in rows]

    assert displacements == sorted(displacements)
    assert math.isclose(displacements[1], K6_SUPERCELL_PERIOD_NM / 6)
    assert rows[3]["phase_target_deg"] == -180


def test_k6_detour_minus_displacement_targets_have_opposite_sign() -> None:
    plus_rows = build_k6_detour_displacement_targets(
        "plus",
        supercell_period_nm=K6_SUPERCELL_PERIOD_NM,
        order_m=1,
    )
    minus_rows = build_k6_detour_displacement_targets(
        "minus",
        supercell_period_nm=K6_SUPERCELL_PERIOD_NM,
        order_m=1,
    )

    for plus_row, minus_row in zip(plus_rows, minus_rows):
        assert math.isclose(float(plus_row["dimer_dx_nm"]), -float(minus_row["dimer_dx_nm"]))


def test_phase_generation_summary_prioritizes_detour_and_deprioritizes_rotation() -> None:
    rows = summarize_phase_generation_options()

    assert rows[0]["mechanism"] == "detour_displacement"
    assert rows[0]["priority"] == "A"
    rotation = next(row for row in rows if row["mechanism"] == "constrained_global_rotation")
    assert "allowed alpha state" in rotation["risk"]


def test_phase_error_handles_equivalent_angles() -> None:
    assert phase_error_deg(179, -181) == 0
    assert phase_error_deg(-179, 181) == 0
    assert phase_error_deg(170, -170) == 20


def test_target_conversion_is_target_amplitude_squared() -> None:
    metrics = compute_phase_state_metrics(
        t_alpha_star_from_alpha=0.6 + 0.8j,
        phase_target_deg=wrap_phase_deg(math.degrees(math.atan2(0.8, 0.6))),
    )

    assert math.isclose(metrics["t_alpha_star_from_alpha_abs"], 1.0)
    assert math.isclose(metrics["target_conversion"], 1.0)
    assert math.isclose(metrics["phase_error_deg"], 0.0)


def test_leakage_ratio_calculation() -> None:
    metrics = compute_phase_state_metrics(
        t_alpha_star_from_alpha=1 + 0j,
        t_alpha_star_from_beta=0.2 + 0j,
        t_beta_star_from_beta=0.3 + 0j,
        phase_target_deg=0,
    )

    assert math.isclose(metrics["beta_to_target_leakage"], 0.04)
    assert math.isclose(metrics["beta_total_leakage"], 0.13)
    assert math.isclose(metrics["target_to_beta_ratio"], 25.0)


def test_pass_fail_threshold_logic() -> None:
    passing = compute_phase_state_metrics(
        t_alpha_star_from_alpha=math.sqrt(0.6) + 0j,
        t_alpha_star_from_beta=math.sqrt(0.05) + 0j,
        t_beta_star_from_beta=math.sqrt(0.05) + 0j,
        phase_target_deg=0,
    )
    decision = evaluate_phase_state_pass_fail(passing)
    assert decision == {
        "amplitude_pass": True,
        "leakage_pass": True,
        "phase_pass": True,
        "overall_pass": True,
    }

    failing = dict(passing)
    failing["phase_error_deg"] = 25.0
    assert evaluate_phase_state_pass_fail(failing)["overall_pass"] is False
    assert evaluate_phase_state_pass_fail(failing)["phase_pass"] is False


def test_schema_rows_contain_required_columns() -> None:
    rows = build_phase_state_schema_rows(K=6)

    assert len(rows) == 12
    assert set(APCD_PHASE_STATE_LIBRARY_FIELDS).issubset(rows[0].keys())
    assert rows[0]["ramp_sign"] == "plus"
    assert rows[6]["ramp_sign"] == "minus"
    assert rows[3]["phase_target_deg"] == -180
    assert rows[10]["phase_target_deg"] == 120
    assert rows[0]["pillar_2_length_nm"] == 85.0
    assert rows[0]["pillar_2_width_nm"] == 150.0
    assert "not a steering result" in str(rows[0]["notes"])


def test_write_schema_csv_contains_all_required_columns(tmp_path: Path) -> None:
    schema_path, criteria_path, rows = write_phase_state_dry_run_outputs(tmp_path)

    assert schema_path.exists()
    assert criteria_path.exists()
    assert len(rows) == 12
    with schema_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded_rows = list(reader)

    assert reader.fieldnames == APCD_PHASE_STATE_LIBRARY_FIELDS
    assert len(loaded_rows) == 12
    assert set(APCD_PHASE_STATE_LIBRARY_FIELDS).issubset(set(reader.fieldnames or []))


def test_dry_run_script_does_not_call_lumapi_or_fdtd_run() -> None:
    script = REPO_ROOT / "scripts" / "20_define_apcd_k6_phase_state_library.py"
    script_text = script.read_text(encoding="utf-8")

    assert "lumapi" not in script_text
    assert "fdtd.run" not in script_text


def test_phase_state_module_analytic_functions_do_not_call_lumapi_or_fdtd_run() -> None:
    module_text = (REPO_ROOT / "src" / "metasurface" / "apcd_phase_states.py").read_text(encoding="utf-8")

    assert "lumapi" not in module_text
    assert "fdtd.run" not in module_text


def test_dry_run_script_writes_schema_and_reports_targets() -> None:
    script = REPO_ROOT / "scripts" / "20_define_apcd_k6_phase_state_library.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--dry-run"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "plus_ramp_phase_targets_deg=0, 60, 120, 180, 240, 300" in completed.stdout
    assert "minus_ramp_phase_targets_deg=0, -60, -120, -180, -240, -300" in completed.stdout
    assert "status=dry_run_schema_only_no_fdtd_no_fsp_not_steering_result" in completed.stdout
    assert (
        REPO_ROOT / "outputs" / "apcd_k6_metagrating_633nm" / "phase_state_library_schema.csv"
    ).exists()
    assert (
        REPO_ROOT / "outputs" / "apcd_k6_metagrating_633nm" / "phase_state_pass_fail_criteria.md"
    ).exists()


def test_criteria_report_states_physical_boundaries(tmp_path: Path) -> None:
    _, criteria_path, _ = write_phase_state_dry_run_outputs(tmp_path)
    text = criteria_path.read_text(encoding="utf-8")

    assert "No FDTD run was performed" in text
    assert "not a steering result" in text
    assert "schema only" in text
    assert "no real phase-state candidate library" in text
    assert "uniform scaffold's 0th-order result cannot be reused" in text
    assert "t_{alpha*<-alpha}" in text
    assert "alpha/beta -> alpha*/beta*" in text
    assert "Do not judge success from total T alone" in text
    assert "Do not judge success from `grating()` power alone" in text
    assert "Global rotation may change the allowed alpha state" in text
    assert "150 x 85 nm" in text


def test_generation_mechanism_report_states_scope_and_detour_warning() -> None:
    text = (REPO_ROOT / "reports" / "apcd_k6_phase_state_generation_mechanism_note.md").read_text(
        encoding="utf-8"
    )

    assert "No FDTD run was performed" in text
    assert "not a steering result" in text
    assert "mechanism note only" in text
    assert "displacement_for_60_deg(order_m=+1) = 407.62069869398687 nm" in text
    assert "does not automatically change the intrinsic single-dimer `t_{alpha*<-alpha}` phase" in text
    assert "Do not use global rotation as the first-priority default phase knob" in text
