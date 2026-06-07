from __future__ import annotations

import argparse
import cmath
import csv
import math
import re
import sys
from pathlib import Path
from typing import Iterable, Sequence


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from metasurface.apcd_active_learning import wrap_phase_deg  # noqa: E402


TARGET_BINS_DEG = [-180.0, -120.0, -60.0, 0.0, 60.0, 120.0]
EARLY_TARGET_MIN = 0.5
EARLY_LEAKAGE_MAX = 0.2
EARLY_RATIO_MIN = 6.0
ZERO_KEYWORDS = ("zero", "p1geom", "l60", "retention")
P165_ZERO_CLIFF_PREFIX = "cpk_zero_l60_lhs_h232"
STAGE_143_TO_163_RE = re.compile(r"p(14[3-9]|15[0-9]|16[0-3])", re.IGNORECASE)

ACTIVE_DIR = REPO_ROOT / "outputs/apcd_k6_active_learning"
RESULT_ROOT = REPO_ROOT / "outputs/apcd_k6_metagrating_633nm/phase_state_candidates"
CONFIG_DIR = REPO_ROOT / "configs/apcd_k6_phase_state_candidates"
DATABASE_CSV = ACTIVE_DIR / "combined_phase_knob_p164_zero_stage_database.csv"
REPORT_MD = REPO_ROOT / "reports/combined_phase_knob_p164_zero_stage_database.md"

DATABASE_FIELDS = [
    "candidate_id",
    "discovery_source",
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a compact local database for stage09 P143-P163 zero-bin candidates."
    )
    parser.add_argument("--active-dir", type=Path, default=ACTIVE_DIR)
    parser.add_argument("--result-root", type=Path, default=RESULT_ROOT)
    parser.add_argument("--config-dir", type=Path, default=CONFIG_DIR)
    parser.add_argument("--output-csv", type=Path, default=DATABASE_CSV)
    parser.add_argument("--report", type=Path, default=REPORT_MD)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    candidates = discover_zero_candidates(args.active_dir, args.result_root, args.config_dir)
    rows = build_database_rows(candidates, args.result_root)
    write_csv_rows(rows, args.output_csv, DATABASE_FIELDS)
    write_report(args.report, rows, args)
    print(f"database_csv={args.output_csv}")
    print(f"report={args.report}")
    print("status=stage09_zero_database_built_no_fdtd_no_lumapi")
    return 0


def discover_zero_candidates(active_dir: Path, result_root: Path, config_dir: Path) -> dict[str, str]:
    candidates: dict[str, str] = {}
    if active_dir.exists():
        for csv_path in sorted(active_dir.glob("*.csv")):
            if not STAGE_143_TO_163_RE.search(csv_path.name):
                continue
            for candidate_id in candidate_ids_from_csv(csv_path):
                if is_zero_candidate(candidate_id) or "zero" in csv_path.name.lower():
                    candidates.setdefault(candidate_id, relative_path(csv_path))

    if config_dir.exists():
        for config_path in sorted(config_dir.glob("*.yaml")):
            candidate_id = config_path.stem
            if is_zero_candidate(candidate_id):
                candidates.setdefault(candidate_id, f"config:{relative_path(config_path)}")

    if result_root.exists():
        for candidate_dir in sorted(path for path in result_root.iterdir() if path.is_dir()):
            candidate_id = candidate_dir.name
            if is_zero_candidate(candidate_id):
                candidates.setdefault(candidate_id, f"result_dir:{relative_path(candidate_dir)}")

    return candidates


def candidate_ids_from_csv(path: Path) -> list[str]:
    try:
        rows = read_csv_rows(path)
    except (OSError, csv.Error):
        return []
    ids: list[str] = []
    for row in rows:
        for key in ("candidate_id", "variant_id", "id", "candidate"):
            value = (row.get(key) or "").strip()
            if value:
                ids.append(value)
                break
    return ids


def is_zero_candidate(candidate_id: str) -> bool:
    lower = candidate_id.lower()
    if lower.startswith(P165_ZERO_CLIFF_PREFIX):
        return False
    return any(keyword in lower for keyword in ZERO_KEYWORDS)


def build_database_rows(candidates: dict[str, str], result_root: Path) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for candidate_id, source in sorted(candidates.items()):
        result_csv = result_root / candidate_id / "results.csv"
        if not result_csv.exists():
            rows.append(missing_result_row(candidate_id, source, result_csv))
            continue
        raw_rows = read_csv_rows(result_csv)
        if not raw_rows:
            rows.append(missing_result_row(candidate_id, source, result_csv, note="empty results.csv"))
            continue
        rows.append(summarize_result_row(candidate_id, source, result_csv, raw_rows[0]))
    return rows


def summarize_result_row(candidate_id: str, source: str, result_csv: Path, raw: dict[str, str]) -> dict[str, object]:
    phase = phase_from_row(raw)
    nearest_bin, phase_error = nearest_phase_bin(phase, TARGET_BINS_DEG)
    target = optional_float(raw, ("target_conversion", "target"))
    leakage = optional_float(raw, ("opposite_spin_leakage", "leakage"))
    ratio = optional_float(raw, ("conversion_to_leakage_ratio", "ratio"))
    pd = optional_float(raw, ("PD", "pd"))
    early = early_pass(target, leakage, ratio)
    opens = bool(early and nearest_bin == 0.0)
    return {
        "candidate_id": candidate_id,
        "discovery_source": source,
        "result_status": raw.get("status", "result_present"),
        "phase_deg": phase,
        "nearest_bin": as_number(nearest_bin),
        "phase_error_deg": phase_error,
        "target_conversion": empty_if_none(target),
        "opposite_spin_leakage": empty_if_none(leakage),
        "conversion_to_leakage_ratio": empty_if_none(ratio),
        "PD": empty_if_none(pd),
        "early_pass": early,
        "opens_0": opens,
        "source_result_csv": relative_path(result_csv),
        "notes": "existing result summarized; no FDTD run by this script",
    }


def missing_result_row(candidate_id: str, source: str, result_csv: Path, note: str = "results.csv missing") -> dict[str, object]:
    return {
        "candidate_id": candidate_id,
        "discovery_source": source,
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
        "source_result_csv": relative_path(result_csv),
        "notes": f"{note}; run real FDTD on the server before interpreting metrics",
    }


def phase_from_row(row: dict[str, str]) -> float:
    for key in ("phase_deg", "phase"):
        value = (row.get(key) or "").strip()
        if value:
            return wrap_phase_deg(float(value))
    value = (row.get("t_alpha_star_from_alpha") or "").strip()
    if not value:
        raise ValueError("Result row has no phase_deg, phase, or t_alpha_star_from_alpha")
    return wrap_phase_deg(math.degrees(cmath.phase(complex(value))))


def nearest_phase_bin(phase_deg: float, bins: Sequence[float]) -> tuple[float, float]:
    nearest = min((float(item) for item in bins), key=lambda item: (abs(wrap_phase_deg(phase_deg - item)), item))
    return nearest, abs(wrap_phase_deg(phase_deg - nearest))


def early_pass(target: float | None, leakage: float | None, ratio: float | None) -> bool:
    if target is None or leakage is None or ratio is None:
        return False
    return target >= EARLY_TARGET_MIN and leakage <= EARLY_LEAKAGE_MAX and ratio >= EARLY_RATIO_MIN


def optional_float(row: dict[str, str], keys: Sequence[str]) -> float | None:
    for key in keys:
        value = (row.get(key) or "").strip()
        if value:
            return float(value)
    return None


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


def write_report(path: Path, rows: Sequence[dict[str, object]], args: argparse.Namespace) -> Path:
    present = [row for row in rows if row["result_status"] != "missing_result"]
    zero_open = [row for row in present if row["opens_0"] is True or row["opens_0"] == "True"]
    lines = [
        "# P164 zero-stage database",
        "",
        "## Scope",
        "",
        "Stage 09 only. This manual script reads existing local `results.csv` files for zero-branch candidates and does not run FDTD or call lumapi.",
        "",
        "No K=6 phase-ramp supercell, steering claim, stage 10 claim, Micro-LED result, or fabricated metric is made.",
        "",
        "## Inputs",
        "",
        f"- active-learning CSV directory: `{relative_path(args.active_dir)}`",
        f"- candidate result root: `{relative_path(args.result_root)}`",
        f"- candidate config directory: `{relative_path(args.config_dir)}`",
        "",
        "## Summary",
        "",
        f"- candidates discovered: {len(rows)}",
        f"- existing result CSVs summarized: {len(present)}",
        f"- zero-bin early-pass openings found: {len(zero_open)}",
        "",
        "## Notes",
        "",
        "Missing rows are retained as `missing_result` so the workflow can be rerun after server FDTD without inventing data.",
        "Do not commit raw candidate `results.csv`, raw `summary.md`, `.fsp`, `pre_run` files, `.npy`, or large outputs.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def relative_path(path: Path) -> str:
    try:
        return path.resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def empty_if_none(value: float | None) -> float | str:
    return "" if value is None else value


def as_number(value: float) -> int | float:
    return int(value) if float(value).is_integer() else value


if __name__ == "__main__":
    raise SystemExit(main())
