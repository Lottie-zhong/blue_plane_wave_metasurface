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

DEFAULT_VARIANTS = [
    ("p1L_m10", "pillar_1_length_nm", -10.0),
    ("p1L_m5", "pillar_1_length_nm", -5.0),
    ("baseline", "none", 0.0),
    ("p1L_p5", "pillar_1_length_nm", 5.0),
    ("p1L_p10", "pillar_1_length_nm", 10.0),
    ("p2W_m5", "pillar_2_width_nm", -5.0),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize existing APCD K=6 candidate subset results.")
    parser.add_argument(
        "--results-root",
        default="outputs/apcd_k6_metagrating_633nm/phase_state_candidates",
        help="Directory containing per-variant results.csv files.",
    )
    parser.add_argument(
        "--output-csv",
        default="outputs/apcd_k6_metagrating_633nm/phase_state_candidates/p1_length_trend_summary.csv",
        help="Output summary CSV path.",
    )
    parser.add_argument(
        "--report",
        default="reports/apcd_k6_p1_length_candidate_trend_note.md",
        help="Output report path.",
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


def build_subset_summary_rows(results_root: Path) -> list[dict[str, object]]:
    return [
        summarize_variant(
            variant_id=variant_id,
            changed_parameter=changed_parameter,
            delta_nm=delta_nm,
            results_root=results_root,
        )
        for variant_id, changed_parameter, delta_nm in DEFAULT_VARIANTS
    ]


def write_summary_csv(rows: list[dict[str, object]], output_csv: Path) -> Path:
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with output_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=SUMMARY_FIELDS)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in SUMMARY_FIELDS} for row in rows)
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


def main() -> int:
    args = parse_args()
    results_root = _resolve_path(args.results_root)
    output_csv = _resolve_path(args.output_csv)
    report_path = _resolve_path(args.report)
    rows = build_subset_summary_rows(results_root)
    write_summary_csv(rows, output_csv)
    write_trend_report(rows, report_path)
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


def _resolve_path(path: str) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


if __name__ == "__main__":
    raise SystemExit(main())
