from pathlib import Path
import csv

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")
OUT = ROOT / "outputs/stage10a_h300_single_pillar_pilot"

files = [
    OUT / "xy_sweep_plan.csv",
    OUT / "xy_sweep_results.csv",
]

print("=== Stage10A pilot output inspect ===")

for path in files:
    print("")
    print(f"file={path}")
    print(f"exists={path.exists()}")
    if path.exists():
        with open(path, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        print(f"rows={len(rows)}")
        if rows:
            print("headers=" + ",".join(rows[0].keys()))
            print("first_row:")
            for k, v in rows[0].items():
                print(f"  {k}={v}")

print("")
print("=== phase_delay_summary files ===")
phase_files = sorted(OUT.rglob("*phase_delay*.csv"))
print(f"phase_delay_csv_count={len(phase_files)}")

for path in phase_files[:5]:
    print("")
    print(f"file={path}")
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"rows={len(rows)}")
    if rows:
        print("headers=" + ",".join(rows[0].keys()))
        print("first_row:")
        for k, v in rows[0].items():
            print(f"  {k}={v}")

print("")
print("=== single x/y summary examples ===")
summary_files = sorted(OUT.rglob("*summary*.csv"))
summary_files = [p for p in summary_files if "phase_delay" not in p.name and "xy_sweep_results" not in p.name]
print(f"summary_csv_count={len(summary_files)}")

for path in summary_files[:6]:
    print("")
    print(f"file={path}")
    with open(path, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"rows={len(rows)}")
    if rows:
        print("headers=" + ",".join(rows[0].keys()))
        print("first_row:")
        for k, v in rows[0].items():
            print(f"  {k}={v}")
