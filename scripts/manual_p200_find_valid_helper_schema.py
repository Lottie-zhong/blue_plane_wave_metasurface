from pathlib import Path
import csv, yaml, math, cmath

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")
CONFIG_DIR = ROOT / "configs" / "apcd_k6_phase_state_candidates"
TARGET_BINS = [-180, -120, -60, 0, 60, 120]

def is_pillar(x):
    return isinstance(x, dict) and "length_nm" in x and "width_nm" in x

def collect_pillars(obj):
    out = []

    def rec(x, path):
        if is_pillar(x):
            out.append((path, x))
        if isinstance(x, dict):
            for k, v in x.items():
                rec(v, f"{path}.{k}" if path else str(k))
        elif isinstance(x, list):
            for i, v in enumerate(x):
                rec(v, f"{path}[{i}]")

    rec(obj, "")
    return out

def safe_float(x):
    try:
        if x is None or str(x).strip() == "":
            return float("nan")
        return float(x)
    except Exception:
        return float("nan")

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

def find_result(cid, cfg):
    result_dir = ""
    try:
        result_dir = cfg.get("output", {}).get("result_dir", "")
    except Exception:
        pass

    if result_dir:
        p = ROOT / result_dir / "results.csv"
        if p.exists():
            return p

    hits = list((ROOT / "outputs").rglob(f"{cid}/results.csv"))
    if hits:
        hits.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return hits[0]

    return None

rows = []

for path in sorted(CONFIG_DIR.glob("*.yaml")):
    cid = path.stem

    # Avoid only showing the newly generated P200 files.
    # We want older working helper examples too.
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
    except Exception:
        continue

    pillars = collect_pillars(cfg)
    if len(pillars) < 3:
        continue

    result_path = find_result(cid, cfg)

    phase = target = leakage = ratio = float("nan")
    nb = ""
    if result_path and result_path.exists():
        try:
            with open(result_path, newline="", encoding="utf-8") as f:
                rr = list(csv.DictReader(f))
            if rr:
                row = rr[0]
                phase = phase_from_row(row)
                nb = nearest_bin(phase)
                target = safe_float(row.get("target_conversion", ""))
                leakage = safe_float(row.get("opposite_spin_leakage", ""))
                ratio = safe_float(row.get("conversion_to_leakage_ratio", ""))
        except Exception:
            pass

    rows.append({
        "candidate_id": cid,
        "config_path": str(path.relative_to(ROOT)).replace("\\", "/"),
        "pillar_like_count": len(pillars),
        "pillar_paths": " | ".join([p for p, _ in pillars[:6]]),
        "result_exists": bool(result_path),
        "phase_deg": "" if math.isnan(phase) else f"{phase:.9f}",
        "nearest_bin_deg": nb,
        "target_conversion": "" if math.isnan(target) else f"{target:.9f}",
        "opposite_spin_leakage": "" if math.isnan(leakage) else f"{leakage:.9f}",
        "conversion_to_leakage_ratio": "" if math.isnan(ratio) else f"{ratio:.9f}",
    })

# prioritize older non-P200 examples with results, then P200.
rows.sort(key=lambda r: (
    r["candidate_id"].startswith("p200_"),
    not r["result_exists"],
    r["candidate_id"]
))

print("candidate_id\tconfig_path\tpillar_like_count\tpillar_paths\tresult_exists\tphase_deg\tnearest_bin_deg\ttarget_conversion\topposite_spin_leakage\tconversion_to_leakage_ratio")
for r in rows[:40]:
    print(
        f"{r['candidate_id']}\t{r['config_path']}\t{r['pillar_like_count']}\t"
        f"{r['pillar_paths']}\t{r['result_exists']}\t{r['phase_deg']}\t"
        f"{r['nearest_bin_deg']}\t{r['target_conversion']}\t"
        f"{r['opposite_spin_leakage']}\t{r['conversion_to_leakage_ratio']}"
    )
