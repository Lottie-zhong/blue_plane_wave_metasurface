from __future__ import annotations

from pathlib import Path
import csv
import math
import cmath
import yaml

ROOT = Path(__file__).resolve().parents[1]

PLAN = ROOT / "outputs/apcd_k6_active_learning/p192_h320_p060_nearmiss_refine_plan.csv"
OUT = ROOT / "outputs/apcd_k6_active_learning/p192_h320_p060_nearmiss_refine_results.csv"
MD = ROOT / "reports/p192_h320_p060_nearmiss_refine_results.md"

TARGET_BINS = [-180, -120, -60, 0, 60, 120]


def safe_float(x, default=float("nan")):
    try:
        if x is None or str(x).strip() == "":
            return default
        return float(x)
    except Exception:
        return default


def nearest_bin(phase: float):
    if math.isnan(phase):
        return ""
    return min(TARGET_BINS, key=lambda b: abs((phase - b + 180) % 360 - 180))


def phase_error(phase: float, b):
    if b == "" or math.isnan(phase):
        return float("nan")
    return abs((phase - b + 180) % 360 - 180)


def parse_complex(s: str) -> complex:
    return complex(str(s).strip().replace("i", "j"))


def read_result_csv(path: Path) -> dict:
    if not path.exists():
        return {"status": "missing_result"}
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else {"status": "empty_result"}


def result_path_from_config(config_path: Path) -> Path:
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    result_dir = cfg.get("output", {}).get("result_dir")
    if not result_dir:
        raise RuntimeError(f"missing output.result_dir in {config_path}")
    return ROOT / result_dir / "results.csv"


def get_phase_deg(r: dict) -> float:
    amp_raw = str(r.get("t_alpha_star_from_alpha", "")).strip()
    if amp_raw:
        try:
            return math.degrees(cmath.phase(parse_complex(amp_raw)))
        except Exception:
            pass
    return safe_float(r.get("phase_deg", ""))


def main() -> int:
    with open(PLAN, newline="", encoding="utf-8") as f:
        plan = list(csv.DictReader(f))

    rows = []

    for p in plan:
        result_csv = result_path_from_config(ROOT / p["config_path"])
        r = read_result_csv(result_csv)

        status = str(r.get("status", "unknown")).strip() or "unknown"
        phase = get_phase_deg(r)
        target = safe_float(r.get("target_conversion", ""))
        leakage = safe_float(r.get("opposite_spin_leakage", ""))
        ratio = safe_float(r.get("conversion_to_leakage_ratio", ""))

        nb = nearest_bin(phase)
        err = phase_error(phase, nb)

        has_metrics = not any(math.isnan(x) for x in [target, leakage, ratio])
        early = bool(has_metrics and target >= 0.5 and leakage <= 0.2 and ratio >= 6)
        opens_p060 = bool(early and nb == 60)

        rows.append({
            "candidate_id": p["candidate_id"],
            "base_key": p["base_key"],
            "variant_id": p["variant_id"],
            "status": status,
            "phase_deg": "" if math.isnan(phase) else f"{phase:.9f}",
            "nearest_bin_deg": nb,
            "phase_error_to_nearest_bin_deg": "" if math.isnan(err) else f"{err:.9f}",
            "target_conversion": "" if math.isnan(target) else f"{target:.9f}",
            "opposite_spin_leakage": "" if math.isnan(leakage) else f"{leakage:.9f}",
            "conversion_to_leakage_ratio": "" if math.isnan(ratio) else f"{ratio:.9f}",
            "early_pass": early,
            "opens_p060": opens_p060,
            "result_csv": str(result_csv.relative_to(ROOT)).replace("\\", "/"),
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    valid = [r for r in rows if r["target_conversion"] != ""]
    early_rows = [r for r in valid if r["early_pass"] is True]
    hit_rows = [r for r in valid if r["opens_p060"] is True]

    best = max(valid, key=lambda r: safe_float(r["conversion_to_leakage_ratio"], -1)) if valid else None
    best_hit = max(hit_rows, key=lambda r: safe_float(r["conversion_to_leakage_ratio"], -1)) if hit_rows else None

    lines = [
        "# P192 h320 p060 near-miss refinement results",
        "",
        "## Scope",
        "",
        "- Fixed-height h320 single-dimer candidates only.",
        "- Target: push P191 near-miss over early-pass threshold for 60 bin.",
        "- No K=6 supercell run.",
        "- No +15 deg steering claim.",
        "",
        "## Summary",
        "",
        f"- tested: {len(rows)}",
        f"- valid: {len(valid)}",
        f"- early_pass: {len(early_rows)}",
        f"- opens_p060: {len(hit_rows)}",
        f"- best_candidate: `{best['candidate_id'] if best else ''}`",
        f"- best_ratio: {best['conversion_to_leakage_ratio'] if best else ''}",
        f"- best_p060_candidate: `{best_hit['candidate_id'] if best_hit else ''}`",
        f"- best_p060_ratio: {best_hit['conversion_to_leakage_ratio'] if best_hit else ''}",
        "",
        "## Candidate results",
        "",
        "| base | variant | status | nearest bin | phase | target | leakage | ratio | early | opens 60 | candidate |",
        "|---|---|---|---:|---:|---:|---:|---:|---|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r['base_key']} | {r['variant_id']} | {r['status']} | "
            f"{r['nearest_bin_deg']} | {r['phase_deg']} | {r['target_conversion']} | "
            f"{r['opposite_spin_leakage']} | {r['conversion_to_leakage_ratio']} | "
            f"{r['early_pass']} | {r['opens_p060']} | `{r['candidate_id']}` |"
        )

    lines += [
        "",
        "## Decision rule",
        "",
        "- If opens_p060 > 0, freeze best 60 candidate.",
        "- If best ratio is still 5-6, use one final tiny recovery around best candidate.",
        "- If phase crosses into 120, do not keep it as 60 anchor.",
        "- Do not proceed to K=6 until fixed-height six-bin coverage exists.",
    ]

    MD.parent.mkdir(parents=True, exist_ok=True)
    MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"results={OUT}")
    print(f"report={MD}")
    if best:
        print("best", best)
    if best_hit:
        print("best_hit", best_hit)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
