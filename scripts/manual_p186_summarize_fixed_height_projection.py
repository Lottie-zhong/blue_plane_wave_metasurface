from __future__ import annotations

from pathlib import Path
import csv
import math
import cmath
import yaml

ROOT = Path(__file__).resolve().parents[1]
SEL = ROOT / "outputs/apcd_k6_active_learning/p185_fixed_height_projection_fdtd_selection.csv"
OUT = ROOT / "outputs/apcd_k6_active_learning/p186_fixed_height_projection_results.csv"
DEC = ROOT / "outputs/apcd_k6_active_learning/p186_fixed_height_projection_decision.csv"
MD = ROOT / "reports/p186_fixed_height_projection_results.md"

TARGET_BINS = [-180, -120, -60, 0, 60, 120]


def safe_float(x, default=float("nan")):
    try:
        if x is None or str(x).strip() == "":
            return default
        return float(x)
    except Exception:
        return default


def parse_bool(x) -> bool:
    return str(x).strip().lower() in {"true", "1", "yes", "ok"}


def nearest_bin(phase: float):
    if math.isnan(phase):
        return ""
    def err(b):
        return abs((phase - b + 180) % 360 - 180)
    return min(TARGET_BINS, key=err)


def phase_error(phase: float, b):
    if b == "" or math.isnan(phase):
        return float("nan")
    return abs((phase - b + 180) % 360 - 180)


def parse_complex(s: str) -> complex:
    return complex(str(s).strip().replace("i", "j"))


def read_result_csv(path: Path) -> dict:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        return {}
    return rows[0]


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
    with open(SEL, newline="", encoding="utf-8") as f:
        selection = list(csv.DictReader(f))

    rows = []

    for s in selection:
        config_path = ROOT / s["config_path"]
        result_csv = result_path_from_config(config_path)

        r = read_result_csv(result_csv) if result_csv.exists() else {}

        status = str(r.get("status", "missing_result")).strip() or "unknown"
        phase_deg = get_phase_deg(r)

        target = safe_float(r.get("target_conversion", r.get("target", "")))
        leakage = safe_float(r.get("opposite_spin_leakage", r.get("leakage", "")))
        ratio = safe_float(r.get("conversion_to_leakage_ratio", r.get("ratio", "")))

        nb = nearest_bin(phase_deg)
        err = phase_error(phase_deg, nb)

        has_metrics = not any(math.isnan(x) for x in [target, leakage, ratio])
        early = bool(has_metrics and target >= 0.5 and leakage <= 0.2 and ratio >= 6)
        opens_source = bool(early and nb != "" and int(float(s["source_target_bin_deg"])) == int(nb))

        rows.append({
            "candidate_id": s["candidate_id"],
            "fixed_height_nm": s["fixed_height_nm"],
            "source_target_bin_deg": s["source_target_bin_deg"],
            "source_candidate_id": s["source_candidate_id"],
            "status": status,
            "phase_deg": "" if math.isnan(phase_deg) else f"{phase_deg:.9f}",
            "nearest_bin_deg": nb,
            "phase_error_to_nearest_bin_deg": "" if math.isnan(err) else f"{err:.9f}",
            "target_conversion": "" if math.isnan(target) else f"{target:.9f}",
            "opposite_spin_leakage": "" if math.isnan(leakage) else f"{leakage:.9f}",
            "conversion_to_leakage_ratio": "" if math.isnan(ratio) else f"{ratio:.9f}",
            "has_metrics": has_metrics,
            "early_pass": early,
            "opens_original_source_bin": opens_source,
            "result_csv": str(result_csv.relative_to(ROOT)).replace("\\", "/"),
        })

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    decision_rows = []
    for h in sorted({r["fixed_height_nm"] for r in rows}, key=float):
        sub = [r for r in rows if r["fixed_height_nm"] == h]
        valid = [r for r in sub if r["has_metrics"] is True]
        early_rows = [r for r in valid if r["early_pass"] is True]

        nearest_bins = sorted({int(r["nearest_bin_deg"]) for r in valid if r["nearest_bin_deg"] != ""})
        early_bins = sorted({int(r["nearest_bin_deg"]) for r in early_rows if r["nearest_bin_deg"] != ""})

        if valid:
            best = max(valid, key=lambda r: safe_float(r["conversion_to_leakage_ratio"], -1))
            best_candidate = best["candidate_id"]
            best_ratio = safe_float(best["conversion_to_leakage_ratio"], -1)
        else:
            best_candidate = ""
            best_ratio = float("nan")

        decision_rows.append({
            "fixed_height_nm": h,
            "tested_count": len(sub),
            "ok_or_metric_count": len(valid),
            "error_or_missing_count": len(sub) - len(valid),
            "early_pass_count": len(early_rows),
            "nearest_bins_seen": ";".join(map(str, nearest_bins)),
            "early_pass_bins_seen": ";".join(map(str, early_bins)),
            "best_candidate_by_ratio": best_candidate,
            "best_ratio": "" if math.isnan(best_ratio) else f"{best_ratio:.9f}",
        })

    with open(DEC, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(decision_rows[0].keys()))
        writer.writeheader()
        writer.writerows(decision_rows)

    lines = [
        "# P186 fixed-height projection results",
        "",
        "## Scope",
        "",
        "- Single-dimer fixed-height projection only.",
        "- No K=6 supercell run.",
        "- No +15 deg steering claim.",
        "- Mixed-height K=6 remains proof-of-concept only.",
        "",
        "## Height-level summary",
        "",
        "| fixed h | tested | valid metrics | error/missing | early-pass count | nearest bins seen | early-pass bins seen | best ratio | best candidate |",
        "|---:|---:|---:|---:|---:|---|---|---:|---|",
    ]

    for d in decision_rows:
        br = d["best_ratio"] if d["best_ratio"] != "" else "nan"
        lines.append(
            f"| {d['fixed_height_nm']} | {d['tested_count']} | {d['ok_or_metric_count']} | "
            f"{d['error_or_missing_count']} | {d['early_pass_count']} | "
            f"{d['nearest_bins_seen']} | {d['early_pass_bins_seen']} | "
            f"{br} | `{d['best_candidate_by_ratio']}` |"
        )

    lines += [
        "",
        "## Candidate results",
        "",
        "| h | source bin | status | nearest bin | phase | target | leakage | ratio | early | candidate |",
        "|---:|---:|---|---:|---:|---:|---:|---:|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r['fixed_height_nm']} | {r['source_target_bin_deg']} | {r['status']} | "
            f"{r['nearest_bin_deg']} | {r['phase_deg']} | {r['target_conversion']} | "
            f"{r['opposite_spin_leakage']} | {r['conversion_to_leakage_ratio']} | "
            f"{r['early_pass']} | `{r['candidate_id']}` |"
        )

    lines += [
        "",
        "## Preliminary interpretation",
        "",
        "- h300 is likely the best next fixed-height branch if it retains two early-pass useful bins.",
        "- h232 remains useful as the zero-bin reference.",
        "- h425 is not preferred unless later recovery improves leakage and failed candidates.",
        "",
        "## Next decision",
        "",
        "- Use this result to choose the next lateral compensation branch.",
        "- Do not re-enter K=6 until a fixed-height six-bin single-dimer library is available.",
    ]

    MD.parent.mkdir(parents=True, exist_ok=True)
    MD.write_text("\n".join(lines), encoding="utf-8")

    print(f"results={OUT}")
    print(f"decision={DEC}")
    print(f"report={MD}")
    for d in decision_rows:
        print(d)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
