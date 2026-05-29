from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Iterable


APCD_PHASE_STATE_LIBRARY_FIELDS = [
    "K",
    "phase_state_index",
    "phase_target_deg",
    "phase_target_rad",
    "ramp_sign",
    "geometry_variant_id",
    "source_geometry",
    "pillar_1_length_nm",
    "pillar_1_width_nm",
    "pillar_1_rotation_deg",
    "pillar_2_length_nm",
    "pillar_2_width_nm",
    "pillar_2_rotation_deg",
    "pillar_1_dx_nm",
    "pillar_1_dy_nm",
    "pillar_2_dx_nm",
    "pillar_2_dy_nm",
    "dimer_dx_nm",
    "dimer_dy_nm",
    "t_alpha_star_from_alpha_real",
    "t_alpha_star_from_alpha_imag",
    "t_alpha_star_from_alpha_abs",
    "t_alpha_star_from_alpha_phase_deg",
    "target_conversion",
    "t_beta_star_from_alpha_abs",
    "t_alpha_star_from_beta_abs",
    "t_beta_star_from_beta_abs",
    "beta_to_target_leakage",
    "beta_total_leakage",
    "phase_error_deg",
    "amplitude_pass",
    "leakage_pass",
    "phase_pass",
    "overall_pass",
    "notes",
]


DEFAULT_PHASE_STATE_THRESHOLDS = {
    "target_conversion_early": 0.5,
    "target_conversion_strong": 0.7,
    "beta_to_target_leakage_max": 0.1,
    "beta_total_leakage_max": 0.2,
    "target_to_beta_ratio_min": 6.0,
    "phase_error_early_deg": 20.0,
    "phase_error_strong_deg": 10.0,
    "eps": 1.0e-12,
}


DEFAULT_ALPHA_PASS_GEOMETRY = {
    "source_geometry": "configs/apcd_fig2_elliptical_633nm_alpha_pass.yaml",
    "pillar_1_length_nm": 130.0,
    "pillar_1_width_nm": 70.0,
    "pillar_1_rotation_deg": 67.5,
    "pillar_2_length_nm": 85.0,
    "pillar_2_width_nm": 150.0,
    "pillar_2_rotation_deg": 112.5,
}


def build_k6_phase_targets(ramp_sign: str) -> list[float]:
    sign = _normalize_ramp_sign(ramp_sign)
    values = [60.0 * index for index in range(6)]
    if sign == "minus":
        return [0.0 if index == 0 else -value for index, value in enumerate(values)]
    return values


def wrap_phase_deg(angle: float, convention: str = "minus180_180") -> float:
    if convention == "minus180_180":
        return ((float(angle) + 180.0) % 360.0) - 180.0
    if convention == "0_360":
        return float(angle) % 360.0
    raise ValueError(f"Unsupported phase convention: {convention}")


def phase_error_deg(measured: float, target: float) -> float:
    return abs(wrap_phase_deg(float(measured) - float(target), convention="minus180_180"))


def compute_phase_state_metrics(
    *,
    t_alpha_star_from_alpha: complex,
    t_beta_star_from_alpha: complex = 0 + 0j,
    t_alpha_star_from_beta: complex = 0 + 0j,
    t_beta_star_from_beta: complex = 0 + 0j,
    phase_target_deg: float,
    eps: float = 1.0e-12,
) -> dict[str, float]:
    target_abs = abs(t_alpha_star_from_alpha)
    target_phase_deg = wrap_phase_deg(math.degrees(math.atan2(t_alpha_star_from_alpha.imag, t_alpha_star_from_alpha.real)))
    target_conversion = target_abs**2
    beta_to_target_leakage = abs(t_alpha_star_from_beta) ** 2
    beta_total_leakage = beta_to_target_leakage + abs(t_beta_star_from_beta) ** 2
    return {
        "t_alpha_star_from_alpha_real": t_alpha_star_from_alpha.real,
        "t_alpha_star_from_alpha_imag": t_alpha_star_from_alpha.imag,
        "t_alpha_star_from_alpha_abs": target_abs,
        "t_alpha_star_from_alpha_phase_deg": target_phase_deg,
        "target_conversion": target_conversion,
        "t_beta_star_from_alpha_abs": abs(t_beta_star_from_alpha),
        "t_alpha_star_from_beta_abs": abs(t_alpha_star_from_beta),
        "t_beta_star_from_beta_abs": abs(t_beta_star_from_beta),
        "beta_to_target_leakage": beta_to_target_leakage,
        "beta_total_leakage": beta_total_leakage,
        "target_to_beta_ratio": target_conversion / max(beta_to_target_leakage, eps),
        "phase_error_deg": phase_error_deg(target_phase_deg, phase_target_deg),
    }


def evaluate_phase_state_pass_fail(
    metrics: dict[str, float],
    thresholds: dict[str, float] | None = None,
    *,
    strength: str = "early",
) -> dict[str, bool]:
    limits = dict(DEFAULT_PHASE_STATE_THRESHOLDS)
    if thresholds:
        limits.update(thresholds)
    if strength not in {"early", "strong"}:
        raise ValueError("strength must be 'early' or 'strong'")

    target_key = "target_conversion_strong" if strength == "strong" else "target_conversion_early"
    phase_key = "phase_error_strong_deg" if strength == "strong" else "phase_error_early_deg"

    amplitude_pass = float(metrics["target_conversion"]) >= limits[target_key]
    leakage_pass = (
        float(metrics["beta_to_target_leakage"]) <= limits["beta_to_target_leakage_max"]
        and float(metrics["beta_total_leakage"]) <= limits["beta_total_leakage_max"]
        and float(metrics["target_to_beta_ratio"]) >= limits["target_to_beta_ratio_min"]
    )
    phase_pass = float(metrics["phase_error_deg"]) <= limits[phase_key]
    return {
        "amplitude_pass": amplitude_pass,
        "leakage_pass": leakage_pass,
        "phase_pass": phase_pass,
        "overall_pass": amplitude_pass and leakage_pass and phase_pass,
    }


def build_phase_state_schema_rows(
    *,
    K: int = 6,
    ramp_signs: Iterable[str] = ("plus", "minus"),
    geometry: dict[str, object] | None = None,
    phase_convention: str = "minus180_180",
) -> list[dict[str, object]]:
    if K != 6:
        raise ValueError("Phase 08 schema scaffold currently supports K=6 only")

    geometry_values = dict(DEFAULT_ALPHA_PASS_GEOMETRY)
    if geometry:
        geometry_values.update(geometry)

    rows: list[dict[str, object]] = []
    for ramp_sign in ramp_signs:
        normalized_sign = _normalize_ramp_sign(ramp_sign)
        for index, target_deg in enumerate(build_k6_phase_targets(normalized_sign)):
            wrapped_target_deg = wrap_phase_deg(target_deg, convention=phase_convention)
            row = {field: math.nan for field in APCD_PHASE_STATE_LIBRARY_FIELDS}
            row.update(
                {
                    "K": K,
                    "phase_state_index": index,
                    "phase_target_deg": wrapped_target_deg,
                    "phase_target_rad": math.radians(wrapped_target_deg),
                    "ramp_sign": normalized_sign,
                    "geometry_variant_id": f"k6_{normalized_sign}_state_{index}_schema_only",
                    "source_geometry": geometry_values["source_geometry"],
                    "pillar_1_length_nm": geometry_values["pillar_1_length_nm"],
                    "pillar_1_width_nm": geometry_values["pillar_1_width_nm"],
                    "pillar_1_rotation_deg": geometry_values["pillar_1_rotation_deg"],
                    "pillar_2_length_nm": geometry_values["pillar_2_length_nm"],
                    "pillar_2_width_nm": geometry_values["pillar_2_width_nm"],
                    "pillar_2_rotation_deg": geometry_values["pillar_2_rotation_deg"],
                    "pillar_1_dx_nm": 0.0,
                    "pillar_1_dy_nm": 0.0,
                    "pillar_2_dx_nm": 0.0,
                    "pillar_2_dy_nm": 0.0,
                    "dimer_dx_nm": 0.0,
                    "dimer_dy_nm": 0.0,
                    "amplitude_pass": "",
                    "leakage_pass": "",
                    "phase_pass": "",
                    "overall_pass": "",
                    "notes": (
                        "dry-run schema row; NaN optical fields; no FDTD run; "
                        "schema only; not a steering result"
                    ),
                }
            )
            rows.append(row)
    return rows


def write_phase_state_library_schema(rows: Iterable[dict[str, object]], path: Path) -> Path:
    row_list = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=APCD_PHASE_STATE_LIBRARY_FIELDS)
        writer.writeheader()
        writer.writerows(
            {field: row.get(field, math.nan) for field in APCD_PHASE_STATE_LIBRARY_FIELDS}
            for row in row_list
        )
    return path


def write_phase_state_pass_fail_criteria(path: Path) -> Path:
    lines = [
        "# APCD K=6 Phase-State Library Pass/Fail Criteria",
        "",
        "## Scope",
        "",
        "This file defines the Phase 08 initial engineering schema and pass/fail criteria for a future K=6 dimer-level phase-state candidate library.",
        "",
        "No FDTD run was performed.",
        "",
        "This is schema only, not a steering result.",
        "",
        "There is currently no real phase-state candidate library.",
        "",
        "The schema prepares later candidate dimer evaluation; it does not prove a true APCD directional metagrating.",
        "",
        "## Phase Convention",
        "",
        "The dry-run CSV uses the `[-180, 180)` wrapped convention for `phase_target_deg` and `t_alpha_star_from_alpha_phase_deg`.",
        "",
        "The plus ramp before wrapping is:",
        "",
        "```text",
        "0, 60, 120, 180, 240, 300 deg",
        "```",
        "",
        "With `[-180, 180)` wrapping this is stored as:",
        "",
        "```text",
        "0, 60, 120, -180, -120, -60 deg",
        "```",
        "",
        "The minus ramp is:",
        "",
        "```text",
        "0, -60, -120, -180, -240, -300 deg",
        "```",
        "",
        "With `[-180, 180)` wrapping this is stored as:",
        "",
        "```text",
        "0, -60, -120, -180, 120, 60 deg",
        "```",
        "",
        "Phase error is the absolute shortest wrapped difference in degrees.",
        "",
        "## Target Channel",
        "",
        "The phase target applies to the APCD target channel:",
        "",
        "```text",
        "t_{alpha*<-alpha}",
        "```",
        "",
        "It is not an ordinary x/y phase target.",
        "",
        "All pass/fail checks must be based on the `alpha/beta -> alpha*/beta*` basis.",
        "",
        "Do not judge success from total T alone.",
        "",
        "Do not judge success from `grating()` power alone.",
        "",
        "The uniform scaffold's 0th-order result cannot be reused as six phase states.",
        "",
        "## Initial Engineering Thresholds",
        "",
        "These are Phase 08 initial engineering thresholds, not final paper metrics.",
        "",
        "| Metric | Early acceptable | Strong candidate |",
        "|---|---:|---:|",
        "| `target_conversion` | `>= 0.5` | `>= 0.7` |",
        "| `beta_to_target_leakage` | `<= 0.1` | `<= 0.1` |",
        "| `beta_total_leakage` | `<= 0.2` | `<= 0.2` |",
        "| `target_to_beta_ratio` | `>= 6` | `>= 6` |",
        "| `phase_error_deg` | `<= 20 deg` | `<= 10 deg` |",
        "",
        "Definitions:",
        "",
        "```text",
        "target_conversion = |t_{alpha*<-alpha}|^2",
        "beta_to_target_leakage = |t_{alpha*<-beta}|^2",
        "beta_total_leakage = |t_{alpha*<-beta}|^2 + |t_{beta*<-beta}|^2",
        "target_to_beta_ratio = target_conversion / max(beta_to_target_leakage, eps)",
        "```",
        "",
        "## Physical Boundaries",
        "",
        "- Global rotation may change the allowed alpha state and should not be the default phase knob.",
        "- APCD here must not be treated as an ordinary PB half-wave-plate design.",
        "- The original beta-selective pillar 2 geometry `150 x 85 nm` must not enter the candidate library baseline.",
        "- The baseline remains pillar 1 `130 x 70 nm`, rotation `67.5 deg`; pillar 2 `85 x 150 nm`, rotation `112.5 deg`.",
        "- K means dimer count. K=6 means 6 dimers and 12 nanopillars.",
        "- Do not switch to K=7, TiO2/450 nm, ML, large sweeps, or phase-ramp supercell assembly in this schema step.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def write_phase_state_dry_run_outputs(output_dir: Path) -> tuple[Path, Path, list[dict[str, object]]]:
    rows = build_phase_state_schema_rows(K=6, ramp_signs=("plus", "minus"))
    schema_path = write_phase_state_library_schema(rows, output_dir / "phase_state_library_schema.csv")
    criteria_path = write_phase_state_pass_fail_criteria(output_dir / "phase_state_pass_fail_criteria.md")
    return schema_path, criteria_path, rows


def _normalize_ramp_sign(ramp_sign: str) -> str:
    value = str(ramp_sign).lower()
    if value in {"plus", "+", "+1", "1"}:
        return "plus"
    if value in {"minus", "-", "-1"}:
        return "minus"
    raise ValueError("ramp_sign must be plus or minus")
