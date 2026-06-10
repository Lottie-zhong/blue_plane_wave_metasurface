from __future__ import annotations

from pathlib import Path
import csv
import math
import cmath
import yaml

ROOT = Path(__file__).resolve().parents[1]

PLAN = ROOT / "outputs/apcd_k6_active_learning/p195_h320_m60_mechanism_scout_plan.csv"
OUT = ROOT / "outputs/apcd_k6_active_learning/p195_h320_m60_mechanism_scout_results.csv"
MD = ROOT / "reports/p195_h320_m60_mechanism_scout_results.md"

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


def abs_phase_to_target(phase: float, target: float) -> float:
    if math.isnan(phase):
        return float("nan")
    return abs((phase - target + 180) % 360 - 180)


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
        abs_m60 = abs_phase_to_target(phase, -60)

        has_metrics = not any(math.isnan(x) for x in [target, leakage, ratio])
        early = bool(has_metrics and target >= 0.5 and leakage <= 0.2 and ratio >= 6)

        m60_phase_hit = bool(nb == -60 and not math.isnan(target) and target > 0.5)
        m60_early = bool(early and nb == -60)
        near_m60_45 = bool(not math.isnan(abs_m60) and abs_m60 <= 45 and not math.isnan(target) and target > 0.5)

        rows.append({
            "candidate_id": p["candidate_id"],
            "group": p["group"],
            "base_key": p["base_key"],
            "variant_id": p["variant_id"],
            "status": status,
            "phase_deg": "" if math.isnan(phase) else f"{phase:.9f}",
            "abs_phase_to_m60_deg": "" if math.isnan(abs_m60) else f"{abs_m60:.9f}",
            "nearest_bin_deg": nb,
            "phase_error_to_nearest_bin_deg": "" if math.isnan(err) else f"{err:.9f}",
            "target_conversion": "" if math.isnan(target) else f"{target:.9f}",
            "opposite_spin_leakage": "" if math.isnan(leakage) else f"{leakage:.9f}",
            "conversion_to_leakage_ratio": "" if math.isnan(ratio) else f"{ratio:.9f}",
            "early_pass": early,
            "m60_phase_hit": m60_phase_hit,
            "m60_early_pass": m60_early,
            "near_m60_45deg": near_m60_45,
            "result_csv": str(result_csv.relative_to(ROOT)).replace("\\", "/"),
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    valid = [r for r in rows if r["target_conversion"] != ""]
    early_rows = [r for r in valid if r["early_pass"] is True]
    m60_hits = [r for r in valid if r["m60_phase_hit"] is True]
    m60_early = [r for r in valid if r["m60_early_pass"] is True]
    near_m60 = [r for r in valid if r["near_m60_45deg"] is True]

    best_ratio = max(valid, key=lambda r: safe_float(r["conversion_to_leakage_ratio"], -1)) if valid else None
    best_m60 = max(m60_hits, key=lambda r: safe_float(r["conversion_to_leakage_ratio"], -1)) if m60_hits else None
    closest_m60 = min(valid, key=lambda r: safe_float(r["abs_phase_to_m60_deg"], 999)) if valid else None

    lines = [
        "# P195 h320 -60 mechanism scout results",
        "",
        "## Scope",
        "",
        "- Fixed-height h320 single-dimer candidates only.",
        "- Target: find -60 phase-hit first.",
        "- Success criterion for this scout: nearest_bin=-60 and target_conversion>0.5.",
        "- Early-pass is welcome but not required.",
        "- No K=6 supercell run.",
        "- No +15 deg steering claim.",
        "",
        "## Summary",
        "",
        f"- tested: {len(rows)}",
        f"- valid_results: {len(valid)}",
        f"- early_pass: {len(early_rows)}",
        f"- m60_phase_hit_count: {len(m60_hits)}",
        f"- m60_early_pass_count: {len(m60_early)}",
        f"- near_m60_45deg_count: {len(near_m60)}",
        f"- best_ratio_candidate: `{best_ratio['candidate_id'] if best_ratio else ''}`",
        f"- best_ratio: {best_ratio['conversion_to_leakage_ratio'] if best_ratio else ''}",
        f"- best_m60_candidate: `{best_m60['candidate_id'] if best_m60 else ''}`",
        f"- best_m60_ratio: {best_m60['conversion_to_leakage_ratio'] if best_m60 else ''}",
        f"- closest_to_m60_candidate: `{closest_m60['candidate_id'] if closest_m60 else ''}`",
        f"- closest_to_m60_abs_phase_deg: {closest_m60['abs_phase_to_m60_deg'] if closest_m60 else ''}",
        "",
        "## Candidate results",
        "",
        "| group | base | variant | status | nearest bin | phase | abs phase to -60 | target | leakage | ratio | early | -60 hit | near -60 45 | candidate |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r['group']} | {r['base_key']} | {r['variant_id']} | {r['status']} | "
            f"{r['nearest_bin_deg']} | {r['phase_deg']} | {r['abs_phase_to_m60_deg']} | "
            f"{r['target_conversion']} | {r['opposite_spin_leakage']} | "
            f"{r['conversion_to_leakage_ratio']} | {r['early_pass']} | "
            f"{r['m60_phase_hit']} | {r['near_m60_45deg']} | `{r['candidate_id']}` |"
        )

    lines += [
        "",
        "## Decision rule",
        "",
        "- If m60_phase_hit_count > 0, use best -60 phase-hit for P196 leakage recovery.",
        "- If m60_early_pass_count > 0, freeze best -60 anchor directly.",
        "- If near_m60_45deg_count > 0 but no -60 hit, refine closest-to--60 mechanism.",
        "- If all candidates remain around -120/-180, stop this rotation-chain route.",
    ]

    MD.parent.mkdir(parents=True, exist_ok=True)
    MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"results={OUT}")
    print(f"report={MD}")
    if best_ratio:
        print("best_ratio", best_ratio)
    if best_m60:
        print("best_m60", best_m60)
    if closest_m60:
        print("closest_m60", closest_m60)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
