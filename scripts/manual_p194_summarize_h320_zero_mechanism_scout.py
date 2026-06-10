from __future__ import annotations

from pathlib import Path
import csv
import math
import cmath
import yaml

ROOT = Path(__file__).resolve().parents[1]

PLAN = ROOT / "outputs/apcd_k6_active_learning/p194_h320_zero_mechanism_scout_plan.csv"
OUT = ROOT / "outputs/apcd_k6_active_learning/p194_h320_zero_mechanism_scout_results.csv"
MD = ROOT / "reports/p194_h320_zero_mechanism_scout_results.md"

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


def phase_abs_to_zero(phase: float) -> float:
    if math.isnan(phase):
        return float("nan")
    return abs((phase - 0 + 180) % 360 - 180)


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
        plan_all = list(csv.DictReader(f))

    plan = [p for p in plan_all if p["generation_status"] == "generated"]
    gen_errors = [p for p in plan_all if p["generation_status"] != "generated"]

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
        abs0 = phase_abs_to_zero(phase)

        has_metrics = not any(math.isnan(x) for x in [target, leakage, ratio])
        early = bool(has_metrics and target >= 0.5 and leakage <= 0.2 and ratio >= 6)

        zero_phase_hit = bool(nb == 0 and not math.isnan(target) and target > 0.5)
        zero_early = bool(early and nb == 0)

        # Softer diagnostic: close to zero even if not in 0-bin.
        near_zero_45 = bool(not math.isnan(abs0) and abs0 <= 45 and not math.isnan(target) and target > 0.5)

        rows.append({
            "candidate_id": p["candidate_id"],
            "group": p["group"],
            "variant_id": p["variant_id"],
            "status": status,
            "phase_deg": "" if math.isnan(phase) else f"{phase:.9f}",
            "abs_phase_to_zero_deg": "" if math.isnan(abs0) else f"{abs0:.9f}",
            "nearest_bin_deg": nb,
            "phase_error_to_nearest_bin_deg": "" if math.isnan(err) else f"{err:.9f}",
            "target_conversion": "" if math.isnan(target) else f"{target:.9f}",
            "opposite_spin_leakage": "" if math.isnan(leakage) else f"{leakage:.9f}",
            "conversion_to_leakage_ratio": "" if math.isnan(ratio) else f"{ratio:.9f}",
            "early_pass": early,
            "zero_phase_hit": zero_phase_hit,
            "zero_early_pass": zero_early,
            "near_zero_45deg": near_zero_45,
            "result_csv": str(result_csv.relative_to(ROOT)).replace("\\", "/"),
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else [
            "candidate_id", "group", "variant_id", "status"
        ])
        writer.writeheader()
        writer.writerows(rows)

    valid = [r for r in rows if r["target_conversion"] != ""]
    early_rows = [r for r in valid if r["early_pass"] is True]
    zero_hits = [r for r in valid if r["zero_phase_hit"] is True]
    zero_early = [r for r in valid if r["zero_early_pass"] is True]
    near_zero = [r for r in valid if r["near_zero_45deg"] is True]

    best_ratio = max(valid, key=lambda r: safe_float(r["conversion_to_leakage_ratio"], -1)) if valid else None
    best_zero = max(zero_hits, key=lambda r: safe_float(r["conversion_to_leakage_ratio"], -1)) if zero_hits else None
    closest_zero = min(valid, key=lambda r: safe_float(r["abs_phase_to_zero_deg"], 999)) if valid else None

    lines = [
        "# P194 h320 zero-bin mechanism scout results",
        "",
        "## Scope",
        "",
        "- Fixed-height h320 single-dimer candidates only.",
        "- Target: find 0-bin phase-hit first.",
        "- Success criterion for this scout: nearest_bin=0 and target_conversion>0.5.",
        "- Early-pass is welcome but not required.",
        "- No K=6 supercell run.",
        "- No +15 deg steering claim.",
        "",
        "## Summary",
        "",
        f"- generated_candidates: {len(plan)}",
        f"- generation_errors: {len(gen_errors)}",
        f"- valid_results: {len(valid)}",
        f"- early_pass: {len(early_rows)}",
        f"- zero_phase_hit_count: {len(zero_hits)}",
        f"- zero_early_pass_count: {len(zero_early)}",
        f"- near_zero_45deg_count: {len(near_zero)}",
        f"- best_ratio_candidate: `{best_ratio['candidate_id'] if best_ratio else ''}`",
        f"- best_ratio: {best_ratio['conversion_to_leakage_ratio'] if best_ratio else ''}",
        f"- best_zero_candidate: `{best_zero['candidate_id'] if best_zero else ''}`",
        f"- best_zero_ratio: {best_zero['conversion_to_leakage_ratio'] if best_zero else ''}",
        f"- closest_to_zero_candidate: `{closest_zero['candidate_id'] if closest_zero else ''}`",
        f"- closest_to_zero_abs_phase_deg: {closest_zero['abs_phase_to_zero_deg'] if closest_zero else ''}",
        "",
    ]

    if gen_errors:
        lines += [
            "## Generation errors",
            "",
            "| group | variant | candidate | error |",
            "|---|---|---|---|",
        ]
        for r in gen_errors:
            lines.append(
                f"| {r['group']} | {r['variant_id']} | `{r['candidate_id']}` | {r['generation_error']} |"
            )
        lines.append("")

    lines += [
        "## Candidate results",
        "",
        "| group | variant | status | nearest bin | phase | abs phase to 0 | target | leakage | ratio | early | zero hit | near zero 45 | candidate |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r['group']} | {r['variant_id']} | {r['status']} | "
            f"{r['nearest_bin_deg']} | {r['phase_deg']} | {r['abs_phase_to_zero_deg']} | "
            f"{r['target_conversion']} | {r['opposite_spin_leakage']} | "
            f"{r['conversion_to_leakage_ratio']} | {r['early_pass']} | "
            f"{r['zero_phase_hit']} | {r['near_zero_45deg']} | `{r['candidate_id']}` |"
        )

    lines += [
        "",
        "## Decision rule",
        "",
        "- If zero_phase_hit_count > 0, use best zero phase-hit for P195 leakage recovery.",
        "- If near_zero_45deg_count > 0 but zero_phase_hit_count = 0, refine the closest-to-zero mechanism.",
        "- If all candidates remain in 60/120 bins, stop h320 zero small-modification route and consider a new geometry family.",
    ]

    MD.parent.mkdir(parents=True, exist_ok=True)
    MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"results={OUT}")
    print(f"report={MD}")
    if best_ratio:
        print("best_ratio", best_ratio)
    if best_zero:
        print("best_zero", best_zero)
    if closest_zero:
        print("closest_zero", closest_zero)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
