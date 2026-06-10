from __future__ import annotations

from pathlib import Path
import csv
import math
import cmath
import yaml
from collections import defaultdict

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")

CONFIG_DIR = ROOT / "configs" / "apcd_k6_phase_state_candidates"
OUT_CSV = ROOT / "outputs" / "apcd_k6_active_learning" / "p197_fixed_height_platform_diagnostic_all_results.csv"
OUT_BY_H = ROOT / "outputs" / "apcd_k6_active_learning" / "p197_fixed_height_platform_diagnostic_by_height.csv"
REPORT = ROOT / "reports" / "p197_fixed_height_platform_diagnostic.md"

TARGET_BINS = [-180, -120, -60, 0, 60, 120]
EARLY_TARGET_MIN = 0.5
EARLY_LEAKAGE_MAX = 0.2
EARLY_RATIO_MIN = 6.0


def safe_float(x, default=float("nan")):
    try:
        if x is None or str(x).strip() == "":
            return default
        return float(x)
    except Exception:
        return default


def parse_complex(s: str) -> complex:
    return complex(str(s).strip().replace("i", "j"))


def phase_from_row(row: dict) -> float:
    raw = str(row.get("t_alpha_star_from_alpha", "")).strip()
    if raw:
        try:
            return math.degrees(cmath.phase(parse_complex(raw)))
        except Exception:
            pass
    return safe_float(row.get("phase_deg", ""))


def phase_dist(a: float, b: float) -> float:
    return abs((a - b + 180) % 360 - 180)


def nearest_bin(phase: float):
    if math.isnan(phase):
        return ""
    return min(TARGET_BINS, key=lambda b: phase_dist(phase, b))


def first_float_from_objects(obj, keys=("height_nm",)):
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in keys:
                val = safe_float(v)
                if not math.isnan(val):
                    return val
            found = first_float_from_objects(v, keys)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = first_float_from_objects(v, keys)
            if found is not None:
                return found
    return None


def collect_pillar_heights(obj):
    heights = []

    def rec(x):
        if isinstance(x, dict):
            if "height_nm" in x:
                val = safe_float(x.get("height_nm"))
                if not math.isnan(val):
                    heights.append(val)
            for v in x.values():
                rec(v)
        elif isinstance(x, list):
            for v in x:
                rec(v)

    rec(obj)
    return heights


def read_first_result(path: Path):
    if not path.exists():
        return None
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else None


def find_result_csv_from_config(cfg: dict, config_path: Path):
    result_dir = cfg.get("output", {}).get("result_dir")
    if result_dir:
        p = ROOT / result_dir / "results.csv"
        if p.exists():
            return p

    candidate_id = config_path.stem
    hits = list((ROOT / "outputs").rglob(f"{candidate_id}/results.csv"))
    if hits:
        hits.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return hits[0]
    return None


def classify_family(candidate_id: str) -> str:
    s = candidate_id.lower()
    if "p196" in s:
        return "p196_h320_zero_scout"
    if "p195" in s:
        return "p195_h320_m60_scout"
    if "p190" in s:
        return "p190_h320_m120_recovery"
    if "p188" in s:
        return "p188_h320_lateral"
    if "p187" in s or "fh" in s:
        return "fixed_height_platform_scan"
    if "p185" in s:
        return "p185_fixed_height_projection"
    if "zero" in s:
        return "zero_family"
    if "060" in s or "p060" in s:
        return "sixty_family"
    return "other"


def main() -> int:
    rows = []

    for config_path in CONFIG_DIR.glob("*.yaml"):
        candidate_id = config_path.stem

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f)
        except Exception:
            continue

        if not isinstance(cfg, dict):
            continue

        heights = collect_pillar_heights(cfg)
        fixed_height = ""
        same_height = False
        if heights:
            rounded = sorted({round(h, 6) for h in heights})
            same_height = len(rounded) == 1
            if same_height:
                fixed_height = rounded[0]
            else:
                fixed_height = "mixed"

        result_csv = find_result_csv_from_config(cfg, config_path)
        if result_csv is None:
            continue

        r = read_first_result(result_csv)
        if not r:
            continue

        phase = phase_from_row(r)
        nb = nearest_bin(phase)
        target = safe_float(r.get("target_conversion", ""))
        leakage = safe_float(r.get("opposite_spin_leakage", ""))
        ratio = safe_float(r.get("conversion_to_leakage_ratio", ""))

        has_metrics = not any(math.isnan(x) for x in [target, leakage, ratio])
        early = bool(has_metrics and target >= EARLY_TARGET_MIN and leakage <= EARLY_LEAKAGE_MAX and ratio >= EARLY_RATIO_MIN)

        # Phase-hit means phase enters a bin and target is not collapsed, regardless of leakage/ratio.
        phase_hit = bool(nb != "" and not math.isnan(target) and target >= EARLY_TARGET_MIN)

        rows.append({
            "candidate_id": candidate_id,
            "family": classify_family(candidate_id),
            "same_height": same_height,
            "height_nm": fixed_height,
            "nearest_bin_deg": nb,
            "phase_deg": "" if math.isnan(phase) else f"{phase:.9f}",
            "target_conversion": "" if math.isnan(target) else f"{target:.9f}",
            "opposite_spin_leakage": "" if math.isnan(leakage) else f"{leakage:.9f}",
            "conversion_to_leakage_ratio": "" if math.isnan(ratio) else f"{ratio:.9f}",
            "early_pass": early,
            "phase_hit": phase_hit,
            "config_path": str(config_path.relative_to(ROOT)).replace("\\", "/"),
            "result_csv": str(result_csv.relative_to(ROOT)).replace("\\", "/"),
        })

    rows.sort(key=lambda r: (str(r["height_nm"]), str(r["nearest_bin_deg"]), r["candidate_id"]))

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            writer.writeheader()
            writer.writerows(rows)

    by_h = defaultdict(list)
    for r in rows:
        if r["same_height"] is True and r["height_nm"] != "mixed":
            by_h[str(r["height_nm"])].append(r)

    summary_rows = []
    for h, items in by_h.items():
        early_items = [r for r in items if r["early_pass"] is True]
        phasehit_items = [r for r in items if r["phase_hit"] is True]

        early_bins = sorted({int(r["nearest_bin_deg"]) for r in early_items if r["nearest_bin_deg"] != ""})
        phasehit_bins = sorted({int(r["nearest_bin_deg"]) for r in phasehit_items if r["nearest_bin_deg"] != ""})
        missing_early = [b for b in TARGET_BINS if b not in early_bins]

        # score emphasizes number of early bins, then phase-hit diversity, then max ratio.
        max_ratio = max([safe_float(r["conversion_to_leakage_ratio"], -1) for r in items], default=-1)
        score = 10 * len(early_bins) + 2 * len(phasehit_bins) + min(max_ratio, 50) / 50

        summary_rows.append({
            "height_nm": h,
            "tested": len(items),
            "early_pass_count": len(early_items),
            "phase_hit_count": len(phasehit_items),
            "early_bins": " ".join(map(str, early_bins)),
            "phase_hit_bins": " ".join(map(str, phasehit_bins)),
            "missing_early_bins": " ".join(map(str, missing_early)),
            "max_ratio": f"{max_ratio:.6f}",
            "platform_score": f"{score:.6f}",
        })

    summary_rows.sort(key=lambda r: safe_float(r["platform_score"], -1), reverse=True)

    if summary_rows:
        with open(OUT_BY_H, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
            writer.writeheader()
            writer.writerows(summary_rows)

    lines = [
        "# P197 fixed-height platform diagnostic",
        "",
        "## Purpose",
        "",
        "- Re-rank fixed-height platforms using existing real FDTD results.",
        "- No new FDTD run.",
        "- No K=6 / steering claim.",
        "- Focus: choose a better fixed-height platform for missing 0 / 60 / -60 bins.",
        "",
        "## By-height summary",
        "",
        "| height_nm | tested | early_pass | phase_hit | early_bins | phase_hit_bins | missing_early_bins | max_ratio | score |",
        "|---:|---:|---:|---:|---|---|---|---:|---:|",
    ]

    for r in summary_rows:
        lines.append(
            f"| {r['height_nm']} | {r['tested']} | {r['early_pass_count']} | {r['phase_hit_count']} | "
            f"{r['early_bins']} | {r['phase_hit_bins']} | {r['missing_early_bins']} | "
            f"{r['max_ratio']} | {r['platform_score']} |"
        )

    lines += [
        "",
        "## Interpretation guide",
        "",
        "- Prefer heights with multiple early bins and at least one missing-bin phase-hit.",
        "- Avoid platforms where all knobs collapse into the same 1-2 phase basins.",
        "- h320 is expected to score high in selectivity but may show basin locking.",
        "- h300/h280-type platforms may be more flexible for 60/0 exploration even if less complete initially.",
        "",
        f"all_results_csv: `{OUT_CSV.relative_to(ROOT)}`",
        f"by_height_csv: `{OUT_BY_H.relative_to(ROOT)}`",
    ]

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"all_results_csv={OUT_CSV}")
    print(f"by_height_csv={OUT_BY_H}")
    print(f"report={REPORT}")
    print("\n=== by-height summary ===")
    print("height_nm\ttested\tearly_pass_count\tphase_hit_count\tearly_bins\tphase_hit_bins\tmissing_early_bins\tmax_ratio\tplatform_score")
    for r in summary_rows:
        print(
            f"{r['height_nm']}\t{r['tested']}\t{r['early_pass_count']}\t{r['phase_hit_count']}\t"
            f"{r['early_bins']}\t{r['phase_hit_bins']}\t{r['missing_early_bins']}\t"
            f"{r['max_ratio']}\t{r['platform_score']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
