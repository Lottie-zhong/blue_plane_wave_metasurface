from __future__ import annotations

from pathlib import Path
import csv
import math
import cmath

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")
INDEX = ROOT / "outputs/stage10b_h300_role_pair_dimer/stage10b_h300_role_pair_candidates.csv"
OUT = ROOT / "outputs/stage10b_h300_role_pair_dimer/stage10b_h300_role_pair_results.csv"
REPORT = ROOT / "reports/stage10b_h300_role_pair_dimer_summary.md"

BINS = [0, 60, 120, 180, -120, -60]


def wrap_deg(x: float) -> float:
    return (x + 180.0) % 360.0 - 180.0


def angular_distance(a: float, b: float) -> float:
    return abs(wrap_deg(a - b))


def nearest_bin(phase: float):
    best = min(BINS, key=lambda b: angular_distance(phase, b))
    return best, angular_distance(phase, best)


def safe_float(x, default=float("nan")):
    try:
        if x is None or str(x).strip() == "":
            return default
        return float(x)
    except Exception:
        return default


def read_first(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else {}


def parse_complex(text: str):
    if text is None:
        return None
    s = str(text).strip()
    if not s:
        return None

    # Support Python complex, i notation, and possible parentheses.
    s = s.replace("i", "j").strip()
    try:
        return complex(s)
    except Exception:
        pass

    try:
        return complex(s.strip("()"))
    except Exception:
        return None


def get_first(row: dict, keys: list[str], default=""):
    for k in keys:
        if k in row and str(row[k]).strip() != "":
            return row[k]
    return default


def get_phase_deg(row: dict) -> float:
    t_text = get_first(
        row,
        [
            "t_alpha_star_from_alpha",
            "t_alpha_star_alpha",
            "target_amplitude",
            "target_complex",
        ],
        "",
    )

    t = parse_complex(t_text)
    if t is not None:
        return wrap_deg(math.degrees(cmath.phase(t)))

    return float("nan")


with open(INDEX, newline="", encoding="utf-8") as f:
    candidates = list(csv.DictReader(f))

rows = []

for c in candidates:
    result_path = ROOT / c["result_csv"]
    r = read_first(result_path)

    target = safe_float(get_first(r, ["target_conversion"]))
    leakage = safe_float(get_first(r, ["opposite_spin_leakage"]))
    ratio = safe_float(get_first(r, ["conversion_to_leakage_ratio"]))
    phase_deg = get_phase_deg(r)

    valid_metric = not any(math.isnan(v) for v in [target, leakage, ratio])

    if math.isnan(phase_deg):
        nb, err = "", ""
    else:
        nb, err = nearest_bin(phase_deg)

    early = (
        valid_metric
        and target >= 0.5
        and leakage <= 0.2
        and ratio >= 6
    )

    rows.append({
        **c,
        "raw_status": r.get("status", "missing_result") if r else "missing_result",
        "gate_pass": r.get("gate_pass", "") if r else "",
        "metric_valid": str(bool(valid_metric)),
        "phase_deg": "" if math.isnan(phase_deg) else f"{phase_deg:.9f}",
        "nearest_bin_deg": nb,
        "phase_error_deg": "" if err == "" else f"{err:.9f}",
        "target_conversion": "" if math.isnan(target) else f"{target:.9f}",
        "opposite_spin_leakage": "" if math.isnan(leakage) else f"{leakage:.9f}",
        "conversion_to_leakage_ratio": "" if math.isnan(ratio) else f"{ratio:.9f}",
        "early_pass": str(bool(early)),
        "raw_result_csv": str(result_path),
    })

fields = [
    "candidate_id",
    "family",
    "p1_length_nm",
    "p1_width_nm",
    "theta1_deg",
    "p2_length_nm",
    "p2_width_nm",
    "theta2_deg",
    "raw_status",
    "gate_pass",
    "metric_valid",
    "phase_deg",
    "nearest_bin_deg",
    "phase_error_deg",
    "target_conversion",
    "opposite_spin_leakage",
    "conversion_to_leakage_ratio",
    "early_pass",
    "config_path",
    "result_csv",
    "note",
]

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    for row in rows:
        w.writerow({k: row.get(k, "") for k in fields})


def sort_key(r: dict):
    early = 1 if r.get("early_pass") == "True" else 0
    metric_valid = 1 if r.get("metric_valid") == "True" else 0
    ratio = safe_float(r.get("conversion_to_leakage_ratio"), -1)
    target = safe_float(r.get("target_conversion"), -1)
    leakage = safe_float(r.get("opposite_spin_leakage"), 999)
    phase_error = safe_float(r.get("phase_error_deg"), 999)
    return (early, metric_valid, ratio, target, -leakage, -phase_error)


ranked = sorted(rows, key=sort_key, reverse=True)

REPORT.parent.mkdir(parents=True, exist_ok=True)
lines = [
    "# Stage10B h300 Jones-role pair dimer summary",
    "",
    f"- candidates: {len(rows)}",
    f"- metric_valid: {sum(1 for r in rows if r['metric_valid'] == 'True')}",
    f"- early_pass: {sum(1 for r in rows if r['early_pass'] == 'True')}",
    "",
    "| candidate | family | phase | bin | err | target | leakage | ratio | early | p1 | p2 | theta2 |",
    "|---|---|---:|---:|---:|---:|---:|---:|---|---|---|---:|",
]

for r in ranked:
    lines.append(
        f"| `{r['candidate_id']}` | {r['family']} | {r['phase_deg']} | "
        f"{r['nearest_bin_deg']} | {r['phase_error_deg']} | "
        f"{r['target_conversion']} | {r['opposite_spin_leakage']} | "
        f"{r['conversion_to_leakage_ratio']} | {r['early_pass']} | "
        f"{r['p1_length_nm']}x{r['p1_width_nm']} | "
        f"{r['p2_length_nm']}x{r['p2_width_nm']} | {r['theta2_deg']} |"
    )

REPORT.write_text("\n".join(lines), encoding="utf-8")

print(f"results={OUT}")
print(f"report={REPORT}")
print("")
print(f"candidate_count={len(rows)}")
print(f"metric_valid={sum(1 for r in rows if r['metric_valid'] == 'True')}")
print(f"early_pass={sum(1 for r in rows if r['early_pass'] == 'True')}")
print("")
print("candidate_id\tfamily\tphase_deg\tnearest_bin_deg\tphase_error_deg\ttarget_conversion\topposite_spin_leakage\tconversion_to_leakage_ratio\tearly_pass\tmetric_valid\tp1\tp2\ttheta2")
for r in ranked:
    print(
        f"{r['candidate_id']}\t{r['family']}\t{r['phase_deg']}\t"
        f"{r['nearest_bin_deg']}\t{r['phase_error_deg']}\t"
        f"{r['target_conversion']}\t{r['opposite_spin_leakage']}\t"
        f"{r['conversion_to_leakage_ratio']}\t{r['early_pass']}\t"
        f"{r['metric_valid']}\t"
        f"{r['p1_length_nm']}x{r['p1_width_nm']}\t"
        f"{r['p2_length_nm']}x{r['p2_width_nm']}\t{r['theta2_deg']}"
    )
