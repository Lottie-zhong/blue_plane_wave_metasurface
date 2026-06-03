from __future__ import annotations

import argparse
import cmath
import csv
import math
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_active_learning import wrap_phase_deg  # noqa: E402
from metasurface.apcd_phase_lowering_candidates import (  # noqa: E402
    PHASE_COVERAGE_V4_FIELDS,
    analyze_phase_coverage_v4,
    classify_phase_region,
    write_csv_rows,
)
from metasurface.config import load_apcd_single_dimer_config  # noqa: E402


BASELINE_PHASE_DEG = 111.31665091018952
SELECTED_IDS = ["pl_zero_bridge_04", "pl_neg60_focus_push_05", "pl_neg120_aspect_03", "pl_pi_wrap_04"]
TOP2_IDS = ["pl_zero_bridge_04", "pl_neg60_focus_push_05"]
BACKUP_IDS = ["pl_neg120_aspect_03", "pl_pi_wrap_04"]

DEFAULT_SELECTION_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_lowering_fdtd_selection_v4.csv"
DEFAULT_POOL_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_lowering_candidate_pool_v4.csv"
DEFAULT_DATASET_V4 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v4.csv"
DEFAULT_CONFIG_DIR = REPO_ROOT / "configs/apcd_k6_phase_state_candidates"
DEFAULT_RUNTIME = REPO_ROOT / "configs/runtime.yaml"
DEFAULT_RESULTS_CSV = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_lowering_selected_fdtd_results_v4.csv"
DEFAULT_DATASET_V5 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v5.csv"
DEFAULT_DATASET_REPORT = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v5_collection_report.md"
DEFAULT_COVERAGE_V5 = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_coverage_v5.csv"
DEFAULT_GAP_ANALYSIS_V5 = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_gap_analysis_v5.md"
DEFAULT_READINESS_V5 = REPO_ROOT / "outputs/apcd_k6_active_learning/k6_phase_state_readiness_v5.md"
DEFAULT_REPORT = REPO_ROOT / "reports/apcd_k6_phase_lowering_selected_fdtd_and_coverage_v5_note.md"

RESULT_FIELDS = [
    "candidate_id",
    "target_bin_deg",
    "candidate_family",
    "run_status",
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
    "source_result_csv",
    "notes",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run and summarize APCD K=6 phase-lowering selected candidates.")
    parser.add_argument("--prepare-configs", action="store_true", help="Write YAML configs for all four selected candidates.")
    parser.add_argument("--dry-run", action="store_true", help="Validate configs without FDTD/lumapi/.fsp.")
    parser.add_argument("--run-top2", action="store_true", help="Run only the two top-ranked selected candidates.")
    parser.add_argument("--run-backups", action="store_true", help="Run backup candidates after top-2 are available.")
    parser.add_argument("--summarize", action="store_true", help="Summarize available raw results into v5 outputs.")
    parser.add_argument("--selection-csv", type=Path, default=DEFAULT_SELECTION_CSV)
    parser.add_argument("--pool-csv", type=Path, default=DEFAULT_POOL_CSV)
    parser.add_argument("--dataset-v4", type=Path, default=DEFAULT_DATASET_V4)
    parser.add_argument("--config-dir", type=Path, default=DEFAULT_CONFIG_DIR)
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--results-csv", type=Path, default=DEFAULT_RESULTS_CSV)
    parser.add_argument("--dataset-v5", type=Path, default=DEFAULT_DATASET_V5)
    parser.add_argument("--dataset-report", type=Path, default=DEFAULT_DATASET_REPORT)
    parser.add_argument("--coverage-v5", type=Path, default=DEFAULT_COVERAGE_V5)
    parser.add_argument("--gap-analysis-v5", type=Path, default=DEFAULT_GAP_ANALYSIS_V5)
    parser.add_argument("--readiness-v5", type=Path, default=DEFAULT_READINESS_V5)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--python", default=sys.executable, help="Python executable for scripts/13_run_apcd_single_dimer.py.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    selected_rows = selected_candidate_rows(args.selection_csv, args.pool_csv)

    if args.prepare_configs:
        paths = write_selected_configs(selected_rows, args.config_dir)
        print(f"prepared_configs={[str(path) for path in paths]}")

    if args.dry_run:
        paths = [args.config_dir / f"{row['candidate_id']}.yaml" for row in selected_rows]
        validation = validate_selected_configs(paths, selected_rows)
        print(f"dry_run_validation_pass={all(row['validation_pass'] for row in validation)}")
        for row in validation:
            print(f"{row['candidate_id']}: {row['validation_pass']} {row['notes']}")
        print("status=config_validation_only_no_fdtd_no_lumapi_no_fsp")

    if args.run_top2:
        run_candidate_ids(TOP2_IDS, args.config_dir, args.runtime, args.python)

    if args.run_backups:
        run_candidate_ids(BACKUP_IDS, args.config_dir, args.runtime, args.python)

    if args.summarize:
        rows = summarize_selected_results(selected_rows)
        write_result_csv(rows, args.results_csv)
        dataset_rows = build_dataset_v5(args.dataset_v4, rows, selected_rows)
        write_dataset_csv(dataset_rows, args.dataset_v5)
        coverage_rows = analyze_phase_coverage_v4(dataset_rows)
        write_csv_rows(coverage_rows, args.coverage_v5, PHASE_COVERAGE_V4_FIELDS)
        write_dataset_report(args.dataset_report, dataset_rows, rows)
        write_gap_analysis(args.gap_analysis_v5, coverage_rows)
        write_readiness(args.readiness_v5, coverage_rows)
        write_report(args.report, rows, dataset_rows, coverage_rows)
        print(f"result_csv={args.results_csv}")
        print(f"dataset_v5={args.dataset_v5}")
        print(f"coverage_v5={args.coverage_v5}")
        print(f"run_statuses={[(row['candidate_id'], row['run_status']) for row in rows]}")

    if not any((args.prepare_configs, args.dry_run, args.run_top2, args.run_backups, args.summarize)):
        print("No action requested.")
    return 0


def read_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def selected_candidate_rows(selection_csv: str | Path, pool_csv: str | Path) -> list[dict[str, str]]:
    selection = sorted(read_csv_rows(selection_csv), key=lambda row: int(row["selection_rank"]))
    selected_ids = [row["candidate_id"] for row in selection]
    if selected_ids != SELECTED_IDS:
        raise ValueError(f"unexpected phase-lowering selected candidates: {selected_ids}")
    pool_by_id = {row["candidate_id"]: row for row in read_csv_rows(pool_csv)}
    missing = [candidate_id for candidate_id in SELECTED_IDS if candidate_id not in pool_by_id]
    if missing:
        raise ValueError(f"selected candidates missing from phase-lowering pool: {missing}")
    return [pool_by_id[candidate_id] for candidate_id in SELECTED_IDS]


def write_selected_configs(candidate_rows: Sequence[dict[str, str]], config_dir: str | Path) -> list[Path]:
    output_dir = Path(config_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for row in candidate_rows:
        path = output_dir / f"{row['candidate_id']}.yaml"
        path.write_text(build_candidate_config(row), encoding="utf-8")
        paths.append(path)
    return paths


def build_candidate_config(candidate: dict[str, str]) -> str:
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
        "project": {"name": "blue_plane_wave_metasurface", "stage": "09_p29_p32_apcd_k6_phase_lowering_selected_fdtd"},
        "candidate": {
            "variant_id": candidate["candidate_id"],
            "candidate_type": candidate["candidate_family"],
            "description": "phase-lowering selected candidate for 09-P29/P32 closure",
            "target_bin_deg": _number(candidate["target_bin_deg"]),
            "source_stage": "09-P29/P32",
            "source_planning_stage": candidate["source_stage"],
            "anchor_candidate": candidate["anchor_candidate"],
            "risk_level": candidate["risk_level"],
            "expected_phase_direction": candidate["expected_phase_direction"],
            "design_rationale": candidate["design_rationale"],
            "source_pool_csv": "outputs/apcd_k6_active_learning/phase_lowering_candidate_pool_v4.csv",
            "source_selection_csv": "outputs/apcd_k6_active_learning/phase_lowering_fdtd_selection_v4.csv",
            "notes": "Config generated for four selected phase-lowering candidates; run top-2 first and backups only if feasible.",
        },
        "boundary": {
            "no_k7": True,
            "not_phase_ramp_supercell": True,
            "not_steering_result": True,
            "not_complete_k6_library_claim": True,
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
        "output": {"result_dir": f"outputs/apcd_k6_metagrating_633nm/phase_state_candidates/{candidate['candidate_id']}"},
    }
    return yaml.safe_dump(data, sort_keys=False)


def validate_selected_configs(config_paths: Sequence[str | Path], candidate_rows: Sequence[dict[str, str]]) -> list[dict[str, object]]:
    expected = {row["candidate_id"]: row for row in candidate_rows}
    rows = []
    for path_like in config_paths:
        path = Path(path_like)
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        candidate_id = str(data["candidate"]["variant_id"])
        row = expected[candidate_id]
        config = load_apcd_single_dimer_config(path)
        checks = [
            candidate_id in SELECTED_IDS,
            float(data["candidate"]["target_bin_deg"]) == float(row["target_bin_deg"]),
            data["candidate"]["source_planning_stage"] == row["source_stage"],
            data["candidate"]["risk_level"] == row["risk_level"],
            config.geometry.nanopillar_1.length_nm == float(row["p1_length_nm"]),
            config.geometry.nanopillar_1.width_nm == float(row["p1_width_nm"]),
            config.geometry.nanopillar_2.length_nm == float(row["p2_length_nm"]),
            config.geometry.nanopillar_2.width_nm == float(row["p2_width_nm"]),
            config.geometry.nanopillar_1.rotation_deg == float(row["p1_rotation_deg"]),
            config.geometry.nanopillar_2.rotation_deg == float(row["p2_rotation_deg"]),
            config.output.result_dir.as_posix().endswith(f"/{candidate_id}"),
        ]
        rows.append(
            {
                "candidate_id": candidate_id,
                "config_path": str(path),
                "validation_pass": all(checks),
                "notes": "config load/dry-run validation only; no FDTD/lumapi/.fsp",
            }
        )
    return rows


def run_candidate_ids(candidate_ids: Sequence[str], config_dir: Path, runtime: Path, python_executable: str) -> None:
    runner = REPO_ROOT / "scripts/13_run_apcd_single_dimer.py"
    for candidate_id in candidate_ids:
        config_path = config_dir / f"{candidate_id}.yaml"
        command = [python_executable, str(runner), "--config", str(config_path), "--runtime", str(runtime)]
        print(f"running_candidate={candidate_id}")
        subprocess.run(command, cwd=REPO_ROOT, check=True)


def summarize_selected_results(candidate_rows: Sequence[dict[str, str]]) -> list[dict[str, object]]:
    rows = []
    for candidate in candidate_rows:
        result_path = REPO_ROOT / "outputs/apcd_k6_metagrating_633nm/phase_state_candidates" / candidate["candidate_id"] / "results.csv"
        if result_path.exists():
            raw = read_csv_rows(result_path)[0]
            rows.append(result_row_from_raw(candidate, raw, result_path))
        else:
            rows.append(not_run_row(candidate))
    return rows


def result_row_from_raw(candidate: dict[str, str], raw: dict[str, str], result_path: Path) -> dict[str, object]:
    status = raw.get("status", "")
    t_value = raw.get("t_alpha_star_from_alpha", "")
    phase = phase_deg_from_complex(t_value) if t_value else ""
    target = float(candidate["target_bin_deg"])
    error = angular_distance_deg(float(phase), target) if phase != "" else ""
    target_conversion = _float_or_blank(raw.get("target_conversion", ""))
    leakage = _float_or_blank(raw.get("opposite_spin_leakage", ""))
    ratio = _float_or_blank(raw.get("conversion_to_leakage_ratio", ""))
    early_target = target_conversion != "" and float(target_conversion) >= 0.5
    early_leakage = leakage != "" and float(leakage) <= 0.2
    early_ratio = ratio != "" and float(ratio) >= 6.0
    early = early_target and early_leakage and early_ratio
    bin_status = target_bin_status(float(error), early, status) if error != "" else "failed"
    return {
        "candidate_id": candidate["candidate_id"],
        "target_bin_deg": _number(target),
        "candidate_family": candidate["candidate_family"],
        "run_status": "completed" if status == "ok" else "failed",
        "status": status,
        "phase_deg": phase,
        "phase_error_to_target_deg": error,
        "target_conversion": target_conversion,
        "opposite_spin_leakage": leakage,
        "conversion_to_leakage_ratio": ratio,
        "PD": _float_or_blank(raw.get("PD", "")),
        "total_transmission": _float_or_blank(raw.get("total_transmission", "")),
        "t_alpha_star_from_alpha": t_value,
        "phase_shift_vs_baseline_deg": wrap_phase_deg(float(phase) - BASELINE_PHASE_DEG) if phase != "" else "",
        "early_target_pass": early_target,
        "early_leakage_pass": early_leakage,
        "early_ratio_pass": early_ratio,
        "early_pass": early,
        "target_bin_pass": bin_status in {"strong_covered", "early_covered"},
        "target_bin_status": bin_status,
        "source_result_csv": _relative(result_path),
        "notes": result_notes(candidate, bin_status, early, error),
    }


def not_run_row(candidate: dict[str, str]) -> dict[str, object]:
    return {
        "candidate_id": candidate["candidate_id"],
        "target_bin_deg": _number(candidate["target_bin_deg"]),
        "candidate_family": candidate["candidate_family"],
        "run_status": "not_run_due_to_time_limit",
        "status": "not_run",
        "phase_deg": "",
        "phase_error_to_target_deg": "",
        "target_conversion": "",
        "opposite_spin_leakage": "",
        "conversion_to_leakage_ratio": "",
        "PD": "",
        "total_transmission": "",
        "t_alpha_star_from_alpha": "",
        "phase_shift_vs_baseline_deg": "",
        "early_target_pass": False,
        "early_leakage_pass": False,
        "early_ratio_pass": False,
        "early_pass": False,
        "target_bin_pass": False,
        "target_bin_status": "not_run_due_to_time_limit",
        "source_result_csv": "",
        "notes": "Selected backup was not run in 09-P29/P32; no result was fabricated.",
    }


def build_dataset_v5(dataset_v4: str | Path, result_rows: Sequence[dict[str, object]], candidate_rows: Sequence[dict[str, str]]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = list(read_csv_rows(dataset_v4))
    fieldnames = list(rows[0].keys())
    candidate_by_id = {row["candidate_id"]: row for row in candidate_rows}
    existing_ids = {str(row["variant_id"]) for row in rows}
    for result in result_rows:
        if result["run_status"] != "completed" or result["status"] != "ok":
            continue
        candidate = candidate_by_id[str(result["candidate_id"])]
        if str(result["candidate_id"]) in existing_ids:
            continue
        rows.append(dataset_row_from_result(candidate, result, fieldnames))
    return rows


def dataset_row_from_result(candidate: dict[str, str], result: dict[str, object], fieldnames: Sequence[str]) -> dict[str, object]:
    t_value = complex(str(result["t_alpha_star_from_alpha"]))
    row: dict[str, object] = {field: "" for field in fieldnames}
    row.update(
        {
            "variant_id": candidate["candidate_id"],
            "candidate_family": candidate["candidate_family"],
            "p1_length_nm": candidate["p1_length_nm"],
            "p1_width_nm": candidate["p1_width_nm"],
            "p2_length_nm": candidate["p2_length_nm"],
            "p2_width_nm": candidate["p2_width_nm"],
            "p1_frac_x": candidate["p1_frac_x"],
            "p1_frac_y": candidate["p1_frac_y"],
            "p2_frac_x": candidate["p2_frac_x"],
            "p2_frac_y": candidate["p2_frac_y"],
            "internal_dx_nm": candidate["internal_dx_nm"],
            "internal_dy_nm": candidate["internal_dy_nm"],
            "p1_rotation_deg": candidate["p1_rotation_deg"],
            "p2_rotation_deg": candidate["p2_rotation_deg"],
            "period_x_nm": candidate["period_x_nm"],
            "period_y_nm": candidate["period_y_nm"],
            "height_nm": candidate["height_nm"],
            "material": candidate["material"],
            "substrate": candidate["substrate"],
            "t_alpha_star_from_alpha_real": t_value.real,
            "t_alpha_star_from_alpha_imag": t_value.imag,
            "t_alpha_star_from_alpha_abs": abs(t_value),
            "phase_deg": result["phase_deg"],
            "phase_shift_vs_baseline_deg": result["phase_shift_vs_baseline_deg"],
            "target_conversion": result["target_conversion"],
            "opposite_spin_leakage": result["opposite_spin_leakage"],
            "conversion_to_leakage_ratio": result["conversion_to_leakage_ratio"],
            "PD": result["PD"],
            "overall_early_pass": result["early_pass"],
            "source_result_csv": result["source_result_csv"],
            "notes": "09-P29/P32 real FDTD phase-lowering selected result; raw results not committed; not a steering result",
            "phase_region": classify_phase_region(
                {
                    "phase_deg": result["phase_deg"],
                    "target_bin_status": result["target_bin_status"],
                    "overall_early_pass": result["early_pass"],
                    "target_conversion": result["target_conversion"],
                    "opposite_spin_leakage": result["opposite_spin_leakage"],
                    "conversion_to_leakage_ratio": result["conversion_to_leakage_ratio"],
                }
            ),
            "target_bin_deg": result["target_bin_deg"],
            "target_bin_status": result["target_bin_status"],
        }
    )
    return row


def write_result_csv(rows: Sequence[dict[str, object]], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=RESULT_FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in RESULT_FIELDS} for row in rows)
    return output_path


def write_dataset_csv(rows: Sequence[dict[str, object]], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fieldnames} for row in rows)
    return output_path


def write_dataset_report(path: str | Path, dataset_rows: Sequence[dict[str, object]], result_rows: Sequence[dict[str, object]]) -> Path:
    completed = [row for row in result_rows if row["run_status"] == "completed"]
    lines = [
        "# APCD K=6 ML-Ready Dataset v5 Collection Report",
        "",
        "Scope: 09-P29/P32 dataset update after phase-lowering selected FDTD closure.",
        "",
        f"Dataset v5 rows: {len(dataset_rows)}",
        f"Completed selected FDTD rows added: {len(completed)}",
        "",
        "Completed candidates:",
        *[f"- `{row['candidate_id']}`: phase={row['phase_deg']}, early_pass={row['early_pass']}, status={row['target_bin_status']}" for row in completed],
        "",
        "Rows with `not_run_due_to_time_limit` were not added to the ML-ready dataset. No raw `results.csv`, `.fsp`, or pre-run files are committed.",
    ]
    return _write_text(path, lines)


def write_gap_analysis(path: str | Path, coverage_rows: Sequence[dict[str, object]]) -> Path:
    lines = [
        "# APCD K=6 Phase Gap Analysis v5",
        "",
        "Scope: coverage update after 09-P29/P32 phase-lowering selected real FDTD. This is not a phase-ramp supercell or steering proof.",
        "",
        "| bin deg | nearest early-pass | early error | nearest evidence-only | evidence error | status |",
        "|---:|---|---:|---|---:|---|",
        *[
            f"| {row['phase_bin_deg']} | {row['nearest_candidate_early_pass']} | {row['nearest_error_early_pass']} | "
            f"{row['nearest_candidate_evidence_only']} | {row['nearest_error_evidence_only']} | {row['coverage_status']} |"
            for row in coverage_rows
        ],
        "",
        "A bin is not closed unless the candidate is both phase-near and early-pass. The K=6 phase-state library remains incomplete unless all six bins are usable.",
    ]
    return _write_text(path, lines)


def write_readiness(path: str | Path, coverage_rows: Sequence[dict[str, object]]) -> Path:
    open_rows = [row for row in coverage_rows if row["coverage_status"] not in {"strong_covered", "early_covered"}]
    lines = [
        "# APCD K=6 Phase-State Readiness v5",
        "",
        "Readiness decision: not ready for K=6 phase-ramp supercell assembly.",
        "",
        f"Bins still not usable: {', '.join(str(row['phase_bin_deg']) for row in open_rows)}",
        "",
        "No +15 deg steering claim is supported.",
    ]
    return _write_text(path, lines)


def write_report(path: str | Path, result_rows: Sequence[dict[str, object]], dataset_rows: Sequence[dict[str, object]], coverage_rows: Sequence[dict[str, object]]) -> Path:
    ran = [row for row in result_rows if row["run_status"] == "completed"]
    not_run = [row for row in result_rows if row["run_status"] != "completed"]
    lines = [
        "# APCD K=6 Phase-Lowering Selected FDTD and Coverage v5 Note",
        "",
        "## Scope",
        "",
        "This is 09-P29/P32. Four selected phase-lowering YAML configs were generated and dry-run/config validated. Real FDTD was run only for candidates listed as completed below; unrun backups are explicitly marked and not fabricated.",
        "",
        "No full 42-row pool, old pool, K=7, phase-ramp supercell, TiO2/450 nm, Micro-LED integration, ML training, +15 deg steering claim, or complete K=6 phase-state library claim was made.",
        "",
        "## Completed FDTD Results",
        "",
        "| candidate | target bin | phase deg | error deg | leakage | ratio | early pass | target bin status |",
        "|---|---:|---:|---:|---:|---:|---|---|",
        *[
            f"| `{row['candidate_id']}` | {row['target_bin_deg']} | {row['phase_deg']} | {row['phase_error_to_target_deg']} | "
            f"{row['opposite_spin_leakage']} | {row['conversion_to_leakage_ratio']} | {row['early_pass']} | {row['target_bin_status']} |"
            for row in ran
        ],
        "",
        "## Not Run",
        "",
        *([f"- `{row['candidate_id']}`: {row['run_status']}" for row in not_run] or ["- none"]),
        "",
        "## Coverage v5",
        "",
        "| bin deg | status | nearest early-pass | early error |",
        "|---:|---|---|---:|",
        *[
            f"| {row['phase_bin_deg']} | {row['coverage_status']} | {row['nearest_candidate_early_pass']} | {row['nearest_error_early_pass']} |"
            for row in coverage_rows
        ],
        "",
        f"Dataset v5 row count: {len(dataset_rows)}",
        "",
        "## Next Step",
        "",
        "Continue with the still-open phase bins using only small selected batches. Do not assemble a phase-ramp supercell until six usable phase states exist.",
    ]
    return _write_text(path, lines)


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


def result_notes(candidate: dict[str, str], bin_status: str, early: bool, error: object) -> str:
    return (
        "09-P29/P32 real FDTD selected phase-lowering closure; "
        f"target={candidate['target_bin_deg']} deg; wrapped_error={error}; "
        f"target_bin_status={bin_status}; early_pass={early}; not a steering result"
    )


def _float_or_blank(value: object) -> float | str:
    if value in {"", None}:
        return ""
    return float(value)


def _number(value: object) -> int | float:
    number = float(value)
    return int(number) if number.is_integer() else number


def _relative(path: Path) -> str:
    return path.resolve().relative_to(REPO_ROOT.resolve()).as_posix()


def _write_text(path: str | Path, lines: Sequence[str]) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


if __name__ == "__main__":
    raise SystemExit(main())
