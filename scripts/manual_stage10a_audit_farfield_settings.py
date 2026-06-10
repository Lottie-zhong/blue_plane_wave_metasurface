from pathlib import Path
import csv
import yaml

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")
PLAN = ROOT / "outputs/stage10a_h300_single_pillar_pilot/xy_sweep_plan.csv"

EXPECTED = {
    "projection_direction": "auto",
    "material_index": "auto",
    "far_field_filter": 1,
    "resolution_2d": 1001,
    "resolution_3d": 1001,
}

with open(PLAN, newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

bad = []
checked = 0

for r in rows:
    for pol in ("x", "y"):
        path = ROOT / r[f"{pol}_config"]
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        ff = cfg.get("far_field", {})
        checked += 1

        for k, expected in EXPECTED.items():
            actual = ff.get(k)
            if actual != expected:
                bad.append({
                    "case_id": r["case_id"],
                    "pol": pol,
                    "config": str(path),
                    "field": k,
                    "expected": expected,
                    "actual": actual,
                })

print(f"checked_configs={checked}")
print(f"far_field_expected={EXPECTED}")
print(f"bad_count={len(bad)}")

if bad:
    print("case_id\tpol\tfield\texpected\tactual\tconfig")
    for b in bad:
        print(
            f"{b['case_id']}\t{b['pol']}\t{b['field']}\t"
            f"{b['expected']}\t{b['actual']}\t{b['config']}"
        )
else:
    print("status=all_far_field_settings_match_image")
