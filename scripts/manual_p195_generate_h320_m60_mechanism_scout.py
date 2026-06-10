from __future__ import annotations

from pathlib import Path
import csv
import copy
import importlib.util
import yaml

ROOT = Path(__file__).resolve().parents[1]

P190_PLAN = ROOT / "outputs/apcd_k6_active_learning/p190_h320_m120_leakage_recovery_plan.csv"
P192_HELPER = ROOT / "scripts/manual_p192_generate_h320_p060_nearmiss_refine.py"

CONFIG_DIR = ROOT / "configs/apcd_k6_phase_state_candidates"
OUT_PLAN = ROOT / "outputs/apcd_k6_active_learning/p195_h320_m60_mechanism_scout_plan.csv"
REPORT = ROOT / "reports/p195_h320_m60_mechanism_scout_plan.md"

FIXED_H = 320

BASE_IDS = {
    # confirmed -120 early-pass anchor
    "m120_anchor": "p190_h320_m120_crot_p30_p1L_m2_p2L_p2",

    # strong -180 alternative, useful as control
    "m180_strong": "p190_h320_m120_crot_p25_p1W_m2_p2W_p2",
}

# Mechanism scout:
# First goal is -60 phase-hit, not early-pass.
VARIANTS = [
    # Group A: continue common rotation from successful -120 anchor.
    ("A_rot", "m120_anchor", "extra_crot_p10", "continue rotation +10 from -120 anchor", [
        {"type": "rotation", "target": "all_core", "delta": 10.0},
    ]),
    ("A_rot", "m120_anchor", "extra_crot_p20", "continue rotation +20 from -120 anchor", [
        {"type": "rotation", "target": "all_core", "delta": 20.0},
    ]),
    ("A_rot", "m120_anchor", "extra_crot_p30", "continue rotation +30 from -120 anchor", [
        {"type": "rotation", "target": "all_core", "delta": 30.0},
    ]),
    ("A_rot", "m120_anchor", "extra_crot_p40", "continue rotation +40 from -120 anchor", [
        {"type": "rotation", "target": "all_core", "delta": 40.0},
    ]),

    # Group B: rotation + compensation, trying to preserve APCD.
    ("B_rot_comp", "m120_anchor", "extra_crot_p20_p1W_m2_p2W_p2", "rotation + width selectivity recovery", [
        {"type": "rotation", "target": "all_core", "delta": 20.0},
        {"type": "lateral", "target": "p1", "kind": "width", "delta": -2.0},
        {"type": "lateral", "target": "p2", "kind": "width", "delta": 2.0},
    ]),
    ("B_rot_comp", "m120_anchor", "extra_crot_p20_p1L_m2_p2L_p2", "rotation + length selectivity recovery", [
        {"type": "rotation", "target": "all_core", "delta": 20.0},
        {"type": "lateral", "target": "p1", "kind": "length", "delta": -2.0},
        {"type": "lateral", "target": "p2", "kind": "length", "delta": 2.0},
    ]),
    ("B_rot_comp", "m120_anchor", "extra_crot_p30_p1W_m2_p2W_p2", "stronger rotation + width recovery", [
        {"type": "rotation", "target": "all_core", "delta": 30.0},
        {"type": "lateral", "target": "p1", "kind": "width", "delta": -2.0},
        {"type": "lateral", "target": "p2", "kind": "width", "delta": 2.0},
    ]),
    ("B_rot_comp", "m120_anchor", "extra_crot_p30_p1L_m2_p2L_p2", "stronger rotation + length recovery", [
        {"type": "rotation", "target": "all_core", "delta": 30.0},
        {"type": "lateral", "target": "p1", "kind": "length", "delta": -2.0},
        {"type": "lateral", "target": "p2", "kind": "length", "delta": 2.0},
    ]),

    # Group C: dynamic-phase probe from -120 anchor.
    ("C_dynamic", "m120_anchor", "p2L_m8_p2W_p4", "p2 aspect dynamic-phase probe", [
        {"type": "lateral", "target": "p2", "kind": "length", "delta": -8.0},
        {"type": "lateral", "target": "p2", "kind": "width", "delta": 4.0},
    ]),
    ("C_dynamic", "m120_anchor", "p2L_m12_p2W_p6", "stronger p2 aspect dynamic-phase probe", [
        {"type": "lateral", "target": "p2", "kind": "length", "delta": -12.0},
        {"type": "lateral", "target": "p2", "kind": "width", "delta": 6.0},
    ]),

    # Group D: control from strong -180 candidate, test whether rotation chain can pass through -120 toward -60.
    ("D_control", "m180_strong", "extra_crot_p30", "strong -180 control with extra +30 rotation", [
        {"type": "rotation", "target": "all_core", "delta": 30.0},
    ]),
    ("D_control", "m180_strong", "extra_crot_p40", "strong -180 control with extra +40 rotation", [
        {"type": "rotation", "target": "all_core", "delta": 40.0},
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
    p190 = {r["candidate_id"]: r for r in load_csv(P190_PLAN)}

    rows = []

    for group, base_key, variant_id, purpose, ops in VARIANTS:
        base_id = BASE_IDS[base_key]

        if base_id not in p190:
            raise RuntimeError(f"Missing P190 base candidate in plan: {base_id}")

        base_config_path = ROOT / p190[base_id]["config_path"]

        with open(base_config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)

        cfg = copy.deepcopy(cfg)
        h.set_all_heights(cfg, FIXED_H)
        changed = h.apply_ops(cfg, ops)
        h.set_all_heights(cfg, FIXED_H)

        candidate_id = h.sanitize(f"p195_h320_m60_{group}_{base_key}_{variant_id}")
        config_path = CONFIG_DIR / f"{candidate_id}.yaml"

        cfg.setdefault("project", {})
        cfg["project"]["stage"] = "p195_h320_m60_mechanism_scout"

        cfg.setdefault("boundary", {})
        cfg["boundary"]["fixed_height_nm"] = FIXED_H
        cfg["boundary"]["fabrication_aware_same_height"] = True
        cfg["boundary"]["not_k6_supercell"] = True
        cfg["boundary"]["not_steering_result"] = True
        cfg["boundary"]["not_micro_led_result"] = True
        cfg["boundary"]["p195_m60_mechanism_scout"] = True

        cfg.setdefault("metadata", {})
        cfg["metadata"]["p195_group"] = group
        cfg["metadata"]["p195_base_key"] = base_key
        cfg["metadata"]["p195_base_candidate_id"] = base_id
        cfg["metadata"]["p195_variant_id"] = variant_id
        cfg["metadata"]["p195_purpose"] = purpose
        cfg["metadata"]["p195_fixed_height_nm"] = FIXED_H
        cfg["metadata"]["p195_success_criterion"] = "phase-hit first: nearest_bin=-60 and target_conversion>0.5"
        cfg["metadata"]["p195_ops"] = ops
        cfg["metadata"]["p195_changed_fields"] = changed[:60]

        h.update_result_dir(cfg, candidate_id)
        h.dump_yaml(cfg, config_path)

        rows.append({
            "candidate_id": candidate_id,
            "group": group,
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
        "# P195 h320 -60 mechanism scout plan",
        "",
        "## Scope",
        "",
        "- Fixed-height h320 single-dimer candidates only.",
        "- Target: find -60 phase-hit first.",
        "- Success criterion for this scout: nearest_bin=-60 and target_conversion>0.5.",
        "- Early-pass is welcome but not required.",
        "- No height scan.",
        "- No K=6 supercell.",
        "- No steering claim.",
        "",
        f"generated_candidates: {len(rows)}",
        "",
        "## Candidate queue",
        "",
        "| group | base | variant | candidate | changed fields | purpose |",
        "|---|---|---|---|---:|---|",
    ]

    for r in rows:
        lines.append(
            f"| {r['group']} | {r['base_key']} | {r['variant_id']} | "
            f"`{r['candidate_id']}` | {r['changed_field_count']} | {r['purpose']} |"
        )

    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"plan={OUT_PLAN}")
    print(f"report={REPORT}")
    print(f"generated_candidates={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
