from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_phase_knob_pilot import (  # noqa: E402
    NEXTGEN_TOP2_IDS,
    PILOT_RESULT_FIELDS,
    WEAK_HELPER_FIELDS,
    WEAK_HELPER_VALIDATION_FIELDS,
    build_dataset_v6,
    build_weak_helper_candidate_pool,
    helper_family_exists,
    read_csv_rows,
    select_top_helper_candidate,
    selected_pilot_rows,
    summarize_pilot_results,
    validate_pilot_configs,
    validate_weak_helper_candidate_pool,
    write_csv_rows,
    write_pilot_configs,
)
from metasurface.apcd_phase_lowering_candidates import PHASE_COVERAGE_V4_FIELDS, analyze_phase_coverage_v4  # noqa: E402


DEFAULT_NEXTGEN_POOL = REPO_ROOT / "outputs/apcd_k6_active_learning/nextgen_candidate_pool_v6.csv"
DEFAULT_DATASET_V5 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v5.csv"
DEFAULT_CONFIG_DIR = REPO_ROOT / "configs/apcd_k6_phase_state_candidates"
DEFAULT_RUNTIME = REPO_ROOT / "configs/runtime.yaml"
DEFAULT_WEAK_POOL = REPO_ROOT / "outputs/apcd_k6_active_learning/weak_helper_candidate_pool_v6.csv"
DEFAULT_WEAK_VALIDATION = REPO_ROOT / "outputs/apcd_k6_active_learning/weak_helper_candidate_pool_v6_geometry_validation.csv"
DEFAULT_RESULTS = REPO_ROOT / "outputs/apcd_k6_active_learning/nextgen_phase_knob_pilot_fdtd_results_v6.csv"
DEFAULT_DATASET_V6 = REPO_ROOT / "outputs/apcd_k6_active_learning/ml_ready_dataset_v6.csv"
DEFAULT_COVERAGE_V6 = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_coverage_v6.csv"
DEFAULT_GAP_V6 = REPO_ROOT / "outputs/apcd_k6_active_learning/phase_gap_analysis_v6.md"
DEFAULT_READINESS_V6 = REPO_ROOT / "outputs/apcd_k6_active_learning/k6_phase_state_readiness_v6.md"
DEFAULT_REPORT = REPO_ROOT / "reports/apcd_k6_nextgen_phase_knob_pilot_fdtd_v6_note.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare, run, and summarize APCD K=6 nextgen phase-knob pilot candidates.")
    parser.add_argument("--prepare", action="store_true", help="Generate weak-helper mini-pool and pilot YAML configs.")
    parser.add_argument("--dry-run", action="store_true", help="Validate generated configs without FDTD/lumapi/.fsp.")
    parser.add_argument("--run-pilot", action="store_true", help="Run actual pilot candidates, max three.")
    parser.add_argument("--summarize", action="store_true", help="Summarize available pilot results and update dataset/coverage v6.")
    parser.add_argument("--nextgen-pool", type=Path, default=DEFAULT_NEXTGEN_POOL)
    parser.add_argument("--dataset-v5", type=Path, default=DEFAULT_DATASET_V5)
    parser.add_argument("--config-dir", type=Path, default=DEFAULT_CONFIG_DIR)
    parser.add_argument("--runtime", type=Path, default=DEFAULT_RUNTIME)
    parser.add_argument("--weak-pool", type=Path, default=DEFAULT_WEAK_POOL)
    parser.add_argument("--weak-validation", type=Path, default=DEFAULT_WEAK_VALIDATION)
    parser.add_argument("--results-csv", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--dataset-v6", type=Path, default=DEFAULT_DATASET_V6)
    parser.add_argument("--coverage-v6", type=Path, default=DEFAULT_COVERAGE_V6)
    parser.add_argument("--gap-analysis-v6", type=Path, default=DEFAULT_GAP_V6)
    parser.add_argument("--readiness-v6", type=Path, default=DEFAULT_READINESS_V6)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--python", default=sys.executable)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    nextgen_rows = read_csv_rows(args.nextgen_pool)
    helper_exists = helper_family_exists(nextgen_rows)
    weak_pool = [] if helper_exists else build_weak_helper_candidate_pool(nextgen_rows)
    weak_validation = [] if helper_exists else validate_weak_helper_candidate_pool(weak_pool)
    helper = None if helper_exists else select_top_helper_candidate(weak_pool, weak_validation)
    pilot_rows = selected_pilot_rows(nextgen_rows, helper)

    print(f"nextgen_pool_has_helper_family={helper_exists}")
    print(f"weak_helper_candidate_count={len(weak_pool)}")
    print(f"weak_helper_geometry_pass_count={sum(str(row['overall_geometry_pass']) == 'True' for row in weak_validation)}")
    print(f"pilot_candidate_ids={[row['candidate_id'] for row in pilot_rows]}")

    if args.prepare:
        if weak_pool:
            write_csv_rows(weak_pool, args.weak_pool, WEAK_HELPER_FIELDS)
            write_csv_rows(weak_validation, args.weak_validation, WEAK_HELPER_VALIDATION_FIELDS)
        config_paths = write_pilot_configs(pilot_rows, args.config_dir)
        print(f"configs={[str(path) for path in config_paths]}")

    if args.dry_run:
        paths = [args.config_dir / f"{row['candidate_id']}.yaml" for row in pilot_rows]
        validation = validate_pilot_configs(paths)
        print(f"dry_run_validation_pass={all(row['validation_pass'] for row in validation)}")
        for row in validation:
            print(f"{row['candidate_id']}: {row['validation_pass']} {row['notes']}")
        print("status=config_validation_only_no_fdtd_no_lumapi_no_fsp")

    if args.run_pilot:
        run_pilot_candidates(pilot_rows, args.config_dir, args.runtime, args.python)

    if args.summarize:
        result_rows = summarize_pilot_results(pilot_rows, REPO_ROOT)
        write_csv_rows(result_rows, args.results_csv, PILOT_RESULT_FIELDS)
        dataset_v5 = read_csv_rows(args.dataset_v5)
        dataset_v6 = build_dataset_v6(dataset_v5, result_rows, pilot_rows)
        write_dataset_csv(dataset_v6, args.dataset_v6)
        coverage_v6 = analyze_phase_coverage_v4(dataset_v6)
        write_csv_rows(coverage_v6, args.coverage_v6, PHASE_COVERAGE_V4_FIELDS)
        write_gap_analysis(args.gap_analysis_v6, coverage_v6, result_rows)
        write_readiness(args.readiness_v6, coverage_v6)
        write_report(args.report, helper_exists, weak_pool, weak_validation, result_rows, dataset_v6, coverage_v6)
        print(f"results={args.results_csv}")
        print(f"dataset_v6_rows={len(dataset_v6)}")
        print(f"coverage_v6={[(row['phase_bin_deg'], row['coverage_status']) for row in coverage_v6]}")

    if not any((args.prepare, args.dry_run, args.run_pilot, args.summarize)):
        print("No action requested.")
    print("status=nextgen_phase_knob_pilot_max3_no_full_pool_no_k7_no_phase_ramp_no_training_not_steering_result")
    return 0


def run_pilot_candidates(candidate_rows: list[dict[str, object]], config_dir: Path, runtime: Path, python_executable: str) -> None:
    runner = REPO_ROOT / "scripts/13_run_apcd_single_dimer.py"
    if len(candidate_rows) > 3:
        raise ValueError("pilot candidate count must be <= 3")
    for row in candidate_rows:
        candidate_id = str(row["candidate_id"])
        command = [python_executable, str(runner), "--config", str(config_dir / f"{candidate_id}.yaml"), "--runtime", str(runtime)]
        print(f"running_candidate={candidate_id}")
        subprocess.run(command, cwd=REPO_ROOT, check=True)


def write_dataset_csv(rows: list[dict[str, object]], path: Path) -> Path:
    fieldnames = list(rows[0].keys())
    return write_csv_rows(rows, path, fieldnames)


def write_gap_analysis(path: Path, coverage_rows: list[dict[str, object]], result_rows: list[dict[str, object]]) -> Path:
    lines = [
        "# APCD K=6 Phase Gap Analysis v6",
        "",
        "Scope: 09-P36/P38 nextgen phase-knob pilot. At most three pilot candidates were run. No full pool, K=7, phase-ramp supercell, TiO2/450 nm, Micro-LED, or ML training.",
        "",
        "| bin deg | status | nearest early-pass | early error | nearest evidence-only | evidence error |",
        "|---:|---|---|---:|---|---:|",
        *[
            f"| {row['phase_bin_deg']} | {row['coverage_status']} | {row['nearest_candidate_early_pass']} | {row['nearest_error_early_pass']} | {row['nearest_candidate_evidence_only']} | {row['nearest_error_evidence_only']} |"
            for row in coverage_rows
        ],
        "",
        "Pilot results:",
        *[
            f"- `{row['candidate_id']}`: phase={row['phase_deg']}, leakage={row['opposite_spin_leakage']}, ratio={row['conversion_to_leakage_ratio']}, early_pass={row['early_pass']}, status={row['target_bin_status']}"
            for row in result_rows
        ],
        "",
        "Do not claim a complete K=6 library or +15 deg steering from these results.",
    ]
    return _write_text(path, lines)


def write_readiness(path: Path, coverage_rows: list[dict[str, object]]) -> Path:
    not_ready = [row for row in coverage_rows if row["coverage_status"] not in {"strong_covered", "early_covered"}]
    lines = [
        "# APCD K=6 Phase-State Readiness v6",
        "",
        "Readiness decision: not ready for K=6 phase-ramp supercell assembly.",
        "",
        f"Bins still not usable: {', '.join(str(row['phase_bin_deg']) for row in not_ready)}",
        "",
        "No +15 deg steering claim is supported.",
    ]
    return _write_text(path, lines)


def write_report(
    path: Path,
    helper_exists: bool,
    weak_pool: list[dict[str, object]],
    weak_validation: list[dict[str, object]],
    result_rows: list[dict[str, object]],
    dataset_rows: list[dict[str, object]],
    coverage_rows: list[dict[str, object]],
) -> Path:
    lines = [
        "# APCD K=6 Nextgen Phase-Knob Pilot FDTD v6 Note",
        "",
        "## Scope",
        "",
        "This is 09-P36/P38. The stage compares released-rotation/dxdy nextgen candidates with one APCD-core plus standalone weak auxiliary phase helper pilot.",
        "",
        "No full 60-row nextgen pool, old pool, K=7, phase-ramp supercell, TiO2/450 nm, Micro-LED integration, ML training, +15 deg steering claim, or complete K=6 phase-state library claim was made.",
        "",
        "## Helper Audit",
        "",
        f"Existing nextgen helper family present: {helper_exists}",
        f"Weak-helper mini-pool generated: {len(weak_pool)} rows",
        f"Weak-helper geometry pass: {sum(str(row['overall_geometry_pass']) == 'True' for row in weak_validation)}/{len(weak_validation)}",
        "",
        "The helper role is `weak_auxiliary_phase_helper`. It is a third standalone weak auxiliary phase shifter, not another APCD dimer and not half of another APCD pair.",
        "",
        "## Pilot Results",
        "",
        "| candidate | family | target | phase | leakage | ratio | early pass | target bin status |",
        "|---|---|---:|---:|---:|---:|---|---|",
        *[
            f"| `{row['candidate_id']}` | `{row['family']}` | {row['target_bin_deg']} | {row['phase_deg']} | {row['opposite_spin_leakage']} | {row['conversion_to_leakage_ratio']} | {row['early_pass']} | {row['target_bin_status']} |"
            for row in result_rows
        ],
        "",
        "## Coverage v6",
        "",
        "| bin deg | status |",
        "|---:|---|",
        *[f"| {row['phase_bin_deg']} | {row['coverage_status']} |" for row in coverage_rows],
        "",
        f"Dataset v6 rows: {len(dataset_rows)}",
        "",
        "## Next Step",
        "",
        "If the weak-helper pilot opens a new usable phase region, design a smaller helper-neighborhood batch. If not, prioritize more radical phase-knob redesign before any phase-ramp supercell work.",
    ]
    return _write_text(path, lines)


def _write_text(path: Path, lines: list[str]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    raise SystemExit(main())
