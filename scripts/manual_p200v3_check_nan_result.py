from pathlib import Path
import csv

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")

cid = "p200v3_h300_zero_validhelper_helper_diag_p35_30x40_r45"
base = ROOT / "outputs" / "apcd_k6_metagrating_633nm" / "phase_state_candidates" / cid

files = [
    base / "results.csv",
    base / "summary.json",
    base / "run.log",
    base / "error.log",
]

print("file\texists\tsize_bytes\theader\tfirst_data_row")

for p in files:
    exists = p.exists()
    size = p.stat().st_size if exists else 0
    header = ""
    first = ""

    if exists and p.name.endswith(".csv"):
        try:
            with open(p, newline="", encoding="utf-8") as f:
                reader = csv.reader(f)
                header = " | ".join(next(reader, []))
                first = " | ".join(next(reader, []))
        except Exception as e:
            first = f"READ_ERROR: {e}"

    elif exists and size > 0:
        try:
            txt = p.read_text(encoding="utf-8", errors="replace").splitlines()
            header = txt[0][:240] if txt else ""
            first = txt[1][:240] if len(txt) > 1 else ""
        except Exception as e:
            first = f"READ_ERROR: {e}"

    print(f"{p}\t{exists}\t{size}\t{header}\t{first}")
