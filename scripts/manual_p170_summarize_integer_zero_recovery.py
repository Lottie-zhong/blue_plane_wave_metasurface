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
PLAN_CSV = ACTIVE_DIR / "combined_phase_knob_p169_integer_zero_recovery_candidate_plan.csv"
RESULTS_CSV = ACTIVE_DIR / "combined_phase_knob_p170_integer_zero_recovery_results.csv"
DECISION_CSV = ACTIVE_DIR / "combined_phase_knob_p171_integer_zero_recovery_decision.csv"
REPORT_MD = REPO_ROOT / "reports/combined_phase_knob_p170_integer_zero_recovery_results.md"

RESULT_FIELDS = [
    "candidate_id",
    "group",
    "family",
    "result_status",
    "phase_deg",
    "nearest_bin",
    "phase_error_deg",
    "target_conversion",
    "opposite_spin_leakage",
    "conversion_to_leakage_ratio",
    "PD",
    "early_pass",
    "opens_0",
    "source_result_csv",
    "notes",
]

DECISION_FIELDS = ["decision_key", "decision_value", "notes"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize existing real FDTD results for P169 integer zero-recovery candidates."
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
    print("status=stage09_integer_zero_recovery_summary_built_no_fdtd_no_lumapi")
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
    row = p164.summarize_result_row(plan["candidate_id"], "p169_plan", result_csv, raw)
    row["group"] = plan.get("group", "")
    row["family"] = plan.get("family", "")
    row["notes"] = "existing real FDTD result summarized; no FDTD run by P170"
    return {field: row.get(field, "") for field in RESULT_FIELDS}


def missing_result_row(plan: dict[str, str], result_csv: Path, note: str = "results.csv missing") -> dict[str, object]:
    return {
        "candidate_id": plan["candidate_id"],
        "group": plan.get("group", ""),
        "family": plan.get("family", ""),
        "result_status": "missing_result",
        "phase_deg": "",
        "nearest_bin": "",
        "phase_error_deg": "",
        "target_conversion": "",
        "opposite_spin_leakage": "",
        "conversion_to_leakage_ratio": "",
        "PD": "",
        "early_pass": False,
        "opens_0": False,
        "source_result_csv": p164.relative_path(result_csv),
        "notes": f"{note}; run this integer candidate on the server before interpreting recovery status",
    }


def build_decision_rows(result_rows: Sequence[dict[str, object]]) -> list[dict[str, object]]:
    existing = [row for row in result_rows if row["result_status"] != "missing_result"]
    opened = [row for row in existing if row["opens_0"] is True or row["opens_0"] == "True"]
    early = [row for row in existing if row["early_pass"] is True or row["early_pass"] == "True"]
    best = best_existing_candidate(existing)
    return [
        {
            "decision_key": "stage",
            "decision_value": "09-P171",
            "notes": "Stage 09 integer zero-recovery summary only; no K=6 phase-ramp or steering claim.",
        },
        {
            "decision_key": "official_height_nm",
            "decision_value": 232,
            "notes": "Fabrication-aware official route fixes integer height.",
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
            "decision_key": "early_pass_count",
            "decision_value": len(early),
            "notes": "Uses target>=0.5, leakage<=0.2, ratio>=6.",
        },
        {
            "decision_key": "best_available_candidate",
            "decision_value": best.get("candidate_id", "") if best else "",
            "notes": "Best among existing results by opens_0, early_pass, phase error to 0, and ratio.",
        },
        {
            "decision_key": "next_action",
            "decision_value": "run_missing_real_fdtd_on_server" if len(existing) < len(result_rows) else "review_zero_opening",
            "notes": "Missing results are not fabricated by this workflow.",
        },
    ]


def best_existing_candidate(rows: Sequence[dict[str, object]]) -> dict[str, object] | None:
    if not rows:
        return None

    def score(row: dict[str, object]) -> tuple[int, int, float, float]:
        opens = 1 if row["opens_0"] is True or row["opens_0"] == "True" else 0
        early = 1 if row["early_pass"] is True or row["early_pass"] == "True" else 0
        phase_error = float(row["phase_error_deg"]) if row["phase_error_deg"] != "" else 999.0
        ratio = float(row["conversion_to_leakage_ratio"]) if row["conversion_to_leakage_ratio"] != "" else -1.0
        return (opens, early, -phase_error, ratio)

    return max(rows, key=score)


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
        "# P170 integer zero-recovery results",
        "",
        "## Scope",
        "",
        "Stage 09 only. This summary reads existing local `results.csv` files from the P169 integer candidate list and does not run FDTD or call lumapi.",
        "",
        "No K=6 phase-ramp supercell, steering claim, stage 10 claim, Micro-LED result, or fabricated metric is made.",
        "",
        "## Fabrication-Aware Rule",
        "",
        "The official route fixes `height_nm = 232` and uses integer-nm geometry. Sub-nm cliff scans remain diagnostic history only.",
        "",
        "## Summary",
        "",
        f"- P169 candidates summarized: {len(rows)}",
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
