from __future__ import annotations

from pathlib import Path
import csv
import yaml
import copy

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")

TEMPLATE = ROOT / "configs/apcd_k6_phase_state_candidates/p185_fh300_p060_from_aggr_lhs_retention_dy_05.yaml"
CONFIG_DIR = ROOT / "configs/apcd_k6_phase_state_candidates"
OUT_DIR = ROOT / "outputs/stage10b_h300_role_pair_dimer"
INDEX = OUT_DIR / "stage10b_h300_role_pair_candidates.csv"

if not TEMPLATE.exists():
    raise FileNotFoundError(TEMPLATE)

with open(TEMPLATE, "r", encoding="utf-8") as f:
    template = yaml.safe_load(f)

# Candidate format:
# id, family, p1L, p1W, theta1, p2L, p2W, theta2, note
candidates = [
    # Control / role-preserving baseline neighborhood
    ("s10b_control_original_p060", "control", 115, 55, 67.5, 75, 135, 112.5, "known h300 60deg healthy anchor geometry; rerun as control if needed"),

    # Same-sign p2 role preserving candidates
    ("s10b_same_01_p1top_p2_80x130", "same_sign_p2", 125, 45, 67.5, 80, 130, 112.5, "p1 top role + p2 same-sign near original"),
    ("s10b_same_02_p1_120x50_p2_85x130", "same_sign_p2", 120, 50, 67.5, 85, 130, 112.5, "p1 stable + p2 same-sign higher ret"),
    ("s10b_same_03_p1_115x70_p2_65x150", "same_sign_p2", 115, 70, 67.5, 65, 150, 112.5, "p1 common positive shift + p2 same-sign"),
    ("s10b_same_04_p1_130x55_p2_70x140", "same_sign_p2", 130, 55, 67.5, 70, 140, 112.5, "p1 positive common + p2 same-sign"),
    ("s10b_same_05_p1_125x50_p2_75x135", "same_sign_p2", 125, 50, 67.5, 75, 135, 112.5, "p1 substitute while preserving original p2"),

    # Axis-swapped p2 branch, original theta2
    ("s10b_axis_01_90x145_theta112", "axis_swapped_p2_origtheta", 115, 55, 67.5, 90, 145, 112.5, "best p2 axis-swapped branch, original theta2"),
    ("s10b_axis_02_90x150_theta112", "axis_swapped_p2_origtheta", 115, 55, 67.5, 90, 150, 112.5, "balanced p2 axis-swapped branch, original theta2"),
    ("s10b_axis_03_85x150_theta112", "axis_swapped_p2_origtheta", 125, 45, 67.5, 85, 150, 112.5, "p1 top + high-quality p2 axis-swapped, original theta2"),
    ("s10b_axis_04_85x145_theta112", "axis_swapped_p2_origtheta", 120, 50, 67.5, 85, 145, 112.5, "p1 stable + p2 axis-swapped, original theta2"),

    # Axis-swapped p2 branch, theta2 compensated by -90 deg
    ("s10b_axis_01_90x145_theta022", "axis_swapped_p2_rotcomp", 115, 55, 67.5, 90, 145, 22.5, "best p2 axis-swapped branch, theta2 compensated"),
    ("s10b_axis_02_90x150_theta022", "axis_swapped_p2_rotcomp", 115, 55, 67.5, 90, 150, 22.5, "balanced p2 axis-swapped branch, theta2 compensated"),
    ("s10b_axis_03_85x150_theta022", "axis_swapped_p2_rotcomp", 125, 45, 67.5, 85, 150, 22.5, "p1 top + high-quality p2 axis-swapped, theta2 compensated"),
    ("s10b_axis_04_85x145_theta022", "axis_swapped_p2_rotcomp", 120, 50, 67.5, 85, 145, 22.5, "p1 stable + p2 axis-swapped, theta2 compensated"),
]

OUT_DIR.mkdir(parents=True, exist_ok=True)
CONFIG_DIR.mkdir(parents=True, exist_ok=True)

rows = []

for cid, family, p1L, p1W, theta1, p2L, p2W, theta2, note in candidates:
    cfg = copy.deepcopy(template)

    cfg.setdefault("project", {})
    cfg["project"]["stage"] = "stage10b_h300_jones_role_pair_dimer_validation"

    cfg.setdefault("metadata", {})
    cfg["metadata"]["candidate_id"] = cid
    cfg["metadata"]["candidate_family"] = family
    cfg["metadata"]["description"] = "Stage10B h300 Jones-role constrained dimer validation"
    cfg["metadata"]["notes"] = note
    cfg["metadata"]["not_phase_ramp_supercell"] = True

    geom = cfg["geometry"]
    p1 = geom["nanopillar_1"]
    p2 = geom["nanopillar_2"]

    p1["length_nm"] = float(p1L)
    p1["width_nm"] = float(p1W)
    p1["height_nm"] = 300.0
    p1["rotation_deg"] = float(theta1)

    p2["length_nm"] = float(p2L)
    p2["width_nm"] = float(p2W)
    p2["height_nm"] = 300.0
    p2["rotation_deg"] = float(theta2)

    cfg.setdefault("output", {})
    result_dir = f"outputs/stage10b_h300_role_pair_dimer/{cid}"
    cfg["output"]["result_dir"] = result_dir

    out_path = CONFIG_DIR / f"{cid}.yaml"
    out_path.write_text(yaml.safe_dump(cfg, sort_keys=False, allow_unicode=True), encoding="utf-8")

    rows.append({
        "candidate_id": cid,
        "family": family,
        "config_path": str(out_path.relative_to(ROOT)),
        "result_dir": result_dir,
        "result_csv": f"{result_dir}/results.csv",
        "p1_length_nm": p1L,
        "p1_width_nm": p1W,
        "theta1_deg": theta1,
        "p2_length_nm": p2L,
        "p2_width_nm": p2W,
        "theta2_deg": theta2,
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
    "note",
]

with open(INDEX, "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=fields)
    w.writeheader()
    w.writerows(rows)

print(f"template={TEMPLATE}")
print(f"written_index={INDEX}")
print(f"candidate_count={len(rows)}")
print("")
print("candidate_id\tfamily\tp1\tp2\ttheta1\ttheta2\tconfig")
for r in rows:
    print(
        f"{r['candidate_id']}\t{r['family']}\t"
        f"{r['p1_length_nm']}x{r['p1_width_nm']}\t"
        f"{r['p2_length_nm']}x{r['p2_width_nm']}\t"
        f"{r['theta1_deg']}\t{r['theta2_deg']}\t"
        f"{r['config_path']}"
    )
