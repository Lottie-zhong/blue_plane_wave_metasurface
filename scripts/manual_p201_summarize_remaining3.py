from pathlib import Path
import csv, math, cmath, yaml

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")
TARGET_BINS = [-180, -120, -60, 0, 60, 120]

IDS = [
    "p201_h300_60to0_B_common_area_down_aspect_restore_p1p2_Lm4_Wp2",
    "p201_h300_60to0_C_relative_rotation_micro_bias_p2rot_m2p5",
    "p201_h300_60to0_C_relative_rotation_micro_bias_p1rot_m2p5_p2rot_p2p5",
]

def safe_float(x, default=float("nan")):
    try:
        if x is None or str(x).strip() == "":
            return default
        return float(x)
    except Exception:
        return default

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

def abs_to_zero(phase):
    if math.isnan(phase):
        return float("nan")
    return abs((phase + 180) % 360 - 180)

def classify(phase, nb, target, leakage, ratio, early):
    a0 = abs_to_zero(phase)

    if math.isnan(phase) or math.isnan(target) or math.isnan(leakage) or math.isnan(ratio):
        return "invalid_or_error"

    if nb == 0 and early:
        return "primary_opens_0"

    if 30 < a0 <= 45 and early:
        return "healthy_trend_to_0"

    if a0 <= 45 and leakage <= 0.25 and 4 <= ratio < 6:
        return "useful_nearmiss"

    if a0 <= 45 and leakage >= 0.35:
        return "phase_pull_selectivity_failed"

    if early and nb == 60:
        return "stays_healthy_60"

    if early:
        return "early_but_not_toward_0"

    return "other_failed"

print("candidate_id\tphase_deg\tnearest_bin_deg\ttarget_conversion\topposite_spin_leakage\tconversion_to_leakage_ratio\tearly_pass\topens_0\topens_60\tresult_csv\tstatus\tnote\tgroup\tvariant\tsource_anchor\tp201_category")

for cid in IDS:
    result_csv = ROOT / "outputs/apcd_k6_metagrating_633nm/phase_state_candidates" / cid / "results.csv"
    cfg_path = ROOT / "configs/apcd_k6_phase_state_candidates" / f"{cid}.yaml"

    group = ""
    variant = ""
    source_anchor = ""
    if cfg_path.exists():
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        meta = cfg.get("metadata", {})
        group = meta.get("p201_group", "")
        variant = meta.get("p201_variant", "")
        source_anchor = meta.get("p201_source_anchor", "")

    phase = target = leakage = ratio = float("nan")
    nb = ""
    status = "missing_result"
    note = ""

    if result_csv.exists():
        with open(result_csv, newline="", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        row = rows[0] if rows else {}
        status = str(row.get("status", "")).strip()
        note = str(row.get("note", "")).strip()
        phase = phase_from_row(row)
        nb = nearest_bin(phase)
        target = safe_float(row.get("target_conversion", ""))
        leakage = safe_float(row.get("opposite_spin_leakage", ""))
        ratio = safe_float(row.get("conversion_to_leakage_ratio", ""))

    early = bool(target >= 0.5 and leakage <= 0.2 and ratio >= 6)
    opens0 = bool(early and nb == 0)
    opens60 = bool(early and nb == 60)
    cat = classify(phase, nb, target, leakage, ratio, early)

    print(
        f"{cid}\t{'' if math.isnan(phase) else f'{phase:.9f}'}\t{nb}\t"
        f"{'' if math.isnan(target) else f'{target:.9f}'}\t"
        f"{'' if math.isnan(leakage) else f'{leakage:.9f}'}\t"
        f"{'' if math.isnan(ratio) else f'{ratio:.9f}'}\t"
        f"{early}\t{opens0}\t{opens60}\t{result_csv}\t"
        f"{status}\t{note}\t{group}\t{variant}\t{source_anchor}\t{cat}"
    )
