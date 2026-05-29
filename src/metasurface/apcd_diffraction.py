from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Iterable


APCD_DIFFRACTION_ORDER_FIELDS = [
    "K",
    "wavelength_nm",
    "supercell_period_nm",
    "target_angle_deg",
    "order_n",
    "order_m",
    "expected_theta_deg",
    "expected_ux",
    "expected_uy",
    "order_power_fraction_of_transmitted",
    "total_transmission",
    "order_efficiency_source_norm",
    "Ex_order_complex_real",
    "Ex_order_complex_imag",
    "Ey_order_complex_real",
    "Ey_order_complex_imag",
    "Ez_order_complex_real",
    "Ez_order_complex_imag",
    "input_basis",
    "output_basis",
    "target_channel",
    "notes",
]


def compute_grating_period_nm(wavelength_nm: float, target_angle_deg: float) -> float:
    sin_theta = math.sin(math.radians(target_angle_deg))
    if sin_theta <= 0:
        raise ValueError("target_angle_deg must give a positive grating period")
    return wavelength_nm / sin_theta


def expected_order_angle_deg(order_m_or_n: int, wavelength_nm: float, period_nm: float) -> float:
    argument = order_m_or_n * wavelength_nm / period_nm
    if abs(argument) > 1:
        return math.nan
    return math.degrees(math.asin(argument))


def normalize_order_efficiency(grating_fraction: float, total_transmission: float) -> float:
    return grating_fraction * total_transmission


def build_expected_order_table(
    K: int,
    wavelength_nm: float = 633.0,
    target_angle_deg: float = 15.0,
    orders: Iterable[int] = (-1, 0, 1),
) -> list[dict[str, object]]:
    period_nm = compute_grating_period_nm(wavelength_nm, target_angle_deg)
    rows: list[dict[str, object]] = []
    for order in orders:
        theta = expected_order_angle_deg(order, wavelength_nm, period_nm)
        rows.append(
            {
                "K": K,
                "wavelength_nm": wavelength_nm,
                "supercell_period_nm": period_nm,
                "target_angle_deg": target_angle_deg,
                "order_n": order,
                "order_m": 0,
                "expected_theta_deg": theta,
                "expected_ux": math.sin(math.radians(theta)) if not math.isnan(theta) else math.nan,
                "expected_uy": 0.0,
                "order_power_fraction_of_transmitted": "",
                "total_transmission": "",
                "order_efficiency_source_norm": "",
                "Ex_order_complex_real": "",
                "Ex_order_complex_imag": "",
                "Ey_order_complex_real": "",
                "Ey_order_complex_imag": "",
                "Ez_order_complex_real": "",
                "Ez_order_complex_imag": "",
                "input_basis": "",
                "output_basis": "alpha_star_beta_star_future",
                "target_channel": "t_alpha_star_from_alpha_order_resolved_future",
                "notes": "dry-run schema row; not an optical result",
            }
        )
    return rows


def select_target_order_by_angle(
    order_table: list[dict[str, object]],
    target_angle_deg: float,
) -> dict[str, object]:
    return min(order_table, key=lambda row: abs(float(row["expected_theta_deg"]) - target_angle_deg))


def summarize_order_efficiencies(rows: list[dict[str, object]], epsilon: float = 1e-12) -> dict[str, float]:
    alpha_target = _float_or_zero(_find_metric(rows, "eta_alpha_to_target_order"))
    beta_target = _float_or_zero(_find_metric(rows, "eta_beta_to_target_order"))
    alpha_other = _float_or_zero(_find_metric(rows, "eta_alpha_to_other_orders"))
    return {
        "target_order_ER_dB": 10 * math.log10((alpha_target + epsilon) / (beta_target + epsilon)),
        "spin_selective_directionality_ratio": alpha_target / max(alpha_other + beta_target, epsilon),
    }


def extract_fdtd_grating_orders(fdtd: object, monitor_name: str = "T", K: int = 0) -> list[dict[str, object]]:
    order_n = _as_list(fdtd.gratingn(monitor_name))
    order_m = _as_list(fdtd.gratingm(monitor_name))
    ux = _as_list(fdtd.gratingu1(monitor_name))
    uy = _as_list(fdtd.gratingu2(monitor_name))
    grating_fraction = _as_list(fdtd.grating(monitor_name))
    total_transmission = float(fdtd.transmission(monitor_name))
    vectors = _try_gratingvector(fdtd, monitor_name)

    count = len(grating_fraction)
    rows: list[dict[str, object]] = []
    for index in range(count):
        vector = _vector_at(vectors, index)
        rows.append(
            {
                "K": K,
                "wavelength_nm": "",
                "supercell_period_nm": "",
                "target_angle_deg": "",
                "order_n": _value_at(order_n, index),
                "order_m": _value_at(order_m, index, default=0),
                "expected_theta_deg": "",
                "expected_ux": _value_at(ux, index),
                "expected_uy": _value_at(uy, index, default=0.0),
                "order_power_fraction_of_transmitted": grating_fraction[index],
                "total_transmission": total_transmission,
                "order_efficiency_source_norm": normalize_order_efficiency(float(grating_fraction[index]), total_transmission),
                "Ex_order_complex_real": vector[0].real if vector else "",
                "Ex_order_complex_imag": vector[0].imag if vector else "",
                "Ey_order_complex_real": vector[1].real if vector else "",
                "Ey_order_complex_imag": vector[1].imag if vector else "",
                "Ez_order_complex_real": vector[2].real if vector else "",
                "Ez_order_complex_imag": vector[2].imag if vector else "",
                "input_basis": "",
                "output_basis": "cartesian_vector_from_gratingvector",
                "target_channel": "future_order_resolved_alpha_beta",
                "notes": "extracted scaffold row; requires solved FDTD result",
            }
        )
    return rows


def write_diffraction_order_schema(rows: Iterable[dict[str, object]], path: Path) -> Path:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=APCD_DIFFRACTION_ORDER_FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in APCD_DIFFRACTION_ORDER_FIELDS} for row in rows)
    return path


def write_diffraction_order_extraction_plan(
    rows: list[dict[str, object]],
    path: Path,
) -> Path:
    if not rows:
        raise ValueError("Cannot write diffraction-order plan without rows")
    first = rows[0]
    K = int(first["K"])
    plus_row = next(row for row in rows if int(row["order_n"]) == 1)
    minus_row = next(row for row in rows if int(row["order_n"]) == -1)
    lines = [
        f"# APCD K={K} Diffraction-Order Extraction Plan",
        "",
        "## Current State",
        "",
        "- K=6/K=7 setup-only scaffold has been generated.",
        "- Dimer-level structure-group organization has been completed.",
        "- Phase 2.3A showed that a uniform scaffold is not equivalent to a +15 deg directional metagrating.",
        "- This file is not an optical result and no FDTD run was performed.",
        "- Current structure remains a scaffold only.",
        "",
        "## Stage Goal",
        "",
        "- Establish a grating-order extraction schema.",
        "- Prepare for later FDTD or RCWA result analysis.",
        "- Verify the diffraction-order sign convention.",
        "- Do not produce real optical efficiency conclusions in this stage.",
        "",
        "## Lumerical Basis",
        "",
        "- Ansys Lumerical FDTD grating projection commands can report grating-order direction and intensity for periodic structures.",
        "- `grating()` gives the power fraction in each order relative to transmitted power.",
        "- `transmission()` is needed with `grating()` to get source-normalized order efficiency.",
        "- `gratingn()`, `gratingm()`, `gratingu1()`, and `gratingu2()` identify order indices and direction unit-vector components.",
        "- `gratingvector()` and `gratingpolar()` are needed for later vector, polarization, phase, and order-resolved Jones analysis.",
        "- Do not use `grating()` alone to claim polarization-selective extraction.",
        "",
        "## Expected Order Mapping",
        "",
        f"- wavelength_nm: {first['wavelength_nm']}",
        f"- supercell_period_nm: {first['supercell_period_nm']}",
        f"- target_angle_deg: {first['target_angle_deg']}",
        f"- expected +1 theta_deg: {plus_row['expected_theta_deg']}",
        f"- expected -1 theta_deg: {minus_row['expected_theta_deg']}",
        "",
        "Lumerical order sign depends on +x/-x, monitor normal, and the u1/u2 convention. Plus-ramp or minus-ramp correspondence to GUI/FDTD +15 deg must be verified later by real diffraction-order extraction.",
        "",
        "## Output Metrics",
        "",
        "```text",
        "eta_order_source_norm = grating_fraction * total_transmission",
        "target_order_ER_dB = 10 log10(eta_alpha_to_target_order / eta_beta_to_target_order)",
        "spin_selective_directionality_ratio = eta_alpha_to_target_order / max(eta_alpha_to_other_orders + eta_beta_to_target_order, epsilon)",
        "```",
        "",
        "Final APCD metagrating evaluation must use the order-resolved target channel:",
        "",
        "```text",
        "t_{alpha*<-alpha}^{(m)}",
        "```",
        "",
        "Future real runs need x/y input-basis simulations, order-resolved Jones matrices, and conversion to input alpha/beta and output alpha*/beta* bases.",
        "",
        "Future metrics should include:",
        "",
        "- eta_alpha_to_target_order",
        "- eta_beta_to_target_order",
        "- target_order_ER_dB",
        "- eta_alpha_to_zero_order",
        "- eta_alpha_to_minus_order",
        "- spin_selective_directionality_ratio",
        "",
        "## Later Real-Run Route",
        "",
        "Step 1: run one small K=6 or K=7 uniform scaffold case only to validate extraction and order sign convention. Expected m=+/-1 orders should not be strong because the scaffold has no target-channel phase ramp.",
        "",
        "Step 2: design a dimer phase-state mechanism.",
        "",
        "Step 3: compare plus-ramp and minus-ramp candidates to identify which convention maps to +15 deg.",
        "",
        "## Explicit Non-Goals",
        "",
        "- Do not treat the current scaffold as the final metagrating.",
        "- Do not claim +15 deg steering.",
        "- Do not use total transmission alone.",
        "- Do not use only `grating()` to claim polarization-selective extraction.",
        "- Do not switch to TiO2 or 450 nm.",
        "- Do not do ML.",
        "- Do not do a large sweep.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_diffraction_dry_run_outputs(
    K: int,
    output_dir: Path,
    wavelength_nm: float = 633.0,
    target_angle_deg: float = 15.0,
) -> tuple[Path, Path, list[dict[str, object]]]:
    rows = build_expected_order_table(K, wavelength_nm=wavelength_nm, target_angle_deg=target_angle_deg)
    schema_path = write_diffraction_order_schema(rows, output_dir / "diffraction_order_schema.csv")
    plan_path = write_diffraction_order_extraction_plan(rows, output_dir / "diffraction_order_extraction_plan.md")
    return schema_path, plan_path, rows


def _try_gratingvector(fdtd: object, monitor_name: str) -> list[object] | None:
    if not hasattr(fdtd, "gratingvector"):
        return None
    try:
        return _as_list(fdtd.gratingvector(monitor_name))
    except Exception:
        return None


def _vector_at(vectors: list[object] | None, index: int) -> tuple[complex, complex, complex] | None:
    if vectors is None or index >= len(vectors):
        return None
    vector = vectors[index]
    if isinstance(vector, (list, tuple)) and len(vector) >= 3:
        return (complex(vector[0]), complex(vector[1]), complex(vector[2]))
    return None


def _as_list(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    try:
        import numpy as np

        if isinstance(value, np.ndarray):
            return list(value.ravel())
    except Exception:
        pass
    return [value]


def _value_at(values: list[object], index: int, default: object = "") -> object:
    return values[index] if index < len(values) else default


def _find_metric(rows: list[dict[str, object]], name: str) -> object:
    for row in rows:
        if row.get("metric") == name:
            return row.get("value", 0)
    return 0


def _float_or_zero(value: object) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0
