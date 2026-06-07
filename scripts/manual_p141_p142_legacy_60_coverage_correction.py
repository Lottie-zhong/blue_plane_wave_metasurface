from pathlib import Path
import pandas as pd
from datetime import datetime

root = Path(r"D:\project\blue_plane_wave_metasurface")
out_dir = root / "outputs" / "apcd_k6_active_learning"
report_dir = root / "reports"
out_dir.mkdir(parents=True, exist_ok=True)
report_dir.mkdir(parents=True, exist_ok=True)

src = out_dir / "manual_legacy_60_bin_verification.csv"
if not src.exists():
    raise FileNotFoundError(f"Missing verification CSV: {src}")

df = pd.read_csv(src)

required = [
    "candidate_id",
    "phase_deg_recomputed_from_t_alpha_star",
    "nearest_bin",
    "target_conversion",
    "opposite_spin_leakage",
    "conversion_to_leakage_ratio",
    "early_pass",
    "opens_60",
]
missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Missing columns in verification CSV: {missing}")

# Re-validate using current early-pass criteria.
df["revalidated_early_pass"] = (
    (df["target_conversion"] >= 0.5)
    & (df["opposite_spin_leakage"] <= 0.2)
    & (df["conversion_to_leakage_ratio"] >= 6)
)

df["revalidated_opens_60"] = (
    (df["nearest_bin"] == 60)
    & (df["revalidated_early_pass"])
)

if not df["revalidated_opens_60"].any():
    raise RuntimeError("No verified legacy candidate opens 60 under current criteria.")

verified = df[df["revalidated_opens_60"]].copy()

# Official补录文件
verification_path = out_dir / "combined_phase_knob_p141_legacy_60_bin_verification.csv"
coverage_path = out_dir / "combined_phase_knob_phase_state_coverage_p142.csv"
decision_path = out_dir / "combined_phase_knob_p142_coverage_correction_decision.csv"

verification_report = report_dir / "combined_phase_knob_p141_legacy_60_bin_verification.md"
coverage_report = report_dir / "combined_phase_knob_p142_coverage_correction.md"

df.to_csv(verification_path, index=False)

coverage_rows = [
    {"target_bin_deg": -180, "status": "early_pass", "source": "existing_stage09_coverage"},
    {"target_bin_deg": -120, "status": "early_pass", "source": "existing_stage09_coverage"},
    {"target_bin_deg": -60, "status": "early_pass", "source": "existing_stage09_coverage"},
    {"target_bin_deg": 0, "status": "missing", "source": "current_remaining_gap"},
    {"target_bin_deg": 60, "status": "early_pass", "source": "legacy_v5_recomputed_phase_from_t_alpha_star"},
    {"target_bin_deg": 120, "status": "early_pass", "source": "existing_stage09_coverage"},
]
pd.DataFrame(coverage_rows).to_csv(coverage_path, index=False)

decision_rows = [{
    "decision": "legacy_60_bin_accepted",
    "is_new_fdtd": False,
    "early_pass_bins_after_correction": "[-180, -120, -60, 60, 120]",
    "remaining_missing_bins_after_correction": "[0]",
    "basis": "legacy v5 raw FDTD outputs exist; phase recomputed from t_alpha_star_from_alpha; current early-pass criteria satisfied",
    "accepted_candidates": ";".join(verified["candidate_id"].astype(str).tolist()),
}]
pd.DataFrame(decision_rows).to_csv(decision_path, index=False)

with open(verification_report, "w", encoding="utf-8") as f:
    f.write("# P141 Legacy 60-bin verification\n\n")
    f.write("This is a schema/coverage correction, not a new FDTD run.\n\n")
    f.write("Legacy `results.csv` files do not contain `phase_deg`; phase was recomputed from `t_alpha_star_from_alpha`.\n\n")
    f.write("## Verified candidates\n\n")
    for _, r in verified.iterrows():
        f.write(f"- `{r['candidate_id']}`: ")
        f.write(f"phase={r['phase_deg_recomputed_from_t_alpha_star']:.4f} deg, ")
        f.write(f"nearest={int(r['nearest_bin'])}, ")
        f.write(f"target={r['target_conversion']:.6f}, ")
        f.write(f"leakage={r['opposite_spin_leakage']:.6f}, ")
        f.write(f"ratio={r['conversion_to_leakage_ratio']:.6f}, ")
        f.write("early_pass=True, opens_60=True\n")
    f.write("\n## Decision\n\n")
    f.write("The 60 deg bin is accepted as legacy-verified early-pass coverage.\n")

with open(coverage_report, "w", encoding="utf-8") as f:
    f.write("# P142 Coverage correction after legacy 60-bin verification\n\n")
    f.write("## Decision\n\n")
    f.write("- Accepted 60 deg as an early-pass bin based on verified legacy v5 raw FDTD evidence.\n")
    f.write("- This is not a new FDTD run.\n")
    f.write("- Phase was recomputed from the target-channel complex amplitude `t_alpha_star_from_alpha`.\n\n")
    f.write("## Updated coverage\n\n")
    f.write("- early-pass bins: `[-180, -120, -60, 60, 120]`\n")
    f.write("- remaining missing bins: `[0]`\n\n")
    f.write("## Accepted legacy candidates\n\n")
    for _, r in verified.iterrows():
        f.write(f"- `{r['candidate_id']}`: phase={r['phase_deg_recomputed_from_t_alpha_star']:.4f} deg, ")
        f.write(f"target={r['target_conversion']:.6f}, leakage={r['opposite_spin_leakage']:.6f}, ")
        f.write(f"ratio={r['conversion_to_leakage_ratio']:.6f}\n")

print("Saved:")
print(verification_path)
print(coverage_path)
print(decision_path)
print(verification_report)
print(coverage_report)

print("\nUpdated coverage:")
print("early-pass bins = [-180, -120, -60, 60, 120]")
print("remaining missing bins = [0]")
