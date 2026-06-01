from __future__ import annotations

import argparse
import cmath
import csv
import math
import sys
from pathlib import Path

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_active_learning import wrap_phase_deg  # noqa: E402


BASELINE_PHASE_DEG = 111.31665091018952
EARLY_TARGET_CONVERSION_MIN = 0.5
EARLY_OPPOSITE_SPIN_LEAKAGE_MAX = 0.2
EARLY_CONVERSION_TO_LEAKAGE_RATIO_MIN = 6.0

DEFAULT_SCHEMA_CSV = "outputs/apcd_k6_active_learning/ml_ready_dataset_schema.csv"
DEFAULT_CONFIG_INDEX_CSV = "outputs/apcd_k6_metagrating_633nm/phase_state_candidate_config_index.csv"
DEFAULT_RESULTS_ROOT = "outputs/apcd_k6_metagrating_633nm/phase_state_candidates"
DEFAULT_OUTPUT_CSV = "outputs/apcd_k6_active_learning/ml_ready_dataset_v0.csv"
DEFAULT_COLLECTION_REPORT = "outputs/apcd_k6_active_learning/ml_ready_dataset_v0_collection_report.md"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect APCD K=6 ML-ready dataset v0 from existing real results.")
    parser.add_argument("--schema-csv", default=DEFAULT_SCHEMA_CSV, help="09-P0 ML-ready dataset schema CSV.")
    parser.add_argument("--config-index", default=DEFAULT_CONFIG_INDEX_CSV, help="Candidate config index CSV.")
    parser.add_argument("--results-root", default=DEFAULT_RESULTS_ROOT, help="Per-variant results root directory.")
    parser.add_argument("--output-csv", default=DEFAULT_OUTPUT_CSV, help="Output ML-ready dataset v0 CSV.")
    parser.add_argument("--collection-report", default=DEFAULT_COLLECTION_REPORT, help="Output collection report Markdown.")
    return parser.parse_args()


def read_schema_columns(schema_csv: str | Path) -> list[str]:
    path = _resolve_path(schema_csv)
    with path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return [row["column_name"] for row in rows]


def read_candidate_config_index(config_index_csv: str | Path) -> list[dict[str, str]]:
    path = _resolve_path(config_index_csv)
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_complex_text(value: str) -> complex:
    return complex(str(value).strip())


def phase_deg(value: complex) -> float:
    return wrap_phase_deg(math.degrees(cmath.phase(value)))


def phase_shift_vs_baseline_deg(phase_value_deg: float, baseline_phase_deg: float = BASELINE_PHASE_DEG) -> float:
    return wrap_phase_deg(float(phase_value_deg) - float(baseline_phase_deg))


def overall_early_pass(
    *,
    target_conversion: float,
    opposite_spin_leakage: float,
    conversion_to_leakage_ratio: float,
) -> bool:
    return (
        float(target_conversion) >= EARLY_TARGET_CONVERSION_MIN
        and float(opposite_spin_leakage) <= EARLY_OPPOSITE_SPIN_LEAKAGE_MAX
        and float(conversion_to_leakage_ratio) >= EARLY_CONVERSION_TO_LEAKAGE_RATIO_MIN
    )


def candidate_input_row(index_row: dict[str, str]) -> dict[str, object]:
    config_path = _resolve_path(index_row["config_path"])
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle)
    geometry = config["geometry"]
    p1 = geometry["nanopillar_1"]
    p2 = geometry["nanopillar_2"]
    material = config["material"]

    return {
        "variant_id": index_row["variant_id"],
        "candidate_family": index_row["candidate_type"],
        "p1_length_nm": _number(p1["length_nm"]),
        "p1_width_nm": _number(p1["width_nm"]),
        "p2_length_nm": _number(p2["length_nm"]),
        "p2_width_nm": _number(p2["width_nm"]),
        "p1_frac_x": _number(p1["frac_x"]),
        "p1_frac_y": _number(p1["frac_y"]),
        "p2_frac_x": _number(p2["frac_x"]),
        "p2_frac_y": _number(p2["frac_y"]),
        "internal_dx_nm": 0.0,
        "internal_dy_nm": 0.0,
        "p1_rotation_deg": _number(p1["rotation_deg"]),
        "p2_rotation_deg": _number(p2["rotation_deg"]),
        "period_x_nm": _number(geometry["period_x_nm"]),
        "period_y_nm": _number(geometry["period_y_nm"]),
        "height_nm": _number(geometry["height_nm"]),
        "material": material["meta_material"],
        "substrate": material["substrate"],
    }


def read_result_row(result_csv: str | Path) -> dict[str, str] | None:
    path = Path(result_csv)
    with path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    return rows[0] if rows else None


def build_dataset_row(index_row: dict[str, str], result_csv: Path) -> dict[str, object]:
    result = read_result_row(result_csv)
    if result is None:
        raise ValueError(f"empty results.csv: {result_csv}")

    t_alpha = parse_complex_text(result["t_alpha_star_from_alpha"])
    target_phase_deg = phase_deg(t_alpha)
    target_conversion = float(result["target_conversion"])
    opposite_spin_leakage = float(result["opposite_spin_leakage"])
    ratio = float(result["conversion_to_leakage_ratio"])
    row = candidate_input_row(index_row)
    row.update(
        {
            "t_alpha_star_from_alpha_real": t_alpha.real,
            "t_alpha_star_from_alpha_imag": t_alpha.imag,
            "t_alpha_star_from_alpha_abs": abs(t_alpha),
            "phase_deg": target_phase_deg,
            "phase_shift_vs_baseline_deg": phase_shift_vs_baseline_deg(target_phase_deg),
            "target_conversion": target_conversion,
            "opposite_spin_leakage": opposite_spin_leakage,
            "conversion_to_leakage_ratio": ratio,
            "PD": float(result["PD"]),
            "overall_early_pass": overall_early_pass(
                target_conversion=target_conversion,
                opposite_spin_leakage=opposite_spin_leakage,
                conversion_to_leakage_ratio=ratio,
            ),
            "source_result_csv": _relative_posix(result_csv),
            "notes": "existing real FDTD result collected for 09-P1; no new FDTD run; no training; not a steering result",
        }
    )
    return row


def collect_ml_dataset_v0(
    *,
    schema_csv: str | Path = DEFAULT_SCHEMA_CSV,
    config_index_csv: str | Path = DEFAULT_CONFIG_INDEX_CSV,
    results_root: str | Path = DEFAULT_RESULTS_ROOT,
) -> tuple[list[dict[str, object]], list[str], list[str], list[str]]:
    columns = read_schema_columns(schema_csv)
    index_rows = read_candidate_config_index(config_index_csv)
    result_root = _resolve_path(results_root)
    included: list[str] = []
    missing: list[str] = []
    dataset_rows: list[dict[str, object]] = []

    for index_row in index_rows:
        variant_id = index_row["variant_id"]
        result_csv = result_root / variant_id / "results.csv"
        if not result_csv.exists():
            missing.append(variant_id)
            continue
        dataset_rows.append(_align_row(build_dataset_row(index_row, result_csv), columns))
        included.append(variant_id)
    return dataset_rows, included, missing, columns


def write_dataset_csv(rows: list[dict[str, object]], output_csv: str | Path, columns: list[str]) -> Path:
    path = _resolve_path(output_csv)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_collection_report(
    path: str | Path,
    *,
    rows: list[dict[str, object]],
    included: list[str],
    missing: list[str],
) -> Path:
    report_path = _resolve_path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    phases = [float(row["phase_deg"]) for row in rows]
    early_pass = [str(row["variant_id"]) for row in rows if str(row["overall_early_pass"]) == "True"]
    lines = [
        "# APCD K=6 ML-Ready Dataset v0 Collection Report",
        "",
        "Scope: 09-P1 collection only. No new FDTD run was performed. No lumapi call was made. No `.fsp` file was exported. No model was trained. No new candidate pool was generated. This is not a steering result.",
        "",
        f"Dataset rows: {len(rows)}",
        f"Included variants: {', '.join(included) if included else 'none'}",
        f"Missing variants: {', '.join(missing) if missing else 'none'}",
        f"Phase range deg: {_range_text(phases)}",
        f"Overall early pass count: {len(early_pass)}",
        f"Overall early pass variants: {', '.join(early_pass) if early_pass else 'none'}",
        "",
        "Early pass thresholds:",
        "",
        "- `target_conversion >= 0.5`",
        "- `opposite_spin_leakage <= 0.2`",
        "- `conversion_to_leakage_ratio >= 6`",
        "",
        "This dataset is only suitable for initial surrogate/data plumbing. It is too small to train a reliable model.",
    ]
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report_path


def write_outputs(
    *,
    schema_csv: str | Path = DEFAULT_SCHEMA_CSV,
    config_index_csv: str | Path = DEFAULT_CONFIG_INDEX_CSV,
    results_root: str | Path = DEFAULT_RESULTS_ROOT,
    output_csv: str | Path = DEFAULT_OUTPUT_CSV,
    collection_report: str | Path = DEFAULT_COLLECTION_REPORT,
) -> tuple[Path, Path, list[dict[str, object]], list[str], list[str]]:
    rows, included, missing, columns = collect_ml_dataset_v0(
        schema_csv=schema_csv,
        config_index_csv=config_index_csv,
        results_root=results_root,
    )
    dataset_path = write_dataset_csv(rows, output_csv, columns)
    report_path = write_collection_report(collection_report, rows=rows, included=included, missing=missing)
    return dataset_path, report_path, rows, included, missing


def main() -> int:
    args = parse_args()
    dataset_path, report_path, rows, included, missing = write_outputs(
        schema_csv=args.schema_csv,
        config_index_csv=args.config_index,
        results_root=args.results_root,
        output_csv=args.output_csv,
        collection_report=args.collection_report,
    )
    phases = [float(row["phase_deg"]) for row in rows]
    early_pass_count = sum(1 for row in rows if str(row["overall_early_pass"]) == "True")
    print(f"rows={len(rows)}")
    print(f"included_variants={','.join(included)}")
    print(f"missing_variants={','.join(missing) if missing else 'none'}")
    print(f"phase_range_deg={_range_text(phases)}")
    print(f"overall_early_pass_count={early_pass_count}")
    print(f"output_csv={dataset_path}")
    print(f"collection_report={report_path}")
    print("status=collection_only_no_fdtd_no_lumapi_no_fsp_no_training_no_new_candidates")
    return 0


def _align_row(row: dict[str, object], columns: list[str]) -> dict[str, object]:
    return {column: row.get(column, "") for column in columns}


def _resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


def _number(value: object) -> int | float:
    number = float(value)
    return int(number) if number.is_integer() else number


def _relative_posix(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def _range_text(values: list[float]) -> str:
    if not values:
        return "none"
    return f"{min(values):.12g} to {max(values):.12g}"


if __name__ == "__main__":
    raise SystemExit(main())
