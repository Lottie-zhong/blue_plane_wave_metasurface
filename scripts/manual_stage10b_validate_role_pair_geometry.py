from __future__ import annotations

from pathlib import Path
import csv
import math
import yaml

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")
INDEX = ROOT / "outputs/stage10b_h300_role_pair_dimer/stage10b_h300_role_pair_candidates.csv"
OUT = ROOT / "outputs/stage10b_h300_role_pair_dimer/stage10b_h300_role_pair_geometry_validation.csv"

MARGIN_NM = 3.0


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


def rotated_bbox(center_x, center_y, length, width, rot_deg):
    theta = math.radians(rot_deg)
    c = abs(math.cos(theta))
    s = abs(math.sin(theta))

    half_x = 0.5 * (length * c + width * s)
    half_y = 0.5 * (length * s + width * c)

    return {
        "xmin": center_x - half_x,
        "xmax": center_x + half_x,
        "ymin": center_y - half_y,
        "ymax": center_y + half_y,
        "half_x": half_x,
        "half_y": half_y,
    }


def pillar_row(candidate_id, pillar_name, p, period_x, period_y):
    cx, cy = get_center(p)

    L = float(p["length_nm"])
    W = float(p["width_nm"])
    rot = float(p["rotation_deg"])

    b = rotated_bbox(cx, cy, L, W, rot)

    hx = period_x / 2.0
    hy = period_y / 2.0

    clearance_left = b["xmin"] + hx
    clearance_right = hx - b["xmax"]
    clearance_bottom = b["ymin"] + hy
    clearance_top = hy - b["ymax"]

    min_clearance = min(clearance_left, clearance_right, clearance_bottom, clearance_top)

    valid = min_clearance >= MARGIN_NM

    return {
        "candidate_id": candidate_id,
        "pillar": pillar_name,
        "period_x_nm": period_x,
        "period_y_nm": period_y,
        "length_nm": L,
        "width_nm": W,
        "rotation_deg": rot,
        "center_x_nm": cx,
        "center_y_nm": cy,
        "xmin_nm": b["xmin"],
        "xmax_nm": b["xmax"],
        "ymin_nm": b["ymin"],
        "ymax_nm": b["ymax"],
        "clearance_left_nm": clearance_left,
        "clearance_right_nm": clearance_right,
        "clearance_bottom_nm": clearance_bottom,
        "clearance_top_nm": clearance_top,
        "min_clearance_nm": min_clearance,
        "valid_with_margin": str(bool(valid)),
    }


with open(INDEX, newline="", encoding="utf-8") as f:
    candidates = list(csv.DictReader(f))

rows = []

for c in candidates:
    path = ROOT / c["config_path"]
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    geom = cfg["geometry"]

    period_x = float(get_value(geom, ["period_x_nm", "period_nm"], 340))
    period_y = float(get_value(geom, ["period_y_nm", "period_nm"], period_x))

    p1 = geom["nanopillar_1"]
    p2 = geom["nanopillar_2"]

    rows.append(pillar_row(c["candidate_id"], "nanopillar_1", p1, period_x, period_y))
    rows.append(pillar_row(c["candidate_id"], "nanopillar_2", p2, period_x, period_y))

fields = [
    "candidate_id",
    "pillar",
    "period_x_nm",
    "period_y_nm",
    "length_nm",
    "width_nm",
    "rotation_deg",
    "center_x_nm",
    "center_y_nm",
    "xmin_nm",
    "xmax_nm",
    "ymin_nm",
    "ymax_nm",
    "clearance_left_nm",
    "clearance_right_nm",
    "clearance_bottom_nm",
    "clearance_top_nm",
    "min_clearance_nm",
    "valid_with_margin",
]

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

print(f"validation={OUT}")
print(f"rows={len(rows)}")

invalid = [r for r in rows if r["valid_with_margin"] != "True"]
print(f"invalid_pillars={len(invalid)}")

bad_candidates = sorted(set(r["candidate_id"] for r in invalid))
print(f"invalid_candidates={len(bad_candidates)}")
for cid in bad_candidates:
    print(f"invalid_candidate={cid}")

print("")
print("candidate_id\tpillar\tL\tW\trot\tcx\tcy\txmin\txmax\tymin\tymax\tmin_clearance\tvalid")
for r in rows:
    print(
        f"{r['candidate_id']}\t{r['pillar']}\t"
        f"{float(r['length_nm']):.1f}\t{float(r['width_nm']):.1f}\t"
        f"{float(r['rotation_deg']):.1f}\t"
        f"{float(r['center_x_nm']):.1f}\t{float(r['center_y_nm']):.1f}\t"
        f"{float(r['xmin_nm']):.2f}\t{float(r['xmax_nm']):.2f}\t"
        f"{float(r['ymin_nm']):.2f}\t{float(r['ymax_nm']):.2f}\t"
        f"{float(r['min_clearance_nm']):.2f}\t{r['valid_with_margin']}"
    )
