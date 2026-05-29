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

from metasurface.apcd_diffraction import (
    APCD_ORDER_RESOLVED_JONES_FIELDS,
    OrderResolvedJones,
    build_alpha_beta_basis,
    build_jones_xy_from_columns,
    order_resolved_apcd_metrics,
    transform_jones_xy_to_alpha_beta,
    write_order_resolved_jones_dry_run_outputs,
)


def _inner(a: tuple[complex, complex], b: tuple[complex, complex]) -> complex:
    return a[0].conjugate() * b[0] + a[1].conjugate() * b[1]


def _norm(v: tuple[complex, complex]) -> float:
    return math.sqrt(abs(v[0]) ** 2 + abs(v[1]) ** 2)


def _outer(u: tuple[complex, complex], v: tuple[complex, complex]) -> list[list[complex]]:
    return [
        [u[0] * v[0].conjugate(), u[0] * v[1].conjugate()],
        [u[1] * v[0].conjugate(), u[1] * v[1].conjugate()],
    ]


def test_alpha_beta_basis_vectors_are_normalized_and_orthogonal() -> None:
    basis = build_alpha_beta_basis(psi_deg=112.5, chi_deg=22.5)

    assert math.isclose(_norm(basis["alpha"]), 1.0)
    assert math.isclose(_norm(basis["beta"]), 1.0)
    assert math.isclose(_norm(basis["alpha_star"]), 1.0)
    assert math.isclose(_norm(basis["beta_star"]), 1.0)
    assert abs(_inner(basis["alpha"], basis["beta"])) < 1e-12
    assert abs(_inner(basis["alpha_star"], basis["beta_star"])) < 1e-12


def test_identity_jones_transform_has_correct_shape() -> None:
    j_ab = transform_jones_xy_to_alpha_beta(
        [[1 + 0j, 0 + 0j], [0 + 0j, 1 + 0j]],
        psi_deg=112.5,
        chi_deg=22.5,
    )

    assert len(j_ab) == 2
    assert len(j_ab[0]) == 2
    assert len(j_ab[1]) == 2


def test_mock_perfect_apcd_matrix_maps_alpha_to_alpha_star_only() -> None:
    basis = build_alpha_beta_basis(psi_deg=112.5, chi_deg=22.5)
    j_xy = _outer(basis["alpha_star"], basis["alpha"])

    j_ab = transform_jones_xy_to_alpha_beta(j_xy, psi_deg=112.5, chi_deg=22.5)

    assert abs(j_ab[0][0] - 1) < 1e-12
    assert abs(j_ab[1][0]) < 1e-12
    assert abs(j_ab[0][1]) < 1e-12
    assert abs(j_ab[1][1]) < 1e-12


def test_build_jones_xy_from_columns_preserves_column_order() -> None:
    j_xy = build_jones_xy_from_columns(
        x_input_output=(1 + 2j, 3 + 4j),
        y_input_output=(5 + 6j, 7 + 8j),
    )

    assert j_xy == [[1 + 2j, 5 + 6j], [3 + 4j, 7 + 8j]]


def test_order_resolved_metrics_and_er_db_are_reasonable() -> None:
    j_ab = [[1 + 0j, 0.1 + 0j], [0.2 + 0j, 0.3 + 0j]]
    metrics = order_resolved_apcd_metrics(j_ab, eps=1e-12)

    assert metrics["target_conversion"] == 1.0
    assert math.isclose(metrics["alpha_cross_leakage"], 0.04)
    assert math.isclose(metrics["beta_to_target_leakage"], 0.01)
    assert math.isclose(metrics["beta_total_leakage"], 0.10)
    assert metrics["target_order_ER_dB"] > 19.9


def test_order_resolved_jones_schema_row_contains_metrics() -> None:
    j_xy = [[1 + 0j, 0 + 0j], [0 + 0j, 0 + 0j]]
    j_ab = [[1 + 0j, 0 + 0j], [0 + 0j, 0 + 0j]]
    row = OrderResolvedJones(
        K=6,
        order_m=0,
        order_n=1,
        expected_theta_deg=15.0,
        J_xy=j_xy,
        J_alpha_beta=j_ab,
        notes="mock",
    ).to_schema_row()

    assert row["t_alpha_star_from_alpha_real"] == 1.0
    assert row["target_conversion"] == 1.0
    assert row["beta_to_target_leakage"] == 0.0
    assert row["notes"] == "mock"


def test_dry_run_outputs_write_schema_and_plan(tmp_path: Path) -> None:
    schema_path, plan_path, rows = write_order_resolved_jones_dry_run_outputs(K=6, output_dir=tmp_path)

    assert schema_path.exists()
    assert plan_path.exists()
    assert len(rows) == 3
    with schema_path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        loaded_rows = list(reader)
    assert reader.fieldnames == APCD_ORDER_RESOLVED_JONES_FIELDS
    assert len(loaded_rows) == 3
    text = plan_path.read_text(encoding="utf-8")
    assert "not an optical result" in text
    assert "no FDTD run was performed" in text
    assert "scaffold only" in text
    assert "grating()` power fraction alone is not enough" in text


def test_order_resolved_jones_script_writes_k6_k7_outputs() -> None:
    script = REPO_ROOT / "scripts" / "18_analyze_apcd_order_resolved_jones.py"
    script_text = script.read_text(encoding="utf-8")
    assert "lumapi" not in script_text
    assert "fdtd.run" not in script_text

    completed = subprocess.run(
        [sys.executable, str(script), "--all", "--dry-run"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "K=6" in completed.stdout
    assert "K=7" in completed.stdout
    assert (
        REPO_ROOT / "outputs" / "apcd_k6_metagrating_633nm" / "order_resolved_jones_schema.csv"
    ).exists()
    assert (
        REPO_ROOT / "outputs" / "apcd_k6_metagrating_633nm" / "order_resolved_jones_plan.md"
    ).exists()
    assert (
        REPO_ROOT / "outputs" / "apcd_k7_metagrating_633nm" / "order_resolved_jones_schema.csv"
    ).exists()
    assert (
        REPO_ROOT / "outputs" / "apcd_k7_metagrating_633nm" / "order_resolved_jones_plan.md"
    ).exists()
