from pathlib import Path
import csv, math, cmath

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")
TARGET_BINS = [-180, -120, -60, 0, 60, 120]

IDS = [
    "p200v3_h300_zero_validhelper_helper_far_p55_30x40_r45",
    "p200v3_h300_zero_validhelper_helper_far_m55_30x40_r45",
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

def phase_from_row(row):
    raw = str(row.get("t_alpha_star_from_alpha", "")).strip()
    if raw:
        try:
            return math.degrees(cmath.phase(parse_complex(raw)))
        except Exception:
            pass
    return safe_float(row.get("phase_deg", ""))

def nearest_bin(phase):
    return min(TARGET_BINS, key=lambda b: abs((phase - b + 180) % 360 - 180))

print("candidate_id\tphase_deg\tnearest_bin_deg\ttarget_conversion\topposite_spin_leakage\tconversion_to_leakage_ratio\tearly_pass\topens_0\tresult_csv")

for cid in IDS:
    path = ROOT / "outputs" / "apcd_k6_metagrating_633nm" / "phase_state_candidates" / cid / "results.csv"
    with open(path, newline="", encoding="utf-8") as f:
        row = list(csv.DictReader(f))[0]

    status = str(row.get("status", "")).strip()
    note = str(row.get("note", "")).strip()

    phase = phase_from_row(row)
    nb = nearest_bin(phase) if not math.isnan(phase) else ""
    target = safe_float(row.get("target_conversion", ""))
    leakage = safe_float(row.get("opposite_spin_leakage", ""))
    ratio = safe_float(row.get("conversion_to_leakage_ratio", ""))
    early = bool(target >= 0.5 and leakage <= 0.2 and ratio >= 6)
    opens0 = bool(early and nb == 0)

    print(
        f"{cid}\t{phase:.9f}\t{nb}\t{target:.9f}\t{leakage:.9f}\t"
        f"{ratio:.9f}\t{early}\t{opens0}\t{path}"
    )

    if status == "error" or note:
        print(f"# {cid} status={status} note={note}")
