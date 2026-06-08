from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import manual_p164_build_zero_stage_database as p164  # noqa: E402


ACTIVE_DIR = REPO_ROOT / "outputs/apcd_k6_active_learning"
RESULT_ROOT = REPO_ROOT / "outputs/apcd_k6_metagrating_633nm/phase_state_candidates"
PLAN_CSV = ACTIVE_DIR / "p176_h232_zero_coupled_candidate_plan.csv"
RESULTS_CSV = ACTIVE_DIR / "p177_h232_zero_coupled_results.csv"
DECISION_CSV = ACTIVE_DIR / "p178_h232_zero_coupled_decision.csv"
REPORT_MD = REPO_ROOT / "reports/p177_h232_zero_coupled_results.md"

BASELINE_PHASE_DEG = 19.94
BASELINE_LEAKAGE = 0.179
BASELINE_RATIO = 4.57

RESULT_FIELDS = [
    "candidate_id",
    "group",
    "family",
    "result_status",
    "phase_deg",
    "nearest_bin",
    "err_to_0",
    "target",
    "leakage",
    "ratio",
    "PD",
    "early_pass",
    "opens_0",
    "leakage_improved_vs_h232_baseline",
    "source_result_csv",
    "notes",
]

DECISION_FIELDS = ["decision_key", "decision_value", "notes"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize existing real FDTD results for P176 h232 zero coupled recovery candidates."
    )
    parser.add_argument("--plan-csv", type=Path, default=PLAN_CSV)
    parser.add_argument("--result-root", type=Path, default=RESULT_ROOT)
    parser.add_argument("--output-csv", type=Path, default=RESULTS_CSV)
    parser.add_argument("--decision-csv", type=Path, default=DECISION_CSV)
    parser.add_argument("--report", type=Path, default=REPORT_MD)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    plan_rows = read_csv_rows(args.plan_csv)
    result_rows = summarize_plan_results(plan_rows, args.result_root)
    decision_rows = build_decision_rows(result_rows)
    write_csv_rows(result_rows, args.output_csv, RESULT_FIELDS)
    write_csv_rows(decision_rows, args.decision_csv, DECISION_FIELDS)
    write_report(args.report, result_rows, decision_rows)
    print(f"results_csv={args.output_csv}")
    print(f"decision_csv={args.decision_csv}")
    print(f"report={args.report}")
    print("status=stage09_h232_zero_coupled_summary_built_no_fdtd_no_lumapi")
    return 0


def summarize_plan_results(plan_rows: Sequence[dict[str, str]], result_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for plan in plan_rows:
        candidate_id = plan["candidate_id"]
        result_csv = result_root / candidate_id / "results.csv"
        if not result_csv.exists():
            rows.append(missing_result_row(plan, result_csv))
            continue
        raw_rows = p164.read_csv_rows(result_csv)
        if not raw_rows:
            rows.append(missing_result_row(plan, result_csv, note="empty results.csv"))
            continue
        rows.append(summarize_existing_result(plan, result_csv, raw_rows[0]))
    return rows


def summarize_existing_result(plan: dict[str, str], result_csv: Path, raw: dict[str, str]) -> dict[str, object]:
    base = p164.summarize_result_row(plan["candidate_id"], "p176_plan", result_csv, raw)
    leakage = float(base["opposite_spin_leakage"])
    return {
        "candidate_id": plan["candidate_id"],
        "group": plan.get("group", ""),
        "family": plan.get("family", ""),
        "result_status": base["result_status"],
        "phase_deg": base["phase_deg"],
        "nearest_bin": base["nearest_bin"],
        "err_to_0": abs(p164.wrap_phase_deg(float(base["phase_deg"]))),
        "target": base["target_conversion"],
        "leakage": base["opposite_spin_leakage"],
        "ratio": base["conversion_to_leakage_ratio"],
        "PD": base["PD"],
        "early_pass": base["early_pass"],
        "opens_0": base["opens_0"],
        "leakage_improved_vs_h232_baseline": leakage < BASELINE_LEAKAGE,
        "source_result_csv": base["source_result_csv"],
        "notes": "existing real FDTD result summarized; no FDTD run by P177",
    }


def missing_result_row(plan: dict[str, str], result_csv: Path, note: str = "results.csv missing") -> dict[str, object]:
    return {
        "candidate_id": plan["candidate_id"],
        "group": plan.get("group", ""),
        "family": plan.get("family", ""),
        "result_status": "missing_result",
        "phase_deg": "",
        "nearest_bin": "",
        "err_to_0": "",
        "target": "",
        "leakage": "",
        "ratio": "",
        "PD": "",
        "early_pass": False,
        "opens_0": False,
        "leakage_improved_vs_h232_baseline": False,
        "source_result_csv": p164.relative_path(result_csv),
        "notes": f"{note}; run this h232 coupled candidate on the server before interpreting recovery status",
    }


def build_decision_rows(result_rows: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    existing = [row for row in result_rows if row["result_status"] != "missing_result"]
    opened = [row for row in existing if row["opens_0"] is True or row["opens_0"] == "True"]
    zero_with_improved_leakage = [
        row
        for row in existing
        if row.get("nearest_bin") in (0, "0", 0.0, "0.0") and float(row.get("leakage", 999.0)) < BASELINE_LEAKAGE
    ]
    if opened:
        decision = "0_bin_opened"
        decision_note = "At least one result has nearest_bin=0 and early_pass=true."
    elif not existing:
        decision = "run_missing_real_fdtd_on_server"
        decision_note = "No real result CSVs are present, so no mechanism decision is claimed."
    elif zero_with_improved_leakage:
        decision = "continue_coupled_recovery"
        decision_note = "At least one 0-bin phase-hit improves leakage versus the h232 baseline."
    else:
        decision = "mechanism_shift_needed"
        decision_note = "No 0-bin opening and no 0-bin leakage improvement versus h232 baseline."
    return [
        {
            "decision_key": "stage",
            "decision_value": "09-P178",
            "notes": "Stage 09 h232 zero coupled summary only; no K=6 phase-ramp or steering claim.",
        },
        {
            "decision_key": "baseline_phase_deg",
            "decision_value": BASELINE_PHASE_DEG,
            "notes": "h232 p1geom120x58 baseline supplied by current decision context.",
        },
        {
            "decision_key": "baseline_leakage",
            "decision_value": BASELINE_LEAKAGE,
            "notes": "Leakage improvement is measured against this baseline.",
        },
        {
            "decision_key": "existing_results_count",
            "decision_value": len(existing),
            "notes": "Candidates with a local result CSV available.",
        },
        {
            "decision_key": "opens_0_count",
            "decision_value": len(opened),
            "notes": "Counts only nearest_bin=0 with early_pass=true.",
        },
        {
            "decision_key": "zero_bin_leakage_improved_count",
            "decision_value": len(zero_with_improved_leakage),
            "notes": "Counts nearest_bin=0 candidates with leakage below the h232 baseline.",
        },
        {
            "decision_key": "final_decision",
            "decision_value": decision,
            "notes": decision_note,
        },
    ]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv_rows(rows: Iterable[dict[str, object]], path: Path, fieldnames: Sequence[str]) -> Path:
    row_list = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fieldnames} for row in row_list)
    return path


def write_report(path: Path, rows: Sequence[dict[str, object]], decisions: Sequence[dict[str, object]]) -> Path:
    existing = [row for row in rows if row["result_status"] != "missing_result"]
    opened = [row for row in existing if row["opens_0"] is True or row["opens_0"] == "True"]
    lines = [
        "# P177 h232 zero coupled recovery results",
        "",
        "## Scope",
        "",
        "Stage 09 only. This summary reads existing local `results.csv` files from the P176 candidate list and does not run FDTD or call lumapi.",
        "",
        "No K=6 phase-ramp supercell, steering claim, stage 10 claim, Micro-LED result, or fabricated metric is made.",
        "",
        "## H232 Coupled Recovery Rule",
        "",
        "The workflow starts from the h232 0-bin phase-hit and uses integer p2 coupled compensation to recover leakage/ratio.",
        "",
        "## Summary",
        "",
        f"- P176 candidates summarized: {len(rows)}",
        f"- existing result CSVs found: {len(existing)}",
        f"- zero-bin early-pass openings: {len(opened)}",
        "",
        "## Decision",
        "",
    ]
    for row in decisions:
        lines.append(f"- {row['decision_key']}: {row['decision_value']} ({row['notes']})")
    lines.extend(
        [
            "",
            "Missing results are retained as `missing_result`; run real FDTD on the server before claiming any recovery result.",
            "Do not commit raw candidate `results.csv`, raw `summary.md`, `.fsp`, `pre_run` files, `.npy`, or large outputs.",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


if __name__ == "__main__":
    raise SystemExit(main())
