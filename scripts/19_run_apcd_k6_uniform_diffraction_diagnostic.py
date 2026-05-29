from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path
from types import ModuleType
from typing import Callable


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_diffraction import (
    APCD_DIFFRACTION_ORDER_FIELDS,
    APCD_ORDER_RESOLVED_JONES_FIELDS,
    OrderResolvedJones,
    build_jones_xy_from_columns,
    expected_order_angle_deg,
    extract_fdtd_grating_orders,
    transform_jones_xy_to_alpha_beta,
    write_diffraction_order_schema,
    write_order_resolved_jones_schema,
)
from metasurface.config import load_runtime_config
from metasurface.lumapi_runner import import_lumapi


K = 6
WAVELENGTH_NM = 633.0
TARGET_ANGLE_DEG = 15.0
SUPERCELL_PERIOD_NM = 2445.724192163921
OUTPUT_DIR = REPO_ROOT / "outputs" / "apcd_k6_metagrating_633nm" / "diagnostic_uniform_run"
SETUP_FSP = REPO_ROOT / "outputs" / "apcd_k6_metagrating_633nm" / "apcd_k6_metagrating_633nm_setup.fsp"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run K=6 uniform APCD metagrating diffraction diagnostic.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="Write placeholder diagnostic files only.")
    mode.add_argument("--fake-run", action="store_true", help="Run with fake FDTD for tests.")
    mode.add_argument("--run-real", action="store_true", help="Run real Lumerical diagnostic.")
    parser.add_argument("--runtime", default="configs/runtime.yaml", help="Runtime YAML for real lumapi mode.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if args.dry_run:
        run_log = ["mode=dry_run", "no FDTD session was created"]
        _write_error_outputs(run_log, "dry_run placeholder; no FDTD run was performed")
    elif args.fake_run:
        run_log = ["mode=fake_run"]
        _run_diagnostic(lambda: _FakeFDTD(), run_log)
    else:
        run_log = ["mode=run_real"]
        runtime = load_runtime_config(REPO_ROOT / args.runtime)
        lumapi = import_lumapi(runtime)
        _run_diagnostic(lambda: lumapi.FDTD(hide=runtime.hide_gui), run_log)

    return 0


def _run_diagnostic(fdtd_factory: Callable[[], object], run_log: list[str]) -> None:
    try:
        x_result = _run_one_input(fdtd_factory, "X", run_log)
    except Exception as exc:
        run_log.append(f"X input failed: {type(exc).__name__}: {exc}")
        x_result = _failed_input_result("X", exc)

    try:
        y_result = _run_one_input(fdtd_factory, "Y", run_log)
    except Exception as exc:
        run_log.append(f"Y input failed: {type(exc).__name__}: {exc}")
        y_result = _failed_input_result("Y", exc)

    _write_diffraction_orders("X", x_result)
    _write_diffraction_orders("Y", y_result)
    jones_rows, jones_available = _build_order_resolved_jones_rows(x_result, y_result, run_log)
    write_order_resolved_jones_schema(jones_rows, OUTPUT_DIR / "order_resolved_jones.csv")
    _write_summary(x_result, y_result, jones_available, run_log)
    (OUTPUT_DIR / "run_log.txt").write_text("\n".join(run_log) + "\n", encoding="utf-8")


def _run_one_input(fdtd_factory: Callable[[], object], label: str, run_log: list[str]) -> dict[str, object]:
    pre_run_path = OUTPUT_DIR / f"pre_run_{label}.fsp"
    result_path = OUTPUT_DIR / f"result_{label}.fsp"

    setup_fdtd = fdtd_factory()
    try:
        setup_fdtd.load(str(SETUP_FSP))
        run_log.append(f"{label}: setup loaded from {SETUP_FSP}")
        _set_source_polarization(setup_fdtd, label)
        run_log.append(f"{label}: source set to {label}-polarized input")
        setup_fdtd.save(str(pre_run_path))
        run_log.append(f"{label}: pre_run_fsp_saved={pre_run_path}")
    finally:
        _safe_close(setup_fdtd)

    run_fdtd = fdtd_factory()
    try:
        run_fdtd.load(str(pre_run_path))
        run_log.append(f"{label}: pre_run_fsp_loaded={pre_run_path}")
        run_fdtd.run()
        run_log.append(f"{label}: fdtd.run completed")
        run_log.append(f"{label}: switchtolayout_after_run=False")
        extraction_diagnostics: list[str] = []
        orders = extract_fdtd_grating_orders(
            run_fdtd,
            monitor_name="T",
            K=K,
            diagnostics=extraction_diagnostics,
        )
        for diagnostic in extraction_diagnostics:
            run_log.append(f"{label}: {diagnostic}")
        run_log.append(f"{label}: grating power extraction success")
        vector_available = _orders_have_complex_vectors(orders)
        run_log.append(f"{label}: gratingvector complex extraction {'success' if vector_available else 'failed_or_unavailable'}")
        run_fdtd.save(str(result_path))
        run_log.append(f"{label}: result_fsp_saved={result_path}")
        return {
            "label": label,
            "status": "ok",
            "orders": _annotate_order_rows(orders, label),
            "pre_run_path": pre_run_path,
            "result_path": result_path,
            "vector_available": vector_available,
            "error": "",
        }
    finally:
        _safe_close(run_fdtd)


def _set_source_polarization(fdtd: object, label: str) -> None:
    angle = 0 if label.upper() == "X" else 90
    if hasattr(fdtd, "setnamed"):
        fdtd.setnamed("source_x", "polarization angle", angle)
        fdtd.setnamed("source_x", "phase", 0)
        fdtd.setnamed("source_x", "amplitude", 1)
        return
    if hasattr(fdtd, "select"):
        fdtd.select("source_x")
    fdtd.set("polarization angle", angle)
    fdtd.set("phase", 0)
    fdtd.set("amplitude", 1)


def _annotate_order_rows(rows: list[dict[str, object]], label: str) -> list[dict[str, object]]:
    for row in rows:
        order = int(row["order_n"])
        row["wavelength_nm"] = WAVELENGTH_NM
        row["supercell_period_nm"] = SUPERCELL_PERIOD_NM
        row["target_angle_deg"] = TARGET_ANGLE_DEG
        row["expected_theta_deg"] = expected_order_angle_deg(order, WAVELENGTH_NM, SUPERCELL_PERIOD_NM)
        row["input_basis"] = f"{label.lower()}_linear"
        row["notes"] = f"K=6 uniform scaffold diagnostic {label} input; not final metagrating"
    return rows


def _orders_have_complex_vectors(rows: list[dict[str, object]]) -> bool:
    return any(row.get("Ex_order_complex_real") != "" and row.get("Ey_order_complex_real") != "" for row in rows)


def _build_order_resolved_jones_rows(
    x_result: dict[str, object],
    y_result: dict[str, object],
    run_log: list[str],
) -> tuple[list[dict[str, object]], bool]:
    x_orders = x_result.get("orders", [])
    y_orders = y_result.get("orders", [])
    if not isinstance(x_orders, list) or not isinstance(y_orders, list):
        return _empty_jones_rows("order-resolved Jones matrix was not available because grating extraction failed"), False
    if not x_result.get("vector_available") or not y_result.get("vector_available"):
        run_log.append("order-resolved Jones unavailable: complex vector output extraction failed")
        return _empty_jones_rows(
            "order-resolved Jones matrix was not available because complex vector output extraction failed"
        ), False

    rows = []
    for order in (-1, 0, 1):
        x_row = _find_order_row(x_orders, order)
        y_row = _find_order_row(y_orders, order)
        if x_row is None or y_row is None:
            rows.append(_empty_jones_row(order, "order missing in X or Y extraction"))
            continue
        j_xy = build_jones_xy_from_columns(
            _source_normalized_xy_from_order_row(x_row),
            _source_normalized_xy_from_order_row(y_row),
        )
        j_ab = transform_jones_xy_to_alpha_beta(j_xy, psi_deg=112.5, chi_deg=22.5)
        rows.append(
            OrderResolvedJones(
                K=K,
                order_m=int(x_row.get("order_m", 0)),
                order_n=order,
                expected_theta_deg=float(x_row.get("expected_theta_deg", "")),
                J_xy=j_xy,
                J_alpha_beta=j_ab,
                notes=(
                    "K=6 uniform scaffold diagnostic; gratingvector columns scaled by sqrt(total_transmission); "
                    "not final metagrating"
                ),
            ).to_schema_row(wavelength_nm=WAVELENGTH_NM, target_angle_deg=TARGET_ANGLE_DEG)
        )
    run_log.append("order-resolved Jones construction success")
    return rows, True


def _source_normalized_xy_from_order_row(row: dict[str, object]) -> tuple[complex, complex]:
    ex = complex(float(row["Ex_order_complex_real"]), float(row["Ex_order_complex_imag"]))
    ey = complex(float(row["Ey_order_complex_real"]), float(row["Ey_order_complex_imag"]))
    scale = math.sqrt(max(float(row.get("total_transmission", 1.0)), 0.0))
    return (scale * ex, scale * ey)


def _find_order_row(rows: list[dict[str, object]], order_n: int) -> dict[str, object] | None:
    for row in rows:
        try:
            current_order_n = int(row.get("order_n", 999))
        except (TypeError, ValueError):
            continue
        if current_order_n == order_n:
            return row
    return None


def _empty_jones_rows(note: str) -> list[dict[str, object]]:
    return [_empty_jones_row(order, note) for order in (-1, 0, 1)]


def _empty_jones_row(order_n: int, note: str) -> dict[str, object]:
    row = {field: "" for field in APCD_ORDER_RESOLVED_JONES_FIELDS}
    row.update(
        {
            "K": K,
            "wavelength_nm": WAVELENGTH_NM,
            "target_angle_deg": TARGET_ANGLE_DEG,
            "order_m": 0,
            "order_n": order_n,
            "expected_theta_deg": expected_order_angle_deg(order_n, WAVELENGTH_NM, SUPERCELL_PERIOD_NM),
            "input_basis": "x_y_future",
            "output_basis": "alpha_star_beta_star_future",
            "notes": note,
        }
    )
    return row


def _write_diffraction_orders(label: str, result: dict[str, object]) -> None:
    rows = result.get("orders", [])
    if not isinstance(rows, list):
        rows = [_error_order_row(label, str(result.get("error", "unknown error")))]
    write_diffraction_order_schema(rows, OUTPUT_DIR / f"diffraction_orders_{label}.csv")


def _failed_input_result(label: str, exc: Exception) -> dict[str, object]:
    return {
        "label": label,
        "status": "failed",
        "orders": [_error_order_row(label, f"{type(exc).__name__}: {exc}")],
        "pre_run_path": OUTPUT_DIR / f"pre_run_{label}.fsp",
        "result_path": OUTPUT_DIR / f"result_{label}.fsp",
        "vector_available": False,
        "error": f"{type(exc).__name__}: {exc}",
    }


def _error_order_row(label: str, error: str) -> dict[str, object]:
    row = {field: "" for field in APCD_DIFFRACTION_ORDER_FIELDS}
    row.update(
        {
            "K": K,
            "wavelength_nm": WAVELENGTH_NM,
            "supercell_period_nm": SUPERCELL_PERIOD_NM,
            "target_angle_deg": TARGET_ANGLE_DEG,
            "input_basis": f"{label.lower()}_linear",
            "notes": f"error: {error}",
        }
    )
    return row


def _write_error_outputs(run_log: list[str], note: str) -> None:
    for label in ("X", "Y"):
        write_diffraction_order_schema([_error_order_row(label, note)], OUTPUT_DIR / f"diffraction_orders_{label}.csv")
    write_order_resolved_jones_schema(_empty_jones_rows(note), OUTPUT_DIR / "order_resolved_jones.csv")
    _write_summary(_failed_input_result("X", RuntimeError(note)), _failed_input_result("Y", RuntimeError(note)), False, run_log)
    (OUTPUT_DIR / "run_log.txt").write_text("\n".join(run_log) + "\n", encoding="utf-8")


def _write_summary(
    x_result: dict[str, object],
    y_result: dict[str, object],
    jones_available: bool,
    run_log: list[str],
) -> None:
    x_orders = x_result.get("orders", [])
    y_orders = y_result.get("orders", [])
    power_success = x_result.get("status") == "ok" and y_result.get("status") == "ok"
    vector_success = bool(x_result.get("vector_available")) and bool(y_result.get("vector_available"))
    sign_lines = _order_sign_lines(x_orders if isinstance(x_orders, list) else [])
    jones_lines = _jones_metric_lines(jones_available)
    plus_minus_note = _uniform_scaffold_note(x_orders if isinstance(x_orders, list) else [])
    lines = [
        "# K=6 Uniform Scaffold Diffraction Diagnostic Summary",
        "",
        "## Task Scope",
        "",
        "This is a K=6 uniform scaffold diagnostic run.",
        "This is not the final metagrating.",
        "This is not proof of +15 deg steering.",
        "This diagnostic is only for validating the diffraction-order extraction pipeline and order sign convention.",
        "",
        "## Setup Source",
        "",
        f"- input_setup: {SETUP_FSP}",
        "- K: 6",
        "- dimers: 6",
        "- nanopillars: 12",
        "- structure: uniform identical alpha-pass dimer scaffold",
        "",
        "## Run Status",
        "",
        f"- X input run: {x_result.get('status')}",
        f"- Y input run: {y_result.get('status')}",
        f"- grating power extraction: {'success' if power_success else 'failed'}",
        f"- gratingvector or complex field extraction: {'success' if vector_success else 'failed'}",
        f"- order-resolved Jones construction: {'success' if jones_available else 'failed'}",
        "",
        "## Order Sign Convention",
        "",
        *sign_lines,
        "",
        "If the rows above contain positive and negative u1 values, the sign convention can be inferred from the extracted order table. If not, sign convention remains unresolved.",
        "",
        "## Uniform Scaffold Sanity Check",
        "",
        "Phase 2.3A showed that uniform identical dimers should not coherently enhance m=+/-1 orders.",
        plus_minus_note,
        "If m=+/-1 are not weak, do not claim success; first inspect finite aperture effects, monitor normalization, order indexing, geometry uniformity, extraction correctness, source/monitor setup, and boundaries.",
        "",
        "## APCD Order-Resolved Metrics",
        "",
        "Jones columns use `gratingvector` complex components scaled by `sqrt(total_transmission)` for source-normalized amplitudes.",
        *jones_lines,
        "",
        "## Next Step",
        "",
        "If extraction succeeded, proceed to dimer phase-state mechanism design. If extraction failed, fix extraction only and do not change the physical design yet.",
        "",
        "## Run Log Tail",
        "",
        *[f"- {line}" for line in run_log[-20:]],
    ]
    (OUTPUT_DIR / "diagnostic_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _order_sign_lines(rows: list[dict[str, object]]) -> list[str]:
    lines = ["| order_n | order_m | u1 | u2 | expected_theta_deg | order_fraction |", "|---:|---:|---:|---:|---:|---:|"]
    for row in rows:
        lines.append(
            "| "
            f"{row.get('order_n', '')} | {row.get('order_m', '')} | "
            f"{row.get('expected_ux', '')} | {row.get('expected_uy', '')} | "
            f"{row.get('expected_theta_deg', '')} | {row.get('order_power_fraction_of_transmitted', '')} |"
        )
    return lines


def _uniform_scaffold_note(rows: list[dict[str, object]]) -> str:
    plus = _find_order_row(rows, 1)
    minus = _find_order_row(rows, -1)
    zero = _find_order_row(rows, 0)
    if plus is None or minus is None or zero is None:
        return "m=+/-1 weakness cannot be judged because one or more orders were not extracted."
    return (
        "Extracted order fractions are "
        f"m=-1: {minus.get('order_power_fraction_of_transmitted')}, "
        f"m=0: {zero.get('order_power_fraction_of_transmitted')}, "
        f"m=+1: {plus.get('order_power_fraction_of_transmitted')}. "
        "This diagnostic does not convert those values into a performance claim."
    )


def _jones_metric_lines(jones_available: bool) -> list[str]:
    if not jones_available:
        return ["APCD order-resolved Jones metrics are not available in this diagnostic run."]
    path = OUTPUT_DIR / "order_resolved_jones.csv"
    rows = list(csv.DictReader(path.open("r", newline="", encoding="utf-8")))
    lines = [
        "| order_n | target_conversion | beta_to_target_leakage | target_order_ER_dB |",
        "|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['order_n']} | {row['target_conversion']} | "
            f"{row['beta_to_target_leakage']} | {row['target_order_ER_dB']} |"
        )
    return lines


def _safe_close(fdtd: object) -> None:
    try:
        fdtd.close()
    except Exception:
        pass


class _FakeFDTD:
    def __init__(self) -> None:
        self.loaded_path = ""
        self.saved_paths: list[str] = []
        self.run_called = False
        self.switch_after_run = False
        self.calls: list[str] = []

    def load(self, path: str) -> None:
        self.loaded_path = path

    def save(self, path: str) -> None:
        self.saved_paths.append(path)
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_bytes(b"fake fsp")

    def setnamed(self, name: str, prop: str, value: object) -> None:
        self.calls.append(f"setnamed:{name}:{prop}:{value}")

    def run(self) -> None:
        self.run_called = True
        self.calls.append("run")

    def switchtolayout(self) -> None:
        if self.run_called:
            self.switch_after_run = True
        self.calls.append("switchtolayout")

    def gratingn(self, monitor_name: str) -> list[int]:
        self.calls.append(f"gratingn:{monitor_name}")
        return [-1, 0, 1]

    def gratingm(self, monitor_name: str) -> list[int]:
        self.calls.append(f"gratingm:{monitor_name}")
        return [0, 0, 0]

    def gratingu1(self, monitor_name: str) -> list[float]:
        self.calls.append(f"gratingu1:{monitor_name}")
        return [-0.2588190451, 0.0, 0.2588190451]

    def gratingu2(self, monitor_name: str) -> list[float]:
        self.calls.append(f"gratingu2:{monitor_name}")
        return [0.0, 0.0, 0.0]

    def grating(self, monitor_name: str) -> list[float]:
        self.calls.append(f"grating:{monitor_name}")
        return [0.02, 0.96, 0.02]

    def transmission(self, monitor_name: str) -> float:
        self.calls.append(f"transmission:{monitor_name}")
        return 0.5

    def gratingvector(self, monitor_name: str) -> list[list[complex]]:
        self.calls.append(f"gratingvector:{monitor_name}")
        return [
            [0.05 + 0.01j, 0.02 + 0.00j, 0.0 + 0.0j],
            [0.80 + 0.00j, 0.10 + 0.01j, 0.0 + 0.0j],
            [0.04 - 0.01j, 0.02 + 0.00j, 0.0 + 0.0j],
        ]

    def close(self) -> None:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
