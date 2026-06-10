from pathlib import Path
import csv, math, cmath, yaml

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")
TARGET_BINS = [-180, -120, -60, 0, 60, 120]

CANDIDATES = [
    # best 0 phase-hit
    "next_zero_rot_anchor_03",

    # best -60 phase-hit
    "cpk_m60scan_relcomp_m80_diff35_01",

    # best -120 phase-hit
    "cpk_m60scan_common_m100_01",

    # representative known h300 early-pass from platform scan / projection
    "p185_fh300_p000_from_cpk_zero_l60_h232_p1geom120x58_p2geom76x137_01",
    "p185_fh300_p060_from_aggr_lhs_retention_dy_05",
    "p185_fh300_m180_from_cpk_resphase_scale104_nohelper_01",
]

def safe_float(x):
    try:
        if x is None or str(x).strip() == "":
            return float("nan")
        return float(x)
    except Exception:
        return float("nan")

def parse_complex(s):
    return complex(str(s).strip().replace("i", "j"))

def phase_dist(a, b):
    return abs((a - b + 180) % 360 - 180)

def nearest_bin(phase):
    return min(TARGET_BINS, key=lambda b: phase_dist(phase, b))

def find_config(cid):
    hits = list((ROOT / "configs" / "apcd_k6_phase_state_candidates").glob(f"{cid}.yaml"))
    return hits[0] if hits else None

def find_result(cid, cfg):
    if cfg:
        with open(cfg, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        result_dir = data.get("output", {}).get("result_dir")
        if result_dir:
            p = ROOT / result_dir / "results.csv"
            if p.exists():
                return p
    hits = list((ROOT / "outputs").rglob(f"{cid}/results.csv"))
    if hits:
        hits.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return hits[0]
    return None

def read_first_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))[0]

def phase_from_row(row):
    raw = str(row.get("t_alpha_star_from_alpha", "")).strip()
    if raw:
        try:
            return math.degrees(cmath.phase(parse_complex(raw)))
        except Exception:
            pass
    return safe_float(row.get("phase_deg", ""))

def collect_pillars(obj):
    found = []

    def rec(x):
        if isinstance(x, dict):
            # heuristic: a pillar-like dict has length/width/rotation or x/y
            keys = set(x.keys())
            if any(k in keys for k in ["length_nm", "width_nm", "rotation_deg", "x_nm", "y_nm"]):
                found.append(x)
            for v in x.values():
                rec(v)
        elif isinstance(x, list):
            for v in x:
                rec(v)

    rec(obj)

    # filter likely physical pillars
    pillars = []
    for p in found:
        if "length_nm" in p and "width_nm" in p:
            pillars.append(p)

    # remove duplicates by tuple
    unique = []
    seen = set()
    for p in pillars:
        key = (
            p.get("length_nm"), p.get("width_nm"), p.get("height_nm"),
            p.get("rotation_deg"), p.get("x_nm"), p.get("y_nm")
        )
        if key not in seen:
            seen.add(key)
            unique.append(p)

    return unique[:3]

print("candidate_id\theight_nm\tp1_length_nm\tp1_width_nm\tp1_rotation_deg\tp1_x_nm\tp1_y_nm\tp2_length_nm\tp2_width_nm\tp2_rotation_deg\tp2_x_nm\tp2_y_nm\tphase_deg\tnearest_bin_deg\ttarget_conversion\topposite_spin_leakage\tconversion_to_leakage_ratio\tearly_pass")

for cid in CANDIDATES:
    cfg_path = find_config(cid)
    if cfg_path is None:
        print(f"{cid}\tCONFIG_MISSING")
        continue

    with open(cfg_path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    pillars = collect_pillars(cfg)
    p1 = pillars[0] if len(pillars) > 0 else {}
    p2 = pillars[1] if len(pillars) > 1 else {}

    res = find_result(cid, cfg_path)
    if res is None:
        print(f"{cid}\tRESULT_MISSING")
        continue

    row = read_first_csv(res)
    phase = phase_from_row(row)
    nb = nearest_bin(phase)
    target = safe_float(row.get("target_conversion", ""))
    leakage = safe_float(row.get("opposite_spin_leakage", ""))
    ratio = safe_float(row.get("conversion_to_leakage_ratio", ""))
    early = bool(target >= 0.5 and leakage <= 0.2 and ratio >= 6)

    h = p1.get("height_nm", "")

    print(
        f"{cid}\t{h}\t"
        f"{p1.get('length_nm','')}\t{p1.get('width_nm','')}\t{p1.get('rotation_deg','')}\t{p1.get('x_nm','')}\t{p1.get('y_nm','')}\t"
        f"{p2.get('length_nm','')}\t{p2.get('width_nm','')}\t{p2.get('rotation_deg','')}\t{p2.get('x_nm','')}\t{p2.get('y_nm','')}\t"
        f"{phase:.9f}\t{nb}\t{target:.9f}\t{leakage:.9f}\t{ratio:.9f}\t{early}"
    )
