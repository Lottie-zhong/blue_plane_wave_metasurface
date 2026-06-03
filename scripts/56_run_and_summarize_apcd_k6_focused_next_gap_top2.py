from __future__ import annotations

import argparse
import cmath
import csv
import math
import sys
from pathlib import Path
from typing import Iterable, Sequence

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_active_learning import wrap_phase_deg  # noqa: E402
from metasurface.config import load_apcd_single_dimer_config  # noqa: E402


BASELINE_PHASE_DEG = 111.31665091018952
TOP2_IDS = ["focus_zero_leakred_07", "focus_neg60_geom_04"]
SKIPPED_IDS = ["focus_neg120_asym_03", "focus_pi_wrap_04"]
DEFAULT_SELECTION_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/focused_next_gap_fdtd_selection_v3.csv"
DEFAULT_POOL_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/focused_next_gap_candidate_pool_v3.csv"
DEFAULT_CONFIG_DIR = REPO_ROOT / "configs/apcd_k6_phase_state_candidates"
DEFAULT_OUTPUT_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/focused_next_gap_top2_fdtd_results_v3.csv"
DEFAULT_SUMMARY = REPO_ROOT / "outputs/apcd_k6_active_learning/focused_next_gap_top2_fdtd_results_v3_summary.md"
DEFAULT_REPORT = REPO_ROOT / "reports/apcd_k6_focused_next_gap_top2_fdtd_result_note.md"

FOCUSED_NEXT_GAP_TOP2_RESULT_FIELDS = [
    "candidate_id",
    "target_bin_deg",
    "candidate_family",
    "status",
    "phase_deg",
    "phase_error_to_target_deg",
    "target_conversion",
    "opposite_spin_leakage",
    "conversion_to_leakage_ratio",
    "PD",
    "total_transmission",
    "t_alpha_star_from_alpha",
    "phase_shift_vs_baseline_deg",
    "early_target_pass",
    "early_leakage_pass",
    "early_ratio_pass",
    "early_pass",
    "target_bin_pass",
    "target_bin_status",
    "notes",
]

P26_REAL_FDTD_VALUES: list[dict[str, object]] = [
    {
        "candidate_id": "focus_zero_leakred_07",
        "target_bin_deg": 0.0,
        "candidate_family": "zero_bin_leakage_reduction",
        "status": "ok",
        "target_conversion": 0.5327046775079014,
        "opposite_spin_leakage": 0.469513841744978,
        "conversion_to_leakage_ratio": 1.1345878015607294,
        "PD": 0.0630509560030551,
        "total_transmission": 0.5011092596264398,
        "t_alpha_star_from_alpha": "0.4570326202099825+0.269587846215615j",
        "source_result_csv": "outputs/apcd_k6_metagrating_633nm/phase_state_candidates/focus_zero_leakred_07/results.csv",
    },
    {
        "candidate_id": "focus_neg60_geom_04",
        "target_bin_deg": -60.0,
        "candidate_family": "negative_phase_redesign",
        "status": "ok",
        "target_conversion": 0.8929435782636037,
        "opposite_spin_leakage": 0.08113267089413602,
        "conversion_to_leakage_ratio": 11.00596798321521,
        "PD": 0.8334161807872716,
        "total_transmission": 0.48703812457886997,
        "t_alpha_star_from_alpha": "0.1104947046307901+0.9176371519300808j",
        "source_result_csv": "outputs/apcd_k6_metagrating_633nm/phase_state_candidates/focus_neg60_geom_04/results.csv",
    },
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare and summarize APCD K=6 focused next-gap top-2 candidates.")
    parser.add_argument("--write-configs", action="store_true", help="Write top-2 YAML configs only.")
    parser.add_argument("--summarize", action="store_true", help="Write result CSV, summary, and report from recorded P26 values.")
    parser.add_argument("--dry-run", action="store_true", help="Validate configs locally without FDTD/lumapi.")
    parser.add_argument("--check-only", action="store_true", help="Validate existing configs without writing YAML.")
    parser.add_argument("--selection-csv", type=Path, default=DEFAULT_SELECTION_CSV)
    parser.add_argument("--pool-csv", type=Path, default=DEFAULT_POOL_CSV)
    parser.add_argument("--config-dir", type=Path, default=DEFAULT_CONFIG_DIR)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.write_configs or args.check_only:
        selection_rows = read_csv_rows(args.selection_csv)
        pool_rows = read_csv_rows(args.pool_csv)
        top2_rows = top2_candidate_rows(selection_rows, pool_rows)
        if args.check_only:
            config_paths = [args.config_dir / f"{row['candidate_id']}.yaml" for row in top2_rows]
        else:
            config_paths = write_top2_configs(top2_rows, args.config_dir)
        validation_rows = validate_top2_configs(config_paths, top2_rows) if args.dry_run or args.check_only else []
        print(f"top2_candidate_ids={[row['candidate_id'] for row in top2_rows]}")
        print(f"configs={','.join(str(path) for path in config_paths)}")
        print(f"skipped_selected_candidate_ids={SKIPPED_IDS}")
        if validation_rows:
            print(f"dry_run_validation_pass={all(row['validation_pass'] for row in validation_rows)}")
        print("status=focused_top2_config_prepare_only_no_fdtd_no_lumapi_no_fsp_no_results_not_steering_result")
        return 0

    if args.summarize:
        if not P26_REAL_FDTD_VALUES:
            raise ValueError("P26_REAL_FDTD_VALUES is empty; record real FDTD values before summarizing.")
        rows = [result_row_from_values(**values) for values in P26_REAL_FDTD_VALUES]
        write_result_csv(rows, args.output_csv)
        write_summary_md(rows, args.summary)
        write_report_md(rows, args.report)
        print(f"result_csv={args.output_csv}")
        print(f"summary={args.summary}")
        print(f"report={args.report}")
        print(f"candidate_ids={[row['candidate_id'] for row in rows]}")
        print("status=summary_only_after_focused_top2_real_fdtd_no_extra_fdtd_no_k7_no_phase_ramp_no_training_not_steering_result")
        return 0

    print("No action requested. Use --write-configs or --summarize.")
    return 0


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def top2_candidate_rows(
    selection_rows: Iterable[dict[str, str]],
    pool_rows: Iterable[dict[str, str]],
    top2_ids: Sequence[str] = TOP2_IDS,
) -> list[dict[str, str]]:
    selected_by_rank = sorted(selection_rows, key=lambda row: int(row["selection_rank"]))
    actual_top2 = [row["candidate_id"] for row in selected_by_rank[:2]]
    if actual_top2 != list(top2_ids):
        raise ValueError(f"unexpected focused top-2 selection: {actual_top2}")
    skipped = [row["candidate_id"] for row in selected_by_rank[2:]]
    if skipped != SKIPPED_IDS:
        raise ValueError(f"unexpected skipped selected candidates: {skipped}")
    pool_by_id = {row["candidate_id"]: row for row in pool_rows}
    missing = [candidate_id for candidate_id in top2_ids if candidate_id not in pool_by_id]
    if missing:
        raise ValueError(f"focused top-2 candidates missing from pool: {missing}")
    return [pool_by_id[candidate_id] for candidate_id in top2_ids]


def write_top2_configs(candidate_rows: Sequence[dict[str, str]], config_dir: str | Path) -> list[Path]:
    output_dir = Path(config_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for row in candidate_rows:
        path = output_dir / f"{row['candidate_id']}.yaml"
        path.write_text(build_focused_next_gap_candidate_config(row), encoding="utf-8")
        paths.append(path)
    return paths


def build_focused_next_gap_candidate_config(candidate: dict[str, str]) -> str:
    period_x = float(candidate["period_x_nm"])
    period_y = float(candidate["period_y_nm"])
    p1_frac_x = float(candidate["p1_frac_x"])
    p1_frac_y = float(candidate["p1_frac_y"])
    p2_frac_x = float(candidate["p2_frac_x"])
    p2_frac_y = float(candidate["p2_frac_y"])
    internal_dx = float(candidate["internal_dx_nm"])
    internal_dy = float(candidate["internal_dy_nm"])
    p1_x = (p1_frac_x - 0.5) * period_x + internal_dx / 2.0
    p1_y = (p1_frac_y - 0.5) * period_y + internal_dy / 2.0
    p2_x = (p2_frac_x - 0.5) * period_x - internal_dx / 2.0
    p2_y = (p2_frac_y - 0.5) * period_y - internal_dy / 2.0
    data = {
        "project": {
            "name": "blue_plane_wave_metasurface",
            "stage": "09_p26_apcd_k6_focused_next_gap_top2_real_eval",
        },
        "candidate": {
            "variant_id": candidate["candidate_id"],
            "candidate_type": candidate["candidate_family"],
            "description": "focused next-gap selected top-2 candidate",
            "target_bin_deg": _number(candidate["target_bin_deg"]),
            "source_stage": candidate["source_stage"],
            "anchor_candidate": candidate["anchor_candidate"],
            "risk_level": candidate["risk_level"],
            "design_rationale": candidate["design_rationale"],
            "source_pool_csv": "outputs/apcd_k6_active_learning/focused_next_gap_candidate_pool_v3.csv",
            "source_selection_csv": "outputs/apcd_k6_active_learning/focused_next_gap_fdtd_selection_v3.csv",
            "notes": "09-P26 generated config for focused top-2 only; no config generated for selected ranks 3-4.",
        },
        "boundary": {
            "no_k7": True,
            "not_phase_ramp_supercell": True,
            "not_steering_result": True,
        },
        "target": {
            "wavelength_nm": 633,
            "incident_wave": "plane_wave",
            "output_basis": "alpha_beta",
            "target_polarization_type": "elliptical",
            "psi_deg": 112.5,
            "chi_deg": 22.5,
            "eps": 1.0e-12,
            "spin_er_threshold_db": 8,
            "conversion_to_leakage_threshold": 6,
        },
        "material": {
            "substrate": "Al2O3",
            "meta_material": "c-Si",
            "substrate_material_lumerical": "<Object defined dielectric>",
            "meta_material_lumerical": "<Object defined dielectric>",
            "substrate_index": 1.76,
            "meta_index": 3.88,
        },
        "geometry": {
            "layout_mode": "manual_absolute",
            "period_x_nm": _number(period_x),
            "period_y_nm": _number(period_y),
            "height_nm": _number(candidate["height_nm"]),
            "minimum_gap_nm": 5,
            "nanopillar_1": {
                "length_nm": _number(candidate["p1_length_nm"]),
                "width_nm": _number(candidate["p1_width_nm"]),
                "rotation_deg": _number(candidate["p1_rotation_deg"]),
                "x_nm": _number(p1_x),
                "y_nm": _number(p1_y),
                "frac_x": _number(p1_frac_x),
                "frac_y": _number(p1_frac_y),
            },
            "nanopillar_2": {
                "length_nm": _number(candidate["p2_length_nm"]),
                "width_nm": _number(candidate["p2_width_nm"]),
                "rotation_deg": _number(candidate["p2_rotation_deg"]),
                "x_nm": _number(p2_x),
                "y_nm": _number(p2_y),
                "frac_x": _number(p2_frac_x),
                "frac_y": _number(p2_frac_y),
            },
        },
        "simulation": {
            "substrate_thickness_nm": 220,
            "source_offset_nm": 120,
            "monitor_offset_nm": 180,
            "z_padding_above_nm": 260,
            "mesh_accuracy": 1,
            "simulation_time_fs": 250,
        },
        "output": {
            "result_dir": f"outputs/apcd_k6_metagrating_633nm/phase_state_candidates/{candidate['candidate_id']}",
        },
    }
    return yaml.safe_dump(data, sort_keys=False)


def validate_top2_configs(config_paths: Sequence[str | Path], candidate_rows: Sequence[dict[str, str]]) -> list[dict[str, object]]:
    candidate_by_id = {row["candidate_id"]: row for row in candidate_rows}
    rows = []
    for config_path in config_paths:
        path = Path(config_path)
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        candidate_id = str(data["candidate"]["variant_id"])
        expected = candidate_by_id[candidate_id]
        config = load_apcd_single_dimer_config(path)
        checks = [
            candidate_id in TOP2_IDS,
            data["candidate"]["target_bin_deg"] == _number(expected["target_bin_deg"]),
            data["candidate"]["source_stage"] == expected["source_stage"],
            data["candidate"]["risk_level"] == expected["risk_level"],
            config.geometry.nanopillar_1.length_nm == float(expected["p1_length_nm"]),
            config.geometry.nanopillar_1.width_nm == float(expected["p1_width_nm"]),
            config.geometry.nanopillar_2.length_nm == float(expected["p2_length_nm"]),
            config.geometry.nanopillar_2.width_nm == float(expected["p2_width_nm"]),
            config.geometry.nanopillar_1.rotation_deg == float(expected["p1_rotation_deg"]),
            config.geometry.nanopillar_2.rotation_deg == float(expected["p2_rotation_deg"]),
            config.output.result_dir.as_posix().endswith(f"/{candidate_id}"),
        ]
        rows.append(
            {
                "candidate_id": candidate_id,
                "config_path": str(path),
                "validation_pass": all(checks),
                "notes": "local config load/dry-run validation only; no FDTD/lumapi/.fsp/results",
            }
        )
    return rows


def result_row_from_values(
    *,
    candidate_id: str,
    target_bin_deg: float,
    candidate_family: str,
    status: str,
    target_conversion: float,
    opposite_spin_leakage: float,
    conversion_to_leakage_ratio: float,
    PD: float,
    total_transmission: float,
    t_alpha_star_from_alpha: str,
    source_result_csv: str = "",
) -> dict[str, object]:
    phase = phase_deg_from_complex(t_alpha_star_from_alpha)
    error = angular_distance_deg(phase, target_bin_deg)
    early_target = float(target_conversion) >= 0.5
    early_leakage = float(opposite_spin_leakage) <= 0.2
    early_ratio = float(conversion_to_leakage_ratio) >= 6.0
    early = early_target and early_leakage and early_ratio
    bin_status = target_bin_status(error, early, status)
    return {
        "candidate_id": candidate_id,
        "target_bin_deg": _number(target_bin_deg),
        "candidate_family": candidate_family,
        "status": status,
        "phase_deg": phase,
        "phase_error_to_target_deg": error,
        "target_conversion": target_conversion,
        "opposite_spin_leakage": opposite_spin_leakage,
        "conversion_to_leakage_ratio": conversion_to_leakage_ratio,
        "PD": PD,
        "total_transmission": total_transmission,
        "t_alpha_star_from_alpha": t_alpha_star_from_alpha,
        "phase_shift_vs_baseline_deg": wrap_phase_deg(phase - BASELINE_PHASE_DEG),
        "early_target_pass": early_target,
        "early_leakage_pass": early_leakage,
        "early_ratio_pass": early_ratio,
        "early_pass": early,
        "target_bin_pass": bin_status in {"strong_covered", "early_covered"},
        "target_bin_status": bin_status,
        "notes": _notes(candidate_id, target_bin_deg, bin_status, early, error, source_result_csv),
    }


def phase_deg_from_complex(value: str) -> float:
    return wrap_phase_deg(math.degrees(cmath.phase(complex(value))))


def angular_distance_deg(phase_deg: float, target_deg: float) -> float:
    return abs(wrap_phase_deg(float(phase_deg) - float(target_deg)))


def target_bin_status(phase_error_deg: float, early_pass: bool, status: str = "ok") -> str:
    if status != "ok":
        return "failed"
    if early_pass and phase_error_deg <= 10.0:
        return "strong_covered"
    if early_pass and phase_error_deg <= 20.0:
        return "early_covered"
    if early_pass and phase_error_deg <= 35.0:
        return "near_but_not_covered"
    if phase_error_deg <= 35.0:
        return "evidence_only"
    return "open_gap"


def write_result_csv(rows: Iterable[dict[str, object]], path: str | Path) -> Path:
    row_list = list(rows)
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FOCUSED_NEXT_GAP_TOP2_RESULT_FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in FOCUSED_NEXT_GAP_TOP2_RESULT_FIELDS} for row in row_list)
    return output_path


def write_summary_md(rows: Iterable[dict[str, object]], path: str | Path) -> Path:
    row_list = list(rows)
    lines = [
        "# APCD K=6 Focused Next-Gap Top-2 FDTD Results v3 Summary",
        "",
        "Scope: 09-P26 summary after running only `focus_zero_leakred_07` and `focus_neg60_geom_04`. No other focused or old-pool candidate was run.",
        "",
        "| candidate_id | target bin deg | phase deg | error deg | leakage | ratio | early pass | target bin status |",
        "|---|---:|---:|---:|---:|---:|---|---|",
        *[
            f"| `{row['candidate_id']}` | {row['target_bin_deg']} | {row['phase_deg']} | {row['phase_error_to_target_deg']} | "
            f"{row['opposite_spin_leakage']} | {row['conversion_to_leakage_ratio']} | {row['early_pass']} | {row['target_bin_status']} |"
            for row in row_list
        ],
        "",
        "No raw `results.csv`, `.fsp`, `pre_run_X.fsp`, or `pre_run_Y.fsp` files are included in this summary output.",
    ]
    return _write_text(path, lines)


def write_report_md(rows: Iterable[dict[str, object]], path: str | Path) -> Path:
    row_list = list(rows)
    by_id = {str(row["candidate_id"]): row for row in row_list}
    zero = by_id["focus_zero_leakred_07"]
    neg60 = by_id["focus_neg60_geom_04"]
    zero_success = bool(zero["early_pass"]) and str(zero["target_bin_status"]) in {"strong_covered", "early_covered"}
    neg60_success = bool(neg60["early_pass"]) and str(neg60["target_bin_status"]) in {"strong_covered", "early_covered"}
    lines = [
        "# APCD K=6 Focused Next-Gap Top-2 FDTD Result Note",
        "",
        "## Scope",
        "",
        "This is 09-P26. Only `focus_zero_leakred_07` and `focus_neg60_geom_04` were prepared and run with real FDTD.",
        "",
        "`focus_neg120_asym_03`, `focus_pi_wrap_04`, the full 40-row focused pool, and all old pools were not run. No K=7, phase-ramp supercell, TiO2/450 nm, Micro-LED, DenseNet, or cVAE work was done. This is not a +15 deg steering result and does not complete the K=6 phase-state library.",
        "",
        "## Results",
        "",
        "| candidate | target bin | phase deg | error deg | target conversion | leakage | ratio | PD | early pass | target bin status |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|---|",
        *[
            f"| `{row['candidate_id']}` | {row['target_bin_deg']} | {row['phase_deg']} | {row['phase_error_to_target_deg']} | "
            f"{row['target_conversion']} | {row['opposite_spin_leakage']} | {row['conversion_to_leakage_ratio']} | "
            f"{row['PD']} | {row['early_pass']} | {row['target_bin_status']} |"
            for row in row_list
        ],
        "",
        "## Interpretation",
        "",
        f"`focus_zero_leakred_07` target-bin success: {zero_success}. Its leakage should be compared with `next_zero_rot_anchor_03` leakage 0.45007533270235894 to judge whether zero-bin leakage reduction worked.",
        "",
        f"`focus_neg60_geom_04` target-bin success: {neg60_success}. This tests whether geometry-driven negative-phase redesign improves over the failed rotation-assisted `next_rot_anchor_04` result.",
        "",
        "If a candidate is phase-near but fails leakage/ratio, it is only evidence_only. If it is early-pass but far from target, it is usable-but-not-target and does not close the major gap.",
        "",
        "## Next Step",
        "",
        "Update dataset/coverage with these two rows before running any backup. Do not run the full focused pool.",
    ]
    return _write_text(path, lines)


def _notes(candidate_id: str, target_bin_deg: float, bin_status: str, early: bool, error: float, source_result_csv: str) -> str:
    pieces = [
        "09-P26 real FDTD focused top-2 only",
        f"target bin {target_bin_deg:g} deg",
        f"wrapped phase error {error:.6g} deg",
        f"target_bin_status={bin_status}",
        "early pass" if early else "not early pass",
    ]
    if source_result_csv:
        pieces.append(f"source raw result path not committed: {source_result_csv}")
    pieces.append("not a steering result")
    return "; ".join(pieces)


def _write_text(path: str | Path, lines: Sequence[str]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def _number(value: object) -> int | float:
    number = float(value)
    return int(number) if number.is_integer() else number


if __name__ == "__main__":
    raise SystemExit(main())
