from __future__ import annotations

import argparse
import cmath
import csv
import math
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_PHASE_DEG = 111.31665091018952

SUMMARY_FIELDS = [
    "variant_id",
    "changed_parameter",
    "delta_nm",
    "target_conversion",
    "opposite_spin_leakage",
    "conversion_to_leakage_ratio",
    "PD",
    "total_transmission",
    "t_alpha_star_from_alpha",
    "phase_deg",
    "phase_shift_vs_baseline_deg",
    "early_target_pass",
    "early_leakage_pass",
    "early_ratio_pass",
    "overall_early_pass",
    "notes",
]

P2_WIDTH_SUMMARY_FIELDS = [
    "variant_id",
    "changed_parameter",
    "delta_nm",
    "target_conversion",
    "opposite_spin_leakage",
    "conversion_to_leakage_ratio",
    "PD",
    "total_transmission",
    "phase_deg",
    "phase_shift_vs_baseline_deg",
    "early_target_pass",
    "early_leakage_pass",
    "early_ratio_pass",
    "overall_early_pass",
    "notes",
]

COMBINED_SUMMARY_FIELDS = [
    "variant_id",
    "changed_parameter",
    "delta_nm",
    "target_conversion",
    "opposite_spin_leakage",
    "conversion_to_leakage_ratio",
    "PD",
    "total_transmission",
    "phase_deg",
    "phase_shift_vs_baseline_deg",
    "overall_early_pass",
    "priority",
    "notes",
]

P1_LENGTH_VARIANTS = [
    ("p1L_m10", "pillar_1_length_nm", -10.0),
    ("p1L_m5", "pillar_1_length_nm", -5.0),
    ("baseline", "none", 0.0),
    ("p1L_p5", "pillar_1_length_nm", 5.0),
    ("p1L_p10", "pillar_1_length_nm", 10.0),
    ("p2W_m5", "pillar_2_width_nm", -5.0),
]

P1_LENGTH_WIDTH_VARIANTS = [
    ("p1L_m10", "pillar_1_length_nm", -10.0),
    ("p1L_m5", "pillar_1_length_nm", -5.0),
    ("baseline", "none", 0.0),
    ("p1L_p5", "pillar_1_length_nm", 5.0),
    ("p1L_p10", "pillar_1_length_nm", 10.0),
    ("p1W_m5", "pillar_1_width_nm", -5.0),
    ("p1W_p5", "pillar_1_width_nm", 5.0),
]

P2_WIDTH_VARIANTS = [
    ("p2W_m10", "pillar_2_width_nm", -10.0),
    ("p2W_m5", "pillar_2_width_nm", -5.0),
    ("baseline", "none", 0.0),
    ("p2W_p10", "pillar_2_width_nm", 10.0),
]

PRIORITY_BY_VARIANT = {
    "baseline": "keep_high_priority",
    "p1W_m5": "keep_high_priority",
    "p2W_p10": "keep_high_priority",
    "p1L_m10": "keep_candidate",
    "p1L_m5": "keep_candidate",
    "p1L_p5": "keep_candidate",
    "p1W_p5": "keep_candidate",
    "p2W_m5": "keep_candidate",
    "p1L_p10": "record_not_priority",
    "p2W_m10": "record_not_priority",
}

COMBINED_VARIANT_ORDER = [
    "p1L_m10",
    "p1L_m5",
    "baseline",
    "p1L_p5",
    "p1L_p10",
    "p1W_m5",
    "p1W_p5",
    "p2W_m10",
    "p2W_m5",
    "p2W_p10",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize existing APCD K=6 candidate subset results.")
    parser.add_argument(
        "--subset",
        choices=("p1-length-width", "p2-width", "combined-decision"),
        default="p1-length-width",
        help="Candidate subset to summarize.",
    )
    parser.add_argument(
        "--results-root",
        default="outputs/apcd_k6_metagrating_633nm/phase_state_candidates",
        help="Directory containing per-variant results.csv files.",
    )
    parser.add_argument(
        "--output-csv",
        default=None,
        help="Output summary CSV path.",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Output report path.",
    )
    parser.add_argument(
        "--p1-summary",
        default="outputs/apcd_k6_metagrating_633nm/phase_state_candidates/p1_length_width_trend_summary.csv",
        help="Existing p1 length/width summary CSV used by combined-decision mode.",
    )
    parser.add_argument(
        "--p2-summary",
        default="outputs/apcd_k6_metagrating_633nm/phase_state_candidates/p2_width_trend_summary.csv",
        help="Existing p2 width summary CSV used by combined-decision mode.",
    )
    return parser.parse_args()


def parse_complex_text(value: str) -> complex:
    return complex(value.strip())


def phase_deg(value: complex) -> float:
    return math.degrees(cmath.phase(value))


def wrap_phase_shift_deg(measured_deg: float, reference_deg: float) -> float:
    return ((float(measured_deg) - float(reference_deg) + 180.0) % 360.0) - 180.0


def summarize_variant(
    *,
    variant_id: str,
    changed_parameter: str,
    delta_nm: float,
    results_root: Path,
    baseline_phase_deg: float = BASELINE_PHASE_DEG,
) -> dict[str, object]:
    result_path = results_root / variant_id / "results.csv"
    if not result_path.exists():
        return _missing_row(variant_id, changed_parameter, delta_nm, result_path)

    with result_path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        return _missing_row(variant_id, changed_parameter, delta_nm, result_path, note="missing: empty results.csv")

    row = rows[0]
    target_conversion = _float(row["target_conversion"])
    opposite_leakage = _float(row["opposite_spin_leakage"])
    ratio = _float(row["conversion_to_leakage_ratio"])
    target_amp = parse_complex_text(row["t_alpha_star_from_alpha"])
    target_phase = phase_deg(target_amp)
    phase_shift = wrap_phase_shift_deg(target_phase, baseline_phase_deg)
    early_target_pass = target_conversion >= 0.5
    early_leakage_pass = opposite_leakage <= 0.2
    early_ratio_pass = ratio >= 6
    return {
        "variant_id": variant_id,
        "changed_parameter": changed_parameter,
        "delta_nm": delta_nm,
        "target_conversion": target_conversion,
        "opposite_spin_leakage": opposite_leakage,
        "conversion_to_leakage_ratio": ratio,
        "PD": _float(row["PD"]),
        "total_transmission": _float(row["total_transmission"]),
        "t_alpha_star_from_alpha": row["t_alpha_star_from_alpha"],
        "phase_deg": target_phase,
        "phase_shift_vs_baseline_deg": 0.0 if variant_id == "baseline" else phase_shift,
        "early_target_pass": early_target_pass,
        "early_leakage_pass": early_leakage_pass,
        "early_ratio_pass": early_ratio_pass,
        "overall_early_pass": early_target_pass and early_leakage_pass and early_ratio_pass,
        "notes": "existing real-run result summarized; not a new FDTD run",
    }


def build_subset_summary_rows(
    results_root: Path,
    variants: list[tuple[str, str, float]] | None = None,
) -> list[dict[str, object]]:
    variants = P1_LENGTH_WIDTH_VARIANTS if variants is None else variants
    return [
        summarize_variant(
            variant_id=variant_id,
            changed_parameter=changed_parameter,
            delta_nm=delta_nm,
            results_root=results_root,
        )
        for variant_id, changed_parameter, delta_nm in variants
    ]


def write_summary_csv(
    rows: list[dict[str, object]],
    output_csv: Path,
    fields: list[str] | None = None,
) -> Path:
    fields = SUMMARY_FIELDS if fields is None else fields
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)
    return output_csv


def write_trend_report(rows: list[dict[str, object]], report_path: Path) -> Path:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    p1_rows = [row for row in rows if row["changed_parameter"] in {"pillar_1_length_nm", "none"}]
    early_pass = [row["variant_id"] for row in rows if row["overall_early_pass"] is True]
    missing = [row["variant_id"] for row in rows if str(row["notes"]).startswith("missing")]
    lines = [
        "# APCD K=6 P1-Length Candidate Trend Note",
        "",
        "## Scope",
        "",
        "This report only summarizes existing small-subset real-run results. No new FDTD run was performed by this summary step.",
        "",
        "It is not a K=7 run, not a phase-ramp supercell, not a TiO2/450 nm result, not ML, and not proof of `+15 deg` steering.",
        "",
        "## Inputs",
        "",
        "The summary reads existing `results.csv` files for:",
        "",
        "- baseline",
        "- p1L_m10",
        "- p1L_m5",
        "- p1L_p5",
        "- p1L_p10",
        "- p2W_m5",
        "",
        f"Missing inputs: {', '.join(str(item) for item in missing) if missing else 'none'}",
        "",
        "## P1 Length Trend",
        "",
        "| variant_id | delta_nm | target_conversion | opposite_spin_leakage | ratio | PD | phase_shift_vs_baseline_deg | early pass |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in p1_rows:
        lines.append(
            "| {variant_id} | {delta_nm} | {target_conversion} | {opposite_spin_leakage} | "
            "{conversion_to_leakage_ratio} | {PD} | {phase_shift_vs_baseline_deg} | {overall_early_pass} |".format(
                **row
            )
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The pillar-1 length perturbation now spans `-10, -5, 0, +5, +10 nm`.",
            "- `p1L_m10` is worth retaining: it keeps high target conversion, passes the current early leakage and ratio thresholds, and gives a negative phase shift.",
            "- `p1L_p5` passes the current early thresholds, but its leakage is higher than baseline and should be treated cautiously.",
            "- `p1L_p10` gives the largest positive phase shift in this small set, but fails leakage/ratio and should not be prioritized for the phase-state pool.",
            "- These shifts are far below a full `60 deg` K=6 phase-state separation, so this subset is not enough to form a six-state phase library.",
            "- `p2W_m5` is included as a width-perturbation comparator, not as part of the pillar-1 length trend.",
            "",
            f"Candidates passing all current early thresholds: {', '.join(str(item) for item in early_pass) if early_pass else 'none'}",
            "",
            "## Next Step",
            "",
            "Next, test only a few width perturbations such as `p1W_m5/p1W_p5` or stronger `p2W_m10/p2W_p10`. Do not launch all 13 candidates as a batch.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def write_length_width_trend_report(rows: list[dict[str, object]], report_path: Path) -> Path:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    p1_length_rows = [row for row in rows if row["changed_parameter"] in {"pillar_1_length_nm", "none"}]
    p1_width_rows = [row for row in rows if row["changed_parameter"] == "pillar_1_width_nm"]
    early_pass = [row["variant_id"] for row in rows if row["overall_early_pass"] is True]
    missing = [row["variant_id"] for row in rows if str(row["notes"]).startswith("missing")]
    lines = [
        "# APCD K=6 P1 Length + Width Candidate Trend Note",
        "",
        "## Scope",
        "",
        "This report only summarizes existing small-subset real-run results. No new FDTD run was performed by this summary step.",
        "",
        "It is not a K=7 run, not a phase-ramp supercell, not a TiO2/450 nm result, not ML, and not proof of `+15 deg` steering.",
        "",
        "## Inputs",
        "",
        "The summary reads existing `results.csv` files for:",
        "",
        "- baseline",
        "- p1L_m10",
        "- p1L_m5",
        "- p1L_p5",
        "- p1L_p10",
        "- p1W_m5",
        "- p1W_p5",
        "",
        f"Missing inputs: {', '.join(str(item) for item in missing) if missing else 'none'}",
        "",
        "## P1 Length Trend",
        "",
        "| variant_id | delta_nm | target_conversion | opposite_spin_leakage | ratio | PD | phase_shift_vs_baseline_deg | early pass |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in p1_length_rows:
        lines.append(_trend_table_row(row))
    lines.extend(
        [
            "",
            "## P1 Width Trend",
            "",
            "| variant_id | delta_nm | target_conversion | opposite_spin_leakage | ratio | PD | phase_shift_vs_baseline_deg | early pass |",
            "|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in p1_width_rows:
        lines.append(_trend_table_row(row))
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- The pillar-1 length and pillar-1 width perturbations both provide small intrinsic phase tuning.",
            "- `p1W_m5` and `p1W_p5` both pass the current early thresholds.",
            "- `p1W_m5` has very low leakage and is worth retaining.",
            "- `p1W_p5` still passes, but leakage rises relative to baseline and should be treated cautiously.",
            "- The `p1W` +/-5 nm phase shifts are about +/-6 deg, slightly stronger than the `p1L` +/-5 nm shifts.",
            "- The current pillar-1 perturbations are still far from a `60 deg` K=6 phase-state spacing, so they are not enough to form a six-state phase library.",
            "- This is not proof of `+15 deg` steering.",
            "",
            f"Candidates passing all current early thresholds: {', '.join(str(item) for item in early_pass) if early_pass else 'none'}",
            "",
            "## Next Step",
            "",
            "Next, test only a few pillar-2 width perturbations such as `p2W_m10/p2W_p10`. Do not launch all 13 candidates as a batch.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def write_p2_width_trend_report(rows: list[dict[str, object]], report_path: Path) -> Path:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    early_pass = [row["variant_id"] for row in rows if row["overall_early_pass"] is True]
    missing = [row["variant_id"] for row in rows if str(row["notes"]).startswith("missing")]
    lines = [
        "# APCD K=6 P2 Width Candidate Trend Note",
        "",
        "## Scope",
        "",
        "This report only summarizes existing `p2W` small-subset real-run results. No new FDTD run was performed by this summary step.",
        "",
        "It is not a K=7 run, not a phase-ramp supercell, not a TiO2/450 nm result, not ML, and not proof of `+15 deg` steering.",
        "",
        "## Inputs",
        "",
        "The summary reads existing `results.csv` files for:",
        "",
        "- p2W_m10",
        "- p2W_m5",
        "- baseline",
        "- p2W_p10",
        "",
        f"Missing inputs: {', '.join(str(item) for item in missing) if missing else 'none'}",
        "",
        "## P2 Width Trend",
        "",
        "| variant_id | delta_nm | target_conversion | opposite_spin_leakage | ratio | PD | total_transmission | phase_shift_vs_baseline_deg | early pass |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            "| {variant_id} | {delta_nm} | {target_conversion} | {opposite_spin_leakage} | "
            "{conversion_to_leakage_ratio} | {PD} | {total_transmission} | "
            "{phase_shift_vs_baseline_deg} | {overall_early_pass} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- This report only organizes the existing `p2W_m10 / p2W_m5 / baseline / p2W_p10` subset; it does not add any new simulation.",
            "- `p2W_m10` has clearly excessive leakage and fails the current early leakage and ratio thresholds, so it should not enter the priority pool.",
            "- `p2W_p10` keeps excellent alpha-pass behavior and is worth retaining.",
            "- Within this small subset, increasing pillar-2 width in the positive direction appears to reduce leakage and improve the target-to-leakage ratio.",
            "- The phase shifts are still only a few degrees, far below a `60 deg` K=6 phase-state spacing.",
            "- This is not proof of `+15 deg` steering.",
            "",
            f"Candidates passing all current early thresholds: {', '.join(str(item) for item in early_pass) if early_pass else 'none'}",
            "",
            "## Next Step",
            "",
            "Next, merge the existing `p1L`, `p1W`, and `p2W` small subsets into one comparison table. Then decide whether testing `p2L` is still useful or whether the phase knob needs to be reconsidered.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def build_combined_summary_rows(p1_summary_csv: Path, p2_summary_csv: Path) -> list[dict[str, object]]:
    combined_by_variant: dict[str, dict[str, object]] = {}
    for row in read_summary_csv(p1_summary_csv) + read_summary_csv(p2_summary_csv):
        variant_id = str(row["variant_id"])
        if variant_id in combined_by_variant:
            continue
        priority = PRIORITY_BY_VARIANT.get(variant_id, "review_later")
        combined_by_variant[variant_id] = {
            "variant_id": variant_id,
            "changed_parameter": row["changed_parameter"],
            "delta_nm": row["delta_nm"],
            "target_conversion": row["target_conversion"],
            "opposite_spin_leakage": row["opposite_spin_leakage"],
            "conversion_to_leakage_ratio": row["conversion_to_leakage_ratio"],
            "PD": row["PD"],
            "total_transmission": row["total_transmission"],
            "phase_deg": row["phase_deg"],
            "phase_shift_vs_baseline_deg": row["phase_shift_vs_baseline_deg"],
            "overall_early_pass": row["overall_early_pass"],
            "priority": priority,
            "notes": f"{row['notes']}; 08-P9 combined decision priority={priority}",
        }
    return [combined_by_variant[variant_id] for variant_id in COMBINED_VARIANT_ORDER if variant_id in combined_by_variant]


def phase_coverage_summary(rows: list[dict[str, object]]) -> dict[str, float]:
    passing_shifts = [
        abs(float(row["phase_shift_vs_baseline_deg"]))
        for row in rows
        if str(row["overall_early_pass"]) == "True"
    ]
    all_shifts = [abs(float(row["phase_shift_vs_baseline_deg"])) for row in rows]
    return {
        "max_passing_abs_shift_deg": max(passing_shifts) if passing_shifts else 0.0,
        "max_observed_abs_shift_deg": max(all_shifts) if all_shifts else 0.0,
        "required_k6_step_deg": 60.0,
    }


def write_phase_knob_decision_report(rows: list[dict[str, object]], report_path: Path) -> Path:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    coverage = phase_coverage_summary(rows)
    high_priority = [row["variant_id"] for row in rows if row["priority"] == "keep_high_priority"]
    keep_candidate = [row["variant_id"] for row in rows if row["priority"] == "keep_candidate"]
    not_priority = [row["variant_id"] for row in rows if row["priority"] == "record_not_priority"]
    lines = [
        "# APCD K=6 Phase-Knob Redesign Decision",
        "",
        "## Scope",
        "",
        "This is the 08-P9 closure note. It only combines existing `p1L`, `p1W`, and `p2W` small-subset summaries. No FDTD run was performed by this step.",
        "",
        "This is not a K=7 run, not a phase-ramp supercell, not a TiO2/450 nm result, not ML training, and not a steering result.",
        "",
        "## Current 08 Small-Subset Result",
        "",
        "| variant_id | changed_parameter | delta_nm | target_conversion | opposite_spin_leakage | ratio | phase_shift_vs_baseline_deg | early pass | priority |",
        "|---|---|---:|---:|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            "| {variant_id} | {changed_parameter} | {delta_nm} | {target_conversion} | "
            "{opposite_spin_leakage} | {conversion_to_leakage_ratio} | "
            "{phase_shift_vs_baseline_deg} | {overall_early_pass} | {priority} |".format(**row)
        )
    lines.extend(
        [
            "",
            "## Phase Coverage Decision",
            "",
            "- K=6 needs adjacent dimer target-channel phase spacing of `60 deg` for the intended six-state library.",
            f"- The largest early-passing absolute phase shift in the current one-factor subset is about `{coverage['max_passing_abs_shift_deg']:.2f} deg`.",
            f"- The largest observed absolute phase shift is about `{coverage['max_observed_abs_shift_deg']:.2f} deg`, but that point fails leakage/ratio.",
            "- Therefore, one-factor perturbations are insufficient to form a `0/60/120/180/240/300 deg` phase-state library.",
            "- The current results are not a `+15 deg` steering proof.",
            "- Blindly running the remaining one-factor candidates is not recommended.",
            "",
            "## Priority",
            "",
            f"- keep_high_priority: {', '.join(str(item) for item in high_priority)}",
            f"- keep_candidate: {', '.join(str(item) for item in keep_candidate)}",
            f"- record_not_priority: {', '.join(str(item) for item in not_priority)}",
            "",
            "## 08 Closure",
            "",
            "08 can close as a negative-but-useful phase-knob diagnostic: the alpha-pass baseline and several one-factor variants remain strong, but the phase span is far short of the K=6 requirement.",
            "",
            "## Next Stage: 09 Small-Data Active Learning Surrogate",
            "",
            "09 should not start by training a large model. It should first:",
            "",
            "1. Define an ML-ready dataset schema.",
            "2. Define a multi-parameter candidate space.",
            "3. Design about 20-30 DOE combined-geometry candidates.",
            "4. Use a small-data surrogate / active learning loop only after the schema and DOE set are locked.",
            "",
            "If the single-dimer phase-state library still fails after combined geometry and hybrid knobs, the project should pivot to direct K=6 supercell optimization.",
        ]
    )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def read_summary_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def main() -> int:
    args = parse_args()
    results_root = _resolve_path(args.results_root)
    if args.subset == "combined-decision":
        default_csv = "outputs/apcd_k6_metagrating_633nm/phase_state_candidates/combined_small_subset_trend_summary.csv"
        default_report = "reports/apcd_k6_phase_knob_redesign_decision.md"
        rows = build_combined_summary_rows(_resolve_path(args.p1_summary), _resolve_path(args.p2_summary))
        output_csv = _resolve_path(args.output_csv or default_csv)
        report_path = _resolve_path(args.report or default_report)
        write_summary_csv(rows, output_csv, COMBINED_SUMMARY_FIELDS)
        write_phase_knob_decision_report(rows, report_path)
    elif args.subset == "p2-width":
        default_csv = "outputs/apcd_k6_metagrating_633nm/phase_state_candidates/p2_width_trend_summary.csv"
        default_report = "reports/apcd_k6_p2_width_candidate_trend_note.md"
        rows = build_subset_summary_rows(results_root, P2_WIDTH_VARIANTS)
        output_csv = _resolve_path(args.output_csv or default_csv)
        report_path = _resolve_path(args.report or default_report)
        write_summary_csv(rows, output_csv, P2_WIDTH_SUMMARY_FIELDS)
        write_p2_width_trend_report(rows, report_path)
    else:
        default_csv = "outputs/apcd_k6_metagrating_633nm/phase_state_candidates/p1_length_width_trend_summary.csv"
        default_report = "reports/apcd_k6_p1_length_width_candidate_trend_note.md"
        rows = build_subset_summary_rows(results_root)
        output_csv = _resolve_path(args.output_csv or default_csv)
        report_path = _resolve_path(args.report or default_report)
        write_summary_csv(rows, output_csv)
        write_length_width_trend_report(rows, report_path)
    print(f"rows={len(rows)}")
    print(f"output_csv={output_csv}")
    print(f"report={report_path}")
    print("status=summary_only_no_fdtd_no_fsp")
    return 0


def _missing_row(
    variant_id: str,
    changed_parameter: str,
    delta_nm: float,
    result_path: Path,
    note: str | None = None,
) -> dict[str, object]:
    return {
        "variant_id": variant_id,
        "changed_parameter": changed_parameter,
        "delta_nm": delta_nm,
        "target_conversion": "",
        "opposite_spin_leakage": "",
        "conversion_to_leakage_ratio": "",
        "PD": "",
        "total_transmission": "",
        "t_alpha_star_from_alpha": "",
        "phase_deg": "",
        "phase_shift_vs_baseline_deg": "",
        "early_target_pass": "",
        "early_leakage_pass": "",
        "early_ratio_pass": "",
        "overall_early_pass": "",
        "notes": note or f"missing results.csv: {result_path}",
    }


def _float(value: str) -> float:
    return float(value)


def _trend_table_row(row: dict[str, object]) -> str:
    return (
        "| {variant_id} | {delta_nm} | {target_conversion} | {opposite_spin_leakage} | "
        "{conversion_to_leakage_ratio} | {PD} | {phase_shift_vs_baseline_deg} | {overall_early_pass} |"
    ).format(**row)


def _resolve_path(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


if __name__ == "__main__":
    raise SystemExit(main())
