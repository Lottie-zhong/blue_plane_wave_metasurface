from __future__ import annotations

from pathlib import Path
import csv
import copy
import importlib.util
import yaml

ROOT = Path(__file__).resolve().parents[1]

P192_PLAN = ROOT / "outputs/apcd_k6_active_learning/p192_h320_p060_nearmiss_refine_plan.csv"
P192_HELPER = ROOT / "scripts/manual_p192_generate_h320_p060_nearmiss_refine.py"

CONFIG_DIR = ROOT / "configs/apcd_k6_phase_state_candidates"
OUT_PLAN = ROOT / "outputs/apcd_k6_active_learning/p193_h320_p060_boundary_tiny_recovery_plan.csv"
REPORT = ROOT / "reports/p193_h320_p060_boundary_tiny_recovery_plan.md"

FIXED_H = 320

BASE_IDS = {
    # best ratio, but phase just crossed to 120-bin: phase≈90.18, ratio≈5.70
    "b_ratio": "p192_h320_p060_best_p2W_p1",

    # still in 60-bin: phase≈89.78, ratio≈5.51
    "b_60": "p192_h320_p060_best_p1W_m1_p2W_p1",

    # also in 60-bin: phase≈89.27, ratio≈5.23
    "b_60low": "p192_h320_p060_best_p1W_m1",
}

# Very tiny corrections only.
# Goal: keep phase < 90 and reduce leakage just enough for ratio >= 6.
VARIANTS = [
    # From best ratio candidate, pull phase back below 90 with tiny common-rotation rollback.
    ("b_ratio", "crot_m0p25", "pull 90.18 deg just below 90", [
        {"type": "rotation", "target": "all_core", "delta": -0.25},
    ]),
    ("b_ratio", "crot_m0p5", "slightly stronger phase rollback", [
        {"type": "rotation", "target": "all_core", "delta": -0.5},
    ]),
    ("b_ratio", "crot_m0p25_p2W_p0p5", "phase rollback plus tiny p2 width leakage recovery", [
        {"type": "rotation", "target": "all_core", "delta": -0.25},
        {"type": "lateral", "target": "p2", "kind": "width", "delta": 0.5},
    ]),

    # From 60-bin candidate, try tiny width recovery.
    ("b_60", "p2W_p0p5", "tiny p2 width recovery while staying 60-bin", [
        {"type": "lateral", "target": "p2", "kind": "width", "delta": 0.5},
    ]),
    ("b_60", "p2W_p1", "p2 width recovery", [
        {"type": "lateral", "target": "p2", "kind": "width", "delta": 1.0},
    ]),
    ("b_60", "p1W_m0p5_p2W_p0p5", "tiny balanced width contrast", [
        {"type": "lateral", "target": "p1", "kind": "width", "delta": -0.5},
        {"type": "lateral", "target": "p2", "kind": "width", "delta": 0.5},
    ]),
    ("b_60", "p1W_m0p5", "tiny p1 width reduction", [
        {"type": "lateral", "target": "p1", "kind": "width", "delta": -0.5},
    ]),

    # One safety candidate from lower phase margin.
    ("b_60low", "p2W_p1", "lower phase 60-bin candidate plus p2 width recovery", [
        {"type": "lateral", "target": "p2", "kind": "width", "delta": 1.0},
    ]),
]


def import_helper(path: Path):
    spec = importlib.util.spec_from_file_location("p192_helper", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import helper: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def load_csv(path: Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def main() -> int:
    h = import_helper(P192_HELPER)
    p192 = {r["candidate_id"]: r for r in load_csv(P192_PLAN)}

    rows = []

    for base_key, variant_id, purpose, ops in VARIANTS:
        base_id = BASE_IDS[base_key]
        if base_id not in p192:
            raise RuntimeError(f"Missing P192 base candidate in plan: {base_id}")

        base_config_path = ROOT / p192[base_id]["config_path"]

        with open(base_config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        cfg = copy.deepcopy(cfg)
        h.set_all_heights(cfg, FIXED_H)
        changed = h.apply_ops(cfg, ops)
        h.set_all_heights(cfg, FIXED_H)

        candidate_id = h.sanitize(f"p193_h320_p060_{base_key}_{variant_id}")
        config_path = CONFIG_DIR / f"{candidate_id}.yaml"

        cfg.setdefault("project", {})
        cfg["project"]["stage"] = "p193_h320_p060_boundary_tiny_recovery"

        cfg.setdefault("boundary", {})
        cfg["boundary"]["fixed_height_nm"] = FIXED_H
        cfg["boundary"]["fabrication_aware_same_height"] = True
        cfg["boundary"]["not_k6_supercell"] = True
        cfg["boundary"]["not_steering_result"] = True
        cfg["boundary"]["not_micro_led_result"] = True
        cfg["boundary"]["p193_p060_boundary_tiny_recovery"] = True

        cfg.setdefault("metadata", {})
        cfg["metadata"]["p193_base_key"] = base_key
        cfg["metadata"]["p193_base_candidate_id"] = base_id
        cfg["metadata"]["p193_variant_id"] = variant_id
        cfg["metadata"]["p193_purpose"] = purpose
        cfg["metadata"]["p193_fixed_height_nm"] = FIXED_H
        cfg["metadata"]["p193_ops"] = ops
        cfg["metadata"]["p193_changed_fields"] = changed[:50]

        h.update_result_dir(cfg, candidate_id)
        h.dump_yaml(cfg, config_path)

        rows.append({
            "candidate_id": candidate_id,
            "base_key": base_key,
            "variant_id": variant_id,
            "purpose": purpose,
            "base_candidate_id": base_id,
            "fixed_height_nm": FIXED_H,
            "config_path": str(config_path.relative_to(ROOT)).replace("\\", "/"),
            "changed_field_count": len(changed),
            "changed_fields_preview": " | ".join(changed[:8]),
        })

    OUT_PLAN.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PLAN, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# P193 h320 p060 boundary tiny recovery plan",
        "",
        "## Scope",
        "",
        "- Fixed-height h320 single-dimer candidates only.",
        "- Target: recover early-pass 60 from P192 near-boundary candidates.",
        "- Tiny changes only.",
        "- No height scan.",
        "- No K=6 supercell.",
        "- No steering claim.",
        "",
        f"generated_candidates: {len(rows)}",
        "",
        "## Candidate queue",
        "",
        "| base | variant | candidate | changed fields | purpose |",
        "|---|---|---|---:|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r['base_key']} | {r['variant_id']} | `{r['candidate_id']}` | "
            f"{r['changed_field_count']} | {r['purpose']} |"
        )

    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"plan={OUT_PLAN}")
    print(f"report={REPORT}")
    print(f"generated_candidates={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
