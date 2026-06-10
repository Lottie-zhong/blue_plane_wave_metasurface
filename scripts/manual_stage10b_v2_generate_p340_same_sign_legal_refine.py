from __future__ import annotations

from pathlib import Path
import csv
import math
import yaml
import copy

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")

TEMPLATE = ROOT / "configs/apcd_k6_phase_state_candidates/p185_fh300_p060_from_aggr_lhs_retention_dy_05.yaml"
CONFIG_DIR = ROOT / "configs/apcd_k6_phase_state_candidates"
OUT_DIR = ROOT / "outputs/stage10b_v2_h300_p340_same_sign_legal_refine"
INDEX = OUT_DIR / "stage10b_v2_h300_p340_same_sign_legal_candidates.csv"

MARGIN_NM = 3.0

with open(TEMPLATE, "r", encoding="utf-8") as f:
    template = yaml.safe_load(f)

# id, p1L, p1W, p2L, p2W, note
# All keep original p340 positions and rotations:
# p1 theta=67.5, p2 theta=112.5
candidates = [
    ("s10b_v2_anchor_same02", 120, 50, 85, 130, "valid anchor from Stage10B-v1; phase 83.2 deg, ratio 7.1"),

    # p1 role perturbation, p2 fixed at 85x130
    ("s10b_v2_p1_115x55_p2_85x130", 115, 55, 85, 130, "control p1 with same02 p2"),
    ("s10b_v2_p1_115x60_p2_85x130", 115, 60, 85, 130, "p1 slightly wider; still p1-like"),
    ("s10b_v2_p1_120x55_p2_85x130", 120, 55, 85, 130, "p1 near upper legal margin"),
    ("s10b_v2_p1_110x70_p2_85x130", 110, 70, 85, 130, "p1 positive common-phase variant"),

    # p2 same-sign high-ret variants, p1 fixed at 120x50
    ("s10b_v2_p1_120x50_p2_85x135", 120, 50, 85, 135, "p2 larger W, still legal"),
    ("s10b_v2_p1_120x50_p2_90x125", 120, 50, 90, 125, "p2 higher L lower W, legal"),
    ("s10b_v2_p1_120x50_p2_80x135", 120, 50, 80, 135, "p2 high-ret same-sign"),
    ("s10b_v2_p1_120x50_p2_80x140", 120, 50, 80, 140, "p2 near-HWP-ish same-sign, legal"),
    ("s10b_v2_p1_120x50_p2_70x145", 120, 50, 70, 145, "p2 high-ret same-sign, lower L"),
    ("s10b_v2_p1_120x50_p2_65x150", 120, 50, 65, 150, "p2 same-sign high-ret, valid p2 footprint"),

    # mixed promising combinations
    ("s10b_v2_p1_115x60_p2_90x125", 115, 60, 90, 125, "mixed p1 wider + p2 90x125"),
    ("s10b_v2_p1_120x55_p2_85x135", 120, 55, 85, 135, "upper legal p1 + p2 larger W"),
]


def get_value(d: dict, keys: list[str], default=None):
    for k in keys:
        if k in d:
            return d[k]
    return default


def get_center(p: dict):
    x = get_value(p, ["center_x_nm", "x_center_nm", "x_nm", "position_x_nm"], None)
    y = get_value(p, ["center_y_nm", "y_center_nm", "y_nm", "position_y_nm"], None)

    if x is None and isinstance(p.get("position_nm"), dict):
        x = p["position_nm"].get("x")
        y = p["position_nm"].get("y")

    if x is None and isinstance(p.get("center_nm"), dict):
        x = p["center_nm"].get("x")
        y = p["center_nm"].get("y")

    if x is None:
        raise KeyError(f"cannot find pillar center keys in {p.keys()}")

    return float(x), float(y)


def rotated_bbox(cx, cy, L, W, rot_deg):
    theta = math.radians(rot_deg)
    c = abs(math.cos(theta))
    s = abs(math.sin(theta))
    half_x = 0.5 * (L * c + W * s)
    half_y = 0.5 * (L * s + W * c)
    return cx - half_x, cx + half_x, cy - half_y, cy + half_y


def min_clearance_for_pillar(p: dict, period_x: float, period_y: float):
    cx, cy = get_center(p)
    L = float(p["length_nm"])
    W = float(p["width_nm"])
    rot = float(p["rotation_deg"])

    xmin, xmax, ymin, ymax = rotated_bbox(cx, cy, L, W, rot)

    hx = period_x / 2.0
    hy = period_y / 2.0

    return min(
        xmin + hx,
        hx - xmax,
        ymin + hy,
        hy - ymax,
    )


OUT_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

rows = []

for cid, p1L, p1W, p2L, p2W, note in candidates:
    cfg = copy.deepcopy(template)

    cfg.setdefault("project", {})
    cfg["project"]["stage"] = "stage10b_v2_h300_p340_same_sign_legal_refine"

    cfg.setdefault("metadata", {})
    cfg["metadata"]["candidate_id"] = cid
    cfg["metadata"]["candidate_family"] = "p340_same_sign_legal_refine"
    cfg["metadata"]["description"] = "Stage10B-v2 p340 strict-valid same-sign APCD role refinement"
    cfg["metadata"]["notes"] = note
    cfg["metadata"]["not_phase_ramp_supercell"] = True

    geom = cfg["geometry"]
    period_x = float(get_value(geom, ["period_x_nm", "period_nm"], 340))
    period_y = float(get_value(geom, ["period_y_nm", "period_nm"], period_x))

    p1 = geom["nanopillar_1"]
    p2 = geom["nanopillar_2"]

    p1["length_nm"] = float(p1L)
    p1["width_nm"] = float(p1W)
    p1["height_nm"] = 300.0
    p1["rotation_deg"] = 67.5

    p2["length_nm"] = float(p2L)
    p2["width_nm"] = float(p2W)
    p2["height_nm"] = 300.0
    p2["rotation_deg"] = 112.5

    p1_clear = min_clearance_for_pillar(p1, period_x, period_y)
    p2_clear = min_clearance_for_pillar(p2, period_x, period_y)
    min_clear = min(p1_clear, p2_clear)
    geometry_valid = min_clear >= MARGIN_NM

    cfg.setdefault("output", {})
    result_dir = f"outputs/stage10b_v2_h300_p340_same_sign_legal_refine/{cid}"
    cfg["output"]["result_dir"] = result_dir

    config_path = CONFIG_DIR / f"{cid}.yaml"
    config_path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")

    rows.append({
        "candidate_id": cid,
        "family": "p340_same_sign_legal_refine",
        "config_path": str(config_path.relative_to(ROOT)),
        "result_dir": result_dir,
        "result_csv": f"{result_dir}/results.csv",
        "p1_length_nm": p1L,
        "p1_width_nm": p1W,
        "theta1_deg": 67.5,
        "p2_length_nm": p2L,
        "p2_width_nm": p2W,
        "theta2_deg": 112.5,
        "p1_min_clearance_nm": f"{p1_clear:.6f}",
        "p2_min_clearance_nm": f"{p2_clear:.6f}",
        "min_clearance_nm": f"{min_clear:.6f}",
        "geometry_valid": str(bool(geometry_valid)),
        "note": note,
    })

fields = [
    "candidate_id",
    "family",
    "config_path",
    "result_dir",
    "result_csv",
    "p1_length_nm",
    "p1_width_nm",
    "theta1_deg",
    "p2_length_nm",
    "p2_width_nm",
    "theta2_deg",
    "p1_min_clearance_nm",
    "p2_min_clearance_nm",
    "min_clearance_nm",
    "geometry_valid",
    "note",
]

with open(INDEX, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

print(f"written_index={INDEX}")
print(f"candidate_count={len(rows)}")
print(f"valid_count={sum(1 for r in rows if r['geometry_valid'] == 'True')}")
print("")
print("candidate_id\tp1\tp2\tmin_clearance\tgeometry_valid\tconfig")
for r in rows:
    print(
        f"{r['candidate_id']}\t"
        f"{r['p1_length_nm']}x{r['p1_width_nm']}\t"
        f"{r['p2_length_nm']}x{r['p2_width_nm']}\t"
        f"{r['min_clearance_nm']}\t"
        f"{r['geometry_valid']}\t"
        f"{r['config_path']}"
    )
