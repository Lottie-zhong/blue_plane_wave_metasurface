from pathlib import Path
import csv, math, cmath

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")
TARGET_BINS = [-180, -120, -60, 0, 60, 120]

RESULTS = [
    ROOT / r"outputs\apcd_k6_metagrating_633nm\phase_state_candidates\cpk_p196_zgap_dy_in_03\results.csv",
    ROOT / r"outputs\apcd_k6_metagrating_633nm\phase_state_candidates\cpk_p196_zhelper_diag_09\results.csv",
    ROOT / r"outputs\apcd_k6_metagrating_633nm\phase_state_candidates\cpk_p196_zgap_dx_out_02\results.csv",
    ROOT / r"outputs\apcd_k6_metagrating_633nm\phase_state_candidates\cpk_p196_zgap_shear_04\results.csv",
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

for path in RESULTS:
    with open(path, newline="", encoding="utf-8") as f:
        row = list(csv.DictReader(f))[0]

    cid = path.parent.name
    phase = phase_from_row(row)
    nb = nearest_bin(phase)
    target = safe_float(row.get("target_conversion", ""))
    leakage = safe_float(row.get("opposite_spin_leakage", ""))
    ratio = safe_float(row.get("conversion_to_leakage_ratio", ""))
    early = bool(target >= 0.5 and leakage <= 0.2 and ratio >= 6)
    opens0 = bool(early and nb == 0)

    print(
        f"{cid}\t{phase:.9f}\t{nb}\t{target:.9f}\t{leakage:.9f}\t"
        f"{ratio:.9f}\t{early}\t{opens0}\t{path}"
    )
