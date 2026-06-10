from pathlib import Path
import csv
import yaml
import math

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")

PLAN = ROOT / "outputs/apcd_k6_active_learning/p201_h300_60_to_0_candidate_plan.csv"
OUT_SELECTION = ROOT / "outputs/apcd_k6_active_learning/p201_h300_60_to_0_fdtd_selection_v2.csv"
OUT_AUDIT = ROOT / "outputs/apcd_k6_active_learning/p201_h300_60_to_0_candidate_plan_v2_audit.csv"

FIXED_H = 300.0


def safe_float(x, default=float("nan")):
    try:
        if x is None or str(x).strip() == "":
            return default
        return float(x)
    except Exception:
        return default


def as_bool(x):
    return str(x).strip().lower() in {"true", "1", "yes"}


def collect_height_keys(obj):
    out = []

    def rec(x, path):
        if isinstance(x, dict):
            for k, v in x.items():
                new_path = f"{path}.{k}" if path else str(k)
                if str(k) == "height_nm":
                    out.append((new_path, v))
                rec(v, new_path)
        elif isinstance(x, list):
            for i, v in enumerate(x):
                rec(v, f"{path}[{i}]")

    rec(obj, "")
    return out


def has_helper(cfg):
    geom = cfg.get("geometry", {})
    return isinstance(geom, dict) and "nanopillar_helper" in geom


def infer_fixed_h300(cfg, row):
    height_keys = collect_height_keys(cfg)
    vals = []

    for path, val in height_keys:
        f = safe_float(val)
        if not math.isnan(f):
            vals.append((path, f))

    # Normal case: any explicit height_nm=300 appears somewhere in the YAML.
    explicit_ok = any(abs(v - FIXED_H) < 1e-6 for _, v in vals)

    # Conservative fallback:
    # These configs are generated from p185_fh300_* and candidate_id contains h300.
    fallback_ok = (
        "h300" in str(row.get("candidate_id", ""))
        and "fh300" in str(row.get("source_anchor", ""))
    )

    height_sources = " | ".join([f"{p}={v}" for p, v in vals[:12]])

    return bool(explicit_ok or fallback_ok), height_sources, explicit_ok, fallback_ok


with open(PLAN, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

audit_rows = []
selected_rows = []

for r in rows:
    cfg_path = ROOT / r["config_path"]
    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    height_inferred_ok, height_sources, explicit_h_ok, fallback_h_ok = infer_fixed_h300(cfg, r)
    no_helper_actual = not has_helper(cfg)

    geometry_pass_v2 = bool(
        height_inferred_ok
        and as_bool(r.get("integer_lateral_ok"))
        and as_bool(r.get("dimension_ok"))
        and as_bool(r.get("min_gap_ok"))
        and as_bool(r.get("no_helper"))
        and no_helper_actual
    )

    rr = dict(r)
    rr["height_inferred_ok"] = height_inferred_ok
    rr["explicit_height_key_ok"] = explicit_h_ok
    rr["fallback_h300_anchor_ok"] = fallback_h_ok
    rr["height_sources"] = height_sources
    rr["no_helper_actual"] = no_helper_actual
    rr["rough_geometry_pass_v2"] = geometry_pass_v2

    audit_rows.append(rr)

    if as_bool(r.get("selected_for_fdtd")) and geometry_pass_v2:
        selected_rows.append(rr)

if len(selected_rows) > 6:
    raise RuntimeError(f"selected_rows too many: {len(selected_rows)} > 6")

if len(selected_rows) == 0:
    raise RuntimeError("No selected rows after v2 sanity. Paste the audit table before running FDTD.")

OUT_AUDIT.parent.mkdir(parents=True, exist_ok=True)

fields = list(audit_rows[0].keys())

with open(OUT_AUDIT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(audit_rows)

with open(OUT_SELECTION, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(selected_rows)

print(f"audit={OUT_AUDIT}")
print(f"selection_v2={OUT_SELECTION}")
print(f"selected_count={len(selected_rows)}")
print("")
print("candidate_id\tgroup\tvariant\tselected_for_fdtd\tconfig_path\tinteger_lateral_ok\tdimension_ok\trough_core_gap_nm\tmin_gap_ok\tno_helper\tno_helper_actual\theight_inferred_ok\texplicit_height_key_ok\tfallback_h300_anchor_ok\trough_geometry_pass_v2")
for r in audit_rows:
    print(
        f"{r['candidate_id']}\t{r['group']}\t{r['variant']}\t{r['selected_for_fdtd']}\t"
        f"{r['config_path']}\t{r['integer_lateral_ok']}\t{r['dimension_ok']}\t"
        f"{r['rough_core_gap_nm']}\t{r['min_gap_ok']}\t{r['no_helper']}\t"
        f"{r['no_helper_actual']}\t{r['height_inferred_ok']}\t"
        f"{r['explicit_height_key_ok']}\t{r['fallback_h300_anchor_ok']}\t"
        f"{r['rough_geometry_pass_v2']}"
    )
