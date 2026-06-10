from __future__ import annotations

from pathlib import Path
import csv
import math

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")
OUT = ROOT / "outputs/stage10a_h300_single_pillar_pilot"

XY_RESULTS = OUT / "xy_sweep_results.csv"
LOOKUP = OUT / "single_pillar_lookup_h300_pilot.csv"
RANKED = OUT / "single_pillar_lookup_h300_pilot_ranked.csv"
REPORT = ROOT / "reports/stage10a_h300_single_pillar_pilot_lookup_summary.md"


def wrap_rad(x: float) -> float:
    return (x + math.pi) % (2 * math.pi) - math.pi


def wrap_deg(x: float) -> float:
    return (x + 180.0) % 360.0 - 180.0


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


def classify_retardance(ret_deg_abs: float) -> str:
    if abs(ret_deg_abs - 180.0) <= 15:
        return "near_hwp_15deg"
    if abs(ret_deg_abs - 180.0) <= 25:
        return "near_hwp_25deg"
    if abs(ret_deg_abs - 90.0) <= 15:
        return "near_qwp_15deg"
    if abs(ret_deg_abs - 90.0) <= 25:
        return "near_qwp_25deg"
    if ret_deg_abs <= 25:
        return "near_iso_phase"
    return "other"


def score_row(r: dict) -> float:
    # Pilot score: favor high mean transmission, balanced x/y amplitude,
    # and HWP-like retardance because APCD dimer needs birefringent waveplate-like atoms.
    trans_mean = safe_float(r["trans_mean"])
    amp_balance = safe_float(r["amp_balance"])
    ret_abs = abs(safe_float(r["retardance_deg"]))
    hwp_error = abs(ret_abs - 180.0)

    return (
        2.0 * trans_mean
        + 1.0 * amp_balance
        - 0.01 * hwp_error
    )


if not XY_RESULTS.exists():
    raise FileNotFoundError(f"Missing {XY_RESULTS}")

with open(XY_RESULTS, newline="", encoding="utf-8") as f:
    plan_rows = list(csv.DictReader(f))

rows = []

for row in plan_rows:
    phase_delay_path = ROOT / row["phase_delay_summary"]
    if not phase_delay_path.exists():
        rows.append({
            "case_id": row.get("case_id", ""),
            "status": "missing_phase_delay",
            "note": str(phase_delay_path),
        })
        continue

    pd = read_one_csv(phase_delay_path)

    phase_x = safe_float(pd.get("phase_x_rad"))
    phase_y = safe_float(pd.get("phase_y_rad"))
    tx = safe_float(pd.get("transmission_x"))
    ty = safe_float(pd.get("transmission_y"))

    # In old code, phase_delay_rad is wrapped phase_x - phase_y.
    # For our lookup convention, define retardance = phi_y - phi_x.
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

    out["pilot_score"] = f"{score_row(out):.9f}"
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
    "pilot_score",
    "status",
    "note",
    "phase_delay_summary",
]

LOOKUP.parent.mkdir(parents=True, exist_ok=True)
with open(LOOKUP, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

ranked = sorted(
    rows,
    key=lambda r: safe_float(r.get("pilot_score", "-999")),
    reverse=True,
)

with open(RANKED, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(ranked)

ok_rows = [r for r in rows if r["status"] == "ok"]
hwp25 = [r for r in ok_rows if r["role_class"] in ("near_hwp_15deg", "near_hwp_25deg")]
high_trans = [r for r in ok_rows if safe_float(r["trans_mean"]) >= 0.6]
balanced = [r for r in ok_rows if safe_float(r["amp_balance"]) >= 0.75]

REPORT.parent.mkdir(parents=True, exist_ok=True)
lines = [
    "# Stage10A h300 single-pillar lookup pilot summary",
    "",
    "## Scope",
    "",
    "- wavelength = 633 nm",
    "- height = 300 nm",
    "- period = 340 nm",
    "- single rectangular nanopillar",
    "- x/y normal-incidence lookup",
    "",
    "## Counts",
    "",
    f"- total rows: {len(rows)}",
    f"- ok rows: {len(ok_rows)}",
    f"- near HWP within 25 deg: {len(hwp25)}",
    f"- trans_mean >= 0.6: {len(high_trans)}",
    f"- amp_balance >= 0.75: {len(balanced)}",
    "",
    "## Top ranked pilot rows",
    "",
    "| case | L | W | tx | ty | retardance deg | common deg | trans mean | amp balance | role | score |",
    "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
]

for r in ranked[:16]:
    lines.append(
        f"| `{r['case_id']}` | {r['length_nm']} | {r['width_nm']} | "
        f"{r['tx_amp']} | {r['ty_amp']} | {r['retardance_deg']} | "
        f"{r['common_phase_deg']} | {r['trans_mean']} | {r['amp_balance']} | "
        f"{r['role_class']} | {r['pilot_score']} |"
    )

REPORT.write_text("\n".join(lines), encoding="utf-8")

print(f"lookup={LOOKUP}")
print(f"ranked={RANKED}")
print(f"report={REPORT}")
print("")
print("case_id\tlength_nm\twidth_nm\ttx_amp\tty_amp\tretardance_deg\tcommon_phase_deg\ttrans_mean\tamp_balance\trole_class\tpilot_score\tstatus")
for r in ranked:
    print(
        f"{r['case_id']}\t{r['length_nm']}\t{r['width_nm']}\t"
        f"{r['tx_amp']}\t{r['ty_amp']}\t{r['retardance_deg']}\t"
        f"{r['common_phase_deg']}\t{r['trans_mean']}\t"
        f"{r['amp_balance']}\t{r['role_class']}\t{r['pilot_score']}\t{r['status']}"
    )
