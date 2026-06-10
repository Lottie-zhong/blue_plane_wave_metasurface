from __future__ import annotations

from pathlib import Path
import argparse
import csv
import math


ROOT = Path(r"D:\project\blue_plane_wave_metasurface")


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


def classify_retardance(ret_abs: float, target_ret_abs: float) -> str:
    if abs(ret_abs - target_ret_abs) <= 10:
        return "near_target_ret_10deg"
    if abs(ret_abs - target_ret_abs) <= 15:
        return "near_target_ret_15deg"
    if abs(ret_abs - target_ret_abs) <= 25:
        return "near_target_ret_25deg"
    if abs(ret_abs - 180.0) <= 15:
        return "near_hwp_15deg"
    if abs(ret_abs - 150.0) <= 15:
        return "high_ret_150deg"
    if abs(ret_abs - 120.0) <= 15:
        return "mid_ret_120deg"
    if abs(ret_abs - 90.0) <= 15:
        return "near_qwp_15deg"
    if ret_abs <= 25:
        return "near_iso_phase"
    return "other"


def score_row(r: dict, target_ret_abs: float) -> float:
    trans_mean = safe_float(r["trans_mean"])
    amp_balance = safe_float(r["amp_balance"])
    ret_abs = abs(safe_float(r["retardance_deg"]))
    ret_error = abs(ret_abs - target_ret_abs)

    return (
        3.0 * trans_mean
        + 2.0 * amp_balance
        - 0.02 * ret_error
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--target-ret-abs", type=float, default=135.0)
    args = parser.parse_args()

    out_dir = ROOT / args.out_dir
    xy_results = out_dir / "xy_sweep_results.csv"

    lookup = out_dir / f"single_pillar_lookup_{args.name}.csv"
    ranked_path = out_dir / f"single_pillar_lookup_{args.name}_ranked.csv"
    report = ROOT / "reports" / f"stage10a_{args.name}_lookup_summary.md"

    with open(xy_results, newline="", encoding="utf-8") as f:
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
            "role_class": classify_retardance(abs(retardance_deg), args.target_ret_abs),
            "status": pd.get("status", row.get("status", "")),
            "note": pd.get("note", ""),
            "phase_delay_summary": row.get("phase_delay_summary", ""),
        }

        out["role_score"] = f"{score_row(out, args.target_ret_abs):.9f}"
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
        "role_score",
        "status",
        "note",
        "phase_delay_summary",
    ]

    ranked = sorted(rows, key=lambda r: safe_float(r["role_score"]), reverse=True)

    with open(lookup, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    with open(ranked_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(ranked)

    near_target = [
        r for r in rows
        if r["role_class"] in (
            "near_target_ret_10deg",
            "near_target_ret_15deg",
            "near_target_ret_25deg",
        )
    ]
    usable_target = [
        r for r in near_target
        if safe_float(r["trans_mean"]) >= 0.55
        and safe_float(r["amp_balance"]) >= 0.30
    ]

    report.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Stage10A {args.name} lookup summary",
        "",
        f"- target_ret_abs_deg: {args.target_ret_abs}",
        f"- total rows: {len(rows)}",
        f"- near target within 25 deg: {len(near_target)}",
        f"- usable target-like rows: {len(usable_target)}",
        "",
        "| case | L | W | tx | ty | retardance | common | trans_mean | amp_balance | role | score |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|---:|",
    ]

    for r in ranked[:25]:
        lines.append(
            f"| `{r['case_id']}` | {r['length_nm']} | {r['width_nm']} | "
            f"{r['tx_amp']} | {r['ty_amp']} | {r['retardance_deg']} | "
            f"{r['common_phase_deg']} | {r['trans_mean']} | {r['amp_balance']} | "
            f"{r['role_class']} | {r['role_score']} |"
        )

    report.write_text("\n".join(lines), encoding="utf-8")

    print(f"lookup={lookup}")
    print(f"ranked={ranked_path}")
    print(f"report={report}")
    print("")
    print(f"total_rows={len(rows)}")
    print(f"near_target_25deg_count={len(near_target)}")
    print(f"usable_target_count={len(usable_target)}")
    print("")
    print("case_id\tlength_nm\twidth_nm\ttx_amp\tty_amp\tretardance_deg\tcommon_phase_deg\ttrans_mean\tamp_balance\trole_class\trole_score\tstatus")
    for r in ranked:
        print(
            f"{r['case_id']}\t{r['length_nm']}\t{r['width_nm']}\t"
            f"{r['tx_amp']}\t{r['ty_amp']}\t{r['retardance_deg']}\t"
            f"{r['common_phase_deg']}\t{r['trans_mean']}\t"
            f"{r['amp_balance']}\t{r['role_class']}\t{r['role_score']}\t{r['status']}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
