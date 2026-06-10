from __future__ import annotations

from pathlib import Path
import csv
import math

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")
OUT = ROOT / "outputs/stage10a_h300_hwp_bridge"

XY_RESULTS = OUT / "xy_sweep_results.csv"
LOOKUP = OUT / "single_pillar_lookup_h300_hwp_bridge.csv"
RANKED = OUT / "single_pillar_lookup_h300_hwp_bridge_ranked.csv"
REPORT = ROOT / "reports/stage10a_h300_hwp_bridge_lookup_summary.md"


def wrap_rad(x: float) -> float:
    return (x + math.pi) % (2 * math.pi) - math.pi


def safe_float(x, default=float("nan")):
    try:
        if x is None or str(x).strip() == "":
            return default
        return float(x)
    except Exception:
        return default


def read_one_csv(path: Path) -> dict:
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    return rows[0] if rows else {}


def classify_retardance(ret_abs: float) -> str:
    if abs(ret_abs - 180.0) <= 10:
        return "near_hwp_10deg"
    if abs(ret_abs - 180.0) <= 15:
        return "near_hwp_15deg"
    if abs(ret_abs - 180.0) <= 25:
        return "near_hwp_25deg"
    if abs(ret_abs - 150.0) <= 15:
        return "high_ret_150deg"
    if abs(ret_abs - 120.0) <= 15:
        return "mid_ret_120deg"
    if abs(ret_abs - 90.0) <= 15:
        return "near_qwp_15deg"
    return "other"


def score_row(r: dict) -> float:
    trans_mean = safe_float(r["trans_mean"])
    amp_balance = safe_float(r["amp_balance"])
    ret_abs = abs(safe_float(r["retardance_deg"]))
    hwp_error = abs(ret_abs - 180.0)

    # Bridge score: prioritize HWP proximity first, but penalize severe amplitude imbalance.
    return (
        3.0 * trans_mean
        + 2.0 * amp_balance
        - 0.02 * hwp_error
    )


with open(XY_RESULTS, newline="", encoding="utf-8") as f:
    plan_rows = list(csv.DictReader(f))

rows = []

for row in plan_rows:
    phase_delay_path = ROOT / row["phase_delay_summary"]
    pd = read_one_csv(phase_delay_path)

    phase_x = safe_float(pd.get("phase_x_rad"))
    phase_y = safe_float(pd.get("phase_y_rad"))
    tx = safe_float(pd.get("transmission_x"))
    ty = safe_float(pd.get("transmission_y"))

    retardance_rad = wrap_rad(phase_y - phase_x)
    retardance_deg = math.degrees(retardance_rad)
    common_phase_rad = wrap_rad(0.5 * (phase_x + phase_y))
    common_phase_deg = math.degrees(common_phase_rad)
    trans_mean = 0.5 * (tx + ty)
    amp_balance = 1.0 - abs(tx - ty)

    out = {
        "case_id": row.get("case_id", ""),
        "height_nm": row.get("height_nm", ""),
        "period_nm": "340",
        "length_nm": row.get("length_nm", ""),
        "width_nm": row.get("width_nm", ""),
        "rotation_deg": row.get("rotation_deg", ""),
        "tx_amp": f"{tx:.9f}",
        "tx_phase_rad": f"{phase_x:.9f}",
        "tx_phase_deg": f"{math.degrees(phase_x):.9f}",
        "ty_amp": f"{ty:.9f}",
        "ty_phase_rad": f"{phase_y:.9f}",
        "ty_phase_deg": f"{math.degrees(phase_y):.9f}",
        "retardance_rad": f"{retardance_rad:.9f}",
        "retardance_deg": f"{retardance_deg:.9f}",
        "retardance_abs_deg": f"{abs(retardance_deg):.9f}",
        "common_phase_rad": f"{common_phase_rad:.9f}",
        "common_phase_deg": f"{common_phase_deg:.9f}",
        "trans_mean": f"{trans_mean:.9f}",
        "amp_balance": f"{amp_balance:.9f}",
        "phase_delay_rad_old": row.get("phase_delay_rad", ""),
        "phase_delay_error_to_pi_old": row.get("phase_delay_error_to_pi", ""),
        "role_class": classify_retardance(abs(retardance_deg)),
        "status": pd.get("status", row.get("status", "")),
        "note": pd.get("note", ""),
        "phase_delay_summary": row.get("phase_delay_summary", ""),
    }
    out["bridge_score"] = f"{score_row(out):.9f}"
    rows.append(out)

fields = [
    "case_id",
    "height_nm",
    "period_nm",
    "length_nm",
    "width_nm",
    "rotation_deg",
    "tx_amp",
    "tx_phase_rad",
    "tx_phase_deg",
    "ty_amp",
    "ty_phase_rad",
    "ty_phase_deg",
    "retardance_rad",
    "retardance_deg",
    "retardance_abs_deg",
    "common_phase_rad",
    "common_phase_deg",
    "trans_mean",
    "amp_balance",
    "phase_delay_rad_old",
    "phase_delay_error_to_pi_old",
    "role_class",
    "bridge_score",
    "status",
    "note",
    "phase_delay_summary",
]

ranked = sorted(rows, key=lambda r: safe_float(r["bridge_score"]), reverse=True)

with open(LOOKUP, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

with open(RANKED, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(ranked)

near_hwp = [r for r in rows if r["role_class"] in ("near_hwp_10deg", "near_hwp_15deg", "near_hwp_25deg")]
usable_hwp = [
    r for r in near_hwp
    if safe_float(r["trans_mean"]) >= 0.6 and safe_float(r["amp_balance"]) >= 0.4
]
high_ret_usable = [
    r for r in rows
    if abs(safe_float(r["retardance_deg"])) >= 135
    and safe_float(r["trans_mean"]) >= 0.6
    and safe_float(r["amp_balance"]) >= 0.4
]

REPORT.parent.mkdir(parents=True, exist_ok=True)
lines = [
    "# Stage10A h300 HWP bridge lookup summary",
    "",
    "## Counts",
    "",
    f"- total rows: {len(rows)}",
    f"- near HWP within 25 deg: {len(near_hwp)}",
    f"- usable HWP-like, trans_mean>=0.6 and amp_balance>=0.4: {len(usable_hwp)}",
    f"- high-ret usable, |retardance|>=135, trans_mean>=0.6, amp_balance>=0.4: {len(high_ret_usable)}",
    "",
    "## Top ranked rows",
    "",
    "| case | L | W | tx | ty | retardance | common | trans_mean | amp_balance | role | score |",
    "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
]

for r in ranked[:20]:
    lines.append(
        f"| `{r['case_id']}` | {r['length_nm']} | {r['width_nm']} | "
        f"{r['tx_amp']} | {r['ty_amp']} | {r['retardance_deg']} | "
        f"{r['common_phase_deg']} | {r['trans_mean']} | {r['amp_balance']} | "
        f"{r['role_class']} | {r['bridge_score']} |"
    )

REPORT.write_text("\n".join(lines), encoding="utf-8")

print(f"lookup={LOOKUP}")
print(f"ranked={RANKED}")
print(f"report={REPORT}")
print("")
print(f"total_rows={len(rows)}")
print(f"near_hwp_25deg_count={len(near_hwp)}")
print(f"usable_hwp_count={len(usable_hwp)}")
print(f"high_ret_usable_count={len(high_ret_usable)}")
print("")
print("case_id\tlength_nm\twidth_nm\ttx_amp\tty_amp\tretardance_deg\tcommon_phase_deg\ttrans_mean\tamp_balance\trole_class\tbridge_score\tstatus")
for r in ranked:
    print(
        f"{r['case_id']}\t{r['length_nm']}\t{r['width_nm']}\t"
        f"{r['tx_amp']}\t{r['ty_amp']}\t{r['retardance_deg']}\t"
        f"{r['common_phase_deg']}\t{r['trans_mean']}\t"
        f"{r['amp_balance']}\t{r['role_class']}\t{r['bridge_score']}\t{r['status']}"
    )
