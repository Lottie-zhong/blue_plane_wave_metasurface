from __future__ import annotations

from pathlib import Path
import csv
import copy
import importlib.util
import yaml

ROOT = Path(r"D:\project\blue_plane_wave_metasurface")

BASE_CONFIG = ROOT / "configs/apcd_k6_phase_state_candidates/next_zero_rot_anchor_03.yaml"
P192_HELPER = ROOT / "scripts/manual_p192_generate_h320_p060_nearmiss_refine.py"

CONFIG_DIR = ROOT / "configs/apcd_k6_phase_state_candidates"
OUT_PLAN = ROOT / "outputs/apcd_k6_active_learning/p199_h300_zero_selectivity_recovery_plan.csv"
REPORT = ROOT / "reports/p199_h300_zero_selectivity_recovery_plan.md"

FIXED_H = 300

VARIANTS = [
    # A: common rotation rollback toward the known h300 60° early-pass anchor.
    ("A_crot_rollback", "crot_p2p5", "common rotation rollback +2.5°, try reduce leakage while staying 0-bin", [
        {"type": "rotation", "target": "all_core", "delta": 2.5},
    ]),
    ("A_crot_rollback", "crot_p5", "common rotation rollback +5°, stronger selectivity recovery, still likely near 0-bin", [
        {"type": "rotation", "target": "all_core", "delta": 5.0},
    ]),
    ("A_crot_rollback", "crot_p7p5", "common rotation rollback +7.5°, boundary probe before phase returns to 60-bin", [
        {"type": "rotation", "target": "all_core", "delta": 7.5},
    ]),

    # B: differential rotation. Try to recover APCD interference without fully shifting global PB phase.
    ("B_diff_rot", "p1_p5", "rotate p1 +5 only, differential APCD recovery", [
        {"type": "rotation", "target": "p1", "delta": 5.0},
    ]),
    ("B_diff_rot", "p2_p5", "rotate p2 +5 only, differential APCD recovery", [
        {"type": "rotation", "target": "p2", "delta": 5.0},
    ]),
    ("B_diff_rot", "p1_p5_p2_m2p5", "increase relative-angle asymmetry while keeping phase near 0", [
        {"type": "rotation", "target": "p1", "delta": 5.0},
        {"type": "rotation", "target": "p2", "delta": -2.5},
    ]),
    ("B_diff_rot", "p1_m2p5_p2_p5", "opposite differential rotation recovery", [
        {"type": "rotation", "target": "p1", "delta": -2.5},
        {"type": "rotation", "target": "p2", "delta": 5.0},
    ]),

    # C: lateral geometry compensation toward stronger h300 early-pass family.
    ("C_geom_comp", "p1_120x58", "move p1 geometry toward h300 p000 early-pass shape", [
        {"type": "lateral_set", "target": "p1", "length": 120.0, "width": 58.0},
    ]),
    ("C_geom_comp", "p2_76x137", "move p2 geometry toward h300 p000 early-pass shape", [
        {"type": "lateral_set", "target": "p2", "length": 76.0, "width": 137.0},
    ]),
    ("C_geom_comp", "p1_120x58_p2_76x137", "move both p1/p2 toward known stronger h300 early-pass geometry", [
        {"type": "lateral_set", "target": "p1", "length": 120.0, "width": 58.0},
        {"type": "lateral_set", "target": "p2", "length": 76.0, "width": 137.0},
    ]),

    # D: tiny position/gap correction. next_zero uses y=±103 while early-pass uses y=±101.
    ("D_pos_gap", "y_to_101", "restore y-position to h300 early-pass anchor, tiny coupling correction", [
        {"type": "position_set", "target": "p1", "x": 65.0, "y": 101.0},
        {"type": "position_set", "target": "p2", "x": -65.0, "y": -101.0},
    ]),
    ("D_pos_gap", "y_to_101_crot_p2p5", "position correction plus mild rotation rollback", [
        {"type": "position_set", "target": "p1", "x": 65.0, "y": 101.0},
        {"type": "position_set", "target": "p2", "x": -65.0, "y": -101.0},
        {"type": "rotation", "target": "all_core", "delta": 2.5},
    ]),
]


def import_helper(path: Path):
    spec = importlib.util.spec_from_file_location("p192_helper", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot import helper: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def sanitize(s: str) -> str:
    return "".join(c if c.isalnum() or c == "_" else "_" for c in s).strip("_")


def find_pillars(cfg: dict):
    pillars = []

    def rec(x):
        if isinstance(x, dict):
            if "length_nm" in x and "width_nm" in x:
                pillars.append(x)
            for v in x.values():
                rec(v)
        elif isinstance(x, list):
            for v in x:
                rec(v)

    rec(cfg)

    # unique physical pillars only
    out = []
    seen = set()
    for p in pillars:
        key = (
            p.get("length_nm"), p.get("width_nm"), p.get("height_nm"),
            p.get("rotation_deg"), p.get("x_nm"), p.get("y_nm")
        )
        if key not in seen:
            seen.add(key)
            out.append(p)
    return out[:2]


def apply_custom_ops(cfg: dict, ops: list[dict]) -> list[str]:
    changed = []
    pillars = find_pillars(cfg)
    if len(pillars) < 2:
        raise RuntimeError("Could not locate p1/p2 pillars")

    target_map = {
        "p1": [pillars[0]],
        "p2": [pillars[1]],
        "all_core": pillars[:2],
    }

    for op in ops:
        typ = op["type"]
        targets = target_map[op["target"]]

        if typ == "lateral_set":
            for p in targets:
                p["length_nm"] = float(op["length"])
                p["width_nm"] = float(op["width"])
                changed.append(f"{op['target']}.length_width_set={op['length']}x{op['width']}")

        elif typ == "position_set":
            for p in targets:
                p["x_nm"] = float(op["x"])
                p["y_nm"] = float(op["y"])
                changed.append(f"{op['target']}.position_set=({op['x']},{op['y']})")

        else:
            raise RuntimeError(f"Unsupported custom op: {typ}")

    return changed


def main() -> int:
    h = import_helper(P192_HELPER)

    with open(BASE_CONFIG, "r", encoding="utf-8") as f:
        base = yaml.safe_load(f)

    rows = []

    for group, variant_id, purpose, ops in VARIANTS:
        cfg = copy.deepcopy(base)
        h.set_all_heights(cfg, FIXED_H)

        helper_ops = [op for op in ops if op["type"] == "rotation"]
        custom_ops = [op for op in ops if op["type"] != "rotation"]

        changed = []
        if helper_ops:
            changed.extend(h.apply_ops(cfg, helper_ops))
        if custom_ops:
            changed.extend(apply_custom_ops(cfg, custom_ops))

        h.set_all_heights(cfg, FIXED_H)

        candidate_id = sanitize(f"p199_h300_zero_{group}_{variant_id}")
        config_path = CONFIG_DIR / f"{candidate_id}.yaml"

        cfg.setdefault("project", {})
        cfg["project"]["stage"] = "p199_h300_zero_selectivity_recovery"

        cfg.setdefault("boundary", {})
        cfg["boundary"]["fixed_height_nm"] = FIXED_H
        cfg["boundary"]["fabrication_aware_same_height"] = True
        cfg["boundary"]["not_k6_supercell"] = True
        cfg["boundary"]["not_steering_result"] = True
        cfg["boundary"]["not_micro_led_result"] = True
        cfg["boundary"]["p199_h300_zero_selectivity_recovery"] = True

        cfg.setdefault("metadata", {})
        cfg["metadata"]["p199_base_candidate_id"] = "next_zero_rot_anchor_03"
        cfg["metadata"]["p199_group"] = group
        cfg["metadata"]["p199_variant_id"] = variant_id
        cfg["metadata"]["p199_purpose"] = purpose
        cfg["metadata"]["p199_fixed_height_nm"] = FIXED_H
        cfg["metadata"]["p199_success"] = "nearest_bin=0, target>=0.5, leakage<=0.2, ratio>=6"
        cfg["metadata"]["p199_ops"] = ops
        cfg["metadata"]["p199_changed_fields"] = changed[:80]

        h.update_result_dir(cfg, candidate_id)
        h.dump_yaml(cfg, config_path)

        rows.append({
            "candidate_id": candidate_id,
            "group": group,
            "variant_id": variant_id,
            "purpose": purpose,
            "config_path": str(config_path.relative_to(ROOT)).replace("\\", "/"),
        })

    OUT_PLAN.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PLAN, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# P199 h300 zero selectivity recovery plan",
        "",
        "## Scope",
        "",
        "- Fixed height h300 only.",
        "- Base: next_zero_rot_anchor_03.",
        "- Goal: recover APCD selectivity while keeping nearest_bin=0.",
        "- No FDTD in this generation step.",
        "- No K6 / steering claim.",
        "",
        "## Candidate queue",
        "",
        "| candidate_id | group | variant_id | purpose | config_path |",
        "|---|---|---|---|---|",
    ]

    for r in rows:
        lines.append(
            f"| `{r['candidate_id']}` | {r['group']} | {r['variant_id']} | {r['purpose']} | `{r['config_path']}` |"
        )

    REPORT.write_text("\n".join(lines), encoding="utf-8")

    print(f"plan={OUT_PLAN}")
    print(f"report={REPORT}")
    print("")
    print("candidate_id\tgroup\tvariant_id\tpurpose\tconfig_path")
    for r in rows:
        print(f"{r['candidate_id']}\t{r['group']}\t{r['variant_id']}\t{r['purpose']}\t{r['config_path']}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
