from pathlib import Path
import csv
import math

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")

IN_CSV = ROOT / "outputs" / "apcd_k6_active_learning" / "p197_fixed_height_platform_diagnostic_all_results.csv"
OUT_CSV = ROOT / "outputs" / "apcd_k6_active_learning" / "p198_h300_missing_bin_anchor_mining.csv"
REPORT = ROOT / "reports" / "p198_h300_missing_bin_anchor_mining.md"

MISSING = [-120, -60, 0]


def safe_float(x, default=float("nan")):
    try:
        if x is None or str(x).strip() == "":
            return default
        return float(x)
    except Exception:
        return default


def phase_dist(a, b):
    return abs((a - b + 180) % 360 - 180)


def recoverability_score(target, leakage, ratio, phase_err):
    # Higher is better.
    # Prioritize: target not collapsed, leakage close to <=0.2, ratio close to >=6, phase close to bin center.
    if math.isnan(target) or math.isnan(leakage) or math.isnan(ratio) or math.isnan(phase_err):
        return -999

    target_term = min(target / 0.5, 2.0) * 2.0
    leakage_term = max(0.0, 1.0 - max(0.0, leakage - 0.2) / 0.5) * 3.0
    ratio_term = min(ratio / 6.0, 1.5) * 3.0
    phase_term = max(0.0, 1.0 - phase_err / 30.0) * 2.0
    return target_term + leakage_term + ratio_term + phase_term


def main():
    with open(IN_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    h300 = [
        r for r in rows
        if str(r.get("height_nm", "")).strip() == "300.0"
        and str(r.get("same_height", "")).strip().lower() == "true"
    ]

    out = []

    for target_bin in MISSING:
        candidates = []
        for r in h300:
            nb = str(r.get("nearest_bin_deg", "")).strip()
            if nb == "":
                continue

            try:
                nb_int = int(float(nb))
            except Exception:
                continue

            if nb_int != target_bin:
                continue

            phase = safe_float(r.get("phase_deg"))
            target = safe_float(r.get("target_conversion"))
            leakage = safe_float(r.get("opposite_spin_leakage"))
            ratio = safe_float(r.get("conversion_to_leakage_ratio"))
            phase_err = phase_dist(phase, target_bin)
            score = recoverability_score(target, leakage, ratio, phase_err)

            candidates.append({
                "target_missing_bin": target_bin,
                "candidate_id": r.get("candidate_id", ""),
                "family": r.get("family", ""),
                "height_nm": r.get("height_nm", ""),
                "nearest_bin_deg": nb_int,
                "phase_deg": f"{phase:.9f}",
                "phase_error_to_target_deg": f"{phase_err:.9f}",
                "target_conversion": f"{target:.9f}",
                "opposite_spin_leakage": f"{leakage:.9f}",
                "conversion_to_leakage_ratio": f"{ratio:.9f}",
                "early_pass": r.get("early_pass", ""),
                "recoverability_score": f"{score:.6f}",
                "config_path": r.get("config_path", ""),
                "result_csv": r.get("result_csv", ""),
            })

        candidates.sort(key=lambda x: safe_float(x["recoverability_score"], -999), reverse=True)
        out.extend(candidates[:8])

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "target_missing_bin",
        "candidate_id",
        "family",
        "height_nm",
        "nearest_bin_deg",
        "phase_deg",
        "phase_error_to_target_deg",
        "target_conversion",
        "opposite_spin_leakage",
        "conversion_to_leakage_ratio",
        "early_pass",
        "recoverability_score",
        "config_path",
        "result_csv",
    ]

    with open(OUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(out)

    lines = [
        "# P198 h300 missing-bin anchor mining",
        "",
        "## Purpose",
        "",
        "- Mine existing h300 real FDTD results for missing early bins: -120, -60, 0.",
        "- No new FDTD run.",
        "- Goal: identify phase-hit candidates suitable for leakage/selectivity recovery.",
        "",
        "## Top candidates by missing bin",
        "",
        "| target_missing_bin | candidate_id | family | phase | phase_error | target | leakage | ratio | early | score |",
        "|---:|---|---|---:|---:|---:|---:|---:|---|---:|",
    ]

    for r in out:
        lines.append(
            f"| {r['target_missing_bin']} | `{r['candidate_id']}` | {r['family']} | "
            f"{r['phase_deg']} | {r['phase_error_to_target_deg']} | "
            f"{r['target_conversion']} | {r['opposite_spin_leakage']} | "
            f"{r['conversion_to_leakage_ratio']} | {r['early_pass']} | "
            f"{r['recoverability_score']} |"
        )

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"out_csv={OUT_CSV}")
    print(f"report={REPORT}")
    print("")
    print("target_missing_bin\tcandidate_id\tfamily\theight_nm\tnearest_bin_deg\tphase_deg\tphase_error_to_target_deg\ttarget_conversion\topposite_spin_leakage\tconversion_to_leakage_ratio\tearly_pass\trecoverability_score\tconfig_path\tresult_csv")
    for r in out:
        print(
            f"{r['target_missing_bin']}\t{r['candidate_id']}\t{r['family']}\t{r['height_nm']}\t"
            f"{r['nearest_bin_deg']}\t{r['phase_deg']}\t{r['phase_error_to_target_deg']}\t"
            f"{r['target_conversion']}\t{r['opposite_spin_leakage']}\t"
            f"{r['conversion_to_leakage_ratio']}\t{r['early_pass']}\t"
            f"{r['recoverability_score']}\t{r['config_path']}\t{r['result_csv']}"
        )


if __name__ == "__main__":
    main()
