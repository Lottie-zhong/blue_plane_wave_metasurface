from __future__ import annotations

from pathlib import Path
import csv
import math
import cmath
import yaml

ROOT = Path(__file__).resolve().parents[1]

PLAN = ROOT / "outputs/apcd_k6_active_learning/p188_h320_lateral_compensation_scout_plan.csv"
OUT = ROOT / "outputs/apcd_k6_active_learning/p188_h320_lateral_compensation_scout_results.csv"
DEC = ROOT / "outputs/apcd_k6_active_learning/p188_h320_lateral_compensation_scout_decision.csv"
MD = ROOT / "reports/p188_h320_lateral_compensation_scout_results.md"

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

        rows.append({
            "candidate_id": p["candidate_id"],
            "branch": p["branch"],
            "variant_id": p["variant_id"],
            "purpose": p["purpose"],
            "status": status,
            "phase_deg": "" if math.isnan(phase) else f"{phase:.9f}",
            "nearest_bin_deg": nb,
            "phase_error_to_nearest_bin_deg": "" if math.isnan(err) else f"{err:.9f}",
            "target_conversion": "" if math.isnan(target) else f"{target:.9f}",
            "opposite_spin_leakage": "" if math.isnan(leakage) else f"{leakage:.9f}",
            "conversion_to_leakage_ratio": "" if math.isnan(ratio) else f"{ratio:.9f}",
            "early_pass": early,
            "result_csv": str(result_csv.relative_to(ROOT)).replace("\\", "/"),
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    decision = []
    for branch in ["p060", "p000", "m180"]:
        sub = [r for r in rows if r["branch"] == branch]
        valid = [r for r in sub if r["target_conversion"] != ""]
        early_rows = [r for r in valid if r["early_pass"] is True]
        bins = sorted({int(r["nearest_bin_deg"]) for r in valid if r["nearest_bin_deg"] != ""})
        early_bins = sorted({int(r["nearest_bin_deg"]) for r in early_rows if r["nearest_bin_deg"] != ""})
        best = max(valid, key=lambda r: safe_float(r["conversion_to_leakage_ratio"], -1)) if valid else None

        decision.append({
            "branch": branch,
            "tested_count": len(sub),
            "valid_count": len(valid),
            "early_pass_count": len(early_rows),
            "nearest_bins_seen": ";".join(map(str, bins)),
            "early_pass_bins_seen": ";".join(map(str, early_bins)),
            "best_candidate": best["candidate_id"] if best else "",
            "best_ratio": best["conversion_to_leakage_ratio"] if best else "",
        })

    with open(DEC, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(decision[0].keys()))
        writer.writeheader()
        writer.writerows(decision)

    lines = [
        "# P188 h320 lateral compensation scout results",
        "",
        "## Scope",
        "",
        "- Fixed-height h320 single-dimer candidates only.",
        "- L/W/aspect compensation only.",
        "- No K=6 supercell run.",
        "- No +15 deg steering claim.",
        "",
        "## Branch summary",
        "",
        "| branch | tested | valid | early | bins seen | early bins | best ratio | best candidate |",
        "|---|---:|---:|---:|---|---|---:|---|",
    ]

    for d in decision:
        lines.append(
            f"| {d['branch']} | {d['tested_count']} | {d['valid_count']} | "
            f"{d['early_pass_count']} | {d['nearest_bins_seen']} | {d['early_pass_bins_seen']} | "
            f"{d['best_ratio']} | `{d['best_candidate']}` |"
        )

    lines += [
        "",
        "## Candidate results",
        "",
        "| branch | variant | status | nearest bin | phase | target | leakage | ratio | early | candidate |",
        "|---|---|---|---:|---:|---:|---:|---:|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r['branch']} | {r['variant_id']} | {r['status']} | "
            f"{r['nearest_bin_deg']} | {r['phase_deg']} | {r['target_conversion']} | "
            f"{r['opposite_spin_leakage']} | {r['conversion_to_leakage_ratio']} | "
            f"{r['early_pass']} | `{r['candidate_id']}` |"
        )

    lines += [
        "",
        "## Decision rule",
        "",
        "- If p060 branch recovers early-pass 60 at h320, keep it as h320 60 anchor.",
        "- If p000 branch moves toward 0 but ratio fails, use helper/notch recovery later.",
        "- If m180 branch opens -120 at h320, keep h320 as primary fixed-height platform.",
        "- Do not proceed to K=6 until h320 fixed-height single-dimer coverage is sufficient.",
    ]

    MD.parent.mkdir(parents=True, exist_ok=True)
    MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"results={OUT}")
    print(f"decision={DEC}")
    print(f"report={MD}")
    for d in decision:
        print(d)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
