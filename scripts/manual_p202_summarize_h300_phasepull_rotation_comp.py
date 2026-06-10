from pathlib import Path
import csv, math, cmath

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")
TARGET_BINS = [-180, -120, -60, 0, 60, 120]

SELECTION = ROOT / "outputs/apcd_k6_active_learning/p202_h300_phasepull_rotation_comp_fdtd_selection.csv"
OUT = ROOT / "outputs/apcd_k6_active_learning/p202_h300_phasepull_rotation_comp_fdtd_summary.csv"
REPORT = ROOT / "reports/p202_h300_phasepull_rotation_comp_fdtd_summary.md"


def safe_float(x, default=float("nan")):
    try:
        if x is None or str(x).strip() == "":
            return default
        return float(x)
    except Exception:
        return default


def parse_complex(s):
    return complex(str(s).strip().replace("i", "j"))


def phase_from_row(row):
    raw = str(row.get("t_alpha_star_from_alpha", "")).strip()
    if raw:
        try:
            return math.degrees(cmath.phase(parse_complex(raw)))
        except Exception:
            pass
    return safe_float(row.get("phase_deg", ""))


def nearest_bin(phase):
    if math.isnan(phase):
        return ""
    return min(TARGET_BINS, key=lambda b: abs((phase - b + 180) % 360 - 180))


def abs_to_zero(phase):
    if math.isnan(phase):
        return float("nan")
    return abs((phase + 180) % 360 - 180)


def classify(phase, nb, target, leakage, ratio, early):
    a0 = abs_to_zero(phase)

    if math.isnan(phase) or math.isnan(target) or math.isnan(leakage) or math.isnan(ratio):
        return "invalid_or_error"

    if nb == 0 and early:
        return "primary_opens_0"

    if 30 < a0 <= 45 and early:
        return "healthy_trend_to_0"

    if a0 <= 45 and leakage <= 0.25 and 4 <= ratio < 6:
        return "useful_nearmiss"

    if a0 <= 45 and leakage >= 0.35:
        return "phase_pull_selectivity_failed"

    if early and nb == 60:
        return "stays_healthy_60"

    if early:
        return "early_but_not_toward_0"

    return "other_failed"


def read_first_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else {}


if not SELECTION.exists():
    raise FileNotFoundError(f"Missing selection: {SELECTION}")

with open(SELECTION, newline="", encoding="utf-8") as f:
    selected = list(csv.DictReader(f))

out_rows = []

for pr in selected:
    cid = pr["candidate_id"]
    result_csv = ROOT / "outputs/apcd_k6_metagrating_633nm/phase_state_candidates" / cid / "results.csv"

    phase = target = leakage = ratio = float("nan")
    nb = ""
    status = "missing_result"
    note = ""

    if result_csv.exists():
        row = read_first_csv(result_csv)
        status = str(row.get("status", "")).strip()
        note = str(row.get("note", "")).strip()
        phase = phase_from_row(row)
        nb = nearest_bin(phase)
        target = safe_float(row.get("target_conversion", ""))
        leakage = safe_float(row.get("opposite_spin_leakage", ""))
        ratio = safe_float(row.get("conversion_to_leakage_ratio", ""))

    early = bool(target >= 0.5 and leakage <= 0.2 and ratio >= 6)
    opens0 = bool(early and nb == 0)
    opens60 = bool(early and nb == 60)
    cat = classify(phase, nb, target, leakage, ratio, early)

    out_rows.append({
        "candidate_id": cid,
        "phase_deg": "" if math.isnan(phase) else f"{phase:.9f}",
        "nearest_bin_deg": nb,
        "target_conversion": "" if math.isnan(target) else f"{target:.9f}",
        "opposite_spin_leakage": "" if math.isnan(leakage) else f"{leakage:.9f}",
        "conversion_to_leakage_ratio": "" if math.isnan(ratio) else f"{ratio:.9f}",
        "early_pass": early,
        "opens_0": opens0,
        "opens_60": opens60,
        "result_csv": str(result_csv),
        "status": status,
        "note": note,
        "base_key": pr.get("base_key", ""),
        "base_candidate_id": pr.get("base_candidate_id", ""),
        "variant": pr.get("variant", ""),
        "p202_category": cat,
    })

OUT.parent.mkdir(parents=True, exist_ok=True)

fields = [
    "candidate_id",
    "phase_deg",
    "nearest_bin_deg",
    "target_conversion",
    "opposite_spin_leakage",
    "conversion_to_leakage_ratio",
    "early_pass",
    "opens_0",
    "opens_60",
    "result_csv",
    "status",
    "note",
    "base_key",
    "base_candidate_id",
    "variant",
    "p202_category",
]

with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(out_rows)

lines = [
    "# P202 h300 phase-pull + rotation compensation FDTD summary",
    "",
    "| candidate_id | base | variant | phase | nearest | target | leakage | ratio | early | opens0 | opens60 | category |",
    "|---|---|---|---:|---:|---:|---:|---:|---|---|---|---|",
]

for r in out_rows:
    lines.append(
        f"| `{r['candidate_id']}` | {r['base_key']} | {r['variant']} | "
        f"{r['phase_deg']} | {r['nearest_bin_deg']} | "
        f"{r['target_conversion']} | {r['opposite_spin_leakage']} | "
        f"{r['conversion_to_leakage_ratio']} | {r['early_pass']} | "
        f"{r['opens_0']} | {r['opens_60']} | {r['p202_category']} |"
    )

REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text("\n".join(lines), encoding="utf-8")

print(f"summary={OUT}")
print(f"report={REPORT}")
print("")
print("candidate_id\tphase_deg\tnearest_bin_deg\ttarget_conversion\topposite_spin_leakage\tconversion_to_leakage_ratio\tearly_pass\topens_0\topens_60\tresult_csv\tstatus\tnote\tbase_key\tbase_candidate_id\tvariant\tp202_category")

for r in out_rows:
    print(
        f"{r['candidate_id']}\t{r['phase_deg']}\t{r['nearest_bin_deg']}\t"
        f"{r['target_conversion']}\t{r['opposite_spin_leakage']}\t"
        f"{r['conversion_to_leakage_ratio']}\t{r['early_pass']}\t"
        f"{r['opens_0']}\t{r['opens_60']}\t{r['result_csv']}\t"
        f"{r['status']}\t{r['note']}\t{r['base_key']}\t"
        f"{r['base_candidate_id']}\t{r['variant']}\t{r['p202_category']}"
    )
